"""Hand-and-forearm matte from MediaPipe's selfie multiclass segmenter (class 2 = body skin), for a
busy room where a colour key or rembg (a whole-person cut-out) cannot isolate the hands: the finger
web (web/PLAN.md section 4.5; verified 2026-09-18 on web/work/seg_classes.png, where class 2 cleanly
separated the hands and forearms from the face (class 3), the hair (1) and the shirt (4), and cut the
gaps between spread fingers).

    python extract_skin_matte.py <master.mp4> <hands.npz> <out_dir> [from=0] [to=n] [check=300,420,789,1080,1300]
                                 [band=8] [shrink=0.12] [roi=60] [min_area=15000] [hand_px=50] [feather=30] [hold=10] [out=matte.npy]

Writes out_dir/matte.npy (uint8, n x H x W memmap, 255 = hand or forearm, i.e. IN FRONT of the effect;
frames outside from..to stay 0) and out_dir/matte_check.png (1:1 crops on the check frames:
plate | refined matte tinted | the raw class-2 mask tinted).

ROUND THREE (2026-09-19, the finger web's round-two verdict, HANDOFF items 2 and 4): the matte is cut to the HANDS.
The alpha is kept only within `hand_px` px of a hand's landmark hull (the 21 landmarks include the wrist, so the palm
and the fingers are inside; the margin takes the wrist joint) and fades to 0 over `feather` px beyond it. Two things
were wrong with the whole body-skin component: (a) the forearm of a flipped hand lay OVER the sheet while its fingertip
held the sheet from the front (source 660-668: the sheet went behind the arm), and with the cut the forearm falls behind
the sheet and only the fingers stay in front; (b) a hand next to the face merged with the chin's and neck's skin
component and that part fluttered on and off (source 1174-1264, the chin box 0 -> 6 -> 0 -> 5 -> 1 %), and skin more
than the margin from the hull is now never kept. When a hand is untracked its last hull is held for `hold` frames (the
model bridges the same gaps); beyond that the sheet is not drawn at all (the model needs all its tips), so the matte
does not matter there. `hand_px=0` restores the round-two behaviour (the whole component, large components kept).

Method, and why each step:
- The segmenter runs in VIDEO mode on the full frame (0.34 s a frame on the RTX 2060 box, measured
  2026-09-18; a 640x800 hand crop cost 0.19 s and two hands need two crops, so cropping buys nothing:
  the model resamples its input to 256x256 either way).
- The class-2 CONFIDENCE mask (soft, 0..1) is used rather than the argmax category mask, whose edge is
  a step at the model's 256 px resolution.
- Only connected components of the hard mask (confidence > 0.5) that touch a tracked hand's landmark
  hull dilated by `roi` px are kept, plus any component above `min_area` px (an untracked hand or arm
  still on screen: MediaPipe drops a hand at the frame's edge in ~9% of frames). This drops the loose
  blobs the segmenter puts at the frame's edges (frame 1100, top right, in the planning session).
- The edge treatment is the hand-puppet matte's (tools/scripts/extract_hand_matte.py, 2026-09-11):
  inside a +-band px edge band the soft alpha goes through the guided filter (He, Sun & Tang 2010) on
  the plate's luminance, which snaps the 256 px model's ramp to the picture's own edge, and a `shrink`
  erosion of the ramp takes the halo.
"""
import os, sys, time
import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "..", "models", "selfie_multiclass_256x256.tflite")   # MediaPipe's model card: 0 background, 1 hair, 2 body-skin, 3 face-skin, 4 clothes, 5 others
BODY_SKIN = 2


def box(x, r):
    return cv2.blur(x, (2 * r + 1, 2 * r + 1), borderType=cv2.BORDER_REFLECT)


def guided_filter(I, p, r, eps):
    """He, Sun & Tang 2010 (ECCV; TPAMI 2013): grey guide I in [0,1], input p in [0,1]. As in extract_hand_matte.py."""
    mI, mp_ = box(I, r), box(p, r)
    cov = box(I * p, r) - mI * mp_
    var = box(I * I, r) - mI * mI
    a = cov / (var + eps)
    b = mp_ - a * mI
    return box(a, r) * I + box(b, r)


