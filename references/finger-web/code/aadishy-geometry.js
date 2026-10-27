/**
 * geometry.js - 3D Perspective Depth Portal Geometry, Volumetric Parallax Shadowing & Precision Touch Detection
 * Features real-time 3D yaw/pitch plane rotation, volumetric depth extrusion, and closer-hand perspective foreshortening.
 */

/**
 * Calculates metrics between left and right hand fingertips:
 * - topW: Distance between Left Index (p1) and Right Index (p3)
 * - bottomW: Distance between Left Thumb (p2) and Right Thumb (p4)
 * - leftPinch: Distance between Left Index (p1) and Left Thumb (p2)
 * - rightPinch: Distance between Right Index (p3) and Right Thumb (p4)
 */
export function getPortalMetrics(p1, p2, p3, p4) {
    const topW = Math.hypot(p3.x - p1.x, p3.y - p1.y);
    const bottomW = Math.hypot(p4.x - p2.x, p4.y - p2.y);
    const leftPinchDist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
    const rightPinchDist = Math.hypot(p3.x - p4.x, p3.y - p4.y);

    const touchSpan = Math.max(topW, bottomW);
    const minFingertipDist = Math.min(topW, bottomW, (topW + bottomW) / 2.0);

    return {
        topW,
        bottomW,
        touchSpan,
        minFingertipDist,
        leftPinchDist,
        rightPinchDist,
        avgWidth: (topW + bottomW) / 2.0
    };
}

export function portalWidth(p1, p2, p3, p4) {
    const topW = Math.hypot(p3.x - p1.x, p3.y - p1.y);
    const bottomW = Math.hypot(p4.x - p2.x, p4.y - p2.y);
    return (topW + bottomW) / 2.0;
}

export function portalMinFingertipDist(p1, p2, p3, p4) {
    const metrics = getPortalMetrics(p1, p2, p3, p4);
    return metrics.minFingertipDist;
}

/**
 * Strict Fingertip Touch Detector
 */
export class ClosingGestureDetector {
    constructor(closeRatio = 0.045, openRatio = 0.08) {
        this.closeRatio = closeRatio;
        this.openRatio = openRatio;
        this.isClosed = false;
        this.lastTriggerTime = 0;
        this.cooldownMs = 350;
    }

    setThresholds(closeRatio, openRatio) {
        this.closeRatio = closeRatio;
        this.openRatio = openRatio;
    }

    updateFromMetrics(metrics, frameW) {
        const closeThreshold = this.closeRatio * frameW;
        const openThreshold = this.openRatio * frameW;
        const now = performance.now();

        const isFingertipsTouching = (metrics.topW <= closeThreshold && metrics.bottomW <= closeThreshold);
        let triggered = false;

        if (!this.isClosed) {
            if (isFingertipsTouching) {
                if (now - this.lastTriggerTime > this.cooldownMs) {
                    this.isClosed = true;
                    triggered = true;
                    this.lastTriggerTime = now;
                }
            }
        } else {
            if (metrics.topW >= openThreshold && metrics.bottomW >= openThreshold) {
                this.isClosed = false;
            }
        }

        return triggered;
    }

    getProgress(metrics, frameW) {
        const closeThreshold = this.closeRatio * frameW;
        const openThreshold = this.openRatio * frameW;
        const dist = typeof metrics === "number" ? metrics : Math.max(metrics.topW, metrics.bottomW);

        if (dist <= closeThreshold) return 1.0;
        if (dist >= openThreshold) return 0.0;
        return 1.0 - ((dist - closeThreshold) / (openThreshold - closeThreshold));
    }
}

// Reusable offscreen canvas for ROI rendering
let offscreenCanvas = null;
let offscreenCtx = null;

function getOffscreen(w, h) {
    if (!offscreenCanvas) {
        offscreenCanvas = document.createElement("canvas");
        offscreenCtx = offscreenCanvas.getContext("2d", { willReadFrequently: true });
    }
    if (offscreenCanvas.width !== w || offscreenCanvas.height !== h) {
        offscreenCanvas.width = w;
        offscreenCanvas.height = h;
    }
    return { canvas: offscreenCanvas, ctx: offscreenCtx };
}

/**
 * Builds the portal boundary path (straight quad or elastic curved bezier path with 3D perspective curvature)
 */
