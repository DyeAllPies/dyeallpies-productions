/**
 * tracking.js - High-Precision Kinematic Hand Tracking & 3D Depth Spatial Stabilization
 * Features 3D hand depth estimation, yaw/pitch rotation tracking, and temporal grace persistence
 * to ensure that separating both hands far apart NEVER fails or drops the portal.
 */

// Landmark Indices
const WRIST = 0;
const THUMB_CMC = 1;
const THUMB_MCP = 2;
const THUMB_IP = 3;
const THUMB_TIP = 4;
const INDEX_MCP = 5;
const INDEX_PIP = 6;
const INDEX_DIP = 7;
const INDEX_TIP = 8;
const MIDDLE_MCP = 9;

/**
 * 1-Euro Adaptive Filter with High-Speed Responsiveness
 */
class AdaptivePointFilter {
    constructor(minCutoff = 0.08, beta = 0.85, deadbandPx = 1.0) {
        this.minCutoff = minCutoff;
        this.beta = beta;
        this.deadbandPx = deadbandPx;

        this.xPrev = null;
        this.yPrev = null;
        this.dxPrev = 0;
        this.dyPrev = 0;
        this.tPrev = null;
    }

    filter(x, y, timestamp) {
        if (this.xPrev === null || this.tPrev === null) {
            this.xPrev = x;
            this.yPrev = y;
            this.dxPrev = 0;
            this.dyPrev = 0;
            this.tPrev = timestamp;
            return { x, y };
        }

        const dt = Math.max((timestamp - this.tPrev) / 1000.0, 0.001);
        this.tPrev = timestamp;

        const dist = Math.hypot(x - this.xPrev, y - this.yPrev);
        if (dist < this.deadbandPx) {
            return { x: this.xPrev, y: this.yPrev };
        }

        const dx = (x - this.xPrev) / dt;
        const dy = (y - this.yPrev) / dt;
        const speed = Math.hypot(dx, dy);

        const cutoff = this.minCutoff + this.beta * speed;
        const alpha = Math.min(1.0, (2.0 * Math.PI * cutoff * dt) / (2.0 * Math.PI * cutoff * dt + 1.0));

        const xFiltered = this.xPrev + alpha * (x - this.xPrev);
        const yFiltered = this.yPrev + alpha * (y - this.yPrev);

        this.xPrev = xFiltered;
        this.yPrev = yFiltered;

        return { x: xFiltered, y: yFiltered };
    }

    reset() {
        this.xPrev = null;
        this.yPrev = null;
        this.dxPrev = 0;
        this.dyPrev = 0;
        this.tPrev = null;
    }
}

class PortalPointSmoother {
    constructor() {
        this.fP1 = new AdaptivePointFilter(0.06, 0.90, 1.0); // Left Index
        this.fP2 = new AdaptivePointFilter(0.05, 0.90, 1.2); // Left Thumb
        this.fP3 = new AdaptivePointFilter(0.06, 0.90, 1.0); // Right Index
        this.fP4 = new AdaptivePointFilter(0.05, 0.90, 1.2); // Right Thumb
    }

    smooth(current, timestamp) {
        if (!current) {
            this.reset();
            return null;
        }

        return {
            p1: this.fP1.filter(current.p1.x, current.p1.y, timestamp),
            p2: this.fP2.filter(current.p2.x, current.p2.y, timestamp),
            p3: this.fP3.filter(current.p3.x, current.p3.y, timestamp),
            p4: this.fP4.filter(current.p4.x, current.p4.y, timestamp),
            leftHand: current.leftHand,
            rightHand: current.rightHand,
            depth3D: current.depth3D,
            count: 2
        };
    }

    reset() {
        this.fP1.reset();
        this.fP2.reset();
        this.fP3.reset();
        this.fP4.reset();
    }
}

