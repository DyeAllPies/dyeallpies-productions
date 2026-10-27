"""The finger web's membrane: round one (2026-09-18) an elastic dough sheet held by the ten fingertips; round two
(2026-09-19) the same mechanism on FOUR anchors, the thumbs and index fingers, as a thick ribbon that appears at
the four-finger touch, twists when a hand flips and snaps into the second touch. Modelled in image space and
written out one record per frame for render_web.py.

    python web_membrane.py <hands.npz> <out.npz> [rest_frame=auto] [jstar=1.15] [n_defects=24] [seed=7]
        [grid=48] [v_open=0.75] [v_close=0.30] [r_max=0.55] [margin=0.35] [thr_spread=0.25]
        [min_cutoff=1.5] [beta=0.01] [d_cutoff=15] [max_gap=10] [fall=1] [warp=mls|tps] [eps_mls=0.02] [eps_def=0.5]
        [tips=all|thumb,index] [outline=hull|ring] [touch=0.8] [appear=auto|<frame>|none] [snap=auto|<frame>|none]
        [snap_after=1000] [snap_frames=5] [grow=1]
        [reel=1] [pinch=0.6] [pinch_open=1.2] [relax=1.5] [snap_mode=fade|contract] [settle_v=8] [settle_n=5]
        [short_sag=0] [tsmooth=5] [contact=twist|pinch|none] [contact_px=18] [fold_in=4] [fold_out=8] [fold_w=0.22] [twist=helicoid|none] [couple=1] [nu=0.5]

ROUND THREE, SECOND PASS (2026-09-19 late night, his notes on the export):
- THE SHORT EDGES NEVER SAG (`short_sag=0`): the thumb -> index edge inside one hand has the effective rest length min(L0, span),
  a straight line; the material between two fingers of one hand lies across the hand, it does not hang. The long edges keep
  their catenaries. (Before: 0.4-0.8 palm loops beside each thumb at source 1174-1294, read as "an extra hanger".)
- THE EDGE STRETCH IS WRITTEN OUT (`stretch`, span / effective rest length per edge): the lines are coloured on the sheet's own
  ramp at lambda^2, so a line and the material next to it read one scale.
- `tsmooth=9` in the shipped command (was 5): the look field's temporal median, against the one real colour flash of the round-three
  export (source 1010, the whole band blue -> yellow over two frames as the hull's J crossed the ramp's yellow -> blue band); the
  ramp's band is also wider now (render_web.LOOKS["spectrum"]).

ROUND THREE (2026-09-19, Dennis's verdict on round two, HANDOFF items 3, 5 and 6):
- THE REEL-IN (`reel=1`): a pinch that closes gathers the ribbon into itself. Per hand, the pinch gap is the thumb-to-
  index distance in palms; the hand is REELING while the gap is under `pinch` palms (closed) or under `pinch_open`
  palms and closing (the 3-frame difference negative). While a hand reels, every edge that ends at that hand has its
  rest length ratchet DOWN to its current span (never up), so the short edge tightens as the fingers close and the
  long edges tighten as the two pinches approach; when the hand stops reeling the rest length relaxes back toward
  its rest value at `relax` palms/s. The rest lengths are otherwise round two's (the pull-out before the rest frame,
  the rest quad after). Measured on the take before this rule: from source 1264 every edge was slack (the long ones
  1.8-3.5 palms) because the rest is the 514 quad and the pinches close 3 palms apart, and at 454-484 the left short
  edge carried 0.74 palm of slack from a loose pinch at the touch. The printed check is the slack per edge per second
  (source and export clocks), which must read 0 from the pinch's closing (~source 1280) to the snap and at the start.
  The mechanism (the catenary when slack, straight when taut) is unchanged; only the rest length gains a state.
- THE SNAP IS A FADE (`snap_mode=fade`): with the reel-in the band has no length left at the second touch, so the
  sheet FADES over `snap_frames` (snap_f is the alpha the renderer applies) instead of contracting into the centre
  (`snap_mode=contract` is round two's).
- THE NEAR EDGE AT A CROSSING (`near_edge` per frame, -1 when the outline is simple): when a hand flips the two long
  edges cross in the image at the fold line. Which passes in front is set by the twist's sense, read off MediaPipe's
  per-hand depth (z, smaller = nearer the camera) of the flipping hand's thumb and index tips at the entry of each
  bow-tie run: the projected thumb -> index segment reverses exactly when it is edge-on, and at that instant the
  tip that is nearer is the tip whose edge is nearer at every crossing until the ribbon untwists (the ruling at the
  crossing is the hand's ruling at its edge-on instant, rotated along). Measured on this take: at all three flips the
  thumb tip is the farther one (dz +0.03..+0.07), so the index edge is drawn over the thumb edge. The decision per
  run is printed (frame, hand, dz, edge).
- THE THUMBS-UP SETTLE (`fire_frame` in params): the first frame after the snap at which both thumb tips are above
  their wrists and no tip moved more than `settle_v` px/frame over the last `settle_n` frames: the fire's in-point
  (render_web_scene.py `fire=auto`). Measured: source 1435 (export 40.7 s); the hands rise at 1418-1429 at up to
  250 px/frame and hold from 1430.

ROUND TWO (2026-09-19, Dennis's verdict on round one; `tips=thumb,index`):
- Only the thumbs and index fingers hold the sheet (landmarks 4 and 8 of each hand: four anchors). Measured on
  the take: from source 300 to 480 each hand's thumb and index are pinched to 0.1-0.2 palm with the two pinches
  6 palms apart, so the four points ARE a line; the quad opens at 492-498 (1.3 -> 9.8 palm^2).
- NOTHING APPEARS until the four tips touch (`appear=auto`: the first frame where all four are within `touch`
  palms of each other; source 240 here, export 0.9 s) and the sheet SNAPS INTO THE SECOND TOUCH (`snap=auto`:
  the first such frame after `snap_after`; source 1338, 37.5 s): over `snap_frames` frames its image contracts
  into the tips' centre, then it is gone. No release and no fall (the plan's section 12 sting is superseded).
- THE OUTLINE IS THE RIBBON'S OWN EDGES (`outline=ring`, the default with four anchors): the ring thumb0 ->
  thumb1 -> index1 -> index0, the two long edges between the hands and the two short edges inside each hand.
  With ten tips a fixed ring self-intersected in his pose and the convex hull replaced it (round one); with
  four it is a simple quad whenever no hand is flipped and becomes the BOW-TIE exactly when one is: the
  projection of a ribbon twisted half a turn, which is the picture Dennis asked for ("twisting like a very
  thick ribbon"). The convex hull would put the rest DIAGONALS on the outline at a flip and the interior
  would crush instead of twist. `outline=hull` keeps round one's rule.
- THE TWIST NEEDS NO NEW MODEL: the flipped hand's thumb -> index direction reverses, so the rest quad maps
  to a quad with one end reversed and the MLS interior FOLDS across the middle (J < 0 on the far half,
  `grid_Jraw`): the renderer draws the J < 0 region as the ribbon's back face. The fold appears, travels and
  resolves with the hand because the anchors are the real tips through the whole rotation; the printed check
  is the folded fraction per frame through each flip (a step means a tip was lost mid-flip).
- THE REST STATE is the first fully open quad, source 514 (`rest_frame=514`, Dennis's default; the largest
  quad of the take, 11.9 palm^2 at 668, is mid-flip). Before it the ribbon is being PULLED OUT of the touch
  (`grow=1`): each string's rest length is the largest span that pair has reached so far, capped at its rest
  length, so the band grows out of the touch point taut as the hands part and sags only where they come back;
  from the rest frame on the rest lengths are fixed and the mechanism is round one's ("the first stretch is
  the taut reference", applied to the stretch while it is being made).
- Everything else is round one's: palm units, the 1-Euro filter, the catenaries, the MLS-affine interior
  and its areal stretch J, the seeded holes.

What the sheet is (web/PLAN.md sections 3 and 7; every constant's source and rank in web/WEB-MODEL.md):

- ANCHORS: the ten fingertips (MediaPipe landmarks 4, 8, 12, 16, 20 of each hand), the two hands told
  apart by CONTINUITY of the palm centre frame to frame, not by MediaPipe's slot order (the slots swap
  in 584 of the 1335 two-hand frames of the 2026-09-18 take) nor by its handedness label (disagrees
  with continuity in 8 hand-frames). Gaps of up to `max_gap` frames are bridged by linear interpolation
  (the prior art's 10-frame temporal grace, references/finger-web/code/aadishy-hand-gesture-filter-README.md).
- SMOOTHING: the 1-Euro filter (Casiez, Roussel & Vogel 2012, papers/casiez2012-one-euro-filter.pdf)
  per coordinate: a first-order low-pass whose cutoff rises with speed, f_c = min_cutoff + beta |dx/dt|.
  The take's jitter floor is 0.7 px and its fastest snap 274 px/frame (data/01-membrane-numbers.csv);
  min_cutoff 1.5 Hz smooths a hold, beta 0.01 (per px/s) opens the cutoff to ~80 Hz on the snap, and the
  derivative's own low-pass d_cutoff is 15 Hz rather than the paper's 1 Hz default so the cutoff opens
  within a frame of the snap (at 1 Hz the sheet trailed the fingertip by 100 px on the fastest frames).
  The prior art's 0.06 / 0.85 are in its own units and are not reused.
- SCALE: everything is solved in PALM UNITS (px / the mean index-MCP-to-pinky-MCP distance of the two
  hands, smoothed at 1 Hz), so leaning toward the lens does not stretch the sheet (plan section 2).
- REST STATE: "the first stretch is the taut reference" (Dennis): the rest configuration is the ten
  tips at the frame of the largest hull area in the first two-hand run (frames 29-129 of this take,
  plan section 3.6), in palm units about their centroid. Written into the output as constants, so a
  re-trim of the video leaves the material alone (plan section 3.6's trap).
- THE OUTLINE AND THE STRINGS: the sheet's visible outline is the CONVEX HULL of the ten tips in each
  frame (plan section 1: 6 of the 10 tips on a typical frame; the rest are interior pins pressing on
  the sheet). Each hull edge (a, b) is a string with the rest length L0 = |R_a - R_b|, the two tips'
  distance in the rest configuration. An edge whose span is >= L0 is TAUT and straight, with
  tension = span / L0 - 1; one whose span is < L0 is SLACK by L0 - span and hangs as the EXACT
  CATENARY of an inextensible thread, ported verbatim from tools/scripts/render_puppet.py:122
  (catenary_points; memory port-referenced-look-from-code) with image y-down mapped to its z-up. The
  parabolic closed form sag = sqrt(3 span dL / 8) (papers/johndcook-catenary-sag-approximation.txt) is
  printed against the port as the check on it. A fixed ring through all ten tips in anatomical order
  was tried first (2026-09-18) and is not a simple polygon in his pose (the thumbs hang below the
  pinky-to-pinky chord), so the sheet folded over itself in 1331 frames; the hull never does.
- THE INTERIOR: the sheet between the strings is the MOVING-LEAST-SQUARES AFFINE deformation of the rest
  sheet by the ten pins and the strings (Schaefer, McPhail & Warren 2006; `warp=mls`, the default): at
  every material point the affine map that best fits the controls under weights 1 / (r^2 + eps^2), so
  the sheet passes through every fingertip and along every string and, between them, deforms like the
  weighted average of its neighbours' motion. It is kinematic: round one has no inertia and no in-plane
  elasticity of its own; the plan's XPBD sheet (section 3.1) is the round-two upgrade if the interior
  needs to jiggle or lag. The local matrix gives, per point, the AREAL STRETCH J = det(dImage/dRest)
  (rest = 1) and the principal stretches: the quantity every look and hole rule keys off (plan section
  3.1, Wang, O'Brien & Ramamoorthi 2010 for J = lambda1 lambda2). A defect senses the strain of its
  neighbourhood, the same map evaluated with a wide kernel (eps_def palms), not the pixel under it.
  The thin-plate spline (Bookstein 1989; `warp=tps`) was the first choice and is kept for comparison:
  its interpolant overshoots between pins that are pinched together and folded the sheet in 1274 of
  1338 frames. Between the strings the sheet is bounded by them in the image (the renderer masks it by
  the outline polyline); material the outline no longer encloses is not drawn.
- THICKNESS: the sheet is volume-incompressible, h = h0 / J (plan section 3.3): thin where stretched,
  thick and opaque where slack (the renderer draws that).
- HOLES (plan section 3.4, references/finger-web/01 section 5): (a) nucleation at a SEEDED DEFECT FIELD:
  `n_defects` defects at fixed-seed random rest positions at least `margin` palms inside the rest
  outline (the rim of a hand-held sheet is thicker: assumed), each with its own threshold J*_i = jstar +
  Exp(thr_spread) (Gent & Lindley 1959 via papers/lopezpamies2024-cavitation-jmps.pdf: a strength
  threshold per defect; the spread is assumed). A defect opens when the 5-frame median of J at its
  rest position passes J*_i (the median because |dJ| spikes are tracking glitches, plan section 8.4).
  (b) growth at the Taylor-Culick speed, v = v_open sqrt(J / jstar) palms/s (v_TC = sqrt(2 gamma / rho h)
  with h = h0 / J, papers/villermaux2022 eq. 1.1: the thinner, the faster). (c) a hole stops growing
  when J falls under its threshold and CLOSES at v_close once J is below 0.9 J*_i (Griffith: growth needs
  the released elastic energy to exceed the fracture energy; the closing is the viscoelastic recovery
  the honest framing allows, "holes stop growing and slowly close"). r is capped at r_max palms.
- RELEASE: after the last frame with both hands the sheet FALLS under real gravity in pixels,
  g_px = 9.81 m/s^2 x (palm px / 0.080 m) (index-MCP to pinky-MCP breadth 8.0 cm: assumed from the
  ANSUR II male hand breadth of 8.9 cm at the metacarpals, ranked in WEB-MODEL.md), which is the
  ending the plan's section 12 sting picks up.

Output (np.savez, K = the number of anchors, 10 or 4): valid (n,), released (n,), grid_px (n, Gy, Gx, 2) the
sheet's rest grid mapped to the image in px (with the fall or the snap applied), grid_J (n, Gy, Gx), grid_lmin
(n, Gy, Gx) the smaller principal stretch, grid_uv (Gy, Gx, 2) the grid's rest coordinates in palm units,
rest_poly (k, 2) the rest outline in palm units, n_hull (n,), hull_idx (n, K) the tips on the outline in cyclic
order (-1 padded), strings_px (n, K, 25, 2) the outline's edges in that order (nan padded), tension (n, K),
slack (n, K), span (n, K), L0 (K, K) rest distances, holes_r (n, N) radii in palm units, defects (N, 2), thr
(N,), scale (n,) px per palm, tips_px (n, K, 2) smoothed, J_global (n,), fall_dy (n,), snap_f (n,) the snap's
contraction (1 = intact, 0 = gone), folded (n,) the folded fraction of the rest sheet, twisted (n,) the outline
self-intersects (a flip), params (json: appear, snap, rest_frame, tips, outline, ...).
"""
import json, os, sys, time
import numpy as np
from scipy.optimize import brentq
from scipy.spatial import ConvexHull, QhullError

