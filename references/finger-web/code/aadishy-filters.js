/**
 * filters.js - Real-Time Optical, Icy Crystal, Liquid Chrome with Glowing Particles, X-Ray & Graphic Shaders
 * High-performance WebGL & Canvas ImageData processing for AR Portal.
 */

// Helper to compute grayscale luminance
function getLuminance(r, g, b) {
    return 0.299 * r + 0.587 * g + 0.114 * b;
}

// Precomputed JET Colormap lookup table (256 entries) for instant thermal rendering
const JET_LUT = (() => {
    const lut = new Uint8Array(256 * 3);
    for (let i = 0; i < 256; i++) {
        const v = i / 255.0;
        const r = Math.min(Math.max(1.5 - Math.abs(4.0 * v - 3.0), 0.0), 1.0);
        const g = Math.min(Math.max(1.5 - Math.abs(4.0 * v - 2.0), 0.0), 1.0);
        const b = Math.min(Math.max(1.5 - Math.abs(4.0 * v - 1.0), 0.0), 1.0);

        lut[i * 3] = Math.round(r * 255);
        lut[i * 3 + 1] = Math.round(g * 255);
        lut[i * 3 + 2] = Math.round(b * 255);
    }
    return lut;
})();

// Precomputed 8x8 Bayer Dither Matrix (values 0 to 63)
const BAYER_8X8 = [
    [ 0, 32,  8, 40,  2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44,  4, 36, 14, 46,  6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [ 3, 35, 11, 43,  1, 33,  9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47,  7, 39, 13, 45,  5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21]
];

// Local ASCII Texture Strip Loader (5680 x 80 -> 71 glyphs of 80x80)
let asciiTextureImg = null;
let asciiTextureData = null;
let asciiTextureW = 5680;
let asciiTextureH = 80;
const TOTAL_ASCII_GLYPHS = 71;
const GLYPH_SIZE = 80;

if (typeof window !== "undefined") {
    asciiTextureImg = new Image();
    asciiTextureImg.src = "./assets/test.jpg";
    asciiTextureImg.onload = () => {
        try {
            const offCanvas = document.createElement("canvas");
            offCanvas.width = asciiTextureImg.width;
            offCanvas.height = asciiTextureImg.height;
            const offCtx = offCanvas.getContext("2d", { willReadFrequently: true });
            offCtx.drawImage(asciiTextureImg, 0, 0);
            asciiTextureW = offCanvas.width;
            asciiTextureH = offCanvas.height;
            asciiTextureData = offCtx.getImageData(0, 0, offCanvas.width, offCanvas.height).data;
        } catch (e) {
            console.warn("ASCII texture canvas load warning:", e);
        }
    };
}

// Fallback ASCII 6x6 Glyphs
const ASCII_GLYPHS_6X6 = [
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 12, 12],
    [0, 12, 12, 0, 12, 12],
    [0, 0, 62, 62, 0, 0],
    [0, 12, 62, 62, 12, 0],
    [0, 42, 28, 62, 28, 42],
    [34, 18, 12, 24, 36, 34],
    [20, 62, 20, 62, 20, 0],
    [12, 30, 24, 14, 60, 12],
    [28, 34, 42, 46, 32, 28]
];

// Precomputed Procedural Scratch Normal Map (512x512) for Ice & Glass
const SCRATCH_SIZE = 512;
const scratchNormalField = (() => {
    const field = new Float32Array(SCRATCH_SIZE * SCRATCH_SIZE * 3);
    const heightMap = new Float32Array(SCRATCH_SIZE * SCRATCH_SIZE);

    for (let i = 0; i < 450; i++) {
        let x = Math.random() * SCRATCH_SIZE;
        let y = Math.random() * SCRATCH_SIZE;
        const angle = Math.random() * Math.PI * 2;
        const len = Math.random() * 120 + 20;

        for (let s = 0; s < len; s += 1.0) {
            const px = Math.floor((x + Math.cos(angle) * s + SCRATCH_SIZE) % SCRATCH_SIZE);
            const py = Math.floor((y + Math.sin(angle) * s + SCRATCH_SIZE) % SCRATCH_SIZE);
            heightMap[py * SCRATCH_SIZE + px] = Math.min(1.0, heightMap[py * SCRATCH_SIZE + px] + 0.7);
        }
    }

    for (let y = 0; y < SCRATCH_SIZE; y++) {
        for (let x = 0; x < SCRATCH_SIZE; x++) {
            const getH = (gx, gy) => heightMap[((gy + SCRATCH_SIZE) % SCRATCH_SIZE) * SCRATCH_SIZE + ((gx + SCRATCH_SIZE) % SCRATCH_SIZE)];

            const dx = (getH(x + 1, y - 1) + 2 * getH(x + 1, y) + getH(x + 1, y + 1)) -
                       (getH(x - 1, y - 1) + 2 * getH(x - 1, y) + getH(x - 1, y + 1));
            const dy = (getH(x - 1, y + 1) + 2 * getH(x, y + 1) + getH(x + 1, y + 1)) -
                       (getH(x - 1, y - 1) + 2 * getH(x, y - 1) + getH(x + 1, y - 1));

            const nx = -dx * 0.08;
            const ny = -dy * 0.08;
            const nz = 1.0;
            const len = Math.hypot(nx, ny, nz) || 1.0;

            const idx = (y * SCRATCH_SIZE + x) * 3;
            field[idx]     = nx / len;
            field[idx + 1] = ny / len;
            field[idx + 2] = nz / len;
        }
    }
    return field;
})();