function buildPortalPath(ctx, p1, p2, p3, p4, elasticBending = true, offsetX = 0, offsetY = 0) {
    ctx.beginPath();

    const x1 = p1.x + offsetX, y1 = p1.y + offsetY;
    const x2 = p2.x + offsetX, y2 = p2.y + offsetY;
    const x3 = p3.x + offsetX, y3 = p3.y + offsetY;
    const x4 = p4.x + offsetX, y4 = p4.y + offsetY;

    if (!elasticBending) {
        ctx.moveTo(x1, y1);
        ctx.lineTo(x3, y3);
        ctx.lineTo(x4, y4);
        ctx.lineTo(x2, y2);
        ctx.closePath();
        return;
    }

    // Dynamic Elastic Membrane Curvature based on hand tension & 3D tilt
    const center = {
        x: (x1 + x2 + x3 + x4) / 4,
        y: (y1 + y2 + y3 + y4) / 4
    };

    const bendFactor = 0.07;

    const cpTop = {
        x: (x1 + x3) / 2 + (center.x - (x1 + x3) / 2) * bendFactor,
        y: (y1 + y3) / 2 + (center.y - (y1 + y3) / 2) * bendFactor
    };

    const cpRight = {
        x: (x3 + x4) / 2 + ((x3 + x4) / 2 - center.x) * (bendFactor * 0.4),
        y: (y3 + y4) / 2 + ((y3 + y4) / 2 - center.y) * (bendFactor * 0.4)
    };

    const cpBottom = {
        x: (x4 + x2) / 2 + (center.x - (x4 + x2) / 2) * bendFactor,
        y: (y4 + y2) / 2 + (center.y - (y4 + y2) / 2) * bendFactor
    };

    const cpLeft = {
        x: (x2 + x1) / 2 + ((x2 + x1) / 2 - center.x) * (bendFactor * 0.4),
        y: (y2 + y1) / 2 + ((y2 + y1) / 2 - center.y) * (bendFactor * 0.4)
    };

    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo(cpTop.x, cpTop.y, x3, x3.y || y3);
    ctx.quadraticCurveTo(cpRight.x, cpRight.y, x4, y4);
    ctx.quadraticCurveTo(cpBottom.x, cpBottom.y, x2, y2);
    ctx.quadraticCurveTo(cpLeft.x, cpLeft.y, x1, y1);
    ctx.closePath();
}

/**
 * Renders the perspective portal with full 3D volumetric extrusion, yaw/pitch depth tilt & perspective foreshortening
 */