TIP_LM = dict(thumb=4, index=8, middle=12, ring=16, pinky=20)   # MediaPipe hand landmarks
TIPS = [4, 8, 12, 16, 20]          # thumb, index, middle, ring, pinky (round one: all five per hand)
PALM = (5, 17)                     # index MCP, pinky MCP: the palm-width scale reference (analyze_finger_web.py)
PALM_CENTRE = [0, 5, 17]           # wrist, index MCP, pinky MCP: the palm centre used for the continuity assignment
NAMES = ["t0", "i0", "m0", "r0", "p0", "t1", "i1", "m1", "r1", "p1"]   # hand 0 = the image-left hand
FPS = 30.0
RUN_A = (29, 130)                  # the first two-hand run of the take (plan section 2): the calibration window
HAND_BREADTH_M = 0.080             # index-MCP to pinky-MCP, metres: ASSUMED (ANSUR II male hand breadth 8.9 cm is at the metacarpal heads,
                                   # the MCP-to-MCP landmark distance is a little less); ranked in web/WEB-MODEL.md. Only the fall uses it.
G = 9.81                           # m/s^2
NS = 25                            # points per string polyline


# ----------------------------------------------------------------------------------------------------
# the catenary, ported verbatim from tools/scripts/render_puppet.py:122 (2026-09-12 version) -- world
# coordinates with z up; catenary_2d below maps image space (y down) onto it. Do not edit here: a fix
# belongs in both files (memory port-referenced-look-from-code).
def catenary_points(A, B, L, n=40):
    """Points along an inextensible thread of length L hanging between A and B (world, z up). Straight
    when L <= chord. The catenary z = a cosh((x - x0)/a) + c in the vertical plane through A-B: a from
    2 a sinh(h / 2a) = sqrt(L^2 - v^2) (brentq), then x0, c from the endpoints (03 confirms the form)."""
    A = np.asarray(A, float); B = np.asarray(B, float)
    d = B - A; v = d[2]; hvec = d.copy(); hvec[2] = 0; h = np.linalg.norm(hvec)
    chord = np.linalg.norm(d); s = np.linspace(0, 1, n)
    if L <= chord * 1.0005 or h < 1e-6:
        if h < 1e-6 and L > chord:      # hanging straight down with slack: the thread bows out sideways (a vertical
            ex = (L - chord) / 2          # droop drew as a spike under the fist at the release, 2026-09-12)
            pts = A[None] + s[:, None] * d[None]
            pts[:, 0] += np.sin(np.pi * s) * ex * 0.8
            pts[:, 2] -= np.sin(np.pi * s) * ex * 0.3
            return pts
        return A[None] + s[:, None] * d[None]
    span = np.sqrt(max(L * L - v * v, 1e-12))
    if span <= h * (1 + 1e-6):                  # no sag to speak of: the root is beyond any bracket (crashed the bake, 2026-09-11)
        return A[None] + s[:, None] * d[None]
    f = lambda a: 2 * a * np.sinh(min(h / (2 * a), 700)) - span
    try:
        a = brentq(f, 1e-4, 1e4)
    except ValueError:
        return A[None] + s[:, None] * d[None]
    # x along the horizontal chord from A (x=0) to B (x=h); solve x0 so that z(h) - z(0) = v
    x0 = h / 2 - a * np.arcsinh(v / (2 * a * np.sinh(h / (2 * a))))
    c = A[2] - a * np.cosh((0 - x0) / a)
    x = s * h; z = a * np.cosh((x - x0) / a) + c
    u = hvec / h
    pts = A[None] + x[:, None] * u[None] + (z - A[2])[:, None] * np.array([0, 0, 1.0])[None]
    if h < 0.02 and L > chord + 0.01:     # a loop whose chord runs along the depth axis projects as a vertical spike
        ex = (L - chord) / 2               # (the head string at the release, 2026-09-12): bow it sideways, as a real
        pts[:, 0] += np.sin(np.pi * s) * ex * 0.6 * (1 - h / 0.02)     # slack thread never hangs in one plane
    return pts
# ----------------------------------------------------------------------------------------------------


def catenary_2d(A, B, L, n=NS):
    """The exact catenary in image space (x right, y DOWN): (x, y) -> world (x, 0, -y), so gravity points to +y.
    Returned with `n` points at EQUAL ARC LENGTH (equal material fractions): the port samples equal x
    steps along the chord, and the interior warp needs material fractions."""
    A3 = np.array([A[0], 0.0, -A[1]]); B3 = np.array([B[0], 0.0, -B[1]])
    p = catenary_points(A3, B3, L, 64)
    pts = np.stack([p[:, 0], -p[:, 2]], 1)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    if cum[-1] < 1e-9: return np.repeat(pts[:1], n, 0)
    f = np.linspace(0, 1, n) * cum[-1]
    return np.stack([np.interp(f, cum, pts[:, 0]), np.interp(f, cum, pts[:, 1])], 1)


def sag_parabolic(span, dL):
    """The shallow-sag closed form, papers/johndcook-catenary-sag-approximation.txt (Frame 1950 refines it):
    extra length = 8 sag^2 / (3 span)  =>  sag = sqrt(3 span dL / 8). The check on the port, not the model."""
    return np.sqrt(3.0 * span * dL / 8.0)


class OneEuro:
    """Casiez, Roussel & Vogel 2012: x_hat = a x + (1 - a) x_hat_prev with a from the cutoff
    f_c = min_cutoff + beta |dx_hat/dt|, the derivative itself low-passed at d_cutoff."""

    def __init__(self, rate, min_cutoff, beta, d_cutoff=1.0):
        self.rate = rate; self.min_cutoff = min_cutoff; self.beta = beta; self.d_cutoff = d_cutoff; self.x = None; self.dx = 0.0

    @staticmethod
    def alpha(rate, cutoff):
        tau = 1.0 / (2 * np.pi * cutoff); te = 1.0 / rate
        return 1.0 / (1.0 + tau / te)

    def __call__(self, v):
        if self.x is None:
            self.x = v; self.dx = 0.0; return v
        dx = (v - self.x) * self.rate
        self.dx = self.dx + self.alpha(self.rate, self.d_cutoff) * (dx - self.dx)
        fc = self.min_cutoff + self.beta * abs(self.dx)
        self.x = self.x + self.alpha(self.rate, fc) * (v - self.x)
        return self.x

    def reset(self):
        self.x = None; self.dx = 0.0


def smooth_signal(x, rate, min_cutoff, beta, d_cutoff=1.0):
    """1-Euro over a 1-D signal with nan gaps: the filter restarts after a gap."""
    f = OneEuro(rate, min_cutoff, beta, d_cutoff); out = np.full_like(x, np.nan)
    for i, v in enumerate(x):
        if np.isnan(v): f.reset(); continue
        out[i] = f(float(v))
    return out


