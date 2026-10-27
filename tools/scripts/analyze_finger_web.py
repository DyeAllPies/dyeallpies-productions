"""Measure the TEN-fingertip membrane in a two-hand recording: the anchor cloud, its areal stretch,
its rate of change, and how often the tracking is good enough to hang an elastic sheet on it.

    python analyze_finger_web.py <hands.npz> [out.npz]

Why ten tips and not the reference reel's four: mishu.ksv frames a rectangle with the thumb and
index of each hand (render_portal(frame, p1..p4, FILTRO)); Dennis's take (web/originals/IMG_6268.MOV,
2026-09-18) is both palms to camera with all five fingers SPREAD. Measured on that take, her four
points fit it badly: in 35% of the two-hand frames at least one hand is pinched (thumb tip to index
tip under half a palm width), collapsing the quad to a triangle, and the quad covers a median 0.47
of the area the ten fingertips span (0.04 at p10). The ten fingertips are the anchors his gesture
actually offers, and they are what an elastic sheet with "lines between the fingers" must hang
from.

Signals, per frame:
  tips      (10, 2) the fingertip pixels, hand 0 then hand 1, thumb->pinky (landmarks 4,8,12,16,20)
  hull_a    the convex hull area of the ten tips, in px^2 -- the membrane's current spanned area
  J         hull_a / hull_rest, the AREAL STRETCH RATIO. hull_rest is taken as a low percentile of
            hull_a over the take (the relaxed, hands-together state), so J >= 1 means stretched.
            A hyperelastic sheet's holes open where J passes a threshold (see the plan's model).
  sep       distance between the two hands' palm centres (mean of landmarks 0,5,17) -- the blunt
            "how far he pushed it" signal, independent of finger spread.
  spread    per hand, the mean distance from that hand's five tips to their own centroid, in palm
            widths -- fingers open vs closed, which changes the sheet's boundary independently of
            the hands' separation.
  palm      per hand, the index-MCP to pinky-MCP distance in px: the scale reference that turns
            pixels into hand-relative units when he moves toward or away from the lens.
  z         per hand, the mean model z of the five tips (MediaPipe's image-space depth, roughly in
            units of image width, negative = nearer the camera than the wrist).
"""
import sys

import numpy as np

TIPS = [4, 8, 12, 16, 20]          # thumb, index, middle, ring, pinky
PALM = [0, 5, 17]                  # wrist, index MCP, pinky MCP -- the palm centre triangle

z = np.load(sys.argv[1])
img = z["img"]; W, H, fps = int(z["width"]), int(z["height"]), float(z["fps"])
n = img.shape[0]
px = np.stack([img[..., 0] * W, img[..., 1] * H], -1)
present = ~np.isnan(px[:, :, 0, 0])
both = present.all(axis=1)

tips = np.full((n, 10, 2), np.nan, np.float32)
tips[:, :5] = px[:, 0, TIPS]
tips[:, 5:] = px[:, 1, TIPS]

palm = np.full((n, 2), np.nan, np.float32)
centre = np.full((n, 2, 2), np.nan, np.float32)
spread = np.full((n, 2), np.nan, np.float32)
depth = np.full((n, 2), np.nan, np.float32)
for h in range(2):
    ok = present[:, h]
    palm[ok, h] = np.linalg.norm(px[ok, h][:, 5] - px[ok, h][:, 17], axis=-1)
    centre[ok, h] = px[ok, h][:, PALM].mean(axis=1)
    t = px[ok, h][:, TIPS]                                          # (m, 5, 2)
    spread[ok, h] = np.linalg.norm(t - t.mean(1, keepdims=True), axis=-1).mean(1) / np.maximum(palm[ok, h], 1)
    depth[ok, h] = img[ok, h][:, TIPS, 2].mean(1)

sep = np.full(n, np.nan, np.float32)
sep[both] = np.linalg.norm(centre[both, 0] - centre[both, 1], axis=-1)


def hull_area(p):
    """Convex hull area by an Andrew monotone chain + shoelace (no scipy dependency)."""
    p = p[np.lexsort((p[:, 1], p[:, 0]))]
    def cross2(o, a, b):                                            # numpy 2 dropped the 2-D np.cross
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    def half(pts):
        out = []
        for q in pts:
            while len(out) >= 2 and cross2(out[-2], out[-1], q) <= 0: out.pop()
            out.append(q)
        return out[:-1]
    h = np.array(half(p) + half(p[::-1]))
    x, y = h[:, 0], h[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))), len(h)


hull_a = np.full(n, np.nan, np.float32)
hull_k = np.zeros(n, np.int8)
for i in np.flatnonzero(both):
    hull_a[i], hull_k[i] = hull_area(tips[i].astype(np.float64))

palm_mean = np.where(both, np.nanmean(palm, axis=1), np.nan)
hull_norm = hull_a / palm_mean ** 2                                  # area in palm-widths squared
rest = np.nanpercentile(hull_norm, 10)                               # the relaxed state of THIS take
J = hull_norm / rest

dJ = np.full(n, np.nan, np.float32); dJ[1:] = J[1:] - J[:-1]


def q(a, ps=(2, 10, 25, 50, 75, 90, 98), scale=1.0, nd=2):
    """Percentiles, scaled then rounded ONCE -- rounding before a caller's own scaling turned a
    median hull area of 8.3% of the frame into 8.0% (2026-09-18)."""
    v = a[~np.isnan(a)]
    return {f"p{p}": round(float(np.percentile(v, p)) * scale, nd) for p in ps} if v.size else {}


print(f"frames {n}  fps {fps:.3f}  {W}x{H}   both hands {both.sum()} ({100*both.mean():.0f}%)")
print(f"hull px^2 / frame area %   {q(hull_a / (W * H), scale=100)}")
print(f"hull in palm^2             {q(hull_norm)}   rest (p10) = {rest:.2f}")
print(f"J = areal stretch          {q(J)}   max {np.nanmax(J):.2f}")
print(f"|dJ| per frame             {q(np.abs(dJ))}   max {np.nanmax(np.abs(dJ)):.2f}")
print(f"hull vertices (of 10)      {np.bincount(hull_k[both], minlength=11)[3:].tolist()} for k=3..10")
print(f"palm width px              {q(palm_mean)}")
print(f"hand separation px         {q(sep)}")
print(f"separation in palms        {q(sep / palm_mean)}")
print(f"finger spread (palms)      h0 {q(spread[:, 0], (10, 50, 90))}  h1 {q(spread[:, 1], (10, 50, 90))}")
print(f"tip depth z (img units)    h0 {q(depth[:, 0], (10, 50, 90))}  h1 {q(depth[:, 1], (10, 50, 90))}")

# where the sheet would be at its most stretched, and where it rests
order = np.argsort(np.where(np.isnan(J), -1, J))
print(f"\nmost stretched frames: {[(int(i), round(float(J[i]), 2), round(i/fps, 2)) for i in order[-6:][::-1]]}")
print(f"most relaxed frames:   {[(int(i), round(float(J[i]), 2), round(i/fps, 2)) for i in order[both.sum()//40:both.sum()//40+6] if not np.isnan(J[i])]}")

if len(sys.argv) > 2:
    np.savez_compressed(sys.argv[2], tips=tips, both=both, hull_a=hull_a, hull_norm=hull_norm, J=J,
                        sep=sep, spread=spread, palm=palm, depth=depth, centre=centre,
                        rest=rest, fps=fps, W=W, H=H)
    print(f"\nwrote {sys.argv[2]}")
