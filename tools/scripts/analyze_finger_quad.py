"""Measure the two-hand "finger frame" in a recording: which frames carry a usable quad, how wide
the corner span gets, and how fast it changes.

    python analyze_finger_quad.py <hands.npz> [out.json]

The quad corners are the thumb tip (landmark 4) and the index tip (landmark 8) of each hand -- the
same four points the reference reel feeds to render_portal(frame, p1, p2, p3, p4, FILTRO)
(mishu.ksv, "#spiderman #python #software", screen recording 2026-09-18, web/originals/).

Signals printed, all in pixels of the upright master unless noted:
  span    the diagonal of the quad's corner cloud (max pairwise corner distance) -- the raw
          "how far apart are his hands" measure the elastic rest length will be calibrated against.
  area    the quad's polygon area by the shoelace formula, in fractions of the frame area; the
          membrane's areal stretch J = area / area_rest drives the hole opening.
  hand_px the palm width of each hand (landmark 5 index MCP to 17 pinky MCP) -- the per-frame
          scale reference that turns pixel spans into hand-relative units, so the numbers survive
          the subject moving toward or away from the lens.
  d/dt    the per-frame change of span, in px per frame, the input to any velocity-dependent
          (viscoelastic) term.
"""
import json
import sys

import numpy as np

LM_THUMB, LM_INDEX, LM_IMCP, LM_PMCP, LM_WRIST = 4, 8, 5, 17, 0

z = np.load(sys.argv[1])
img, score, handed = z["img"], z["score"], z["handed"]
W, H, fps = int(z["width"]), int(z["height"]), float(z["fps"])
n = img.shape[0]

px = np.stack([img[..., 0] * W, img[..., 1] * H], -1)           # (n, 2 hands, 21, xy) in master pixels
present = ~np.isnan(px[:, :, 0, 0])                              # (n, 2) a hand was detected
both = present.all(axis=1)

# The quad: four corners per frame, ordered so the polygon does not self-intersect (sort the four
# points by angle about their own centroid -- the hands may swap left/right across the frame).
corners = np.full((n, 4, 2), np.nan, np.float32)
for i in np.flatnonzero(both):
    pts = np.array([px[i, 0, LM_THUMB], px[i, 0, LM_INDEX], px[i, 1, LM_THUMB], px[i, 1, LM_INDEX]])
    c = pts.mean(0)
    corners[i] = pts[np.argsort(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))]

# span = the largest distance between any two corners (the quad's diagonal when it is convex)
span = np.full(n, np.nan, np.float32)
area = np.full(n, np.nan, np.float32)
for i in np.flatnonzero(both):
    p = corners[i]
    span[i] = max(np.linalg.norm(p[a] - p[b]) for a in range(4) for b in range(a + 1, 4))
    x, y = p[:, 0], p[:, 1]                                       # shoelace, absolute (winding-free)
    area[i] = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

# palm width per hand: the knuckle line 5->17, MediaPipe's most stable in-plane scale reference
palm = np.full((n, 2), np.nan, np.float32)
for h in range(2):
    ok = present[:, h]
    palm[ok, h] = np.linalg.norm(px[ok, h, LM_IMCP] - px[ok, h, LM_PMCP], axis=-1)
palm_mean = np.nanmean(palm, axis=1)

dspan = np.full(n, np.nan, np.float32)
dspan[1:] = span[1:] - span[:-1]

runs, start = [], None                                            # contiguous stretches with both hands
for i in range(n + 1):
    if i < n and both[i] and start is None: start = i
    elif (i == n or not both[i]) and start is not None:
        if i - start >= 5: runs.append((start, i - 1))
        start = None


def q(a, ps=(5, 25, 50, 75, 95)):
    v = a[~np.isnan(a)]
    return {f"p{p}": round(float(np.percentile(v, p)), 1) for p in ps} if v.size else {}


print(f"frames {n}  fps {fps:.3f}  {W}x{H}  both hands on {both.sum()} ({100*both.mean():.0f}%)")
print(f"span px      {q(span)}  min {np.nanmin(span):.0f} max {np.nanmax(span):.0f}")
print(f"area %frame  { {k: round(v / (W*H) * 100, 2) for k, v in q(area).items()} }")
print(f"palm px      {q(palm_mean)}")
print(f"span / palm  {q(span / palm_mean)}")
print(f"|dspan| px/f {q(np.abs(dspan))}  max {np.nanmax(np.abs(dspan)):.1f}  "
      f"(= {np.nanmax(np.abs(dspan))*fps:.0f} px/s)")
print(f"\n{len(runs)} usable runs (>=5 frames with both hands):")
for a, b in runs:
    s = span[a:b + 1]
    print(f"  {a:4d}-{b:4d}  {a/fps:5.2f}-{b/fps:5.2f}s  {b-a+1:4d}f  "
          f"span {np.nanmin(s):4.0f}-{np.nanmax(s):4.0f} px  "
          f"(x{np.nanmax(s)/max(np.nanmin(s),1):.2f} stretch)")

if len(sys.argv) > 2:
    json.dump({"fps": fps, "W": W, "H": H, "both": both.tolist(),
               "span": np.where(np.isnan(span), None, span).tolist(),
               "area": np.where(np.isnan(area), None, area).tolist(),
               "palm": np.where(np.isnan(palm_mean), None, palm_mean).tolist(),
               "runs": runs}, open(sys.argv[2], "w"), indent=0)
    print(f"\nwrote {sys.argv[2]}")