def keep_hand_components(hard, lm_px, roi, min_area):
    """hard: bool (H, W). lm_px: (2, 21, 2) landmark pixels per hand slot, nan when absent. Keeps the components
    that overlap a hand's dilated landmark hull, or that are large enough to be an untracked hand or arm."""
    H, W = hard.shape
    n, lab, stats, _ = cv2.connectedComponentsWithStats(hard.astype(np.uint8), connectivity=8)
    if n < 2: return np.zeros_like(hard)
    roi_mask = np.zeros((H, W), np.uint8)
    for h in range(lm_px.shape[0]):
        if np.isnan(lm_px[h, 0, 0]): continue
        pts = np.clip(lm_px[h], [-2000, -2000], [W + 2000, H + 2000]).astype(np.int32)
        hull = cv2.convexHull(pts)
        cv2.fillConvexPoly(roi_mask, hull, 1)
    if roi > 0 and roi_mask.any():
        roi_mask = cv2.dilate(roi_mask, np.ones((2 * roi + 1, 2 * roi + 1), np.uint8))
    keep = np.zeros(n, bool)
    for c in range(1, n):
        area = stats[c, cv2.CC_STAT_AREA]
        if area >= min_area: keep[c] = True; continue
        x, y, w, hh = stats[c, cv2.CC_STAT_LEFT], stats[c, cv2.CC_STAT_TOP], stats[c, cv2.CC_STAT_WIDTH], stats[c, cv2.CC_STAT_HEIGHT]
        if roi_mask[y:y + hh, x:x + w][lab[y:y + hh, x:x + w] == c].any(): keep[c] = True
    return keep[lab]


def hand_weight(lm_px, H, W, hand_px, feather):
    """(H, W) float32 in [0, 1]: 1 inside every tracked hand's landmark hull and to `hand_px` beyond it, then a linear fade
    to 0 over `feather` px (the round-three cut: the forearm and the face fall out of the matte). None when no hand is
    tracked (the caller holds the previous weight)."""
    hull = np.zeros((H, W), np.uint8); any_ = False
    for h in range(lm_px.shape[0]):
        if np.isnan(lm_px[h, 0, 0]): continue
        pts = np.clip(lm_px[h], [-2000, -2000], [W + 2000, H + 2000]).astype(np.int32)
        cv2.fillConvexPoly(hull, cv2.convexHull(pts), 255); any_ = True
    if not any_: return None
    d = cv2.distanceTransform(255 - hull, cv2.DIST_L2, 5)          # px outside the hulls (0 inside)
    return np.clip(1.0 - (d - hand_px) / max(feather, 1e-6), 0.0, 1.0).astype(np.float32)


def refine(bgr, conf, keep, band, shrink):
    """The soft class confidence, restricted to the kept components (dilated by the band so the soft edge
    survives), then the guided-filter band and the ramp erosion of extract_hand_matte.refine_frame."""
    hard = (conf > 0.5) & keep
    ker = np.ones((2 * band + 1, 2 * band + 1), np.uint8)
    inner = cv2.erode(hard.astype(np.uint8), ker) > 0
    outer = cv2.dilate(hard.astype(np.uint8), ker) > 0
    alpha = np.where(inner, 1.0, np.where(outer, conf, 0.0)).astype(np.float32)
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    a2 = guided_filter(g, alpha, 4, 2e-3)
    a2 = np.clip((a2 - shrink) / (1.0 - shrink), 0.0, 1.0)
    a2 = np.where(inner, 1.0, np.where(outer, a2, 0.0))
    return np.clip(a2 * 255.0 + 0.5, 0, 255).astype(np.uint8)


