# The finger web — the membrane model, round one (2026-09-18)

What `tools/scripts/web_membrane.py` computes from the tracked hands and what `tools/scripts/render_web.py`
draws from it, every constant with its source and rank, and the checks the script prints before a render
(CLAUDE.md, "Model code"). The plan is `web/PLAN.md`; the research is `references/finger-web/01-...md`
(item 01) and its `data/01-membrane-numbers.csv`. Round one is the first thing Dennis sees; the open
decisions are listed at the end.

## 1. What is modelled, and what is not

The sheet is a **kinematic** membrane in image space: its outline, its strings and its interior are
computed from the ten fingertips of the current frame alone, with two pieces of state carried from
frame to frame (the hole radii and the 5-frame strain history). It has **no inertia and no in-plane
elasticity of its own**: it does not jiggle after a snap, and the interior's shape is an interpolation of
the anchors, not the solution of an elastic energy. The plan's XPBD sheet (§3.1: substeps, strain
limiting, compliance as a material parameter) is the round-two upgrade if the interior needs to lag,
wrinkle or bounce. What IS physical in round one: the strings' catenaries (exact), the areal stretch
field J and the thickness it implies, and the three-stage hole law (nucleation at seeded defects, growth
at the Taylor–Culick rate, arrest and closing). The dough strain-hardening index **b (plan §3.3) does
not enter a kinematic model**; the tear threshold J\* and the closing rule stand in for it, and that
is a limitation to say out loud, not a result.

## 2. The signals

| step | what | value | source / rank |
|---|---|---|---|
| anchors | MediaPipe landmarks 4, 8, 12, 16, 20 of each hand (`web/work/hands.npz`) | 1335 two-hand frames of 1497 | measured (`extract_hands_mp.py`) |
| hand identity | continuity of the palm centre (landmarks 0, 5, 17), hand 0 = the image-left hand at the first two-hand frame | MediaPipe's slot order swapped against continuity in **584** frames; its handedness label disagreed in 8 hand-frames | measured this session; the label is unusable, the slots are |
| gaps | linear interpolation across ≤ 10 missing frames | 3 single-frame dropouts bridged (864, 1420, 1449) | the prior art's 10-frame temporal grace (`code/aadishy-...README.md`), cited |
| outliers | a 3-point median per coordinate before the smoothing: a one-frame spike (a, b, a) is removed, a step (a, b, b) kept, no lag | 324 frames had a tip moved by > 5 px, the largest 151 px at frame 862 | chosen here: the 1-Euro filter alone passed that spike (its cutoff opens with speed) and the sheet distorted for one frame, the flicker gate's 21.6 s event |
| smoothing | 1-Euro filter per coordinate (Casiez, Roussel & Vogel 2012, `papers/casiez2012-one-euro-filter.pdf`) | min_cutoff 1.5 Hz, beta 0.01 per px/s, d_cutoff 15 Hz | chosen here: the paper's default d_cutoff 1 Hz made the sheet trail the fingertip by 100 px on the 274 px/frame snaps; at 15 Hz the lag is 18–25 px on the five fastest frames and the quiet-hold jitter drops 0.86 → 0.70 px |
| scale | px per palm = the mean index-MCP-to-pinky-MCP distance of the two hands, 1-Euro at 1 Hz | 126 px at the rest frame, 78–160 over the take | measured; "everything in palm units" is plan §2 (leaning in must not read as a stretch) |

## 3. The rest state ("the first stretch is the taut reference")

The rest configuration is the ten tips at the frame of the largest hull area within the first two-hand
run (frames 29–129), in palm units about their centroid: **frame 98 (3.27 s), hull 15.80 palm²**. The
plan's table (§3.6) gives 14.60 at frame 107 from the unsmoothed tips and the per-frame palm width; the
difference is the smoothing and the 1 Hz scale, the event is the same. The rest outline is the convex
hull of the rest tips — **7 of 10**: both pinkies, both ring tips, both middle tips and the image-left
thumb; the index tips and the image-right thumb are interior pins. The rest tips are written into
`membrane.npz` as constants (`rest_tips`, `rest_poly`), so a re-trim leaves the material alone (§3.6's
trap).

## 4. The strings (the lines between the fingers)

- The visible outline is the **convex hull of the ten tips in each frame** (plan §1). Its tip set
  changes 162 times over the take (a tip crossing an edge); the geometry at such a change is nearly
  continuous because the tip is on the edge's line when it crosses.
- Each hull edge (a, b) is a string with the rest length **L0 = |R_a − R_b|**, the two tips' distance in
  the rest configuration (so any pair has one). span ≥ L0: **taut**, straight, tension = span/L0 − 1;
  span < L0: **slack** by L0 − span and hung as the **exact catenary** of an inextensible thread.
- The catenary is `catenary_points()` ported **verbatim** from `tools/scripts/render_puppet.py:122`
  (memory `port-referenced-look-from-code`), with image y-down mapped onto its z-up and the result
  resampled at equal arc length (equal material fractions). Check printed every run against the
  parabolic closed form sag = √(3·span·ΔL/8) (`papers/johndcook-catenary-sag-approximation.txt`):
  **+0.7 % at 2 % slack, +1.7 % at 5 % slack** (the closed form is the shallow-sag limit; the exact
  curve sags a little more, as it should).
- Measured over the take: taut on 23 % of edge-frames, slack median 0.26 palms, max slack 7.2 palms
  (the bottom edge when the hands come together), max tension 2.73 (a cross-hand edge at the widest push).
- **A fixed ring through all ten tips in anatomical order was tried first and rejected**: in his pose the
  thumbs hang below the pinky-to-pinky chord, the ring polygon self-intersects at the rest frame and the
  sheet folded over itself in 1331 of 1338 frames. The hull never self-intersects.

## 5. The interior