const POISSON_OFFSETS_8 = [
    [-0.326, -0.406], [-0.840, -0.074],
    [-0.696,  0.457], [-0.203,  0.621],
    [ 0.962, -0.194], [ 0.473, -0.480],
    [ 0.519,  0.767], [ 0.185, -0.893]
];

function sampleBilinearRGB(src, fx, fy, w, h) {
    const clX = Math.max(0, Math.min(w - 1, fx));
    const clY = Math.max(0, Math.min(h - 1, fy));

    const x0 = Math.floor(clX);
    const y0 = Math.floor(clY);
    const x1 = Math.min(w - 1, x0 + 1);
    const y1 = Math.min(h - 1, y0 + 1);

    const sX = clX - x0;
    const sY = clY - y0;
    const invX = 1.0 - sX;
    const invY = 1.0 - sY;

    const i00 = (y0 * w + x0) * 4;
    const i10 = (y0 * w + x1) * 4;
    const i01 = (y1 * w + x0) * 4;
    const i11 = (y1 * w + x1) * 4;

    const r = (src[i00] * invX + src[i10] * sX) * invY + (src[i01] * invX + src[i11] * sX) * sY;
    const g = (src[i00 + 1] * invX + src[i10 + 1] * sX) * invY + (src[i01 + 1] * invX + src[i11 + 1] * sX) * sY;
    const b = (src[i00 + 2] * invX + src[i10 + 2] * sX) * invY + (src[i01 + 2] * invX + src[i11 + 2] * sX) * sY;

    return { r, g, b };
}

/**
 * 1. Enhanced Crimson Noir / Cyberpunk Blood Red Poster with Sculpted Depth (filtro_crimson_noir)
 * - Multi-stage depth tone mapping with sculpted edge definition
 * - Rich blood-crimson midtones, deep cherry shadows & radiant porcelain skin
 */
function filtro_crimson_noir(imageData, w, h) {
    const src = new Uint8ClampedArray(imageData.data);
    const dst = imageData.data;

    // Luminance array for edge normal depth calculation
    const lums = new Float32Array(w * h);
    for (let i = 0; i < w * h; i++) {
        const idx = i * 4;
        lums[i] = 0.299 * src[idx] + 0.587 * src[idx + 1] + 0.114 * src[idx + 2];
    }

    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const pIdx = y * w + x;
            const idx = pIdx * 4;
            const gray = lums[pIdx];

            // Edge gradient depth enhancement
            let edge = 0;
            if (x > 0 && x < w - 1 && y > 0 && y < h - 1) {
                const gx = (lums[pIdx + 1] - lums[pIdx - 1]);
                const gy = (lums[pIdx + w] - lums[pIdx - w]);
                edge = Math.hypot(gx, gy);
            }

            const depthFactor = Math.min(1.0, edge / 45.0);

            if (gray < 35) {
                // Tier 1: Deep obsidian cherry shadow
                dst[idx]     = 18;
                dst[idx + 1] = 3;
                dst[idx + 2] = 8;
            } else if (gray < 95) {
                // Tier 2: Rich blood crimson mid-shadow
                const t = (gray - 35) / 60.0;
                dst[idx]     = Math.round(115 + t * 45 + depthFactor * 25);
                dst[idx + 1] = Math.round(8 + t * 10);
                dst[idx + 2] = Math.round(16 + t * 12);
            } else if (gray < 160) {
                // Tier 3: Vibrant scarlet contour
                const t = (gray - 95) / 65.0;
                dst[idx]     = Math.round(160 + t * 48);
                dst[idx + 1] = Math.round(18 + t * 16);
                dst[idx + 2] = Math.round(28 + t * 18);
            } else if (gray < 210) {
                // Tier 4: Soft luminous rose transition
                const t = (gray - 160) / 50.0;
                dst[idx]     = Math.round(208 + t * 40);
                dst[idx + 1] = Math.round(214 + t * 32);
                dst[idx + 2] = Math.round(224 + t * 24);
            } else {
                // Tier 5: Brilliant porcelain white highlight
                dst[idx]     = 252;
                dst[idx + 1] = 246;
                dst[idx + 2] = 242;
            }
        }
    }

    const margin = 10;
    const tickLen = 24;
    for (let y = margin; y < margin + tickLen && y < h; y++) {
        const idxL = (y * w + margin) * 4;
        const idxR = (y * w + (w - margin - 1)) * 4;
        dst[idxL] = 245; dst[idxL + 1] = 248; dst[idxL + 2] = 255;
        dst[idxR] = 245; dst[idxR + 1] = 248; dst[idxR + 2] = 255;
    }
    for (let x = margin; x < margin + tickLen && x < w; x++) {
        const idxT = (margin * w + x) * 4;
        const idxB = ((h - margin - 1) * w + x) * 4;
        dst[idxT] = 245; dst[idxT + 1] = 248; dst[idxT + 2] = 255;
        dst[idxB] = 245; dst[idxB + 1] = 248; dst[idxB + 2] = 255;
    }

    return imageData;
}