def main():
    video, hands_npz, out_dir = sys.argv[1:4]
    kw = dict(a.split("=", 1) for a in sys.argv[4:])
    os.makedirs(out_dir, exist_ok=True)
    z = np.load(hands_npz); img = z["img"]; W, H = int(z["width"]), int(z["height"]); n = img.shape[0]
    lm_px = img[..., :2] * np.array([W, H], np.float32)                 # (n, 2, 21, 2)
    f0 = int(kw.get("from", 0)); f1 = int(kw.get("to", n)); band = int(kw.get("band", 8)); shrink = float(kw.get("shrink", 0.12))
    roi = int(kw.get("roi", 60)); min_area = int(kw.get("min_area", 15000))
    hand_px = float(kw.get("hand_px", 50)); feather = float(kw.get("feather", 30)); hold = int(kw.get("hold", 10))   # round three: the cut to the hands
    want = [int(x) for x in kw.get("check", "300,420,789,1080,1300").split(",")]
    opts = vision.ImageSegmenterOptions(base_options=BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.VIDEO,
                                        output_category_mask=False, output_confidence_masks=True)
    seg = vision.ImageSegmenter.create_from_options(opts)
    cap = cv2.VideoCapture(video); fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    path = os.path.join(out_dir, kw.get("out", "matte.npy"))
    out = np.lib.format.open_memmap(path, mode="r+" if os.path.exists(path) else "w+", dtype=np.uint8, shape=(n, H, W))
    cap.set(cv2.CAP_PROP_POS_FRAMES, f0); t0 = time.time(); checks = {}
    wgt = None; wgt_age = 0; held = 0; chin = []
    print(f"matte: band {band}, shrink {shrink}, roi {roi}, min_area {min_area}; hand cut {hand_px:.0f} px + {feather:.0f} px feather beyond the landmark hull (hold {hold} frames)" if hand_px > 0 else "matte: no hand cut (round two's whole components)")
    for i in range(f0, f1):
        ok, fr = cap.read()
        if not ok: break
        res = seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)), int(round(i * 1000.0 / fps)))
        conf = np.asarray(res.confidence_masks[BODY_SKIN].numpy_view(), np.float32).reshape(H, W)
        keep = keep_hand_components(conf > 0.5, lm_px[i], roi, min_area if hand_px <= 0 else 10 ** 9)   # with the cut, only components at a tracked hand
        m = refine(fr, conf, keep, band, shrink)
        if hand_px > 0:
            w = hand_weight(lm_px[i], H, W, hand_px, feather)
            if w is not None: wgt = w; wgt_age = 0
            elif wgt is not None and wgt_age < hold: wgt_age += 1; held += 1
            else: wgt = None
            m = (m.astype(np.float32) * wgt + 0.5).astype(np.uint8) if wgt is not None else np.zeros_like(m)
        m[:2] = 0; m[-2:] = 0; m[:, :2] = 0; m[:, -2:] = 0          # border rows never carry alpha (the puppet's black-plate lesson)
        out[i] = m
        chin.append((i, 100.0 * (m[900:1050, 420:660] > 128).mean()))     # the round-two flutter's box (HANDOFF 2026-09-19 item 2), printed at the end
        if i in want: checks[i] = (fr, m.copy(), (conf > 0.5).astype(np.uint8) * 255)
        if (i - f0) % 20 == 0: print(f"{i}/{f1} {(time.time() - t0) / (i - f0 + 1):.2f} s/frame", flush=True)
    out.flush()
    c = [(i, v) for i, v in chin if 1174 <= i <= 1264]
    if c: print("chin box (y 900-1050, x 420-660) coverage over 1174-1264, %: max " + f"{max(v for _, v in c):.1f}, " + " ".join(f"{i}:{v:.0f}" for i, v in c if i % 3 == 0))
    if held: print(f"hand hull held across {held} untracked frames")
    rows = []
    for i, (fr, m, raw) in checks.items():
        for h in range(2):
            if np.isnan(lm_px[i, h, 0, 0]): continue
            cx, cy = np.nanmean(lm_px[i, h], axis=0).astype(int)
            y0, y1 = max(cy - 260, 0), min(cy + 260, H); x0, x1 = max(cx - 220, 0), min(cx + 220, W)
            def tint(mm):
                o = fr.copy(); w = mm < 128; o[w] = (o[w] * 0.55 + np.array([255, 60, 0]) * 0.45).astype(np.uint8); return o
            tiles = [fr[y0:y1, x0:x1], tint(m)[y0:y1, x0:x1], tint(raw)[y0:y1, x0:x1]]
            row = np.hstack(tiles); cv2.putText(row, f"{i} h{h}", (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            rows.append(row)
    if rows:
        w = max(r.shape[1] for r in rows)
        rows = [np.hstack([r, np.zeros((r.shape[0], w - r.shape[1], 3), np.uint8)]) if r.shape[1] < w else r for r in rows]
        cv2.imwrite(os.path.join(out_dir, "matte_check.png"), np.vstack(rows))
    print(f"matte done: frames {f0}..{f1 - 1} in {time.time() - t0:.0f} s -> {path}")


if __name__ == "__main__":
    main()