export class HandTracker {
    constructor() {
        this.hands = null;
        this.isLoaded = false;
        this.onResultsCallback = null;
        this.lastResults = null;
        this.smoother = new PortalPointSmoother();

        // Persistent Hand Identity Tracking
        this.prevLeftWrist = null;
        this.prevRightWrist = null;

        // Temporal Grace Persistence (holds 2-hand portal for up to 10 frames during fast movement/separation)
        this.lastValidPortalData = null;
        this.graceCounter = 0;
        this.MAX_GRACE_FRAMES = 10;
    }

    async init() {
        if (typeof window.Hands === "undefined") {
            throw new Error("MediaPipe Hands library is not loaded from CDN.");
        }

        this.hands = new window.Hands({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
        });

        // Hyper-sensitive thresholds (0.15) for flawless detection when hands separate far apart
        this.hands.setOptions({
            maxNumHands: 2,
            modelComplexity: 1,
            minDetectionConfidence: 0.15,
            minTrackingConfidence: 0.15
        });

        this.hands.onResults((results) => {
            this.lastResults = results;
            if (this.onResultsCallback) {
                this.onResultsCallback(results);
            }
        });

        this.isLoaded = true;
    }

    onResults(callback) {
        this.onResultsCallback = callback;
    }

    async send(imageElement) {
        if (this.hands) {
            await this.hands.send({ image: imageElement });
        }
    }

    /**
     * Estimates 3D relative depth of hand based on palm scale and z coordinate
     * Smaller value = closer to camera, Larger value = further from camera
     */
    estimateHandDepth(handLandmarks) {
        const wrist = handLandmarks[WRIST];
        const middleMcp = handLandmarks[MIDDLE_MCP];
        const indexMcp = handLandmarks[INDEX_MCP];

        // Palm physical span in image normalized coords
        const palmSpan = Math.hypot(wrist.x - middleMcp.x, wrist.y - middleMcp.y);
        const rawZ = (wrist.z + middleMcp.z + indexMcp.z) / 3.0;

        // Effective depth: inverse of palm span (larger palm = closer hand) + landmark z
        const scaleDepth = 1.0 / Math.max(0.04, palmSpan);
        return scaleDepth * 0.75 + rawZ * 2.5;
    }

    /**
     * Kinematic Phalanx Bone Projection for Index Finger
     */
    getStabilizedIndexTip(handLandmarks, width, height) {
        const dip = handLandmarks[INDEX_DIP];
        const pip = handLandmarks[INDEX_PIP];
        const tip = handLandmarks[INDEX_TIP];

        const dipX = dip.x * width;
        const dipY = dip.y * height;
        const pipX = pip.x * width;
        const pipY = pip.y * height;
        const tipX = tip.x * width;
        const tipY = tip.y * height;

        const boneVx = dipX - pipX;
        const boneVy = dipY - pipY;
        const boneLen = Math.hypot(boneVx, boneVy) || 1.0;

        const tipDist = Math.hypot(tipX - dipX, tipY - dipY);
        const projTipX = dipX + (boneVx / boneLen) * tipDist;
        const projTipY = dipY + (boneVy / boneLen) * tipDist;

        return {
            x: tipX * 0.85 + projTipX * 0.15,
            y: tipY * 0.85 + projTipY * 0.15,
            z: tip.z || 0
        };
    }

    /**
     * Kinematic Phalanx Bone Projection for Thumb
     */
    getStabilizedThumbTip(handLandmarks, width, height) {
        const mcp = handLandmarks[THUMB_MCP];
        const ip = handLandmarks[THUMB_IP];
        const tip = handLandmarks[THUMB_TIP];

        const mcpX = mcp.x * width;
        const mcpY = mcp.y * height;
        const ipX = ip.x * width;
        const ipY = ip.y * height;
        const tipX = tip.x * width;
        const tipY = tip.y * height;

        const boneVx = ipX - mcpX;
        const boneVy = ipY - mcpY;
        const boneLen = Math.hypot(boneVx, boneVy) || 1.0;

        const tipDist = Math.hypot(tipX - ipX, tipY - ipY);
        const projTipX = ipX + (boneVx / boneLen) * tipDist;
        const projTipY = ipY + (boneVy / boneLen) * tipDist;

        return {
            x: tipX * 0.85 + projTipX * 0.15,
            y: tipY * 0.85 + projTipY * 0.15,
            z: tip.z || 0
        };
    }