def fill_gaps(x, max_gap):
    """Linear interpolation across nan runs of at most max_gap frames (1-D)."""
    x = x.copy(); n = len(x); ok = ~np.isnan(x)
    if ok.sum() < 2: return x
    i = 0
    while i < n:
        if not np.isnan(x[i]): i += 1; continue
        j = i
        while j < n and np.isnan(x[j]): j += 1
        if i > 0 and j < n and (j - i) <= max_gap:
            x[i:j] = np.interp(np.arange(i, j), [i - 1, j], [x[i - 1], x[j]])
        i = j
    return x


def assign_hands(px, present):
    """Continuity assignment of MediaPipe's two slots to two persistent hands: hand 0 is the hand on the
    image's LEFT at the first two-hand frame; afterwards the permutation that moves the palm centres
    least is kept. Returns (n, 2) slot indices (-1 = absent) and the count of frames where the slots
    were swapped relative to the previous frame's order."""
    n = px.shape[0]
    with np.errstate(all="ignore"):
        centre = np.nanmean(px[:, :, PALM_CENTRE, :], axis=2)
    assign = np.full((n, 2), -1, int); prev = None; swaps = 0
    for i in range(n):
        ok = present[i]
        if ok.all():
            if prev is None: assign[i] = np.argsort(centre[i, :, 0])
            else:
                d0 = np.linalg.norm(centre[i, 0] - prev[0]) + np.linalg.norm(centre[i, 1] - prev[1])
                d1 = np.linalg.norm(centre[i, 1] - prev[0]) + np.linalg.norm(centre[i, 0] - prev[1])
                assign[i] = [0, 1] if d0 <= d1 else [1, 0]
            if assign[i, 0] != 0: swaps += 1
            prev = centre[i, assign[i]].copy()
        elif ok.any():
            s = int(np.flatnonzero(ok)[0])
            if prev is None: assign[i, 0] = s; prev = np.stack([centre[i, s], centre[i, s] + [1e6, 0]])
            else:
                a = 0 if np.linalg.norm(centre[i, s] - prev[0]) <= np.linalg.norm(centre[i, s] - prev[1]) else 1
                assign[i, a] = s; prev = prev.copy(); prev[a] = centre[i, s]
    return assign, swaps


def polygon_simple(P):
    """True when the closed polygon P (k, 2) has no two non-adjacent edges crossing."""
    k = len(P)
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    def inter(p1, p2, p3, p4):
        d1 = cross(p3, p4, p1); d2 = cross(p3, p4, p2); d3 = cross(p1, p2, p3); d4 = cross(p1, p2, p4)
        return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))
    for i in range(k):
        for j in range(i + 2, k):
            if i == 0 and j == k - 1: continue
            if inter(P[i], P[(i + 1) % k], P[j], P[(j + 1) % k]): return False
    return True


def point_in_polygon(pts, P):
    """Even-odd test of pts (m, 2) against the polygon P (k, 2)."""
    x, y = pts[:, 0], pts[:, 1]; inside = np.zeros(len(pts), bool); k = len(P)
    for i in range(k):
        x1, y1 = P[i]; x2, y2 = P[(i + 1) % k]
        c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)
        inside ^= c
    return inside