**Moving-least-squares affine deformation** (Schaefer, McPhail & Warren 2006, "Image deformation using
moving least squares", §2.1): at every material point v the affine map that best fits the controls
(the ten pins plus six samples along every string) under weights 1/(|p_i − v|² + eps²), eps = 0.02 palm,
so the sheet passes through every fingertip and along every string and, between them, moves like the
weighted average of its neighbours. The local matrix is the deformation gradient: its determinant is
the **areal stretch J** (rest = 1) and its singular values the principal stretches (plan §3.1; Wang,
O'Brien & Ramamoorthi 2010 for J = λ₁λ₂).

- The **thin-plate spline** (Bookstein 1989) was the first choice (`warp=tps`, kept for comparison) and
  failed on this take: the interpolant overshoots between pins a palm apart that are pinched to one
  point; its Jacobian ran from −8 to +7 and folded the sheet in 1274 frames, so every defect tripped
  (holes on 44 s of the take). MLS: local J at 11.0 s median 1.25, p98 1.55; at 36.0 s median 0.85,
  p98 1.40.
- The MLS map still **folds** (J < 0 somewhere inside the rest sheet) in 829 frames — always in the
  crushed region next to a pinched hand, where five rest tips a palm apart sit on one image point. The
  renderer reads J ≤ 0 as crushed (thick, opaque dough) and fades the pattern there; the folds are not
  visible as such. A real sheet would bunch out of plane; a 2D model cannot, and round two's XPBD sheet
  would bunch in plane instead. Neither is what the eye expects at a pinch; the opaque dough is the
  honest 2D stand-in.
- **What the outline encloses is drawn; material outside it is not.** The renderer masks the sheet by
  the outline polyline (the strings), so a tip that moves inside the hull becomes a pin pressing on the
  sheet rather than a notch in its edge (plan §1's reading).
- **The folded layer is not drawn.** Where the map folds, the mesh covers a pixel twice with opposite
  orientation; drawing both gave alternating sawtooth slivers of cream and amber at every pinched hand
  (the flicker gate's 14.6 s and 16.7 s events). The renderer discards the back-facing triangles
  (`front=1`) and a second pass paints whatever the outline encloses that no front-facing triangle
  covered as crushed dough (cream at 0.72 over the plate, no pattern): material that bunched.
- **The strain the LOOK reads is a neighbourhood's, smoothed in space and time.** The exact field (eps
  0.02 palm) is steep between adjacent vertices next to a pinched hand, so the heat's isolines crossed
  the mesh's triangles as a sawtooth that flickered as vertices crossed the ramp, and a one-frame
  tracking jump at 21.6 s flashed the whole field. The look field is the same MLS map with
  eps_look = 0.6 palm on a 96 × 120 grid (cells of 0.1 palm), then a 5-frame median per vertex
  (`tsmooth=5`; the grid is the rest sheet, so a vertex is the same material every frame) and a
  Gaussian of 1.5 cells (`jblur`): its change is 0.12 per frame and 0.05 per cell at the 98th
  percentile. A first pass at eps_look 0.3 on the 48-grid without the blur still striped. The exact
  field is kept as `grid_Jraw` for the statistics; the defects read their own eps_def = 0.5 field.
- A defect senses the strain of its **neighbourhood**: the same MLS map evaluated at the defect with
  eps = 0.5 palm (a defect has a size; assumed), median-filtered over the last 5 frames (plan §8.4:
  |dJ| spikes are tracking glitches, p98 0.47 but max 4.71 per frame).

## 6. Thickness and the look (render_web.py, all in linear light)

| quantity | rule | value | rank |
|---|---|---|---|
| thickness | h = h₀ / J (volume-incompressible sheet) | — | plan §3.3, Dobraszczyk's dough in biaxial extension |
| opacity ("milk") | 0.10 + 0.8·(1 − exp(−0.5 / J)) | J = 1: 0.41; J = 0.3: 0.75; J = 3: 0.22 | assumed: thick dough hides the picture, thin dough shows it; capped at 0.9 because a crushed sheet is folds and air (it hid his face at the thumbs-up), floored at 0.10 so the thinnest dough keeps a body |
| heat | smoothstep(0.85, J\* + 0.8, J), cream → amber | — | assumed (plan §5, "tie the filter to the strain"); the red is reserved for the tear rims |
| the picture through the sheet | a posterised duotone of the plate's luminance, shadow #6B4226 → the sheet's colour, 5 levels at rest → 2 when hot, blended at 0.75 | — | the reference's filtered portal (item 01 §1), the strength a look choice; the dark #3A2415 tried first painted his dark shirt as black blobs where the sheet is thin |
| the pattern | a grid every 0.30 palm in REST space, line 0.02 palm / √J, alpha 0.32, faded where J < 0.6 | — | the reference's warped grid filter (`web/work/ref2_grid_t4.0.png`); `pattern=web` draws 16 spokes and rings instead, `none` nothing |
| the edge | a 22 % darkening within 6 px of the outline | — | item 09: a dark edge, not a bright rim, on a light plate |
| holes | alpha 0 inside; a rolled rim 0.08 palm wide in the hot colour lit from the upper left; 4 dark radial cracks per hole, 0.7 r long | — | plan §3.4c (the rim: Taylor–Culick; the cracks: Petit et al. 2015); the widths assumed |
| strings | dark base #231F20 (brand main) + a core dull #6B4A2E → hot #FF3B00 with tension (saturating at 0.5), 5 px slack → 3 px taut, a soft offset shadow | — | item 09: contrast not width; "thinner and hotter when stretched" (plan §3.5) |
| the sheet's shadow | 0.6 × 0.18 darkening, offset (14, 22) px, σ 10 px, outside the outline only | — | item 11's ranked list: a contact shadow is the cheapest realism cue; the offset assumed |
| hands | the matte (`extract_skin_matte.py`) composites the plate back over everything | — | the fingers hold the sheet from the front (plan §4.5) |

## 7. Holes

| quantity | value | source / rank |
|---|---|---|
| defect field | 16 sites, fixed seed 7, uniformly random in the rest sheet at least 0.5 palm inside its outline | plan §3.4a (a seeded defect field: Gent & Lindley 1959 via López-Pamies 2024, `papers/lopezpamies2024-cavitation-jmps.pdf`); the count and the margin assumed (the rim of a hand-held sheet is thicker) |
| thresholds | J\*ᵢ = 1.4 + Exp(0.3): 1.45–2.26, median 1.60 | the base 1.4 chosen against the printed hole time (plan §3.6 targets ~10 s at J\* = 1.15 on the GLOBAL J; the local J in the stretched band runs higher, so the local threshold sits higher); the spread assumed |
| nucleation | the 5-frame median of the defect's neighbourhood J passes J\*ᵢ | plan §3.4a |
| growth | v = 0.6 · √(J / 1.4) palm/s | Taylor–Culick v ∝ √(1/h) = √J (`papers/villermaux2022...` eq. 1.1, plan §3.4b); the scale 0.6 palm/s assumed (a hole reaches 0.3 palm in half a second) |
| arrest and closing | no growth below J\*ᵢ; closing at 0.4 palm/s below 0.9 J\*ᵢ | plan §3.4d (Griffith arrest; "holes stop growing and slowly close"); the speed assumed |
| size cap | 0.4 palm (≈ 50 px) | assumed: a bigger hole is the sheet |
| **measured on the take** | open **9.7 s** in 5 runs (16.6 s, 21.5 s, 25.7 s, 36.3 s, 38.3 s), the longest **3.5 s**, at most **5** at once, peak hole area 1.9 of the 15.8 palm² sheet; **7 of 16** defects ever open, at 0.37 of the outline's mean radius from its centre | the plan's table at the recommended calibration: 10.6 s, longest 2.93 s. The holes are earned at the pushes and heal between them, and they are in the middle |

## 8. The release

The sheet falls from **frame 1300 (43.3 s)**, when the hands drop into the lap (`release=1300`); the
automatic choice is the last two-hand frame (1450, 48.3 s), which kept a translucent sheet hanging
between the fists through the double thumbs-up at 48 s. **Dennis's call** (decision 5 below). The fall
is ballistic at real gravity in pixels, g_px = 9.81 m/s² × (palm px / 0.080 m) = 17.5 px/frame² here,
off the bottom of the frame in 15 frames. The 8.0 cm index-MCP-to-pinky-MCP breadth is **assumed**
(ANSUR II gives 8.9 cm for the male hand breadth at the metacarpal heads; the landmark distance is a
little less); it only sets the fall's speed.

## 9. The checks the script prints (and this run's values)

1. hand identity: two-hand frames, slot swaps corrected (1335; 584)
2. gaps bridged and the valid range (3; 29..1450)
3. smoothing: jitter on the quiet hold before/after, lag on the five fastest frames (0.94 → 0.71 px; 22–25 px at 225–275 px/frame)
4. the rest state and its outline (frame 98, 15.80 palm², 7 tips) and every rest edge length
5. the catenary port against the parabolic closed form (+0.7 %, +1.7 %)
6. the defect field (16, thresholds 1.45–2.26, at 0.43 of the mean radius)
7. the solve: outline changes, rest-chord self-intersections, fold frames (162; 222; 829)
8. J_global per second against the plan's table (agrees within the rest-area ratio 15.80/14.60)
9. local J inside the sheet at 11.0, 26.3, 36.0 and 46.0 s
10. hole time, runs, the longest run, the most at once, the peak area, where they open (§7)
11. strings: taut share, slack median and max, tension max (§4)
12. the release frame and the fall (§8)
13. the look strain field's kernel, median and blur, and its change per frame and per cell (0.6 palm, 5 frames, 1.5 cells; p98 0.12 and 0.05)
14. the 3-point median's effect on the raw tips: frames with a tip moved by more than 5 px, and the largest move (324; 151 px at frame 862, the one-frame outlier the flicker gate had flagged)

## 10. Open for Dennis after round one

1. The look inside: cream dough with the amber heat and the posterised picture, or something closer to
   the reference's harder filters (halftone, thermal), or the brand violet? (`LOOKS`, `filt=`, `pattern=`)
2. The pattern: grid (shipped), spider web (`pattern=web`), or none.
3. The holes: more or fewer (`jstar=`, `n_defects=`), bigger (`r_max=`), faster (`v_open=`), whether the
   cracks and the rim read on a phone.
4. The strings: their width and colours (`string_px=`, the look's `string_*`).
5. The release: at the lap drop (43.3 s, shipped) or at the last hand (48.3 s), i.e. whether the sheet
   hangs through the thumbs-up.
6. Length: 214–1466 shipped (41.7 s with the thumbs-up); the plan's cheapest trim is the 14–20 s hold.
7. Everything in plan §11 (the scene) and §12 (the sting), untouched this round.

---

# Round two — the four-tip violet ribbon (2026-09-19)

Dennis's verdict on round one gave the video its choreography (HANDOFF of 2026-09-19, measured beat by beat
against the tracking). The mechanism is round one's on **four anchors** (`tips=thumb,index`), with an appear,
a snap and a new outline rule; nothing above changes for the ten-tip mode. Every number here is either
measured on the take, ported from the puppet's code, or marked assumed.

## 11. What changed, and why

| step | round one | round two | source / rank |
|---|---|---|---|
| anchors | the ten tips | the thumbs and index fingers (landmarks 4 and 8), K = 4 | Dennis: "only the thumbs and index fingers hold the sheet"; measured: from source 300 to 480 each hand's thumb and index are pinched 0.1–0.2 palm apart with the pinches 6 palms apart |
| appear | the sheet exists from the first valid frame | **nothing until the four tips touch**: the first run of ≥ 3 frames with all four within 0.8 palm (`touch=0.8 touch_min=3`) after the export's in-point (`appear_after=214`): **source 240**, export 0.9 s | Dennis: "nothing appears until they touch at 1 s"; the 0.8-palm radius and the 3-frame minimum are assumed (runs of 1–2 frames at 128 and 220 are brushes) |
| the outline | the convex hull of the tips | **the ribbon's own edges** (`outline=ring`): thumb0 → thumb1 → index1 → index0, two long edges between the hands (rest 4.38 and 4.17 palms) and two short ones inside each hand (2.16 and 2.21) | with ten tips a fixed ring self-intersected in his pose (§4); with four it is a simple quad whenever no hand is flipped and the **bow-tie** exactly when one is: the projection of a ribbon twisted half a turn. The hull would have put the rest diagonals on the outline at a flip and the interior would have crushed instead of twisted |
| the rest state | the largest hull of the first run (frame 98) | **the first fully open quad, source 514** (8.28 palm²; `rest_frame=514`) | Dennis's default; the quad opens at 492–498 (1.3 → 9.8 palm²); the take's largest quad (11.9 at 668) is mid-flip and would make every open pose slack |
| before the rest frame | the sheet is slack against a later rest | **the pull-out** (`grow=1`): each pair's rest length is the largest span it has reached so far, capped at its rest length | "the first stretch is the taut reference", applied while the stretch is being made: the band grows out of the touch taut and sags only where the hands come back; with a fixed rest a 4-palm loop would have dropped out of the touching fingers at 240 |
| the twist | a fold was painted as crushed dough | the MLS map **folds** where the flipped hand reverses its thumb → index direction (J < 0 on the far half of the rest sheet); the renderer draws that region as the **back face** (the limbs' blue-violet, 0.62 of the light), soft across the fold line (`smoothstep(-0.10, 0)` on J) so the sign noise of the line state (J ≈ 0 ± 0.1) cannot flip the colour | Dennis: "twisting like a very thick ribbon", consistent with the flip because the anchors are the real tips through the rotation. The back face's colour and darkening are assumed |
| the end | a release and a fall at 1300 | **the snap into the second touch**: the first ≥ 3-frame touch run after `snap_after=1000` is **source 1339** (export 37.5 s); over 5 frames (`snap_frames`) the whole picture contracts into the tips' centre, (1 − k/5)^1.5, then it is gone. No fall | Dennis: "the four fingers touch and the sheet disappears, it snaps into the touch point"; the 5 frames and the exponent are assumed |
| the look | cream dough, amber heat | **the neon puppet's violet** (`look=violet`): front #8F00FF (the trunk), back #6900FF (the limbs), warming to #FF00E1 (the upper arms' magenta), hot #FF0000 (the boots), the tear rims lit with the strings' #CBA0FF; dark violets for the edges and the duotone's shadow (#2A0A55, #3C1478); the edge 12 px (the ribbon's thickness), the outline band 8 px | ported from `render_puppet.py LOOKS["violet-mix"]` (linear BGR → sRGB, memory `port-referenced-look-from-code`); item 09 still binds on the daylit wall (no bloom, dark lines); the dark violets and the widths assumed |
| the fire | — | a particle flame from each thumb from source 1409 (the thumbs-up) in the same ramp (#3A0090 → #6900FF → #8F00FF → #FF00E1 → #CBA0FF over temperature), alpha-composited on the room (no bloom), emission with the sting's glow on the black ground | Dennis: "fire out of the thumbs, a violet flame, hot core, no bloom"; `web_fire.py`: 110 particles a frame, life 10–22 frames, 3–9 px/frame upward, buoyancy 0.3 px/frame², tongues 2.6× taller than wide, shrinking with age; all assumed, chosen on the test strip `web/work/flame_test2.png` |
| the sting | plan §12 (superseded) | the two flames fly from the thumbs to the wordmark's left end while the scene dips to black (15 frames), the merged flame sweeps the wordmark and lights it letter by letter (12 frames), PRODUCTIONS and the red tick (8), the URL (6), the hold; 90 frames, 3.0 s | the brand's beats and layout (`render_brand_sting.layout`, `draw_marks`, `neon_composite`: refactored out of the sting on 2026-09-19 with a bit-identical check) in the video's colours; the dip because the brand's safe band is y 270–1250 and the black band above the window is under the platforms' UI |
| the panel | the strain field on the REST sheet | the band's CURRENT shape in image space: every other grid cell filled with its strain colour (the fold colour for the back face), the ring's four edges by tension, the tips as dots; the workspace reads `DyeAllPies-Productions` | Dennis asked why the form on the right had that shape (it was the rest outline) |

## 12. Measured on the take (the script's printed checks, `web/work/model_r2.log`)

- touch runs (all four within 0.8 palm): 128–129, 220–221, **240–245, 248–285**, **1339–1347**, 1353–1355, 1409–1414; appear 240, snap 1339.
- line-ness per second (16 · area / perimeter² of the four tips' hull, 1 = a square): 0.65–0.90 at source 8–9 s (the tiny quad at the touch), **0.08–0.13 from 10 s to 16 s** (the line), **0.79–0.86 from 17 s** (the form), 0.45–0.65 through the flips, 0.92–0.97 at 40–43 s, 0.03 at 44 s (the line again before the snap). On the export's clock: a line from 1 s to 8 s, a form from 9 s, a line at 36 s: Dennis's beats.
- the twist: the outline is the bow-tie on **207** frames; the folded fraction of the rest sheet runs 0.03 → 0.68 → 0.02 through the screen-right hand's first flip (636–732), 0 → 0.53 → 0 through the screen-left hand's (786–866) and 0 → 0.49 → 0 through the screen-right hand's second (1114–1146); the largest step per frame is 0.35 at 790, where the left hand flips in three frames (its facing sign changes at 789, 790, 791) and the fastest tip moves under 100 px: the flip itself, not a tracking loss. The twist starts a few frames before the palm passes edge-on (the tips cross first) and resolves a few after: consistent with the hand.
- strings: taut on 32 % of edge-frames, max tension 1.04 (the long edges in the line state are stretched 43 % beyond the rest quad's 4.4 palms, so the line draws red: a stretched band), max slack 3.8 palms.
- holes: **none open** in this take with the four-tip map (the local J never passes the 1.45 threshold: p98 1.57 at 26 s for a few frames only). The hole law is still in the model; it fires on a take with a harder pull.
- the snap: 1339–1343 contract 0.72 → 0; no sheet from 1344; the tips stay tracked to 1450 and the fire holds the last position across 1451–1465.
- the crop path: all four tips inside the 4:5 crop on 100 % of the 1237 four-tip frames.

## 13. Known limits of round two

- The line state draws the two long edges as two 12-px rods 12–25 px apart with the violet sliver between them, because that is the tracked pinch gap; "one thick line" would need the pinched tips merged, a look decision (`string_px`, or a merge threshold in the model).
- The twist is a 2-D fold: the back face appears where the map's orientation reverses, with no shading of the ribbon's thickness at the fold line beyond the drawn edges.
- The flame is a stylised particle flame, not a fluid: tongues taper and flutter, but there is no vorticity.
- The fire's emitters follow the thumb tips; where the tracking drops (1451–1465) they hold.

---

# Round three — the spectrum, the reel-in, the hand-cut matte, the crossing (2026-09-19, night)

Dennis's verdict on round two (HANDOFF of 2026-09-19 night, eight notes, each measured before anything was built). The
mechanism is round two's; what changed is listed with its source and rank, and §15 gives the printed checks of this run
(`web/work/model_r3.log`, `matte3.log`, `render_r3.log`, `scene_r3.log`).

## 14. What changed, and why

| item | round two | round three | source / rank |
|---|---|---|---|
| 1 the colour | the puppet's violet at rest warming through magenta to red | **the strain ramp in the spectrum's order, no green at any stop** (`render_web.LOOKS["spectrum"]`): J 0 → #FF0000, 0.5 → #FF00FF, 1 (rest) → #B400FF, J\* → #8F00FF, J\* + 0.6 → #4B00FF; the back face is the ramp at \|J\| darkened ×0.62; the tear rims the top stop lit with #FF00FF; the strings red when slack → blue-violet when taut; the crushed fill red; the edge and duotone darks #2A0055 / #3C0078; the panel's LUT, J value, bar and string bars read the same stops (`ramp_stops`, `ramp_rgb`) | Dennis: red for the least strained, then magenta, violet, blue-violet for the most, G = 0 everywhere. The stop positions are assumed (the take's local J peaks at 1.57, so the top stop sits at J\* + 0.6); the fire's ramp is temperature and is unchanged |
| 2, 4 the matte | the whole body-skin component touching a hand's hull | **cut to the hands** (`extract_skin_matte.py hand_px=50 feather=30 hold=10`): alpha within 50 px of each landmark hull, feathered over 30 px, the last hull held 10 frames across a drop; the forearm and the face never enter | measured: the flipped hand's forearm lay over the sheet at 660–668 while its fingertip held it; the neck merged with a hand at the face and the chin box fluttered 0 → 6 → 0 → 5 → 1 % over 1195–1215. The margin and the feather are assumed (the wrist joint is inside 50 px); judged at 1:1 on 660/664/668 and 1183/1197/1206/1209 (`web/work/m3check/`) |
| the hands (his note on the round-three export, 2026-09-19 late night) | the hands composited in front through the matte | **no matte at all in the shipped export** (`none`): the sheet and the strings draw in front of the fingers everywhere | Dennis: the start of a line at a fingertip rendered behind the finger through the matte, and on top it looks sharper. The hand-cut matte of items 2 and 4 stays the knob for the hands-in-front reading (`matte3.npy`, the `-matte` exports) |
| 3 the reel-in | fixed rest lengths after the rest frame | **a rest length is a state**: while a hand is pinched (thumb–index gap < 0.6 palm) or closing (gap < 1.2 and falling over 3 frames), every pair at that hand has its rest length pulled toward its span at 6 palm/s (never below it); otherwise it relaxes back toward the rest length at 1.5 palm/s; before the rest frame the pull-out still lets material slip out of the pinch | Dennis's proposal (a pinch that closes gathers the ribbon). Measured: the pinches close at 1297–1300 (gap 1.24 → 0.20 in 6 frames) and the hands then approach at up to 5 palm/s (spans 3.1 → 0.6 over 1318–1339); at 2 palm/s 1.2 palms of sag rebuilt before the touch, at 6 the slack reads 0.09 / 0 / 0 / 0 in the touch second. The thresholds and speeds are assumed |
| 3 the snap | the picture contracts into the tips' centre over 5 frames | **a fade over the same 5 frames** (`snap_mode=fade`; `snap_f` is the alpha in the shader and on the strings) | with the reel-in the band has no length left at the touch; a contraction would move material that no longer exists |
| 5 the crossing | the strings drawn in ring order, no front/back | **the near long edge per bow-tie run** from MediaPipe's per-hand z of the flipping hand's thumb and index tips (median over 5 frames from the run's entry: the projected thumb → index segment reverses exactly when it is edge-on); the renderer draws the far edge first, then the near edge over it with its own shadow, widened 12 % within a 60-px Gaussian of the crossing and the far one narrowed | measured: the thumb tip is the farther one at all three flips (dz +0.029, +0.061, +0.049; the index edge in front on 637–727, 789–861, 863–864, 1115–1145, 1310–1319). The ribbon's edges are a ribbon's width apart in depth at the fold line and never touch, so the physics of the crossing is occlusion, not a bump in the image plane; the perspective widening is assumed |
| 6 the fire | from source 1409, the first thumbs-up frame | **from the thumbs-up settle, source 1435** (export 40.7 s): both thumb tips above their wrists, both index tips folded > 0.5 palm below the thumb tips, every tip under 8 px/frame for 5 frames (`fire_frame` in params, the scene's `fire=auto`) | Dennis: only once the thumbs-up is fully positioned. Measured: the hands rise at 1418–1429 (up to 250 px/frame) and hold from 1430; the index fold is +1.0 palm at the thumbs-up and −0.3 to −1.2 at the second touch (the first detector without it fired at 1359) |
| 7 the holes | none (J\* 1.4 + Exp(0.3): 1.45–2.26; the local J never passed 1.45) | **J\* 1.2 + Exp(0.2): 1.23–1.77, median 1.33; r_max 0.3 palm; margin 0.3** | Dennis: the holes must appear again. Measured: J\* 1.15 + Exp(0.15) opened 10 at once on 55 % of the sheet at the peak; this calibration opens on the pushes only (§15). The count at once is a knob (`n_defects`) if he wants fewer |
| 8 the panel | `J* 1.40` beside the value, `· 16 defects` in the field's label, the holes block at zero | the J\* number gone (the tick and the dashed line stay), the label reads `strain field`, the holes block stays because the holes vary now; **the script counts the distinct strings per slot over the export and names any value slot that printed one string** (labels are declared) | Dennis: remove every value that does not change through the video. The rule is in the scene script's docstring and its last printed line |

## 15. Measured on the take (this run's printed checks)

- reel-in: hand 0 reels on 311 frames, hand 1 on 325; slack per edge per second at the pinches: source 8 s (the touch) 0.07 / 0 / 0 / 0.29 palm,
  9–15 s all 0, 44 s (the touch second) 0.09 / 0 / 0 / 0; the 43 s second still carries the pre-pinch sag (2.31) on its first frames, gone
  within 12 frames of the pinch. The sags with open hands at 31–35 s and 39–42 s (the hands 2.2–3.5 palms apart, the pinches open at 1.5–1.9
  palm) are unchanged: nothing gathers them.
- crossings: five bow-tie runs, the index edge in front on all (the thumb farther by dz +0.03…+0.06 at every flip's entry).
- the settle: 1435 (47.83 s source, 40.7 s export).
- holes (r > 0.04 palm): open on **6.9 s** in 4 runs (749, 881, 989, 1093: the pushes), the longest 2.13 s, at most 9 at once, peak hole area
  1.98 of 8.3 palm²; 9 of 16 defects ever open at 0.39 of the outline's mean radius (the middle).
- the matte: the chin box's coverage over 1174–1264 is the hand's own pixels (max 6 % at 1197 where hand 0's hull spans x 193–459 into the box);
  the hull held across 10 untracked frames.
- the spectrum: the renderer prints the stops and their green channels ([0, 0, 0, 0, 0]).

## 16. Known limits of round three

- The reel-in is gated on the pinch (closed, or closing under 1.2 palm): a slow closing from 1.5 palm (1240–1294, 0.016 palm per 3 frames) is
  indistinguishable from jitter and does not reel; the sag of the approaching open hands stays until the pinch.
- The crossing's depth cue is occlusion plus a 12 % width change; there is no shading of the ribbon's edge-on surface at the fold line.
- The fold colour on the panel is the rest colour darkened, not the local |J| the shader reads.

## 17. His three notes on the round-three export (2026-09-19, late night; what ships)

- **The effect draws in front of the fingers**: no matte in the export (`none`); the with-matte exports are kept as `-matte`.
- **The logo at 38 s, no thumbs-up**: the export is trimmed at source 1354 (ten frames after the fade ends at 1344), and the tail's
  flames start at the tips' last tracked position, the touch point (`fire=none`); the fire from the thumbs and the settle
  detector are unused.
- **No holes**: `n_defects=0`; the hole law stays in the model and the renderer with nothing to act on, and the panel has no holes block.
  §14's item 7 and §15's hole line describe the calibration that was measured before this note, not what ships.
- **Orange, yellow and blue as the middle tones**: the ramp is red (J 0), orange (0.5), yellow (1, the rest), blue (J\*), violet
  (J\* + 0.6); no stop is a green hue, and the only grey-green is the short yellow → blue mix above the rest. The strings still run
  red (slack) → blue-violet (taut).

## 18. Round three, second pass (2026-09-19 late night; his notes on the shipped export, what ships now)

| item | before | now | source / rank |
|---|---|---|---|
| the short edges | every ring edge a catenary when slack (0.37–0.79 palm of slack on i1–t1 and t0–i0 at source 1174–1294: small loops beside each thumb, read as "one extra hanger to each thumb") | **a pair with both anchors on one hand never sags**: its effective rest length is min(L0, span), a straight thumb → index line, slack 0, tension only past the rest spread (`short_sag=0`) | the material between two fingers of one hand lies across the hand; a held ribbon end does not hang between the fingers holding it (assumed, judged on 1183 and 1206). Printed: "their slack is 0.00 palm at most" |
| the ramp (the r3b exports; the code has since replaced the neutral stop by a hard yellow → cyan step at J\* − 0.1, his later note, not yet exported) | red 0, orange 0.5, yellow 1, blue J\*, violet J\* + 0.6 (the yellow → blue band 1.0–1.2 flipped the whole sheet blue → yellow in two frames at source 1010) | **red 0, orange 0.5, yellow 1, the brand's neutral #F2F0EA at J\* − 0.1, cyan #00D8FF at J\*, blue #0040FF at J\* + 0.25, violet #8F00FF at J\* + 0.45** (= 1.65, the take's largest local stretch 1.57); the shader mixes the stops in linear light and `ramp_rgb` now does the same, so the panel and the sheet agree | Dennis: "red orange yellow cyan (cyan only if possible with no green) blue violet". Any path from yellow (hue 60°) to cyan (190°) that keeps its saturation passes green (120°); the only green-free path runs through the achromatic axis, so the ramp crosses through the neutral over a tenth of a stretch. `ramp_check` samples the ramp at 400 points and reports any sample of hue 75–165° at saturation > 0.2: none. The look field's temporal median is 9 frames (was 5) |
| the lines | red when slack → blue-violet when taut, by tension | **the sheet's ramp read at λ², λ = span / effective rest length per edge** (`stretch` in the model file): slack red → orange, rest yellow, taut cyan → blue → violet; the panel's map and its edge rows use the same colour | an isotropic areal stretch λ² has the linear stretch λ, so a line and the material beside it read one scale (assumed; the edge's own strain is one-dimensional). The width still thins with tension |
| the interior at the lines | the MLS mesh (pinned to the tips and six samples per string) fell a few px short of the drawn line between the samples and the fill pass painted that gap in the crushed red: a red seam along a yellow or blue sheet | **the fill pass carries the nearest drawn colour** to the outline (16 rings of 8 samples within `ext_px` 40); the crushed colour only where nothing is drawn within that radius | Dennis: "some inside doesn't touch the lines". The outline SDF already clipped the mesh to the strings' polygon (nothing drew past a line); the seam was the gap on the inside |
| the panel's map | every other grid cell filled if its diagonal corners were inside the rest sheet: the fill overshot a line where a cell straddled it and stopped short where the mesh did | **cells with any corner inside are rasterised, the field is clipped to the polygon of the strings, bare pixels inside take their nearest rasterised colour** (SciPy's EDT with indices), the lines on a 1-px ground of the panel's colour | Dennis: "the strain field isn't neat, some inside doesn't touch the lines or goes over the lines" |
| the panel | a stat, a bar, a trace, the map, up/down bars, a state line, a gap where the holes block had been | **one type scale (Inter labels, JetBrains Mono numbers), hairlines between sections, the brand accent as a 6-px mark by the heading; the meter under the hero figure is the ramp itself (full colour to the current J, dimmed beyond, the J\* tick), the trace labelled "last 6 s", the map framed, one row per edge (name, pair, a bar of λ on the ramp with the rest tick, "slack 0.41" / "+38 %" / "rest")**; the ten-tip dough keeps the up/down bars | Dennis: "doesn't look like something Fable would do"; the dataviz skill's stat-tile and meter rules (the track a lighter step of the same ramp, text in text tokens, thin marks, recessive grid). Every slot still passes the constant-value check |

Measured on this run (`web/work/model_r3b.log`): the short edges' slack 0.00 palm at most; edge stretch 0.42–10 (the top is the reeled pinch at the
pull-out); the long edges' slack at the pinch second unchanged from §15 (43 s: 2.31 palm before the reel catches up, 44 s: 0.09); the look
field's per-frame |dJ| p98 0.111 at the 9-frame median (0.112 at 5).

---

# Round four — the lines are physical: the yellow → cyan step, the crossing as a pinch point, the contact fold (2026-09-19, late night)

Dennis's three notes on the r3b export and his round-four brief (HANDOFF of 2026-09-19 late night). Every number here is measured on
the take (`web/work/model_r4.log`, `flicker_r4a.png`, `web_edge_contact.py`), read off the archive (`references/finger-web/02-...md`), or
marked assumed.

## 19. What changed, and why

| item | before (r3b) | now (r4) | source / rank |
|---|---|---|---|
| yellow → cyan | the brand's neutral between yellow (J 1.0) and cyan (J\*) as the only green-free mix: a pale band he did not want | **a hard step at J\* − 0.1 with a Cornsweet cusp** (`render_web.py yc_mode=cornsweet`, `yc_amp` 0.25, `yc_w` 0.06 J): within 0.06 of the step the yellow side darkens and the cyan side brightens by a quarter, the luminance ramp the eye reads across an edge (Craik–O'Brien–Cornsweet). Two other modes are knobs: `step` (the bare step) and `dither` (coarse stripes in rest space, 0.15 palm = 19 px at 1080, whose cyan share runs 0 → 1 over J 1.0 → J\*) | Dennis: "make the yellow transition directly to the next colour without white (green)", then "try forcing an illusory gradient". Measured: the additive mix of #FFE000 and #00D8FF is (128, 220, 128), hue 120°: any pattern fine enough to FUSE (in the eye, in the 720 downscale, in the encoder's 4:2:0 chroma average) comes out green, so only a visible grating is green-free, and on 664 / 700 / 1010 it reads as teeth along the isoline, not as a gradient (`web/work/yc7_compare.png`). Green pixels inside the sheet as the file carries them (`web_green_check.py`, 720 + 4:2:0): step 0.31 %, stripes 0.59 %, cusp 0.07 % on 664, all thin boundary blobs (≤ 28 px), none a band. The cusp's amplitude and width are assumed |
| the step's cost | the neutral band mixed over 0.1 J | the isoline sweeps: where the sheet's strain is near-uniform and near 1.1, the WHOLE sheet flips yellow ↔ cyan (export 21.3, 21.9, 23.6, 25.6, 26.5, 28.9, 32.0 s in `flicker_r4a.png`; 28 gate events against 17 for r3b) | the hard step's own nature under his rule; `yc_step=` moves it (the sheet's J_global runs 1.1–1.3 over 21–32 s, so 1.2 still flips), the stripes spread it over the zone. His call on the export |
| the pinch's colour | yellow → cream → cyan over three frames at export 36.3 s | yellow → cyan in ONE frame (source 1302 → 1304: λ 1.04 → 1.07, λ² crossing 1.10) at `reel_v` 6 palm/s; at 3 palm/s the line stays yellow through 1310 (λ 1.03) but 0.59 / 0.65 palm of sag survive into the touch second (0.09 / 0 at 6) | measured on both models (`model_r4_reel3.log`, `pinch7_compare.png`); the reel stays at 6: the sag was his note, the colour jump is the model's own event |
| the crossing at a flip | the near long edge drawn over the far one (occlusion, a 12 % width cue) | **both long edges taper by 70 % into the crossing point** over a 60-px Gaussian (`xmode=pinch`, `xtaper`): the rods converge into the point as a ribbon's edges do where it is edge-on; `xmode=occlude` keeps round three's draw | Dennis: "the crossing is a pinch point, not one line drawn over the other"; the taper is assumed, judged on 641 / 664 / 700 / 792 / 1130 (`cross7_compare.png`) |
| contact by bending | none: the rods were pictures | **the contact fold** (`web_membrane.py contact=twist`): when the two long edges come within `contact_px` (18) at an interior point (arc fraction 0.15–0.85 on both) with neither hand pinched or closing (gap ≥ 1.2 palm) and no bow-tie, a fold strength rises over `fold_in` 4 frames and decays over `fold_out` 8; both polylines are pulled to MEET at the contact point (the centreline drawn to it under a Gaussian of half `fold_w`), and in `twist` mode the edges swap sides over an arc of `fold_w` 0.22 of their length: two pinch points with the back face between them, a local loop; `pinch` mode only meets. The MLS interior is pinned to the deformed polylines, so the sheet folds with them. Printed: the events, the min distance, the peak fold, the chain's length ratio (a fold gathers: > 1.05 would be a pull) | Dennis: "the top and bottom lines might spatially touch each other when bending, which should trigger an extra twist where the lines touch". The loop is Chopin & Kudrolli 2013's self-contact regime in projection (item 02: below T\* ≈ 0.8 h/W a slacker ribbon self-contacts at a LOWER twist). A first-order kinematic fold, not the XPBD chain of the brief (item 02 §7 has the recipe: a hard capsule constraint at the closest points, 10–50 iterations); the thresholds and times are assumed |
| **measured: contact on this take** | — | **zero interior events.** Every approach under 18 px outside a bow-tie is at an edge's END (the crossing enters and leaves through the flipping hand's end: 636 d 31 px at t_b 1.00, 728 17 px at t_b 1.00, 1114 6 px at t_b 1.00, 1146 6 px at t_a 1.00) or with a hand pinched (862–867, 1110–1114, 1144–1149: gaps 0.17–0.5 palm); the sag alone reaches 67 px. His "second 14" is the first flip's entry (the index tip's corner reaching the thumb edge at 634–636), so the contact he saw IS the bow-tie's crossing, now a pinch point | `web_edge_contact.py`, the per-frame table in this session; the fold mechanism stays with nothing to act on, and fires on a take where the sag brings the edges together |
| the twist's turn | — | the near-edge decision's dz keeps its sign through every bow-tie run (+0.03..+0.06 at the three entries, the index edge in front on all five runs): his twist never passes a half turn | `model_r4.log` crossings |

Known limits: the fold is kinematic (no inertia, no real capsule pair, the "settle" a first-order ramp); the Cornsweet cusp cannot stop the sheet-wide
flip of a hard step; the stripes' teeth follow the isoline's shape and cannot be made to read as a smooth gradient without fusing to green.

---

# Round five — the fade, the helicoid twist, the short edges' spread, the logo on the ramp (2026-09-22)

Dennis's five notes on the r4 export (HANDOFF of 2026-09-22): the yellow → cyan transition as a gradient ("like a button that fades from one
colour to the other", no dark part, and "No green!" for the stops), the lines that touch at the flips and should physically twist, the thumb →
index lines on the heat map too (red at the least spread, violet at the most), the one scale from red (loose) to violet (tight), the logo's
writing in the animation's predominant colours on a black ground. Every number here is measured on the take (`web/work/model_r5.log`, the
r5 gate logs) or marked assumed.

## 20. What changed, and why

| item | before (r4) | now (r5) | source / rank |
|---|---|---|---|
| yellow → cyan | a hard step at J\* − 0.1 with a Cornsweet cusp (the sheet flipped yellow ↔ cyan seven times where its strain sat at the step) | **a plain fade**: yellow at J 1.0, cyan at J\* (1.2), mixed in linear light like every other segment (`render_web.py yc_mode=fade`, the default; step, dither and cornsweet insert their step into the fade at `yc_step=`) | Dennis: a gradient as a button fades, no dark seam, no white bridge, no step. The fade's middle is a pale mint by the physics of the two lights: `ramp_check` reports 5 of 400 samples over the hue rule (saturation ≤ 0.25) and 7 pale ones over J 1.07–1.12, as facts; no stop is green and no stop is white. The fade also removes the step's sheet-wide flips |
| the twist | each long edge its own string between two tips (straight or a catenary): a flipped hand gave a bow-tie of two straight-edged triangles, the crossing wherever the chords met | **the long edges are a helicoid's projection** (`web_membrane.py twist=helicoid`, the default): with the two hands' frames differing by a twist, the width vector rotates uniformly along the length and the projected half-width across the axis is W(s) cos θ(s), θ linear in s; the edges bow in a cosine toward the crossing (where θ passes 90° the ribbon is edge-on and the edges meet), full near the hands, pinching fast into the point. θ per hand: cos θ_h = (the projected half-width of its thumb → index vector across the axis) / (the physical half-width, at least that pair's rest spread); the projection's sign gives the branch, so a flipped hand reads θ > 90°. The centreline is the mean of the two strings (the sag survives); the tips' offsets along the axis interpolate linearly; the ends are the tips exactly | Dennis: "the lines touch and should physically twist, like second 14". Uniform twist is the elastic rod's under tension (item 02: Chopin & Kudrolli 2013 for the regimes where it localises; assumed uniform here). Measured: the hands' frames differ by > 10° on 425 frames (median 37°, max 129°); the edges bow up to 53 px from the straight strings (median 10 px on the bow-tie frames); the edge-on point sits at 0.02–0.90 of the length on the bow-tie frames, median 0.48 (the middle: a completed half turn); with equal angles the formula is the straight edge, so the untwisted frames move 0 px. The near edge (which lobe is in front) still comes from MediaPipe's z at the run's entry (§14) |
| the short edges' colour | yellow (their effective rest length min(L0, span) kept their stretch ≥ 1) | **the finger spread against the hand's usual spread**, span / median(span over the hand's open frames): a pinch red, the usual spread yellow, wider cyan → blue → violet; the geometry stays the straight line with no slack | Dennis: "can't they also follow a heat map for how stretched it is, with max being violet, lowest being red". The reference is the usual spread, not the rest frame's: the rest frame (514) is the WIDEST spread of the take (2.16 / 2.21 palms), against which the lines sat below 0.9 on 1004 of 1104 frames and never reached cyan. Measured: the usual spreads 1.86 (hand 0, 793 open frames) and 1.87 palms (hand 1, 779); the range 0.01–1.27 (λ² 1.61, a hair under the violet stop at 1.65); below 0.9 on 582 frames, above 1.1 on 288 |
| the one scale | the sheet's J and the long edges' λ² on one ramp; the short edges clipped at yellow | the sheet's J, the long edges' λ² and the short edges' (spread ratio)² on the one ramp; the renderer prints the stops as J and as line stretch (red 0 / 0, orange 0.5 / 0.71, yellow 1 / 1, cyan 1.2 / 1.10, blue 1.45 / 1.20, violet 1.65 / 1.28); the panel's edge rows print `-N %` for a short edge below its usual spread | Dennis: "looser, further down until red, tighter, further up the colours until violet; I'm not sure how consistent it currently is" |
| the logo | the puppet video's violet neon (accent #8F00FF, core #CBA0FF, a red tick) | **the wordmark's letters on the ramp's stops** (D red, y e orange, A l yellow, l P cyan, i e blue, s violet: each letter the nearest stop, no mixing inside a glyph), the tick as the six stops in segments, PRODUCTIONS in the rest yellow, the URL and the tube cores in the brand's neutral #F2F0EA, the ground black (`web_fire.Sting(ramp=)`, fed by the scene from `render_web.ramp_stops`) | Dennis: "the background continues black, but the writing will have the predominant colours of the animation". The letter assignment is assumed (nearest stop by position); the flame that writes the letters keeps its temperature ramp |

Known limits: the helicoid's twist is uniform (a slack ribbon localises it), and the edges' bow is the projection only (no width-by-depth cue, no
shadow of the near lobe on the far one: item 4 of the round-four brief, still open); the fade's middle is a pale mint by physics and stays so
in the file; the short edges' top stop is just out of reach on this take (1.27 against 1.28).

---

# Round six — the colour measured in the file, the helicoid shaded, the short edges coupled to the long ones (2026-09-22)

Dennis's notes on the r5 export (HANDOFF of 2026-09-22, evening): the red-orange and the violet are good, the yellow is not; the twist is
"missing something to make it look more real" (friction where the lines touch, or a full 3D model with collision); seconds 15 and 19 have the
prettiest colours; the thumb → index lines should have their stretching take the longer links (index to index, thumb to thumb) into account.
Every number here is measured on the r5 file or the take (`web/work/model_r6.log`, `render_r6.log`, the r6 gate logs) or marked assumed.

## 21. What changed, and why

| item | before (r5) | now (r6) | source / rank |
|---|---|---|---|
| **measured: the colour as the file carries it** | judged by the stops | the sheet's INTERIOR (the coverage eroded by 31 px, the strings excluded) per export second on the r5 720 file: at 10 s (the rest yellow) the median pixel is (209, 186, 92), saturation 0.57, hue 50°: a mustard, while the stop is #FFE000 (saturation 1); at 25 and 28 s (orange, J 0.6) (209, 150, 77), saturation 0.64; at 19 s (his "prettiest", the cyan → blue sheet) (82, 148, 208), saturation 0.61 but a dark hue, so it reads rich; at 15 s (the bow-tie: red, yellow, cyan and blue in one frame) saturation 0.88. Two leaks, both in the composite, neither in the ramp: the duotone `mix(shadow_col, sheet, q)` blends the FIXED dark violet #3C0078 into every stop wherever the plate's posterised luminance q is below 1 (the wall reads q 0.6), and a violet shadow turns yellow, and only yellow, to mud (red, cyan, blue, violet keep their hue against it); and `filt` 0.75 let a quarter of the plate's light through, which desaturates the brightest stop most (computed: yellow on the wall (242, 214, 90) at saturation 0.63 before the shadow, cyan (94, 207, 240) at 0.61, red (251, 45, 47) at 0.82) | this session's measurement script (the r5 720 file, `sheet_cov8.npy`), the composite rebuilt in NumPy from the shader's own formula |
| the duotone's shadow | the fixed dark violet #3C0078 for every stop | **the sheet's own colour × 0.22 in linear light** (`render_web.py shadow_mode=hue`, `shadow_k`; `fixed` keeps r5's): a yellow gel's dark is a dark gold, a cyan gel's a deep teal; the picture inside stays the plate's posterised luminance | a translucent coloured sheet in front of a scene is a filter: what it darkens keeps its hue (assumed as a look rule; the constant 0.22 assumed, judged on 574, 1010, 1183, 1206) |
| the plate's light through the sheet | `filt` 0.75 (25 % of the plate added) | **`filt` 1.0 for the spectrum look** (in the look; the CLI still overrides): the plate enters only through q | measured above; the r5 yellow's saturation 0.57 → the r6 preview's interior (574) is the stop's hue at saturation ≈ 0.85 |
| the twist's depth | the helicoid's projection only (the lobes' outline; flat colour inside) | **Lambert shading of the helicoid** (`heli=1`, `heli_k` 0.55): the model saves each hand's angle out of the image plane (`heli_th`, the same θ that bows the edges), the shader interpolates θ along the ribbon's REST axis (from hand 0's tips to hand 1's, 4.27 palm) and scales the colour by `mix(1, |cos θ(s)|, heli_k)`: a matte face lit from the camera's side is bright face-on and 45 % at the edge-on point, so each lobe darkens into the crossing and brightens toward its hand; with equal angles at both hands the factor is a constant near 1 | a diffuse surface under a frontal light (Lambert's cosine law); the depth 0.55 assumed, judged on `twist9_compare.png` (700, 792, 1130). His two proposals, measured against the take: a contact / friction rule has nothing to act on here (round four: zero interior contacts, every approach under 18 px is at an edge's end or a pinch), and a full 3D ribbon with collision (the XPBD chain, item 02 §7) would produce the same projection on a take whose edges never touch; what the eye missed on the flips was the shading, the cue the projection cannot carry. The near lobe's shadow on the far lobe and the width-by-depth cue stay open |
| the short edges' stretch | span / the hand's usual spread | **× the long edges' width factor λ_L^ν** (`couple=1`, `nu=0.5`): the ribbon is one sheet, so pulling it along its length narrows it; a membrane of an incompressible material held at the lengthwise stretch λ_L has the natural width W0 λ_L^(−ν), and fingers holding the end at the usual spread stretch the width by λ_L^ν on top of span / usual. λ_L is the mean of the two long edges' stretch (both end at every hand), floored at 1 (a slack catenary carries no tension and does not widen the ribbon) | Poisson's ratio 0.5 for rubber-like membranes (Treloar, The Physics of Rubber Elasticity, the uniaxial case: transverse stretch λ^(−1/2)); ν for this ribbon assumed. Measured: the long edges' mean stretch is above 1.04 on 669 frames, the width factor up to 1.38 (median 1.18 on those frames), the short edges' stretch moved by 0.33 at most; the range is now 0.01–1.56, above 1.1 on 507 frames (288 before), above the violet stop on 140 (0 before): the short edges reach violet at the taut flips |

Known limits: the shading is a single frontal Lambert term (no specular, no shadow of the near lobe on the far one); the fade's middle stays a
pale mint by the physics of the mix (the pinch line at 43 s and a short edge near the usual spread sit there); the coupling reads the mean of
both long edges, not the one nearer each finger; the yellow stop itself (#FFE000) is unchanged and is his call after this composite.