    /**
     * Extracts portal points (p1, p2, p3, p4), 3D depth differentials, and rotation angles.
     */
    extractPortalPoints(results, width, height) {
        const now = performance.now();

        if (!results || !results.multiHandLandmarks || results.multiHandLandmarks.length === 0) {
            // Check temporal grace period
            if (this.lastValidPortalData && this.graceCounter < this.MAX_GRACE_FRAMES) {
                this.graceCounter++;
                return this.lastValidPortalData;
            }
            this.smoother.reset();
            this.prevLeftWrist = null;
            this.prevRightWrist = null;
            this.lastValidPortalData = null;
            this.graceCounter = 0;
            return null;
        }

        const handCount = results.multiHandLandmarks.length;

        // 1. Duplicate single-hand check
        if (handCount >= 2) {
            const h0 = results.multiHandLandmarks[0];
            const h1 = results.multiHandLandmarks[1];
            const wristDist = Math.hypot(h0[WRIST].x - h1[WRIST].x, h0[WRIST].y - h1[WRIST].y);

            if (wristDist < 0.035) {
                this.smoother.reset();
                this.prevLeftWrist = null;
                this.prevRightWrist = null;

                const isLeft = h0[WRIST].x > 0.5;
                const indexTip = this.getStabilizedIndexTip(h0, width, height);
                const thumbTip = this.getStabilizedThumbTip(h0, width, height);
                return {
                    singleHand: { isLeft, hand: h0, indexTip, thumbTip },
                    count: 1
                };
            }
        }

        // 2. Single hand mode with grace period support
        if (handCount === 1) {
            // If we previously had 2 hands and one hand momentarily drifted, maintain portal for grace frames
            if (this.lastValidPortalData && this.graceCounter < this.MAX_GRACE_FRAMES) {
                this.graceCounter++;
                return this.lastValidPortalData;
            }

            this.smoother.reset();
            this.prevLeftWrist = null;
            this.prevRightWrist = null;
            this.lastValidPortalData = null;
            this.graceCounter = 0;

            const h = results.multiHandLandmarks[0];
            let isLeft = h[WRIST].x > 0.5;
            if (results.multiHandedness && results.multiHandedness.length > 0) {
                const label = results.multiHandedness[0].label || results.multiHandedness[0].displayName || "";
                if (label === "Left") isLeft = true;
                else if (label === "Right") isLeft = false;
            }

            const indexTip = this.getStabilizedIndexTip(h, width, height);
            const thumbTip = this.getStabilizedThumbTip(h, width, height);

            return {
                singleHand: { isLeft, hand: h, indexTip, thumbTip },
                count: 1
            };
        }

        // 3. Two distinct hands mode (Portal Active)
        this.graceCounter = 0; // Reset grace on solid 2-hand detection

        const h0 = results.multiHandLandmarks[0];
        const h1 = results.multiHandLandmarks[1];

        let leftHand = null;
        let rightHand = null;

        // Continuous spatial identity: In mirrored viewport, screen-left hand has raw x > other.x
        if (h0[WRIST].x > h1[WRIST].x) {
            leftHand = h0;
            rightHand = h1;
        } else {
            leftHand = h1;
            rightHand = h0;
        }

        this.prevLeftWrist = { x: leftHand[WRIST].x, y: leftHand[WRIST].y };
        this.prevRightWrist = { x: rightHand[WRIST].x, y: rightHand[WRIST].y };

        const p1 = this.getStabilizedIndexTip(leftHand, width, height);
        const p2 = this.getStabilizedThumbTip(leftHand, width, height);
        const p3 = this.getStabilizedIndexTip(rightHand, width, height);
        const p4 = this.getStabilizedThumbTip(rightHand, width, height);

        // 4. Calculate 3D Depth Differentials & Rotation Angles
        const zLeft = this.estimateHandDepth(leftHand);
        const zRight = this.estimateHandDepth(rightHand);
        const avgDepth = (zLeft + zRight) / 2.0;
        const depthDelta = (zRight - zLeft) / Math.max(0.5, avgDepth); // > 0 if left hand is closer

        // 3D Angles
        const dx = (p3.x - p1.x);
        const dy = (p3.y - p1.y);
        const rollRad = Math.atan2(dy, dx);
        const yawDeg = Math.max(-60, Math.min(60, depthDelta * 48.0)); // degrees
        const pitchDeg = Math.max(-45, Math.min(45, (((p1.y + p3.y) / 2.0 - (p2.y + p4.y) / 2.0) / height) * 60.0));

        const depth3D = {
            zLeft,
            zRight,
            depthDelta,
            yawDeg,
            pitchDeg,
            rollRad,
            closerHand: depthDelta > 0.08 ? "left" : (depthDelta < -0.08 ? "right" : "even")
        };

        const rawPoints = { p1, p2, p3, p4, leftHand, rightHand, depth3D };
        const smoothedData = this.smoother.smooth(rawPoints, now);
        this.lastValidPortalData = smoothedData;
        return smoothedData;
    }