export function renderPortal(ctx, p1, p2, p3, p4, filterFn, styleOptions = {}) {
    const {
        borderThickness = 2.5,
        borderStyle = "glow",
        showAnchors = true,
        triggerRipple = 0,
        elasticBending = true,
        depth3D = null
    } = styleOptions;

    const canvasW = ctx.canvas.width;
    const canvasH = ctx.canvas.height;

    // 1. Calculate 3D Depth Differentials & Rotation Vectors
    const leftZ = (p1.z !== undefined && p2.z !== undefined) ? (p1.z + p2.z) / 2.0 : 0;
    const rightZ = (p3.z !== undefined && p4.z !== undefined) ? (p3.z + p4.z) / 2.0 : 0;

    // Left vs Right hand depth disparity (closer hand = smaller z or larger pinch span)
    const leftSpan = Math.hypot(p1.x - p2.x, p1.y - p2.y);
    const rightSpan = Math.hypot(p3.x - p4.x, p3.y - p4.y);
    const spanRatio = (leftSpan - rightSpan) / Math.max(20, (leftSpan + rightSpan) / 2.0);

    const effectiveDepthDelta = (depth3D && depth3D.depthDelta !== undefined) ? depth3D.depthDelta : spanRatio;

    // 3D Parallax Extrusion Vectors
    const yawOffset = effectiveDepthDelta * 28.0; // Positive = left hand closer, negative = right hand closer
    const pitchOffset = (((p1.y + p3.y) / 2.0 - (p2.y + p4.y) / 2.0) / canvasH) * 18.0;

    // Calculate bounding box of the polygon
    const minX = Math.floor(Math.max(0, Math.min(p1.x, p2.x, p3.x, p4.x) - 16));
    const minY = Math.floor(Math.max(0, Math.min(p1.y, p2.y, p3.y, p4.y) - 16));
    const maxX = Math.ceil(Math.min(canvasW, Math.max(p1.x, p2.x, p3.x, p4.x) + 16));
    const maxY = Math.ceil(Math.min(canvasH, Math.max(p1.y, p2.y, p3.y, p4.y) + 16));

    const bw = maxX - minX;
    const bh = maxY - minY;

    if (bw <= 4 || bh <= 4) return;

    // 2. Draw 3D Volumetric Parallax Drop Shadow (gives deep 3D floating glass slab feel)
    if (borderStyle !== "none") {
        ctx.save();
        const shadowX = -yawOffset * 0.8;
        const shadowY = Math.abs(pitchOffset) * 0.5 + 10.0;

        ctx.shadowColor = "rgba(0, 0, 0, 0.65)";
        ctx.shadowBlur = 24;
        ctx.shadowOffsetX = shadowX;
        ctx.shadowOffsetY = shadowY;

        buildPortalPath(ctx, p1, p2, p3, p4, elasticBending, shadowX * 0.4, shadowY * 0.4);
        ctx.fillStyle = "rgba(2, 6, 16, 0.45)";
        ctx.fill();
        ctx.restore();
    }

    // 3. Extract ROI ImageData & Run Filter
    const roiImageData = ctx.getImageData(minX, minY, bw, bh);
    const processedImageData = filterFn(roiImageData, bw, bh);

    // 4. Put filtered pixels into offscreen buffer
    const { canvas: offCanvas, ctx: offCtx } = getOffscreen(bw, bh);
    offCtx.putImageData(processedImageData, 0, 0);

    // 5. Clip to dynamic 3D perspective path & composite onto canvas
    ctx.save();
    buildPortalPath(ctx, p1, p2, p3, p4, elasticBending);
    ctx.clip();

    ctx.drawImage(offCanvas, minX, minY);

    // 6. Draw 3D Perspective Glass Light Glint along the closer tilted plane
    if (Math.abs(effectiveDepthDelta) > 0.06) {
        const glintX = effectiveDepthDelta > 0 ? (p1.x + p2.x) / 2.0 : (p3.x + p4.x) / 2.0;
        const glintY = (p1.y + p2.y + p3.y + p4.y) / 4.0;
        const grad = ctx.createRadialGradient(glintX, glintY, 10, glintX, glintY, bw * 0.6);
        grad.addColorStop(0, "rgba(255, 255, 255, 0.22)");
        grad.addColorStop(0.4, "rgba(0, 240, 255, 0.08)");
        grad.addColorStop(1, "rgba(0, 0, 0, 0)");

        ctx.fillStyle = grad;
        ctx.fill();
    }

    ctx.restore();

    // 7. Draw 3D Perspective Border Outline (Thicker & Brighter on the Closer Hand side)
    if (borderStyle !== "none" && borderThickness > 0) {
        ctx.save();
        buildPortalPath(ctx, p1, p2, p3, p4, elasticBending);

        const leftCloser = effectiveDepthDelta > 0.05;
        const rightCloser = effectiveDepthDelta < -0.05;

        if (borderStyle === "glow") {
            const glowSize = triggerRipple > 0 ? (borderThickness * 4 + triggerRipple * 18) : (borderThickness * 3.8);

            // Red Chromatic Edge
            ctx.save();
            ctx.translate(-1.8 + yawOffset * 0.08, 0);
            ctx.shadowColor = "rgba(255, 30, 60, 0.85)";
            ctx.shadowBlur = Math.max(6, glowSize * 0.85);
            ctx.strokeStyle = "rgba(255, 40, 70, 0.9)";
            ctx.lineWidth = borderThickness * (leftCloser ? 1.4 : (rightCloser ? 0.9 : 1.1));
            ctx.stroke();
            ctx.restore();

            // Cyan Chromatic Edge
            ctx.save();
            ctx.translate(1.8 - yawOffset * 0.08, 0);
            ctx.shadowColor = "rgba(0, 240, 255, 0.95)";
            ctx.shadowBlur = Math.max(6, glowSize * 0.85);
            ctx.strokeStyle = "rgba(0, 240, 255, 0.95)";
            ctx.lineWidth = borderThickness * (rightCloser ? 1.4 : (leftCloser ? 0.9 : 1.1));
            ctx.stroke();
            ctx.restore();

            // Bright White Core Line
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = Math.max(1, borderThickness * 0.8);
            ctx.shadowColor = triggerRipple > 0 ? "#ffffff" : "rgba(255, 255, 255, 0.95)";
            ctx.shadowBlur = Math.max(4, glowSize * 0.5);
            ctx.stroke();
        } else if (borderStyle === "white") {
            ctx.shadowBlur = 0;
            ctx.shadowColor = "transparent";
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = borderThickness;
            ctx.stroke();
        }
        ctx.restore();
    }

    // 8. Draw 3D Depth Anchor Nodes with 3D Depth Rings
    if (showAnchors && borderStyle !== "none") {
        ctx.save();
        const anchors = [
            { pt: p1, isLeft: true },
            { pt: p2, isLeft: true },
            { pt: p3, isLeft: false },
            { pt: p4, isLeft: false }
        ];

        for (const { pt, isLeft } of anchors) {
            const isCloser = (isLeft && effectiveDepthDelta > 0.05) || (!isLeft && effectiveDepthDelta < -0.05);
            const nodeRadius = Math.max(3.5, Math.min(8.0, (borderThickness + 2.5) * (isCloser ? 1.35 : 0.95)));

            ctx.beginPath();
            ctx.arc(pt.x, pt.y, nodeRadius, 0, Math.PI * 2);

            if (borderStyle === "glow") {
                ctx.fillStyle = triggerRipple > 0 ? "#ffffff" : "rgba(255, 255, 255, 0.98)";
                ctx.shadowColor = isLeft ? "rgba(0, 240, 255, 0.95)" : "rgba(255, 40, 90, 0.95)";
                ctx.shadowBlur = isCloser ? 14 : 8;
                ctx.fill();
                ctx.strokeStyle = isLeft ? "#00f0ff" : "#ff0077";
                ctx.lineWidth = isCloser ? 2.6 : 1.8;
                ctx.stroke();
            } else {
                ctx.fillStyle = "#ffffff";
                ctx.fill();
            }
        }
        ctx.restore();
    }
}
