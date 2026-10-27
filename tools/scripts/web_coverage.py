"""The sheet's coverage per frame, as the matte check_flicker.py measures inside: the composited region
of the finger-web render is the sheet (its outline polygon), not the hands, so the gate gets this
instead of the hand matte.

    python web_coverage.py <membrane.npz> <out.npy> [scale=8]

Writes (n, H/scale, W/scale, 1) uint8, 255 inside the outline; check_flicker resizes it to the frame.
"""
import json, sys
import numpy as np
import cv2

M = np.load(sys.argv[1]); out = sys.argv[2]; kw = dict(a.split("=", 1) for a in sys.argv[3:]); s = int(kw.get("scale", 8))
p = json.loads(str(M["params"])); W, H = int(p["W"]), int(p["H"])
valid = M["valid"] | M["released"]; n_hull = M["n_hull"]; strings = M["strings_px"]; n = len(valid)
cov = np.zeros((n, H // s, W // s, 1), np.uint8)
for i in range(n):
    if not valid[i]: continue
    poly = strings[i, :n_hull[i]].reshape(-1, 2); poly = poly[~np.isnan(poly[:, 0])]
    if len(poly) < 3: continue
    cv2.fillPoly(cov[i, ..., 0], [np.round(np.clip(poly / s, -4000, 4000)).astype(np.int32)], 255)
np.save(out, cov)
print(f"wrote {out} {cov.shape}, sheet present on {int((cov.reshape(n, -1).max(1) > 0).sum())} frames")