    /**
     * Draws targeting aura and nodes for single hand mode
     */
    drawSingleHandAura(ctx, singleHand) {
        if (!singleHand) return;
        const { isLeft, indexTip, thumbTip } = singleHand;
        ctx.save();

        const color = isLeft ? "#00f0ff" : "#ff0077";

        // Connecting arc between index and thumb
        ctx.beginPath();
        ctx.moveTo(indexTip.x, indexTip.y);
        ctx.lineTo(thumbTip.x, thumbTip.y);
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.5;
        ctx.shadowColor = color;
        ctx.shadowBlur = 12;
        ctx.stroke();

        // Node rings
        [indexTip, thumbTip].forEach((pt) => {
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 6.5, 0, Math.PI * 2);
            ctx.fillStyle = "#ffffff";
            ctx.fill();
            ctx.strokeStyle = color;
            ctx.lineWidth = 2.5;
            ctx.stroke();
        });

        ctx.restore();
    }

    /**
     * Draws skeleton connections for a hand
     */
    drawHandSkeleton(ctx, handLandmarks, width, height, isLeft) {
        if (!handLandmarks || handLandmarks.length < 21) return;
        ctx.save();

        const color = isLeft ? "rgba(0, 240, 255, 0.75)" : "rgba(255, 0, 119, 0.75)";
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.8;
        ctx.shadowColor = color;
        ctx.shadowBlur = 8;

        const connections = [
            [0, 1], [1, 2], [2, 3], [3, 4],       // Thumb
            [0, 5], [5, 6], [6, 7], [7, 8],       // Index
            [5, 9], [9, 10], [10, 11], [11, 12],  // Middle
            [9, 13], [13, 14], [14, 15], [15, 16],// Ring
            [13, 17], [17, 18], [18, 19], [19, 20],// Pinky
            [0, 17]                               // Palm base
        ];

        for (const [i, j] of connections) {
            const p1 = handLandmarks[i];
            const p2 = handLandmarks[j];
            ctx.beginPath();
            ctx.moveTo(p1.x * width, p1.y * height);
            ctx.lineTo(p2.x * width, p2.y * height);
            ctx.stroke();
        }

        for (let i = 0; i < 21; i++) {
            const lm = handLandmarks[i];
            ctx.beginPath();
            ctx.arc(lm.x * width, lm.y * height, i % 4 === 0 ? 3.5 : 2.0, 0, Math.PI * 2);
            ctx.fillStyle = i % 4 === 0 ? "#ffffff" : color;
            ctx.fill();
        }

        ctx.restore();
    }
}