def dist_to_polygon(pts, P):
    """Unsigned distance from pts (m, 2) to the polygon's boundary."""
    k = len(P); d = np.full(len(pts), np.inf)
    for i in range(k):
        a = P[i]; b = P[(i + 1) % k]; ab = b - a; t = np.clip(((pts - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        d = np.minimum(d, np.linalg.norm(pts - (a + t[:, None] * ab), axis=1))
    return d


# ---- the thin-plate spline (Bookstein 1989): f(q) = a0 + a1 x + a2 y + sum_i w_i U(|q - X_i|), U(r) = r^2 log r
def tps_fit(X, Y, lam=1e-3):
    """X (K, 2) rest controls, Y (K, 2) their image positions. Returns (w (K, 2), a (3, 2)). lam regularises
    coincident or collinear controls (a pinched pair, a slack loop with a zero chord)."""
    K = len(X); r2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    U = np.where(r2 > 1e-12, 0.5 * r2 * np.log(r2 + 1e-30), 0.0)      # r^2 log r = 0.5 r^2 log r^2
    P = np.concatenate([np.ones((K, 1)), X], 1)
    A = np.zeros((K + 3, K + 3)); A[:K, :K] = U + lam * np.eye(K); A[:K, K:] = P; A[K:, :K] = P.T
    b = np.zeros((K + 3, 2)); b[:K] = Y
    sol = np.linalg.lstsq(A, b, rcond=None)[0]
    return sol[:K], sol[K:]


def tps_eval(X, w, a, Q):
    """Image positions of the rest points Q (M, 2) and the Jacobian (M, 2, 2) of the map, analytically:
    dU/dq = (2 log r + 1) (q - X_i) (the r log r limit at r = 0 is 0)."""
    D = Q[:, None, :] - X[None, :, :]; r2 = (D ** 2).sum(-1)
    logr2 = np.log(r2 + 1e-30)
    U = np.where(r2 > 1e-12, 0.5 * r2 * logr2, 0.0)
    f = a[0][None] + Q @ a[1:] + U @ w                                              # (M, 2)
    g = np.where(r2 > 1e-12, logr2 + 1.0, 0.0)                                       # 2 log r + 1
    Jx = (g * D[..., 0]) @ w; Jy = (g * D[..., 1]) @ w                               # d f / d x, d f / d y  (M, 2)
    Jm = np.stack([Jx, Jy], -1)                                                      # (M, 2 (f component), 2 (d/dx, d/dy))
    Jm[:, 0, 0] += a[1, 0]; Jm[:, 1, 0] += a[1, 1]; Jm[:, 0, 1] += a[2, 0]; Jm[:, 1, 1] += a[2, 1]
    return f, Jm


def stretches(Jm):
    """Areal stretch det F and the smaller principal stretch (the singular values of F, Wang et al. 2010)."""
    det = Jm[:, 0, 0] * Jm[:, 1, 1] - Jm[:, 0, 1] * Jm[:, 1, 0]
    sv = np.linalg.svd(Jm, compute_uv=False)
    return det, sv[:, 1] * np.sign(det)


# ---- moving least squares, affine (Schaefer, McPhail & Warren 2006, "Image deformation using moving least
# squares", section 2.1): at every point v the affine map best fitting the controls P -> Qc under the weights
# w_i = 1 / (|p_i - v|^2 + eps^2) (their alpha = 1; eps keeps the weight finite ON a control). f(v) = (v - p*) M + q*
# with p*, q* the weighted centroids and M = (sum w p^ T p^)^-1 sum w p^ T q^. The local matrix M is the
# deformation gradient's transpose, so its determinant is the areal stretch and its singular values the
# principal stretches. Chosen over the thin-plate spline (2026-09-18): the TPS interpolant overshoots between
# pins a palm apart that are pinched to one point, its Jacobian ran from -8 to +7 and folded the sheet in 1274
# frames; the MLS map stays between the pins' own pairwise stretches.
def mls_affine(P, Qc, V, eps):
    """P (K, 2) rest controls, Qc (K, 2) their image positions, V (M, 2) rest query points. Returns f(V) (M, 2)
    and the local 2x2 matrices (M, 2, 2)."""
    D = V[:, None, :] - P[None, :, :]
    w = 1.0 / ((D ** 2).sum(-1) + eps * eps)
    ws = w.sum(1, keepdims=True)
    ps = (w[..., None] * P[None]).sum(1) / ws; qs = (w[..., None] * Qc[None]).sum(1) / ws
    ph = P[None] - ps[:, None]; qh = Qc[None] - qs[:, None]
    A = np.einsum("mk,mki,mkj->mij", w, ph, ph); B = np.einsum("mk,mki,mkj->mij", w, ph, qh)
    det = A[:, 0, 0] * A[:, 1, 1] - A[:, 0, 1] * A[:, 1, 0]
    Ainv = np.stack([np.stack([A[:, 1, 1], -A[:, 0, 1]], -1), np.stack([-A[:, 1, 0], A[:, 0, 0]], -1)], 1) / np.maximum(det, 1e-12)[:, None, None]
    Mx = Ainv @ B
    f = np.einsum("mi,mij->mj", V - ps, Mx) + qs
    return f, np.transpose(Mx, (0, 2, 1))


def main():
    hands_npz, out = sys.argv[1], sys.argv[2]
    kw = dict(a.split("=", 1) for a in sys.argv[3:])
    jstar = float(kw.get("jstar", 1.15)); n_def = int(kw.get("n_defects", 24)); seed = int(kw.get("seed", 7))
    Gn = int(kw.get("grid", 48)); v_open = float(kw.get("v_open", 0.75)); v_close = float(kw.get("v_close", 0.30))
    r_max = float(kw.get("r_max", 0.55)); margin = float(kw.get("margin", 0.35)); thr_spread = float(kw.get("thr_spread", 0.25))
    min_cutoff = float(kw.get("min_cutoff", 1.5)); beta = float(kw.get("beta", 0.01)); d_cutoff = float(kw.get("d_cutoff", 15.0)); max_gap = int(kw.get("max_gap", 10))
    do_fall = kw.get("fall", "1") == "1"
    warp = kw.get("warp", "mls"); eps_mls = float(kw.get("eps_mls", 0.02)); eps_def = float(kw.get("eps_def", 0.5))
    eps_look = float(kw.get("eps_look", 0.3)); tsmooth = int(kw.get("tsmooth", 5))   # the strain field the LOOK reads: a neighbourhood's, median over 5 frames
    release_kw = kw.get("release", "auto")           # the frame after which the sheet is let go and falls (auto = the last two-hand frame)
    # round two (2026-09-19): the anchor subset, the outline rule, the touch detectors, the pull-out
    tip_names = ["thumb", "index", "middle", "ring", "pinky"] if kw.get("tips", "all") == "all" else kw["tips"].split(",")
    lm = [TIP_LM[t] for t in tip_names]; K = 2 * len(lm)
    names = [t[0] + "0" for t in tip_names] + [t[0] + "1" for t in tip_names]           # hand 0 = the image-left hand
    outline = kw.get("outline", "ring" if K == 4 else "hull")
    touch = float(kw.get("touch", 0.8)); snap_after = int(kw.get("snap_after", 1000)); snap_frames = int(kw.get("snap_frames", 5))
    grow = kw.get("grow", "1") == "1"
    # round three (2026-09-19): the reel-in, the fade at the snap, the thumbs-up settle
    reel = kw.get("reel", "1") == "1" and K == 4; pinch_thr = float(kw.get("pinch", 0.6)); pinch_open = float(kw.get("pinch_open", 1.2)); relax = float(kw.get("relax", 1.5))
    reel_v = float(kw.get("reel_v", 6.0))              # palms/s the rest length is reeled in at: the hands approach at up to 5 palms/s in the last half
                                                       # second of this take (spans 3.1 -> 0.6 palms over 1318-1339), and a slower reel (2 palm/s was
                                                       # tried) let 1.2 palms of sag rebuild before the touch; 6 keeps up and still takes a 2-palm sag
                                                       # over 10 frames rather than one (assumed, judged on the printed slack table)
    settle_fold = float(kw.get("settle_fold", 0.5))    # a thumbs-up: the index tip at least this many palms BELOW the thumb tip (folded), both hands; at the
                                                       # second touch the index tips are level with or above the thumbs (-0.3..-1.2 palms), at the thumbs-up +1.0
    snap_mode = kw.get("snap_mode", "fade"); settle_v = float(kw.get("settle_v", 8)); settle_n = int(kw.get("settle_n", 5))
    short_sag = kw.get("short_sag", "0") == "1"       # 1 = the short edges (thumb -> index inside one hand) may sag as catenaries (rounds two and
                                                       # three); 0 = they are straight, rest length min(L0, span) (2026-09-19 late night, see the loop)
    appear_kw = kw.get("appear", "auto" if K == 4 else "none"); snap_kw = kw.get("snap", "auto" if K == 4 else "none")
    if K == 4 and kw.get("rest_frame", "auto") == "auto": kw["rest_frame"] = "514"   # the first fully open quad (Dennis's default, 2026-09-19)
    z = np.load(hands_npz); img = z["img"]; W, H = int(z["width"]), int(z["height"]); n = img.shape[0]
    px = img[..., :2] * np.array([W, H], np.float32); present = ~np.isnan(px[:, :, 0, 0])

    # 1. two persistent hands
    assign, swaps = assign_hands(px, present)
    tips = np.full((n, K, 2), np.nan, np.float32); palm = np.full((n, 2), np.nan, np.float32)
    wrist = np.full((n, 2, 2), np.nan, np.float32); tipz = np.full((n, 2, 2), np.nan, np.float32)   # per hand: the wrist px; the thumb and index tips' z
    kk = K // 2
    for i in range(n):
        for a in range(2):
            s = assign[i, a]
            if s < 0: continue
            tips[i, a * kk:(a + 1) * kk] = px[i, s, lm]; palm[i, a] = np.linalg.norm(px[i, s, PALM[0]] - px[i, s, PALM[1]])
            wrist[i, a] = px[i, s, 0]
            if img.shape[-1] >= 3: tipz[i, a] = img[i, s, [TIP_LM["thumb"], TIP_LM["index"]], 2]
    print(f"anchors: {K} ({', '.join(names)}), outline {outline}; hands: {present.all(1).sum()} two-hand frames; MediaPipe's slot order was swapped against continuity in {swaps} frames")

    # 2. gaps bridged, then the 1-Euro filter per coordinate
    raw = tips.copy()
    for k in range(K):
        for c in range(2): tips[:, k, c] = fill_gaps(tips[:, k, c], max_gap)
    for a in range(2): palm[:, a] = fill_gaps(palm[:, a], max_gap)
    valid = ~np.isnan(tips[:, :, 0]).any(1)
    print(f"gaps bridged (<= {max_gap} frames): {int((valid & np.isnan(raw[:, :, 0]).any(1)).sum())} frames; valid frames {valid.sum()}: {int(np.flatnonzero(valid)[0])}..{int(np.flatnonzero(valid)[-1])}")
    if kw.get("med3", "1") == "1":
        # a 3-point median per coordinate BEFORE the 1-Euro: a one-frame tracking outlier is removed (a, b, a -> a) while a real
        # step is kept (a, b, b -> b) with no lag. The 1-Euro alone cannot tell a spike from a snap: its cutoff opens with speed,
        # and a spike at frame 862 distorted the whole sheet for one frame (the flicker gate's 21.6 s event, 2026-09-18).
        m3 = tips.copy()
        m3[1:-1] = np.nanmedian(np.stack([tips[:-2], tips[1:-1], tips[2:]]), axis=0)
        moved = np.linalg.norm(m3 - tips, axis=-1); big = np.nan_to_num(moved) > 5
        print(f"3-point median: {int(big.any(1).sum())} frames had a tip moved by more than 5 px (max {np.nanmax(moved):.0f} px at frame {int(np.unravel_index(np.nanargmax(moved), moved.shape)[0])})")
        tips = np.where(np.isnan(tips), tips, m3)
    sm = tips.copy()
    for k in range(K):
        for c in range(2): sm[:, k, c] = smooth_signal(tips[:, k, c], FPS, min_cutoff, beta, d_cutoff)
    quiet = slice(465, 480)          # the take's quietest 15-frame hold (data/01-membrane-numbers.csv)
    j_raw = np.nanmean(np.nanstd(tips[quiet], axis=0)); j_sm = np.nanmean(np.nanstd(sm[quiet], axis=0))
    with np.errstate(all="ignore"):
        speed = np.nanmax(np.linalg.norm(np.diff(tips, axis=0), axis=-1), axis=1)      # per frame, the fastest tip
    fast = np.argsort(np.nan_to_num(speed, nan=-1))[-5:] + 1
    lag = np.nanmax(np.linalg.norm(sm[fast] - tips[fast], axis=-1), axis=1)
    print(f"1-Euro (min_cutoff {min_cutoff} Hz, beta {beta}, d_cutoff {d_cutoff} Hz): jitter std on the quiet hold {j_raw:.2f} -> {j_sm:.2f} px; "
          f"lag at the 5 fastest frames {np.round(lag, 1).tolist()} px (speeds {np.round(speed[fast - 1], 0).tolist()} px/frame)")

    # 3. the scale: px per palm, smoothed at 1 Hz (leaning in must not read as a stretch, and it must not lag a lean either)
    with np.errstate(all="ignore"):
        scale = np.nanmean(palm, axis=1)
    scale = smooth_signal(scale, FPS, 1.0, 0.0)
    for i in range(1, n):                                                      # hold the last value across gaps
        if np.isnan(scale[i]): scale[i] = scale[i - 1]
    first = np.flatnonzero(~np.isnan(scale))[0]; scale[:first] = scale[first]

    # the four-finger touch (round two): every frame where all K tips lie within `touch` palms of each other
    with np.errstate(all="ignore"):
        pair_d = np.linalg.norm(sm[:, :, None] - sm[:, None, :], axis=-1) / scale[:, None, None]
        maxd = np.nanmax(pair_d.reshape(n, -1), 1)
    touching = valid & (maxd <= touch)
    truns = []; i = 0
    while i < n:
        if touching[i]:
            j = i
            while j < n and touching[j]: j += 1
            truns.append((i, j - 1)); i = j
        else: i += 1
    appear = -1; snap = -1
    appear_after = int(kw.get("appear_after", 214)); touch_min = int(kw.get("touch_min", 3))   # from the export's in-point; a brush of 1-2 frames is not a touch
    long_runs = [r for r in truns if r[1] - r[0] + 1 >= touch_min]
    if appear_kw != "none":
        first = [r for r in long_runs if r[0] >= appear_after]
        appear = int(appear_kw) if appear_kw != "auto" else (first[0][0] if first else -1)
    if snap_kw != "none":
        later = [r for r in long_runs if r[0] >= snap_after]
        snap = int(snap_kw) if snap_kw != "auto" else (later[0][0] if later else -1)
    if K == 4 or truns:
        print(f"touch (all {K} tips within {touch} palm): runs " + ", ".join(f"{a}-{b}" for a, b in truns) +
              f"; the sheet appears at {appear} ({appear / FPS:.2f} s)" + (f" and snaps into the touch at {snap} ({snap / FPS:.2f} s) over {snap_frames} frames" if snap >= 0 else "; no snap"))
    if appear >= 0: valid[:appear] = False
    if snap >= 0: valid[snap + snap_frames:] = False; do_fall = False; release_kw = "auto"
    # the thumbs-up settle (round three): both thumb tips above their wrists and every tip slower than settle_v px/frame for settle_n frames
    fire_frame = -1
    if K == 4 and snap >= 0:
        thumb_k = [names.index("t0"), names.index("t1")]; index_k = [names.index("i0"), names.index("i1")]
        sp = np.linalg.norm(np.diff(sm, axis=0), axis=-1)          # (n-1, K) per frame, per tip
        for i in range(snap + snap_frames + settle_n, n):
            if np.isnan(sm[i]).any() or np.isnan(wrist[i]).any(): continue
            up = all(sm[i, thumb_k[a], 1] < wrist[i, a, 1] for a in range(2))
            folded = all((sm[i, index_k[a], 1] - sm[i, thumb_k[a], 1]) / scale[i] > settle_fold for a in range(2))   # the fist: the index tip well below the thumb tip
            if up and folded and np.nanmax(sp[i - settle_n:i]) < settle_v: fire_frame = i; break
        print(f"thumbs-up settle: both thumb tips above their wrists, both index tips folded > {settle_fold} palm below them, every tip under {settle_v:.0f} px/frame for {settle_n} frames: "
              f"from frame {fire_frame} ({fire_frame / FPS:.2f} s, export {(fire_frame - 214) / FPS:.1f} s; the fire's in-point, render_web_scene.py fire=auto)" if fire_frame >= 0 else "thumbs-up settle: not found")

    # 4. the rest state: the largest hull area in the first run (in palm^2), or a given frame
    def hull_norm(i):
        t = sm[i]
        if np.isnan(t).any(): return -1
        try: return ConvexHull(t.astype(np.float64)).volume / scale[i] ** 2
        except QhullError: return 0.0                                          # collinear tips (the four-finger line): no area
    if kw.get("rest_frame", "auto") == "auto":
        cands = [(hull_norm(i), i) for i in range(*RUN_A) if valid[i]]
        rest_area, c = max(cands)
    else:
        c = int(kw["rest_frame"]); rest_area = hull_norm(c)
    R = ((sm[c] - sm[c].mean(0)) / scale[c]).astype(np.float64)               # (K, 2) rest tips, palm units, centred
    rest_hull = ConvexHull(R)
    if outline == "ring":                                                      # the ribbon's own edges: t0 -> t1 -> i1 -> i0 (two long, two short)
        ring = np.array([0, kk, kk + 1, 1]) if K == 4 else np.arange(K)
        if not polygon_simple(R[ring]): ring = ring[[0, 2, 1, 3]]              # a hand already flipped at the rest frame: the other pairing is the simple one
        RP = R[ring]
        e1 = RP[1] - RP[0]; e2 = RP[2] - RP[0]
        if e1[0] * e2[1] - e1[1] * e2[0] < 0: ring = ring[::-1]; RP = R[ring]   # counter-clockwise, as scipy's hull
        rest_vertices = ring
    else:
        RP = R[rest_hull.vertices]; rest_vertices = rest_hull.vertices          # the rest outline (scipy: counter-clockwise)
    L0 = np.linalg.norm(R[:, None] - R[None], axis=-1)                         # (K, K): an outline edge's rest length, for ANY pair
    print(f"rest state: frame {c} (t={c / FPS:.2f} s), hull {rest_area:.2f} palm^2 ({'the first fully open quad, Dennis 2026-09-19' if K == 4 else 'plan section 3.6: 14.60 at frame 107'}), palm {scale[c]:.1f} px; "
          f"the rest outline is the {outline} of {len(RP)} tips {[names[v] for v in rest_vertices]}" + ("" if len(RP) == K else "; the others are interior pins"))
    print("rest outline edge lengths (palms): " + ", ".join(f"{names[a]}-{names[b]} {L0[a, b]:.2f}" for a, b in zip(rest_vertices, np.roll(rest_vertices, -1))))

    # the catenary port against the parabolic closed form (shallow sag: 2 % and 5 % slack over a unit chord)
    for dl in (0.02, 0.05):
        pts = catenary_2d(np.array([0.0, 0.0]), np.array([1.0, 0.0]), 1.0 + dl)
        print(f"catenary check: span 1, slack {dl}: exact sag {pts[:, 1].max():.4f} vs parabolic {sag_parabolic(1.0, dl):.4f} "
              f"({100 * (pts[:, 1].max() / sag_parabolic(1.0, dl) - 1):+.1f} %)")

    # 5. the defect field, seeded in the rest sheet's interior
    rng = np.random.default_rng(seed)
    x0, y0 = RP.min(0) - 0.15; x1, y1 = RP.max(0) + 0.15
    cand = np.stack([rng.uniform(x0, x1, 4000), rng.uniform(y0, y1, 4000)], 1)
    ok = point_in_polygon(cand, RP) & (dist_to_polygon(cand, RP) > margin)
    defects = cand[ok][:n_def]
    if len(defects) < n_def: print(f"WARNING: only {len(defects)} defect sites fit inside the margin {margin}")
    n_def = len(defects)
    thr = jstar + rng.exponential(thr_spread, n_def)
    centroid_r = np.mean(np.linalg.norm(RP - RP.mean(0), axis=1))
    if n_def == 0: print("defects: none (n_defects=0): no holes in this model (2026-09-19 late night)")   # every hole array is empty and the renderer and the panel draw none
    else: print(f"defects: {n_def} seeded at least {margin} palms inside the outline; thresholds J* {thr.min():.2f}..{thr.max():.2f} (median {np.median(thr):.2f}); their distance from the rest centroid is {np.mean(np.linalg.norm(defects - RP.mean(0), axis=1)) / centroid_r:.2f} of the outline's mean radius")

    # 6. the grid over the rest sheet
    gx = np.linspace(x0, x1, Gn); ar = (y1 - y0) / (x1 - x0); Gy = max(int(round(Gn * ar)), 8)
    gy = np.linspace(y0, y1, Gy)
    grid_uv = np.stack(np.meshgrid(gx, gy), -1).astype(np.float32)             # (Gy, Gx, 2)
    Q = grid_uv.reshape(-1, 2).astype(np.float64)
    inside_grid = point_in_polygon(Q, RP)
    fr = np.arange(1, 7) / 7.0                                                 # 6 interior samples of every outline edge

    # 7. per frame
    grid_px = np.zeros((n, Gy, Gn, 2), np.float32); grid_J = np.zeros((n, Gy, Gn), np.float32); grid_lmin = np.zeros((n, Gy, Gn), np.float32)
    grid_Jlook = np.zeros((n, Gy, Gn), np.float32)
    strings = np.full((n, K, NS, 2), np.nan, np.float32); tension = np.zeros((n, K), np.float32); slack = np.zeros((n, K), np.float32); span_ = np.zeros((n, K), np.float32)
    n_hull = np.zeros(n, np.int8); hull_idx = np.full((n, K), -1, np.int8)
    holes_r = np.zeros((n, n_def), np.float32); Jg = np.full(n, np.nan, np.float32); fall_dy = np.zeros(n, np.float32)
    snap_f = np.where(valid, 1.0, 0.0).astype(np.float32); folded = np.zeros(n, np.float32); twisted = np.zeros(n, bool)
    Jd_hist = []; r = np.zeros(n_def); folds = 0; self_x = 0; last_valid = int(np.flatnonzero(valid)[-1]); released = np.zeros(n, bool)
    if release_kw != "auto": last_valid = min(int(release_kw), last_valid)     # he lets go here: the sheet falls from this frame on
    runmax = np.zeros((K, K))                                                  # the pull-out (grow=1): the largest span each pair has reached, in palms
    L_eff_state = np.full((K, K), np.inf)                                      # the reel-in (round three): the reeled rest length per pair, inf = not reeled
    hand_of = np.arange(K) // kk                                               # which hand each anchor belongs to
    same_hand = hand_of[:, None] == hand_of[None, :]                           # the pairs inside one hand (the short edges of the ring)
    reeling = np.zeros((n, 2), bool); gap = np.full((n, 2), np.nan)
    near_edge = np.full(n, -1, np.int8); near_dec = None                        # the near long edge at a crossing (ring index), decided per bow-tie run
    contact = kw.get("contact", "twist"); contact = None if contact in ("0", "none") else contact   # round four: twist | pinch | none
    contact_px = float(kw.get("contact_px", 18.0))    # px: the drawn rods are 12 px wide on a 2-px dark base, so their bodies touch at 14 px centre to
                                                      # centre; 18 lets the fold begin as they close (assumed; the take's approaches: 6 px at source
                                                      # 30.0 / 31.1 s, 14-21 px at the flips' exits, web_edge_contact.py)
    fold_in = float(kw.get("fold_in", 4)); fold_out = float(kw.get("fold_out", 8))   # frames: the fold's rise and its settle (assumed)
    fold_w = float(kw.get("fold_w", 0.22))            # the swapped arc as a fraction of the edge's length (assumed; judged on the event frames)
    helicoid = kw.get("twist", "helicoid") != "none"     # 2026-09-22: the long edges as a helicoid's projection between the hands' frames (see the loop)
    heli_dev = np.full(n, np.nan, np.float32); heli_twist = np.full(n, np.nan, np.float32); heli_s = np.full(n, np.nan, np.float32)
    heli_th = np.full((n, 2), np.nan, np.float32)   # 2026-09-22 (round six): each hand's angle out of the image plane, for the renderer's shading of the helicoid
    fold_f = 0.0; fold_c = None; fold_t = None; contact_frames = 0
    contact_d = np.full(n, np.nan, np.float32); chain_stretch = np.ones(n, np.float32); fold_state = np.zeros(n, np.float32)
    if K == 4 and outline != "ring": reel = False
    if K == 4 and outline == "ring":
        ti = [(names.index("t0"), names.index("i0")), (names.index("t1"), names.index("i1"))]
        with np.errstate(all="ignore"):
            for a in range(2): gap[:, a] = np.linalg.norm(sm[:, ti[a][0]] - sm[:, ti[a][1]], axis=-1) / scale
            dgap = np.full((n, 2), np.nan); dgap[3:] = gap[3:] - gap[:-3]       # the 3-frame difference: closing when negative
            reeling = (gap < pinch_thr) | ((gap < pinch_open) & (dgap < 0))
            reeling &= np.isfinite(gap)
        # the ring's long edges: the edge index k whose two anchors are on different hands
        long_edges = [k for k in range(K) if hand_of[ring[k]] != hand_of[ring[(k + 1) % K]]]
        thumb_edge = [k for k in long_edges if names[ring[k]][0] == "t"][0]; index_edge = [k for k in long_edges if names[ring[k]][0] == "i"][0]
    t0 = time.time(); last = None; hull_changes = 0; prev_hv = None
    for i in range(n):
        if valid[i] and i <= last_valid:
            s = scale[i]; p = sm[i].astype(np.float64) / s
            Jg[i] = hull_norm(i) / rest_area
            if outline == "ring":
                hv = ring; m = K; twisted[i] = not polygon_simple(p[ring])    # the bow-tie: a hand is flipped
                if twisted[i] and K == 4:
                    if near_dec is None:                                       # the run's entry: the flipped hand is the one whose thumb -> index direction reversed
                        d_now = np.array([p[ti[a][1]] - p[ti[a][0]] for a in range(2)]); d_rest = np.array([R[ti[a][1]] - R[ti[a][0]] for a in range(2)])
                        flipped = int(np.argmin([d_now[a] @ d_rest[a] / (np.linalg.norm(d_now[a]) * np.linalg.norm(d_rest[a]) + 1e-9) for a in range(2)]))
                        dz = np.nanmedian([tipz[j, flipped, 0] - tipz[j, flipped, 1] for j in range(i, min(i + 5, n))])   # z(thumb) - z(index): + = the thumb farther
                        near_dec = index_edge if dz > 0 else thumb_edge
                        print(f"  crossing from frame {i}: hand {flipped} flips, its thumb tip is {'farther' if dz > 0 else 'nearer'} than its index tip (dz {dz:+.3f}), "
                              f"so the {'index' if dz > 0 else 'thumb'} edge (ring edge {near_dec}) passes in front")
                    near_edge[i] = near_dec
                else: near_dec = None
            else:
                try: hv = ConvexHull(p).vertices
                except QhullError: hv = np.array([int(np.argmin(p[:, 0])), int(np.argmax(p[:, 0]))])   # collinear: the two extreme tips
                m = len(hv)
            n_hull[i] = m; hull_idx[i, :m] = hv
            if prev_hv is not None and set(hv) != set(prev_hv): hull_changes += 1
            prev_hv = hv
            if not polygon_simple(R[hv]): self_x += 1                          # the outline's tips at rest, in the current order
            D_now = np.linalg.norm(p[:, None] - p[None], axis=-1); runmax = np.maximum(runmax, D_now)
            L0_eff = np.minimum(L0, runmax) if (grow and i < c) else L0       # being pulled out of the touch: taut until the rest length is reached
            if reel:
                # the reel-in: a pair with a reeling hand at either end has its rest length pulled down toward its span at `reel_v` palms/s
                # (the sag is taken up over a second, not in a frame); otherwise the state relaxes back toward the rest length at `relax`.
                # Before the rest frame the pull-out still applies: material slips OUT of a pinch as the hands part, so the state follows the
                # span upward (capped at the rest length); after it the rest quad is all the material there is and the state only ratchets down.
                at_reel = reeling[i][hand_of][:, None] | reeling[i][hand_of][None, :]
                L_eff_state = np.minimum(L_eff_state, L0_eff)
                L_eff_state = np.where(at_reel, np.maximum(L_eff_state - reel_v / FPS, np.minimum(L_eff_state, D_now)), np.minimum(L_eff_state + relax / FPS, L0_eff))
                if grow and i < c: L_eff_state = np.maximum(L_eff_state, np.minimum(D_now, L0_eff))
                L0_eff = np.minimum(L0_eff, L_eff_state)
            if not short_sag:
                # the short edges never sag (2026-09-19 late night, his note on the round-three export: "one extra hanger to each
                # thumb" at export 32-36 s): a ribbon's end held between thumb and index does not hang free between the two fingers,
                # the material between them lies across the hand. So a pair with both anchors on ONE hand has the effective rest
                # length min(L0, span): a straight line thumb -> index, slack 0, tension only when the fingers spread past the rest.
                # Measured before this rule: the i1-t1 and t0-i0 edges carried 0.37-0.79 palm of slack at source 1174-1294 and hung
                # as small catenary loops beside each thumb on top of the long edges' loops (model_r3.log's slack table).
                L0_eff = np.where(same_hand, np.minimum(L0_eff, D_now), L0_eff)
            Xc = [R]; Yc = [p]; polys = []
            for k in range(m):
                ia, ib = int(hv[k]), int(hv[(k + 1) % m]); a_, b_ = p[ia], p[ib]; sp = np.linalg.norm(b_ - a_); l0 = L0_eff[ia, ib]
                span_[i, k] = sp
                if sp >= l0 or l0 < 1e-6:
                    tension[i, k] = sp / l0 - 1.0 if l0 > 1e-6 else 0.0; poly = a_[None] + np.linspace(0, 1, NS)[:, None] * (b_ - a_)[None]
                else:
                    slack[i, k] = l0 - sp; poly = catenary_2d(a_, b_, l0, NS)
                polys.append(poly)
            if helicoid and K == 4 and outline == "ring":
                # THE TWIST IS A HELICOID (2026-09-22, Dennis on the r4 export: "when I do the flips, I suspect that spatially the lines
                # touch and should physically twist, like second 14"). Rounds two to four drew each long edge as its own string between
                # two tips (straight or a catenary), so a flipped hand gave a bow-tie of two straight-edged triangles. A ribbon's two
                # edges are one body: with the ends held in two frames that differ by a twist, an elastic ribbon under tension twists
                # UNIFORMLY along its length (a rod of uniform torsional stiffness; Chopin & Kudrolli 2013, references/finger-web item 02,
                # for the regimes where it does not), and its projection is a helicoid's: the width vector rotates about the centreline,
                # so the projected half-width across the axis is W(s) cos(theta(s)) with theta linear in s. The edges bow in a cosine
                # toward the crossing (where theta passes 90 deg the ribbon is edge-on and the edges MEET at a point), full near the
                # hands and pinching fast into the crossing: the lobes of a twisted ribbon, not two triangles. Each hand's theta comes
                # from its own tips in the image: cos(theta_h) = (projected half-width across the axis) / (the physical half-width, at
                # least the rest spread L0 of that thumb -> index pair), no MediaPipe z needed (z decides only which edge is in FRONT,
                # below, at the bow-tie's entry); the sign of the projection gives the branch, so a flipped hand reads theta > 90 deg.
                # With equal angles at both hands the formula IS the straight edge (a linear taper), so nothing changes where nothing
                # twists; a pinched hand reads as edge-on (its width vector is short) and the lobe funnels into it. The centreline is the
                # mean of the two strings as computed above, so the sag survives; the along-axis offsets of the tips interpolate linearly.
                w = [p[ti[h][1]] - p[ti[h][0]] for h in range(2)]                           # each hand's width vector, thumb -> index (palms)
                mid_h = [0.5 * (p[ti[h][1]] + p[ti[h][0]]) for h in range(2)]
                ax = mid_h[1] - mid_h[0]; La = np.linalg.norm(ax)
                if La > 1e-6:
                    ax = ax / La; nr = np.array([-ax[1], ax[0]])
                    ph = [0.5 * float(w[h] @ nr) for h in range(2)]                         # the signed half-width ACROSS the axis, as projected
                    qh = [0.5 * float(w[h] @ ax) for h in range(2)]                         # the half-offset ALONG the axis (the tips are not square to it)
                    Wh = [0.5 * max(float(L0[ti[h][0], ti[h][1]]), float(np.linalg.norm(w[h]))) for h in range(2)]   # the physical half-width at that hand
                    th = [float(np.arccos(np.clip(ph[h] / max(Wh[h], 1e-9), -1.0, 1.0))) for h in range(2)]        # its angle out of the image plane, 0..pi
                    tt = np.linspace(0.0, 1.0, NS)
                    cross = (Wh[0] + tt * (Wh[1] - Wh[0])) * np.cos(th[0] + tt * (th[1] - th[0]))
                    along = qh[0] + tt * (qh[1] - qh[0])
                    half = cross[:, None] * nr[None] + along[:, None] * ax[None]
                    Pi = polys[index_edge] if hand_of[ring[index_edge]] == 0 else polys[index_edge][::-1]   # both long edges oriented hand 0 -> hand 1
                    Pt = polys[thumb_edge] if hand_of[ring[thumb_edge]] == 0 else polys[thumb_edge][::-1]
                    ctr = 0.5 * (Pi + Pt); Ni = ctr + half; Nt = ctr - half                                    # at s = 0 and 1 these are the tips themselves
                    heli_dev[i] = max(np.linalg.norm(Ni - Pi, axis=1).max(), np.linalg.norm(Nt - Pt, axis=1).max()) * s
                    heli_twist[i] = np.degrees(th[1] - th[0]); heli_th[i] = th
                    if abs(th[1] - th[0]) > 1e-6: heli_s[i] = (np.pi / 2 - th[0]) / (th[1] - th[0])          # where the ribbon is edge-on (the crossing), 0..1 if inside
                    polys[index_edge] = Ni if hand_of[ring[index_edge]] == 0 else Ni[::-1]
                    polys[thumb_edge] = Nt if hand_of[ring[thumb_edge]] == 0 else Nt[::-1]
            if contact and K == 4 and outline == "ring":
                # ROUND FOUR (2026-09-19, Dennis: "the top and bottom lines might spatially touch each other when bending, which should
                # trigger an extra twist where the lines touch"): the two long edges are the two edges of ONE body. Wherever they come
                # within `contact_px` of each other at an interior point (neither hand pinched: a pinch or the line state brings the edges
                # together by construction and must not fold), the ribbon FOLDS there: a fold strength f rises 1/fold_in per frame while
                # the contact holds and decays 1/fold_out per frame after it parts (a settle, not a swap), and both polylines are pulled so
                # that at the contact they MEET AT A POINT (the ribbon's width there goes to zero). contact=twist (the default, his words):
                # over an arc of `fold_w` of the edge around the point the edges SWAP SIDES, two pinch points with the back face between them
                # (a local loop: Chopin & Kudrolli 2013's loop regime in projection, references/finger-web item 02); contact=pinch: they
                # meet at one point and part again. The bow-tie (a flipped hand) already crosses by construction and is left alone, but the
                # state decays through it, so a fold that begins at a flip's exit (the edges 14-21 px apart there on this take) continues
                # from the crossing. A first-order kinematic fold, not an XPBD chain (that is the knob for a later round: the chain would
                # add inertia and a real capsule contact; this pass gives the edges the one property he named, that they cannot pass
                # through each other unnoticed).
                A = polys[thumb_edge]; B = polys[index_edge][::-1]                  # both from hand 0 to hand 1 (the ring runs the index edge back)
                dAB = np.linalg.norm(A[:, None] - B[None], axis=-1); ka, kb = np.unravel_index(dAB.argmin(), dAB.shape)
                d_min = dAB[ka, kb] * s; ta = ka / (NS - 1); tb = kb / (NS - 1)
                pinched = (gap[i] < pinch_open).any() if np.isfinite(gap[i]).all() else True
                touching = (d_min < contact_px) and not pinched and not twisted[i] and (0.15 < ta < 0.85) and (0.15 < tb < 0.85)
                c_now = 0.5 * (A[ka] + B[kb]); t_now = 0.5 * (ta + tb)
                if touching:
                    fold_f = min(1.0, fold_f + 1.0 / fold_in)
                    fold_c = c_now if fold_c is None else 0.5 * (fold_c + c_now); fold_t = t_now if fold_t is None else 0.5 * (fold_t + t_now)
                    contact_frames += 1; contact_d[i] = d_min
                elif fold_f > 0: fold_f = max(0.0, fold_f - 1.0 / fold_out)
                if fold_f > 0 and fold_c is not None and not twisted[i]:
                    t = np.linspace(0, 1, NS); mid = 0.5 * (A + B); half = 0.5 * (A - B)
                    bump = np.exp(-0.5 * ((t - fold_t) / (0.5 * fold_w)) ** 2)                     # the waist: the width goes to zero at the point
                    if contact == "twist":
                        # the sides swap over the arc: a smooth -1 inside |t - fold_t| < fold_w/2, +1 outside, so the edges pinch to a point
                        # at both ends of the arc and cross over between them (the back face shows there, the "extra twist")
                        inside = 1.0 - np.minimum(1.0, np.abs(t - fold_t) / (0.5 * fold_w))
                        g = 1.0 - 2.0 * fold_f * (0.5 - 0.5 * np.cos(np.pi * np.minimum(1.0, 2.0 * inside)))
                        g = np.where(np.abs(t - fold_t) < 0.5 * fold_w, g, 1.0)
                    else: g = 1.0 - fold_f * bump
                    pull = fold_f * bump[:, None] * (fold_c[None] - mid)                            # the centreline is drawn to the contact point
                    A2 = mid + pull + half * g[:, None]; B2 = mid + pull - half * g[:, None]
                    A2[0], A2[-1], B2[0], B2[-1] = A[0], A[-1], B[0], B[-1]                            # the tips stay pinned
                    ch = max(np.linalg.norm(np.diff(A2, axis=0), axis=1).sum() / max(np.linalg.norm(np.diff(A, axis=0), axis=1).sum(), 1e-9),
                             np.linalg.norm(np.diff(B2, axis=0), axis=1).sum() / max(np.linalg.norm(np.diff(B, axis=0), axis=1).sum(), 1e-9))
                    chain_stretch[i] = ch; fold_state[i] = fold_f
                    polys[thumb_edge] = A2; polys[index_edge] = B2[::-1]
                elif fold_f <= 0: fold_c = None; fold_t = None
            for k in range(m):
                ia, ib = int(hv[k]), int(hv[(k + 1) % m]); poly = polys[k]
                Xc.append(R[ia][None] + fr[:, None] * (R[ib] - R[ia])[None])
                cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))]); cum /= max(cum[-1], 1e-9)
                Yc.append(np.stack([np.interp(fr, cum, poly[:, 0]), np.interp(fr, cum, poly[:, 1])], 1))
            Xc = np.concatenate(Xc, 0); Yc = np.concatenate(Yc, 0)
            if warp == "tps":
                w, a = tps_fit(Xc, Yc); f, Jm = tps_eval(Xc, w, a, Q); _, Jmd = tps_eval(Xc, w, a, defects); Jml = Jm
            else:
                f, Jm = mls_affine(Xc, Yc, Q, eps_mls); _, Jmd = mls_affine(Xc, Yc, defects, eps_def)
                _, Jml = mls_affine(Xc, Yc, Q, eps_look)             # the strain the LOOK reads: the neighbourhood's, not the vertex's (the exact
            det, lmin = stretches(Jm); detl, _ = stretches(Jml)      # field drew its own triangles as amber spikes that flickered, 2026-09-18)
            grid_px[i] = (f * s).reshape(Gy, Gn, 2); grid_J[i] = det.reshape(Gy, Gn); grid_lmin[i] = lmin.reshape(Gy, Gn); grid_Jlook[i] = detl.reshape(Gy, Gn)
            folded[i] = float((det[inside_grid] < 0).mean())                   # the back-face share of the rest sheet (the twist's progress)
            if folded[i] > 0: folds += 1
            strings[i, :m] = np.stack(polys) * s
            Jd, _ = stretches(Jmd)
            Jd_hist.append(Jd); Jd_hist = Jd_hist[-5:]; Jmed = np.median(np.stack(Jd_hist), 0)
            growing = Jmed > thr; close = Jmed < 0.9 * thr
            r = r + np.where(growing, v_open * np.sqrt(np.maximum(Jmed, 0) / jstar) / FPS, 0.0) - np.where(close, v_close / FPS, 0.0)
            r = np.clip(r, 0, r_max); holes_r[i] = r
            if snap >= 0 and i >= snap:                                        # the snap: over snap_frames the picture fades (round three, the band has no length
                kf = (i - snap + 1) / snap_frames; fct = float(max(0.0, 1.0 - kf) ** 1.5); snap_f[i] = fct   # left) or contracts into the tips' centre (round two)
                if snap_mode == "contract":
                    ctr = (p.mean(0) * s)[None, None]
                    grid_px[i] = ctr + (grid_px[i] - ctr) * fct; strings[i] = ctr + (strings[i] - ctr) * fct
            last = (grid_px[i].copy(), strings[i].copy(), grid_J[i].copy(), grid_lmin[i].copy(), s, r.copy(), m, hull_idx[i].copy(), grid_Jlook[i].copy())
        elif last is not None and i > last_valid and do_fall:
            k = i - last_valid; t = k / FPS; s = last[4]
            dy = 0.5 * G * (s / HAND_BREADTH_M) * t * t                        # px: real gravity at the hand's scale
            fall_dy[i] = dy; released[i] = True
            grid_px[i] = last[0] + [0, dy]; strings[i] = last[1] + [0, dy]; grid_J[i] = last[2]; grid_lmin[i] = last[3]; holes_r[i] = last[5]
            n_hull[i] = last[6]; hull_idx[i] = last[7]; grid_Jlook[i] = last[8]
        if i % 300 == 0: print(f"  frame {i}/{n} {(time.time() - t0) / (i + 1) * 1000:.1f} ms/frame", flush=True)
    print(f"solved {valid.sum()} frames in {time.time() - t0:.1f} s; the outline's tip set changes {hull_changes} times; the outline's rest chords self-intersect in {self_x} frames; "
          f"the interior folds over (J < 0 inside the rest sheet) in {folds} frames" + (f"; the outline is the bow-tie (a flipped hand) in {int(twisted.sum())} frames" if outline == "ring" else ""))
    print(f"tips on the outline: {np.bincount(n_hull[valid], minlength=K + 1)[2:].tolist()} frames for 2..{K}")

    # 8. the checks against the plan's tables (web/PLAN.md sections 2 and 3.6)
    print("\nJ_global (hull / rest) per second, median-filtered, against the plan's table:")
    row = []
    for t in range(n // 30):
        v = Jg[t * 30:(t + 1) * 30]; v = v[~np.isnan(v)]
        row.append(f"{t}s {np.median(v):.2f}" if v.size else f"{t}s -")
    print("  " + "  ".join(row))
    if K == 4:
        # round two's checks (2026-09-19): the line-ness per second (16 area / perimeter^2 of the tips' hull: 1 = a square, 0 = a
        # line; Dennis's beats: a line from 1 s to 8 s of the export, a form from 9 s), and the twist through each flip
        def lineness(i):
            try: h = ConvexHull(sm[i].astype(np.float64)); return 16 * h.volume / h.area ** 2
            except (QhullError, ValueError): return 0.0
        print("line-ness per second (1 = square, 0 = line), source seconds; Dennis's beats on the export (= source - 214 frames): a line to 8 s, a form at 9 s, a line again at 36 s:")
        print("  " + "  ".join(f"{t}s {lineness(t * 30):.2f}" if valid[t * 30] else f"{t}s -" for t in range(n // 30)))
        # the windows start before the palm's facing sign flips (647, 789, 1117) because the thumb and index tips cross a few frames
        # before the palm passes edge-on, and end after the sign flips back (720, 863, 1144). A flip takes 3-6 frames in this take
        # (the left hand's facing sign changes at 789, 790 and 791), so a step of 0.3 in the folded fraction is the flip itself; a
        # step above that with a tip moving > 100 px in the same frame is a tracking loss (MediaPipe's slot order, the skill's trap)
        for a, b, hand in ((630, 735, "screen-right"), (780, 870, "screen-left"), (1110, 1150, "screen-right")):
            w = folded[a:b + 1]; d = np.abs(np.diff(w)); k = int(d.argmax()); step = float(d[k])
            jump = float(np.nanmax(np.linalg.norm(sm[a + k + 1] - sm[a + k], axis=-1)))
            print(f"flip {a}-{b} ({hand} hand): folded fraction {w[0]:.2f} -> peak {w.max():.2f} at {a + int(w.argmax())} -> {w[-1]:.2f}; largest step per frame {step:.2f} at {a + k + 1} "
                  f"(the fastest tip moved {jump:.0f} px there: {'the flip itself' if step < 0.3 or jump < 100 else 'A TRACKING LOSS, check the slot order'}); "
                  f"the bow-tie on {int(twisted[a:b + 1].sum())} of {b - a + 1} frames")
        if snap >= 0:
            print(f"snap: frames {snap}-{snap + snap_frames - 1} {'fade' if snap_mode == 'fade' else 'contract'} {snap_f[snap]:.2f} -> {snap_f[snap + snap_frames - 1]:.2f}; no sheet from {snap + snap_frames} ({(snap + snap_frames) / FPS:.2f} s); "
                  f"tips still tracked to {int(np.flatnonzero(~np.isnan(sm[:, 0, 0]))[-1])} for the thumbs' fire")
        if reel:
            # the reel-in's check: the pinch gaps and the slack per edge per second, on the source clock and the export's (source - 214)
            print(f"reel-in (pinch {pinch_thr} palm closed, {pinch_open} palm and closing): hand 0 reels on {int(reeling[valid, 0].sum())} frames, hand 1 on {int(reeling[valid, 1].sum())}; "
                  f"slack per edge per second (max, palms; edges {', '.join(names[ring[k]] + '-' + names[ring[(k + 1) % K]] for k in range(K))}), source s [export s]:")
            rows = []; bad = []
            for t in range(n // 30):
                sl = slice(t * 30, (t + 1) * 30); v = valid[sl]
                if not v.any(): continue
                ms = np.nanmax(np.where(v[:, None], slack[sl], np.nan), axis=0)
                rows.append(f"{t}s[{t - 214 / FPS:.0f}] " + "/".join(f"{x:.2f}" for x in ms) + f" g {np.nanmedian(gap[sl, 0]):.1f},{np.nanmedian(gap[sl, 1]):.1f}")
                if (t * 30 >= 1280 or t * 30 < 500) and ms.max() > 0.05: bad.append(f"{t}s {ms.max():.2f}")
            print("  " + "  ".join(rows))
            print(f"  slack at the pinches (before source 500, after 1280): {'NONE above 0.05 palm' if not bad else 'STILL ' + ', '.join(bad)}")
        if K == 4 and outline == "ring":
            runs_x = []; j = 0
            while j < n:
                if near_edge[j] >= 0:
                    k = j
                    while k < n and near_edge[k] >= 0: k += 1
                    runs_x.append((j, k - 1, int(near_edge[j]))); j = k
                else: j += 1
            print("crossings (the near long edge per bow-tie run): " + ", ".join(f"{a}-{b} edge {e} ({names[ring[e]]}-{names[ring[(e + 1) % K]]})" for a, b, e in runs_x))
    ig = inside_grid.reshape(Gy, Gn)
    for i in (330, 789, 1080, 1380):
        if valid[i]:
            Ji = grid_J[i][ig]
            print(f"local J inside the sheet at frame {i} (t={i / FPS:.1f} s, J_global {Jg[i]:.2f}): median {np.median(Ji):.2f}, p90 {np.percentile(Ji, 90):.2f}, p98 {np.percentile(Ji, 98):.2f}, min {Ji.min():.2f}")
    r_vis = 0.04
    open_ = (holes_r > r_vis).any(1) & valid
    runs = []; i = 0
    while i < n:
        if open_[i]:
            j = i
            while j < n and open_[j]: j += 1
            runs.append((i, j - i)); i = j
        else: i += 1
    longest = max(runs, key=lambda x: x[1]) if runs else (0, 0)
    area = (np.pi * holes_r ** 2).sum(1)
    print(f"holes (r > {r_vis} palm): open on {open_.sum() / FPS:.1f} s of the take in {len(runs)} runs, the longest {longest[1] / FPS:.2f} s from frame {longest[0]} "
          f"(plan's table at A0 = 14.60, J* = 1.15: 10.6 s, longest 2.93 s); at most {(holes_r > r_vis).sum(1).max()} at once; peak total hole area {area.max():.2f} palm^2 of a {rest_hull.volume:.1f} palm^2 sheet")
    if runs: print("hole runs (start frame, s): " + ", ".join(f"({a}, {b / FPS:.1f})" for a, b in runs))
    ever = (holes_r > r_vis).any(0)
    if ever.any():
        d = np.linalg.norm(defects[ever] - RP.mean(0), axis=1) / centroid_r
        print(f"{ever.sum()} of {n_def} defects ever open; their distance from the sheet's centre is {d.mean():.2f} (mean) of the outline's mean radius: {'the middle' if d.mean() < 0.6 else 'NOT the middle'}")
    edge_ok = np.arange(K)[None, :] < n_hull[:, None]
    print(f"strings: taut (tension > 0) on {100 * (tension > 0)[edge_ok].mean():.0f} % of edge-frames; slack median {np.median(slack[edge_ok & valid[:, None]]):.2f} palms; "
          f"max tension {tension.max():.2f}; max slack {slack.max():.2f} palms")
    if released.any():
        print(f"release: the sheet falls from frame {last_valid + 1} (t={(last_valid + 1) / FPS:.2f} s), g = {G * scale[last_valid] / HAND_BREADTH_M / FPS ** 2:.1f} px/frame^2; off the bottom after {int((fall_dy > H).argmax() - last_valid) if (fall_dy > H).any() else -1} frames")

    params = dict(jstar=jstar, n_defects=n_def, seed=seed, grid=Gn, v_open=v_open, v_close=v_close, r_max=r_max, margin=margin, thr_spread=thr_spread,
                  min_cutoff=min_cutoff, beta=beta, d_cutoff=d_cutoff, max_gap=max_gap, rest_frame=int(c), rest_area=float(rest_area), fps=FPS, W=W, H=H,
                  hand_breadth_m=HAND_BREADTH_M, warp=warp, eps_mls=eps_mls, eps_def=eps_def, eps_look=eps_look, tsmooth=tsmooth, release=int(last_valid),
                  tips=",".join(tip_names), names=names, outline=outline, touch=touch, appear=int(appear), snap=int(snap), snap_frames=snap_frames, grow=grow,
                  reel=reel, pinch=pinch_thr, pinch_open=pinch_open, relax=relax, reel_v=reel_v, snap_mode=snap_mode, fire_frame=int(fire_frame), settle_v=settle_v, settle_n=settle_n,
                  contact=contact or "none", contact_px=contact_px, fold_in=fold_in, fold_out=fold_out, fold_w=fold_w, twist="helicoid" if helicoid else "none", couple=int(kw.get("couple", 1)), nu=float(kw.get("nu", 0.5)))
    bad = ~np.isfinite(grid_J) | ~np.isfinite(grid_lmin) | ~np.isfinite(grid_Jlook)   # a singular local fit in a crushed fold: not a number for the shader
    if bad.any(): print(f"sanitised {int(bad.sum())} non-finite strain values (of {grid_J.size}) in the crushed folds")
    grid_J = np.clip(np.nan_to_num(grid_J, nan=0.0, posinf=10.0, neginf=-10.0), -10, 10); grid_lmin = np.clip(np.nan_to_num(grid_lmin, nan=0.0, posinf=10.0, neginf=-10.0), -10, 10)
    grid_Jlook = np.clip(np.nan_to_num(grid_Jlook, nan=0.0, posinf=10.0, neginf=-10.0), -10, 10)
    grid_px = np.nan_to_num(grid_px, nan=-1e4, posinf=1e4, neginf=-1e4)
    # the linear stretch of every outline edge, span / effective rest length (1 at rest, < 1 slack, > 1 taut): what the renderer and the
    # panel colour the LINES by, on the same ramp as the sheet read at lambda^2 (an isotropic areal stretch lambda^2 has this linear
    # stretch; 2026-09-19 late night, Dennis: "the lines and inside change colour ... applied to how stretched it is")
    with np.errstate(all="ignore"):
        stretch = np.where(slack > 1e-6, span_ / np.maximum(span_ + slack, 1e-9), 1.0 + tension).astype(np.float32)
    stretch = np.clip(np.nan_to_num(stretch, nan=1.0), 0.0, 10.0)
    short_k = [k for k in range(K) if same_hand[ring[k], ring[(k + 1) % K]]] if (K == 4 and outline == "ring") else []
    if short_k and not short_sag:
        # 2026-09-22 (Dennis: "the lines from index to thumb seem to be yellow, can't they also follow a heat map for how stretched it
        # is, with max being violet, lowest being red"): a short edge's colour reads the SPREAD of its two fingers against that hand's
        # USUAL spread, span / median(span) over the frames where the hand is neither pinched nor closing: below 1 when the fingers are
        # closer than usual (orange -> red at a pinch), 1 at the usual spread (yellow), above 1 spread wider (cyan -> blue -> violet at
        # the widest). The reference is the usual spread and not the rest frame's, because the rest frame (514, the first fully open
        # quad) is the WIDEST spread of the take: against it the short edges sat below 0.9 on 1004 of 1104 frames and never reached cyan
        # (model_r5.log's first run), the opposite of a heat map that uses its range. The geometry stays the straight line with no slack
        # (its effective rest length min(L0, span) draws it); only the colour reads the spread. Before this the short edges clipped at
        # yellow, because their effective rest length followed the span down and their stretch never fell below 1.
        for k in short_k:
            h = int(hand_of[ring[k]]); usual = valid & np.isfinite(span_[:, k]) & ~reeling[:, h]
            ref = float(np.median(span_[usual, k])) if usual.any() else float(L0[int(ring[k]), int(ring[(k + 1) % K])])
            with np.errstate(all="ignore"): stretch[:, k] = np.where(np.isfinite(span_[:, k]), span_[:, k] / max(ref, 1e-9), 1.0)
            print(f"  short edge {k} ({names[ring[k]]}-{names[ring[(k + 1) % K]]}, hand {h}): the usual spread {ref:.2f} palm over {int(usual.sum())} open frames "
                  f"(the rest frame's {float(L0[int(ring[k]), int(ring[(k + 1) % K])]):.2f}) is its yellow")
        stretch = np.clip(np.nan_to_num(stretch, nan=1.0), 0.0, 10.0)
        couple = int(kw.get("couple", 1)); nu = float(kw.get("nu", 0.5))
        if couple:
            # ROUND SIX (2026-09-22, Dennis: the thumb -> index lines should "have their stretching realistically take into account the
            # other longer link, index to index and thumb to thumb"): the ribbon is ONE sheet, so pulling it along its length narrows
            # it. A membrane of an incompressible material (Poisson's ratio 0.5: rubber, dough, skin; Treloar, The Physics of Rubber
            # Elasticity, the uniaxial case; `nu=` is the knob, ranked assumed for this ribbon) held at a lengthwise stretch lambda_L
            # has the natural width W0 * lambda_L^(-nu). Fingers holding the end at the usual spread therefore stretch the width by
            # lambda_L^nu on top of spread / usual: the short edge's stretch is (span / usual) * lambda_L^nu. lambda_L is the mean of
            # the two long edges' stretch (both end at every hand) and never below 1: a slack long edge (a catenary) carries no
            # tension and does not widen the ribbon. The colour reads this coupled stretch; the geometry is unchanged.
            with np.errstate(all="ignore"):
                lamL = np.nanmean(np.where(np.isfinite(span_[:, long_edges]), stretch[:, long_edges], np.nan), axis=1)
            lamL = np.clip(np.nan_to_num(lamL, nan=1.0), 1.0, 10.0); fac = lamL ** nu
            before = stretch[:, short_k].copy()
            for k in short_k: stretch[:, k] = stretch[:, k] * fac
            stretch = np.clip(np.nan_to_num(stretch, nan=1.0), 0.0, 10.0)
            moved = valid & (fac > 1.02)
            print(f"the short edges' stretch is coupled to the long edges' tension (an incompressible membrane narrows: width factor lambda_L^{nu}): "
                  f"the long edges' mean stretch (floored at 1) is above 1.04 on {int(moved.sum())} frames, the width factor up to {fac[valid].max():.2f} "
                  f"(median on those frames {np.median(fac[moved]) if moved.any() else 1.0:.2f}); the short edges' stretch moved by "
                  f"{np.abs(stretch[valid][:, short_k] - before[valid]).max():.2f} at most")
        sk = stretch[valid][:, short_k]
        print(f"the short edges' colour reads the finger spread / the hand's usual spread{' x the long edges'' width factor' if couple else ''}: {sk.min():.2f} (closest) .. {sk.max():.2f} (widest), "
              f"below 0.9 on {int((sk < 0.9).any(1).sum())} frames, above 1.1 on {int((sk > 1.1).any(1).sum())} frames, above 1.28 (violet) on {int((sk > 1.28).any(1).sum())}")
    if helicoid and K == 4 and outline == "ring":
        act = np.isfinite(heli_twist) & (np.abs(heli_twist) > 10); bt = act & (twisted > 0)
        print(f"helicoid twist (the long edges as a twisted ribbon's projection): the hands' frames differ by more than 10 deg on {int(act.sum())} frames "
              f"(median |twist| there {np.nanmedian(np.abs(heli_twist[act])) if act.any() else 0:.0f} deg, max {np.nanmax(np.abs(heli_twist)) if np.isfinite(heli_twist).any() else 0:.0f} deg); "
              f"the edges bow up to {np.nanmax(heli_dev) if np.isfinite(heli_dev).any() else 0:.0f} px from the straight strings "
              f"(median on the bow-tie frames {np.nanmedian(heli_dev[bt]) if bt.any() else 0:.0f} px); "
              f"on the bow-tie frames the edge-on point sits at {np.nanmin(heli_s[bt]) if bt.any() else float('nan'):.2f}..{np.nanmax(heli_s[bt]) if bt.any() else float('nan'):.2f} of the length "
              f"(median {np.nanmedian(heli_s[bt]) if bt.any() else float('nan'):.2f}); with equal angles the formula is the straight edge, so the untwisted frames move 0 px")
    if contact:
        ev = np.flatnonzero(fold_state > 0); groups = np.split(ev, np.flatnonzero(np.diff(ev) > 1) + 1) if ev.size else []
        print(f"contact ({contact}, under {contact_px:.0f} px at an interior point with no hand pinched, outside the bow-tie): touching on {contact_frames} frames, "
              f"the fold active on {int((fold_state > 0).sum())} frames in {len(groups)} events (source a-b [export s]: min distance, peak fold, max chain stretch):")
        for g in groups:
            a, b = int(g[0]), int(g[-1]); dm = np.nanmin(contact_d[a:b + 1]) if np.isfinite(contact_d[a:b + 1]).any() else float("nan")
            print(f"  {a}-{b} [{(a - 214) / FPS:.1f}-{(b - 214) / FPS:.1f} s]: {dm:.0f} px, fold {fold_state[a:b + 1].max():.2f}, chain stretch {chain_stretch[a:b + 1].max():.3f}")
        print(f"  the deformed polylines are at most {chain_stretch.max():.3f} of the undeformed length (a fold gathers, it does not stretch: > 1.05 would be a pull)")
    print(f"edge stretch (span / rest, the lines' colour): min {stretch[edge_ok & valid[:, None]].min():.2f}, max {stretch[edge_ok & valid[:, None]].max():.2f}"
          + (f"; the short edges (ring edges {short_k}, inside one hand) {'may sag' if short_sag else 'never sag'}: their slack is {slack[valid][:, short_k].max():.2f} palm at most" if short_k else ""))
    jblur = float(kw.get("jblur", 1.5))                                      # the look field's spatial blur, in grid cells
    if tsmooth > 1 or jblur > 0:                                             # a one-frame tracking jump flashed the whole heat field (frame 862, 2026-09-18)
        from scipy.ndimage import median_filter, gaussian_filter
        idx = np.flatnonzero(valid | released); a0, a1 = int(idx[0]), int(idx[-1]) + 1
        if tsmooth > 1: grid_Jlook[a0:a1] = median_filter(grid_Jlook[a0:a1], size=(tsmooth, 1, 1), mode="nearest")
        if jblur > 0:   grid_Jlook[a0:a1] = gaussian_filter(grid_Jlook[a0:a1], sigma=(0, jblur, jblur), mode="nearest")   # the heat's isolines crossed the
        print(f"look strain: MLS kernel {eps_look} palm, median over {tsmooth} frames, blur {jblur} cells; |dJ| per frame p98 "          # triangles as a sawtooth next
              f"{np.percentile(np.abs(np.diff(grid_Jlook[a0:a1], axis=0))[:, ig], 98):.3f}, |dJ| per cell p98 "                        # to a pinch (2026-09-18)
              f"{np.percentile(np.abs(np.diff(grid_Jlook[a0:a1], axis=2))[:, ig[:, 1:]], 98):.3f}")
    np.savez(out, valid=valid, released=released, grid_px=grid_px, grid_J=grid_Jlook, grid_Jraw=grid_J, grid_lmin=grid_lmin, grid_uv=grid_uv, inside=ig,
             rest_poly=RP.astype(np.float32), rest_tips=R.astype(np.float32), n_hull=n_hull, hull_idx=hull_idx, strings_px=strings, tension=tension, slack=slack, span=span_,
             L0=L0.astype(np.float32), holes_r=holes_r, defects=defects.astype(np.float32), thr=thr.astype(np.float32), scale=scale.astype(np.float32), tips_px=sm,
             J_global=Jg, fall_dy=fall_dy, snap_f=snap_f, folded=folded, twisted=twisted, near_edge=near_edge, reeling=reeling, gap=gap.astype(np.float32),
             stretch=stretch, fold=fold_state, contact_d=contact_d, heli_twist=heli_twist, heli_dev=heli_dev, heli_th=heli_th, params=json.dumps(params))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