/**
 * 2. Liquid Chrome with Flowing Metal & Glowing Particles STRICTLY on Body, Greyish-Black Background (filtro_liquid_chrome)
 */
function filtro_liquid_chrome(imageData, w, h) {
    const src = new Uint8ClampedArray(imageData.data);
    const dst = imageData.data;

    let bgSumR = 0, bgSumG = 0, bgSumB = 0, bgCount = 0;
    const cornerW = Math.max(8, Math.floor(w * 0.12));
    const cornerH = Math.max(8, Math.floor(h * 0.15));

    for (let cy = 0; cy < cornerH; cy++) {
        for (let cx = 0; cx < cornerW; cx++) {
            let idx = (cy * w + cx) * 4;
            bgSumR += src[idx]; bgSumG += src[idx + 1]; bgSumB += src[idx + 2];
            idx = (cy * w + (w - 1 - cx)) * 4;
            bgSumR += src[idx]; bgSumG += src[idx + 1]; bgSumB += src[idx + 2];
            bgCount += 2;
        }
    }
    const bgAvgR = bgCount > 0 ? (bgSumR / bgCount) : 40;
    const bgAvgG = bgCount > 0 ? (bgSumG / bgCount) : 40;
    const bgAvgB = bgCount > 0 ? (bgSumB / bgCount) : 50;

    const lums = new Float32Array(w * h);
    const isHumanPixel = new Uint8Array(w * h);
    const edges = new Float32Array(w * h);

    const centerX = w / 2.0;
    const maxBodyRadiusX = w * 0.40;

    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const pIdx = y * w + x;
            const idx = pIdx * 4;
            const r = src[idx];
            const g = src[idx + 1];
            const b = src[idx + 2];

            const lum = 0.299 * r + 0.587 * g + 0.114 * b;
            lums[pIdx] = lum;

            const isSkin = (r > 65 && g > 40 && b > 25 && r > g && g > b && (r - g) >= 12 && (r - b) >= 18);
            const distFromCenter = Math.abs(x - centerX);
            const inBodyColumn = distFromCenter < maxBodyRadiusX;
            const diffBg = Math.hypot(r - bgAvgR, g - bgAvgG, b - bgAvgB);

            if (inBodyColumn && (isSkin || (diffBg > 38.0 && lum > 55))) {
                isHumanPixel[pIdx] = 1;
            }
        }
    }

    for (let y = 1; y < h - 1; y++) {
        for (let x = 1; x < w - 1; x++) {
            const pIdx = y * w + x;
            const gx = (lums[pIdx + 1 - w] + 2 * lums[pIdx + 1] + lums[pIdx + 1 + w]) -
                       (lums[pIdx - 1 - w] + 2 * lums[pIdx - 1] + lums[pIdx - 1 + w]);
            const gy = (lums[pIdx - 1 + w] + 2 * lums[pIdx + w] + lums[pIdx + 1 + w]) -
                       (lums[pIdx - 1 - w] + 2 * lums[pIdx - w] + lums[pIdx + 1 - w]);
            edges[pIdx] = Math.hypot(gx, gy);
        }
    }

    const humanField = new Float32Array(w * h);
    const rad = 8;
    for (let y = rad; y < h - rad; y += 2) {
        for (let x = rad; x < w - rad; x += 2) {
            let count = 0, total = 0;
            for (let dy = -rad; dy <= rad; dy += 4) {
                for (let dx = -rad; dx <= rad; dx += 4) {
                    if (isHumanPixel[(y + dy) * w + (x + dx)] === 1) count++;
                    total++;
                }
            }
            const score = total > 0 ? (count / total) : 0;
            humanField[y * w + x] = score;
            humanField[y * w + (x + 1)] = score;
            humanField[(y + 1) * w + x] = score;
            humanField[(y + 1) * w + (x + 1)] = score;
        }
    }

    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const pIdx = y * w + x;
            const idx = pIdx * 4;
            const hScore = humanField[pIdx];

            const rawLum = lums[pIdx];
            const bgGrey = rawLum * 0.32;
            const bgR = Math.min(255, Math.round(bgGrey * 0.95 + 4));
            const bgG = Math.min(255, Math.round(bgGrey * 0.98 + 5));
            const bgB = Math.min(255, Math.round(bgGrey * 1.08 + 8));

            if (hScore < 0.28 || y === 0 || y === h - 1 || x === 0 || x === w - 1) {
                dst[idx]     = bgR;
                dst[idx + 1] = bgG;
                dst[idx + 2] = bgB;
            } else {
                const gx = (lums[pIdx + 1] - lums[pIdx - 1]) * 0.08;
                const gy = (lums[pIdx + w] - lums[pIdx - w]) * 0.08;
                const gz = 1.0;
                const len = Math.hypot(gx, gy, gz) || 1.0;
                const nx = gx / len;
                const ny = gy / len;
                const nz = gz / len;

                const dotLight = Math.max(0, 0.577 * nx + 0.577 * ny + 0.577 * nz);
                const spec = Math.pow(dotLight, 16.0);
                const edgeFresnel = Math.pow(1.0 - nz, 2.5);

                const iridR = Math.sin(spec * 6.28 + 0.0) * 0.5 + 0.5;
                const iridG = Math.sin(spec * 6.28 + 2.09) * 0.5 + 0.5;
                const iridB = Math.sin(spec * 6.28 + 4.18) * 0.5 + 0.5;

                const chromeR = Math.round(spec * 220 + edgeFresnel * 120 + iridR * 35);
                const chromeG = Math.round(spec * 235 + edgeFresnel * 160 + iridG * 35);
                const chromeB = Math.round(spec * 255 + edgeFresnel * 220 + iridB * 55);

                const alpha = Math.min(1.0, (hScore - 0.28) / 0.18);
                dst[idx]     = Math.min(255, Math.round(bgR * (1.0 - alpha) + chromeR * alpha));
                dst[idx + 1] = Math.min(255, Math.round(bgG * (1.0 - alpha) + chromeG * alpha));
                dst[idx + 2] = Math.min(255, Math.round(bgB * (1.0 - alpha) + chromeB * alpha));
            }
        }
    }

    const orbGrid = 4;
    for (let gy = 4; gy < h - 4; gy += orbGrid) {
        for (let gx = 4; gx < w - 4; gx += orbGrid) {
            const gIdx = gy * w + gx;
            const hScore = humanField[gIdx];

            if (hScore >= 0.38) {
                const edgeVal = edges[gIdx];
                const lumVal = lums[gIdx];
                const isSkin = isHumanPixel[gIdx] === 1;

                if (edgeVal > 24.0 || isSkin || lumVal > 110) {
                    const orbHash = (Math.sin(gx * 12.9898 + gy * 78.233) * 43758.5453) % 1.0;
                    if (orbHash > 0.20) {
                        let orbR = 255, orbG = 215, orbB = 35;
                        if (lumVal > 140 || orbHash > 0.68) {
                            orbR = 255; orbG = 42; orbB = 135;
                        } else if (edgeVal > 48.0 || orbHash < 0.45) {
                            orbR = 0; orbG = 240; orbB = 255;
                        }

                        const orbRadius = 3.6;
                        for (let dy = -3; dy <= 3; dy++) {
                            for (let dx = -3; dx <= 3; dx++) {
                                const px = gx + dx;
                                const py = gy + dy;
                                if (px >= 0 && px < w && py >= 0 && py < h) {
                                    const d = Math.hypot(dx, dy);
                                    if (d <= orbRadius) {
                                        const halo = Math.pow(1.0 - d / orbRadius, 1.8);
                                        const dstIdx = (py * w + px) * 4;
                                        if (d < 1.2) {
                                            dst[dstIdx]     = 255;
                                            dst[dstIdx + 1] = 255;
                                            dst[dstIdx + 2] = 255;
                                        } else {
                                            dst[dstIdx]     = Math.min(255, Math.round(dst[dstIdx] + orbR * halo));
                                            dst[dstIdx + 1] = Math.min(255, Math.round(dst[dstIdx + 1] + orbG * halo));
                                            dst[dstIdx + 2] = Math.min(255, Math.round(dst[dstIdx + 2] + orbB * halo));
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    return imageData;
}

/**
 * 3. Crystal Ice & Frost Glass Shader (filtro_cristal)
 */
function filtro_cristal(imageData, w, h) {
    const src = new Uint8ClampedArray(imageData.data);
    const dst = imageData.data;

    for (let y = 0; y < h; y++) {
        const smY = Math.floor((y * 2.5) % SCRATCH_SIZE);
        for (let x = 0; x < w; x++) {
            const smX = Math.floor((x * 2.5) % SCRATCH_SIZE);
            const snIdx = (smY * SCRATCH_SIZE + smX) * 3;

            const snx = scratchNormalField[snIdx];
            const sny = scratchNormalField[snIdx + 1];

            const fHash = Math.sin(x * 0.14 + y * 0.09) * 4.0;
            const iceFracture = Math.abs(Math.sin((x * 0.28 + y * 0.42 + fHash) * 0.18));
            const isIceVein = iceFracture > 0.94 ? (iceFracture - 0.94) / 0.06 : 0.0;

            const facetNormalX = snx * 8.5 + (isIceVein * 5.0);
            const facetNormalY = sny * 8.5 + (isIceVein * 5.0);

            let accR = 0, accG = 0, accB = 0;
            const chromAbb = 3.0;

            for (let i = 0; i < 8; i++) {
                const offX = POISSON_OFFSETS_8[i][0] * 2.8;
                const offY = POISSON_OFFSETS_8[i][1] * 2.8;

                const sampleX = x + facetNormalX + offX;
                const sampleY = y + facetNormalY + offY;

                const sR = sampleBilinearRGB(src, sampleX + chromAbb, sampleY, w, h);
                const sG = sampleBilinearRGB(src, sampleX, sampleY, w, h);
                const sB = sampleBilinearRGB(src, sampleX - chromAbb, sampleY, w, h);

                accR += sR.r;
                accG += sG.g;
                accB += sB.b;
            }

            const rVal = accR / 8.0;
            const gVal = accG / 8.0;
            const bVal = accB / 8.0;

            const iceTintR = 0.96;
            const iceTintG = 1.04;
            const iceTintB = 1.15;

            const spec = Math.pow(Math.max(0, 0.577 * snx + 0.577 * sny + 0.577), 28) * 190.0;
            const veinGlint = isIceVein * 140.0;

            const dstIdx = (y * w + x) * 4;
            dst[dstIdx]     = Math.min(255, Math.round(rVal * iceTintR + spec * 0.9 + veinGlint * 0.85));
            dst[dstIdx + 1] = Math.min(255, Math.round(gVal * iceTintG + spec * 0.95 + veinGlint * 1.0));
            dst[dstIdx + 2] = Math.min(255, Math.round(bVal * iceTintB + spec * 1.1 + veinGlint * 1.25));
        }
    }

    return imageData;
}

/**
 * 4. Studio Matrix Void Silhouette ASCII with Radiant Cosmic Aurora Glow (filtro_void_ascii)
 * - Subject: Full high-definition ASCII matrix glyph terminal with chromatic aberration
 * - Background: Ethereal radiant neon cyan & electric purple cosmic aurora glowing into deep space
 */
function filtro_void_ascii(imageData, w, h) {
    const src = new Uint8ClampedArray(imageData.data);
    const dst = imageData.data;

    const cellW = 10;
    const cellH = 13;

    let totalLum = 0, sampleCount = 0;
    for (let y = 0; y < h; y += 4) {
        for (let x = 0; x < w; x += 4) {
            const idx = (y * w + x) * 4;
            totalLum += getLuminance(src[idx], src[idx + 1], src[idx + 2]);
            sampleCount++;
        }
    }
    const avgSceneLum = sampleCount > 0 ? (totalLum / sampleCount) : 128;
    const voidThreshold = Math.max(38, Math.min(100, avgSceneLum * 0.65));

    const cols = Math.ceil(w / cellW);
    const rows = Math.ceil(h / cellH);
    const gridIsLit = new Uint8Array(cols * rows);
    const gridCharIdx = new Uint8Array(cols * rows);
    const gridColorR = new Uint8Array(cols * rows);
    const gridColorG = new Uint8Array(cols * rows);
    const gridColorB = new Uint8Array(cols * rows);

    for (let gy = 0; gy < rows; gy++) {
        for (let gx = 0; gx < cols; gx++) {
            const bx = gx * cellW;
            const by = gy * cellH;
            let sumR = 0, sumG = 0, sumB = 0, sumLum = 0, count = 0;

            for (let py = 0; py < cellH && by + py < h; py++) {
                for (let px = 0; px < cellW && bx + px < w; px++) {
                    const sIdx = ((by + py) * w + (bx + px)) * 4;
                    const r = src[sIdx];
                    const g = src[sIdx + 1];
                    const b = src[sIdx + 2];
                    sumR += r;
                    sumG += g;
                    sumB += b;
                    sumLum += getLuminance(r, g, b);
                    count++;
                }
            }

            if (count === 0) continue;

            const avgLum = sumLum / count;
            const gIdx = gy * cols + gx;

            if (avgLum >= voidThreshold) {
                gridIsLit[gIdx] = 1;
                const normalizedLum = Math.min(1.0, (avgLum - voidThreshold) / (255.0 - voidThreshold));
                gridCharIdx[gIdx] = Math.min(TOTAL_ASCII_GLYPHS - 1, Math.max(0, Math.floor((1.0 - normalizedLum) * (TOTAL_ASCII_GLYPHS - 1))));
                gridColorR[gIdx] = Math.round(sumR / count);
                gridColorG[gIdx] = Math.round(sumG / count);
                gridColorB[gIdx] = Math.round(sumB / count);
            } else {
                gridIsLit[gIdx] = 0;
            }
        }
    }

    // High-Resolution Distance Field for Background Neon Aurora Glow
    const glowField = new Float32Array(cols * rows);
    for (let gy = 0; gy < rows; gy++) {
        for (let gx = 0; gx < cols; gx++) {
            if (gridIsLit[gy * cols + gx] === 1) {
                glowField[gy * cols + gx] = 1.0;
            } else {
                let maxNear = 0;
                for (let dy = -5; dy <= 5; dy++) {
                    for (let dx = -5; dx <= 5; dx++) {
                        const nx = gx + dx;
                        const ny = gy + dy;
                        if (nx >= 0 && nx < cols && ny >= 0 && ny < rows) {
                            if (gridIsLit[ny * cols + nx] === 1) {
                                const dist = Math.hypot(dx, dy);
                                const factor = Math.max(0, 1.0 - dist / 5.5);
                                if (factor > maxNear) maxNear = factor;
                            }
                        }
                    }
                }
                glowField[gy * cols + gx] = maxNear;
            }
        }
    }

    const chromShift = 3;

    for (let y = 0; y < h; y++) {
        const gy = Math.floor(y / cellH);
        const py = y % cellH;

        for (let x = 0; x < w; x++) {
            const gx = Math.floor(x / cellW);
            const px = x % cellW;
            const gIdx = gy * cols + gx;

            const dstIdx = (y * w + x) * 4;
            const bgGlow = glowField[gIdx];

            if (gridIsLit[gIdx] === 0) {
                // RADIANT NEON COSMIC AURORA IN BACKGROUND VOID
                const auraGlow = Math.pow(bgGlow, 1.35);
                const cosmicDust = Math.sin(x * 0.06 + y * 0.08) * 6.0;

                const glowR = Math.round(16 + auraGlow * 95 + cosmicDust * 0.4);
                const glowG = Math.round(14 + auraGlow * 165 + cosmicDust * 0.8);
                const glowB = Math.round(42 + auraGlow * 240 + cosmicDust * 1.2);

                dst[dstIdx]     = Math.min(255, Math.max(0, glowR));
                dst[dstIdx + 1] = Math.min(255, Math.max(0, glowG));
                dst[dstIdx + 2] = Math.min(255, Math.max(0, glowB));
                continue;
            }

            const charIdx = gridCharIdx[gIdx];
            const avgR = gridColorR[gIdx];
            const avgG = gridColorG[gIdx];
            const avgB = gridColorB[gIdx];

            const cx = cellW / 2.0;
            const cy = cellH / 2.0;
            const distFromCenter = Math.hypot(px - cx, py - cy);
            const haloIntensity = Math.max(0, 1.0 - distFromCenter / (cellW * 0.95));
            const haloGlow = Math.pow(haloIntensity, 1.5) * 135.0;

            let glyphValCenter = 0;
            let glyphValRed = 0;
            let glyphValBlue = 0;

            if (asciiTextureData && asciiTextureW > 0 && asciiTextureH > 0) {
                const glyphOffsetX = charIdx * GLYPH_SIZE;
                const ty = Math.max(0, Math.min(asciiTextureH - 1, Math.floor((py / cellH) * (GLYPH_SIZE - 1))));

                const txC = Math.max(0, Math.min(asciiTextureW - 1, glyphOffsetX + Math.floor((px / cellW) * (GLYPH_SIZE - 1))));
                glyphValCenter = asciiTextureData[(ty * asciiTextureW + txC) * 4] || 0;

                const txR = Math.max(0, Math.min(asciiTextureW - 1, glyphOffsetX + Math.floor((Math.max(0, px - chromShift) / cellW) * (GLYPH_SIZE - 1))));
                glyphValRed = asciiTextureData[(ty * asciiTextureW + txR) * 4] || 0;

                const txB = Math.max(0, Math.min(asciiTextureW - 1, glyphOffsetX + Math.floor((Math.min(cellW - 1, px + chromShift) / cellW) * (GLYPH_SIZE - 1))));
                glyphValBlue = asciiTextureData[(ty * asciiTextureW + txB) * 4] || 0;
            }

            const isGlyph = glyphValCenter > 25;
            const glyphBright = glyphValCenter / 255.0;

            const redFringe = (glyphValRed / 255.0) * 235.0;
            const blueFringe = (glyphValBlue / 255.0) * 255.0;

            if (isGlyph) {
                dst[dstIdx]     = Math.min(255, Math.round(225 * glyphBright + redFringe * 0.45 + haloGlow * 0.45 + avgR * 0.25));
                dst[dstIdx + 1] = Math.min(255, Math.round(248 * glyphBright + haloGlow * 0.55 + avgG * 0.25));
                dst[dstIdx + 2] = Math.min(255, Math.round(255 * glyphBright + blueFringe * 0.45 + haloGlow * 0.65 + avgB * 0.25));
            } else {
                dst[dstIdx]     = Math.min(255, Math.round(22 + redFringe * 0.65 + haloGlow * 0.45 + avgR * 0.28));
                dst[dstIdx + 1] = Math.min(255, Math.round(24 + haloGlow * 0.55 + avgG * 0.30));
                dst[dstIdx + 2] = Math.min(255, Math.round(45 + blueFringe * 0.75 + haloGlow * 0.75 + avgB * 0.38));
            }
        }
    }

    return imageData;
}

/**
 * 5. Vintage Comic Manga Halftone Filter (filtro_manga_halftone) - Classic Edition Restored
 */
function filtro_manga_halftone(imageData, w, h) {
    const data = imageData.data;
    const cell = 6;
    const halfCell = cell / 2;
    const radiusScale = cell / 1.25;

    const inkR = 85, inkG = 18, inkB = 34;
    const paperR = 252, paperG = 246, paperB = 232;

    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const rotX = x * 0.7071 - y * 0.7071;
            const rotY = x * 0.7071 + y * 0.7071;

            const cx = ((rotX % cell) + cell) % cell - halfCell;
            const cy = ((rotY % cell) + cell) % cell - halfCell;
            const distCenter = Math.hypot(cx, cy);

            const idx = (y * w + x) * 4;
            const gray = getLuminance(data[idx], data[idx + 1], data[idx + 2]);
            const radius = (1.0 - gray / 255.0) * radiusScale;

            if (distCenter < radius) {
                data[idx]     = inkR;
                data[idx + 1] = inkG;
                data[idx + 2] = inkB;
            } else {
                data[idx]     = paperR;
                data[idx + 1] = paperG;
                data[idx + 2] = paperB;
            }
        }
    }
    return imageData;
}

/**
 * 6. Medical X-Ray & Radiography Shader (filtro_xray)
 */
function filtro_xray(imageData, w, h) {
    const data = imageData.data;

    for (let y = 0; y < h; y++) {
        const scanline = (y % 3 === 0) ? 0.88 : 1.0;
        for (let x = 0; x < w; x++) {
            const idx = (y * w + x) * 4;
            const gray = getLuminance(data[idx], data[idx + 1], data[idx + 2]);

            const norm = (255.0 - gray) / 255.0;
            const boneDensity = Math.pow(norm, 1.8);

            const r = Math.round(boneDensity * 230 * scanline);
            const g = Math.round(boneDensity * 245 * scanline + (1.0 - boneDensity) * 18);
            const b = Math.round(boneDensity * 255 * scanline + (1.0 - boneDensity) * 48);

            data[idx]     = r;
            data[idx + 1] = g;
            data[idx + 2] = b;
        }
    }

    return imageData;
}

/**
 * 7. High-Definition Full ASCII Matrix Terminal Filter (filtro_ascii)
 */
function filtro_ascii(imageData, w, h) {
    const src = new Uint8ClampedArray(imageData.data);
    const dst = imageData.data;
    const blockSize = 6;

    for (let by = 0; by < h; by += blockSize) {
        for (let bx = 0; bx < w; bx += blockSize) {
            let sumLum = 0, sumR = 0, sumG = 0, sumB = 0, count = 0;

            for (let py = 0; py < blockSize && by + py < h; py++) {
                for (let px = 0; px < blockSize && bx + px < w; px++) {
                    const sIdx = ((by + py) * w + (bx + px)) * 4;
                    const r = src[sIdx];
                    const g = src[sIdx + 1];
                    const b = src[sIdx + 2];
                    sumR += r;
                    sumG += g;
                    sumB += b;
                    sumLum += getLuminance(r, g, b);
                    count++;
                }
            }

            if (count === 0) continue;

            const avgLum = sumLum / count;
            const avgR = sumR / count;
            const avgG = sumG / count;
            const avgB = sumB / count;

            const glyphIdx = Math.min(9, Math.floor((avgLum / 255.0) * 10));
            const glyph = ASCII_GLYPHS_6X6[glyphIdx];

            for (let py = 0; py < blockSize && by + py < h; py++) {
                const rowBits = glyph[py] || 0;
                for (let px = 0; px < blockSize && bx + px < w; px++) {
                    const isLit = (rowBits >> (5 - px)) & 1;
                    const dIdx = ((by + py) * w + (bx + px)) * 4;

                    if (isLit) {
                        const brightness = Math.min(1.5, 0.75 + (avgLum / 255.0) * 0.75);
                        dst[dIdx]     = Math.min(255, Math.round((avgR * 0.35 + 40) * brightness));
                        dst[dIdx + 1] = Math.min(255, Math.round((avgG * 0.45 + 225) * brightness));
                        dst[dIdx + 2] = Math.min(255, Math.round((avgB * 0.35 + 130) * brightness));
                    } else {
                        dst[dIdx]     = 4;
                        dst[dIdx + 1] = 12;
                        dst[dIdx + 2] = 8;
                    }
                }
            }
        }
    }

    return imageData;
}

/**
 * 8. Retro 8x8 Bayer Ordered Dithering Filter (filtro_dither)
 */
function filtro_dither(imageData, w, h) {
    const data = imageData.data;

    for (let y = 0; y < h; y++) {
        const by = y % 8;
        for (let x = 0; x < w; x++) {
            const bx = x % 8;
            const threshold = (BAYER_8X8[by][bx] / 64.0) * 255.0;

            const idx = (y * w + x) * 4;
            const gray = getLuminance(data[idx], data[idx + 1], data[idx + 2]);

            if (gray > threshold) {
                data[idx]     = 240;
                data[idx + 1] = 245;
                data[idx + 2] = 250;
            } else {
                data[idx]     = 16;
                data[idx + 1] = 18;
                data[idx + 2] = 28;
            }
        }
    }

    return imageData;
}

/**
 * 9. Thermal Infrared / JET Colormap Filter (filtro_5)
 */
function filtro_5(imageData, w, h) {
    const data = imageData.data;
    const totalPixels = w * h;

    for (let i = 0; i < totalPixels; i++) {
        const idx = i * 4;
        const gray = Math.round(getLuminance(data[idx], data[idx + 1], data[idx + 2]));
        const lutIdx = gray * 3;

        data[idx]     = JET_LUT[lutIdx];
        data[idx + 1] = JET_LUT[lutIdx + 1];
        data[idx + 2] = JET_LUT[lutIdx + 2];
    }
    return imageData;
}

/**
 * 10. Magenta / Rosa Halftone Filter (filtro_rosa) - Classic Edition Restored
 */
function filtro_rosa(imageData, w, h) {
    const data = imageData.data;
    const cell = 5;
    const halfCell = cell / 2;
    const radiusScale = cell / 1.3;

    const dotR = 130, dotG = 20, dotB = 55;
    const bgR = 245, bgG = 190, bgB = 215;

    for (let y = 0; y < h; y++) {
        const cy = (y % cell) - halfCell;
        for (let x = 0; x < w; x++) {
            const cx = (x % cell) - halfCell;
            const distCenter = Math.hypot(cx, cy);

            const idx = (y * w + x) * 4;
            const gray = getLuminance(data[idx], data[idx + 1], data[idx + 2]);
            const radius = (1.0 - gray / 255.0) * radiusScale;

            if (distCenter < radius) {
                data[idx]     = dotR;
                data[idx + 1] = dotG;
                data[idx + 2] = dotB;
            } else {
                data[idx]     = bgR;
                data[idx + 1] = bgG;
                data[idx + 2] = bgB;
            }
        }
    }
    return imageData;
}

/**
 * Registry of Curated Active Visual Shaders
 */
export const FILTERS = [
    {
        id: "filtro_crimson_noir",
        name: "Crimson Noir",
        description: "Blood red, sculpted depth contours & porcelain white cyberpunk poster",
        icon: "🩸",
        badge: "01",
        fn: filtro_crimson_noir
    },
    {
        id: "filtro_liquid_chrome",
        name: "Liquid Chrome Body",
        description: "Liquid chrome flowing metal & glowing particles on body with greyish-black room",
        icon: "🌊",
        badge: "02",
        fn: filtro_liquid_chrome
    },
    {
        id: "filtro_cristal",
        name: "Crystal Ice Glass",
        description: "Crisp crystal glass refraction with sharp frost veins & glints",
        icon: "🧊",
        badge: "03",
        fn: filtro_cristal
    },
    {
        id: "filtro_void_ascii",
        name: "Matrix Void ASCII",
        description: "Glowing character halos with cosmic neon aurora background & chromatic aberration",
        icon: "🕳️",
        badge: "04",
        fn: filtro_void_ascii
    },
    {
        id: "filtro_manga_halftone",
        name: "Vintage Manga",
        description: "Burgundy ink on cream paper 45° halftone screentone (Classic)",
        icon: "📰",
        badge: "05",
        fn: filtro_manga_halftone
    },
    {
        id: "filtro_xray",
        name: "Medical X-Ray",
        description: "Translucent cyan-blue bone opacity inversion with scanlines",
        icon: "🩻",
        badge: "06",
        fn: filtro_xray
    },
    {
        id: "filtro_ascii",
        name: "HD ASCII Matrix",
        description: "High-definition full-matrix character raster",
        icon: "⌨",
        badge: "07",
        fn: filtro_ascii
    },
    {
        id: "filtro_dither",
        name: "Retro Dither",
        description: "Classic 8x8 Bayer ordered matrix dithering",
        icon: "▦",
        badge: "08",
        fn: filtro_dither
    },
    {
        id: "filtro_5",
        name: "Thermal JET",
        description: "Simulated infrared heat camera vision",
        icon: "♨",
        badge: "09",
        fn: filtro_5
    },
    {
        id: "filtro_rosa",
        name: "Rosa Halftone",
        description: "Vibrant magenta duotone halftone (Classic)",
        icon: "🌸",
        badge: "10",
        fn: filtro_rosa
    }
];
