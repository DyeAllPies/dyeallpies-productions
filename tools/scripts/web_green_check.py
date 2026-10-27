"""Green pixels inside the sheet, as the FILE would carry them (2026-09-19, round four, First 1: the yellow -> cyan band must read as
a gradient with no green pixel, and the two traps are the 720 copy's downscale and the encoder's 4:2:0 chroma average, both of which
mix neighbouring pixels; a fine yellow/cyan pattern comes out green in the file even when no rendered pixel is green).

    python web_green_check.py <sheet_cov.npy> <frame.png|export.mp4> [frames=664,700,1010] [offset=0] [out=<png>]

For a PNG (a preview frame at 1080 x 1920, named ..._fNNNN.png) the check SIMULATES the file: resize to 720 x 1280 (area) and round-trip
through YUV 4:2:0 (cv2's I420), then counts, inside the sheet's coverage, the pixels whose hue is 75-165 deg at saturation > 0.2 and
value > 0.25 (render_web.ramp_check's rule for "green"). For an MP4 the frames are read as they are (the 720 copy is the one to give it;
`offset` = the source frame of the file's first frame). Prints per frame: the sheet's pixel count, the green count and share, the
largest connected green blob (px), and the mean hue of the green pixels; `out=` writes the green mask beside the frame (red = green
pixels) for a look at 1:1. The number to compare across yc modes is the share and the largest blob: a boundary line's blobs are thin
(< ~40 px at 720), a fused pattern's are the band itself.
"""
import os, sys
import numpy as np
import cv2


def green_mask(bgr, sat_min=0.2, val_min=0.25, hue=(75.0, 165.0)):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    h = hsv[..., 0] * 2.0; s = hsv[..., 1] / 255.0; v = hsv[..., 2] / 255.0
    return (h >= hue[0]) & (h <= hue[1]) & (s > sat_min) & (v > val_min), h


def as_file(bgr, W=720, H=1280):
    """The 720 copy through 4:2:0: what the encoder's chroma planes can carry (the luma stays per pixel)."""
    small = cv2.resize(bgr, (W, H), interpolation=cv2.INTER_AREA)
    i420 = cv2.cvtColor(small, cv2.COLOR_BGR2YUV_I420)
    return cv2.cvtColor(i420, cv2.COLOR_YUV2BGR_I420)


def check(bgr, cov, label, out=None):
    H, W = bgr.shape[:2]
    m = cv2.resize(cov, (W, H), interpolation=cv2.INTER_NEAREST) > 127
    g, h = green_mask(bgr); g &= m
    n_sheet = int(m.sum()); n_green = int(g.sum())
    blob = 0
    if n_green:
        nlab, lab, stats, _ = cv2.connectedComponentsWithStats(g.astype(np.uint8), connectivity=8)
        blob = int(stats[1:, cv2.CC_STAT_AREA].max())
    hm = float(np.median(h[g])) if n_green else float("nan")
    print(f"  {label}: sheet {n_sheet} px, green {n_green} px ({100.0 * n_green / max(n_sheet, 1):.2f} %), largest blob {blob} px, median hue {hm:.0f} deg")
    if out:
        vis = bgr.copy(); vis[g] = (0, 0, 255); cv2.imwrite(out, vis)
    return n_green, blob


def main():
    cov_path, src = sys.argv[1:3]; kw = dict(a.split("=", 1) for a in sys.argv[3:])
    cov = np.load(cov_path, mmap_mode="r"); offset = int(kw.get("offset", 0)); out = kw.get("out")
    if src.lower().endswith(".png"):
        i = int(os.path.basename(src).rsplit("_f", 1)[1][:4]) if "_f" in os.path.basename(src) else int(kw.get("frames", "0").split(",")[0])
        bgr = as_file(cv2.imread(src))
        print(f"{src} as the file would carry it (720, 4:2:0):")
        check(bgr, cov[i, ..., 0], f"frame {i}", out)
    else:
        cap = cv2.VideoCapture(src); frames = [int(x) for x in kw.get("frames", "664,700,1010").split(",")]
        print(f"{src}:")
        for i in frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i - offset); ok, fr = cap.read()
            if not ok: print(f"  frame {i}: not in the file"); continue
            check(fr, cov[i, ..., 0], f"frame {i}", out.replace(".png", f"_f{i:04d}.png") if out else None)


if __name__ == "__main__":
    main()
