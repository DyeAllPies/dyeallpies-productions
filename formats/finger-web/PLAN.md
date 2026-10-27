# The finger-web video — plan (2026-09-18, before any build)

Written by Opus for **Fable** to review and carry out. Nothing here is built yet; what *is* already
done in this session is listed in §10, and everything in §9 is a real decision left open on purpose.

**Source:** `web/originals/IMG_6268.MOV` (iPhone 14, 2026-09-18 11:22 local, HEVC, 1920×1080 with a
`rotation=90` tag so it is 1080×1920 upright, 30 fps, 49.90 s, 1497 frames). The audio is room tone
only — mean −53.1 dB, peak −24.7 dB — so there is **no speech to cut around** and music goes on in
CapCut/Instagram as usual. The upright master is made: `web/work/master.mp4` (NVENC, decode-gated).

**Reference:** two screen recordings of reels by `mishu.ksv`, also in `web/originals/`. The one
Dennis means is `ScreenRecording_09-18-2026 15-15-54_1.mp4` (`#spiderman #python #software 🕷️🕸️`).
Her code is legible in the frame: `frame = render_portal(frame, p1, p2, p3, p4, FILTROS[filtro_index])`
with `filtro_index = (filtro_index + 1) % len(FILTROS)` — four fingertips make a quad, the picture
inside it is filtered, the filter cycles. Fully decoded in
`references/finger-web/01-elastic-membrane-and-hole-formation.md` §1.

**What we are making:** the same idea, with the two departures Dennis named — the lines between the
fingers are **elastic** (tighter or looser with how hard he pushes, calibrated so the first stretch
is the taut reference), and the surface behaves like **dough**, which **opens holes in the middle**
when it is pushed past its limit.

---

## 1. The single most important finding: his gesture is not her gesture

`mishu.ksv` holds both hands in the "director's frame" — thumb and index extended, the other fingers
folded — so her four corner points are far apart and make a clean rectangle.

**Dennis does something else.** Both palms face the camera with **all five fingers spread**, and the
hands move apart, together, and diagonally (`web/work/quad_check_a.png`, `quad_check_b.png` — the
thumb/index quad drawn on his actual frames). Measured against her construction, on his take:

- **In 35% of the two-hand frames at least one hand is pinched** — thumb tip to index tip under half
  a palm width — which collapses that hand's pair to nearly a point and the quad to a triangle.
  Frames 330 and 420 are the clear cases. (40% of frames are under a full palm width.)
- **The quad covers a median 0.47 of the area the ten fingertips span**, and only 0.04 at its 10th
  percentile. Her four points throw away **more than half** of what his gesture actually offers —
  median 4.0% of the frame against the ten-tip hull's 8.3%.

So the anchors are the **ten fingertips** (landmarks 4, 8, 12, 16, 20 on each hand). That is not a
workaround — it is the better fit for what Dennis asked for. Ten anchors is what "lines between the
fingers" means literally, it is what a sheet of dough held in two hands is actually held by, and it
gives the sheet a boundary that changes shape as the fingers open and close, independently of how
far apart the hands are.

Measured consequence (`tools/scripts/analyze_finger_web.py`): the convex hull of the ten tips uses
**6 of the 10 tips** in 607 of 1335 two-hand frames. Four anchors are typically *inside* the hull.
They should still be pins — a finger pressing into the middle of the sheet is exactly the dough
behaviour we want — but they must not be treated as boundary vertices.

## 2. What happens in the shot (measured, not guessed)

MediaPipe Hand Landmarker in VIDEO mode over the master (`web/work/hands.npz`): a hand on 1349 of
1497 frames, **both** hands on 1335 (89%). `J` below is the ten-tip hull area normalised by palm
width squared and divided by the take's 10th percentile — a scale-invariant areal stretch, so it
survives him leaning toward or away from the lens. Medians per second, median-filtered over 5 frames:

| time | frames | what the hands do | J |
|---|---|---|---|
| 0.00–0.93 | 0–28 | settling, one hand only | — |
| 0.97–4.30 | 29–129 | **the first stretch** — hands come up and open out | 0.4 → 3.9 |
| 4.33–7.10 | 130–213 | hands drop out of frame | — |
| 7.13–12 | 214–360 | **the build** — opens steadily to near full span | 0.65 → 4.7 |
| 12–20 | 360–600 | hold, oscillating; a dip at 14–15 s | 4.5 → 3.4 → 4.6 |
| 21–26 | 630–780 | **the push** — the peaks | 5.0 → 5.6, max **8.5** at 26.30 s |
| 27–35 | 810–1050 | recovers, oscillates wider and lower | 3.8 ↔ 2.2 |
| 36, 38 | 1080, 1140 | **two more peaks** | 5.28, 5.19 |
| 39–46 | 1170–1380 | **the release** — steady decay to nothing | 2.7 → **0.23** |
| 47–48.3 | 1410–1448 | a short last pose | 1.5 |
| 48.37–49.87 | 1451–1496 | hands gone | — |

**Frames 214–1419 (7.13–47.30 s, 40.2 s) are effectively one continuous take.** The run-detector
reports two runs because of a **single-frame dropout at frame 864**; interpolate it and the whole arc
— build, hold, push, push again, release — plays without a cut. The release is the gift here: J falls
to 0.23 and everything goes slack on its own, which is a natural ending that needs no invention.

## 3. The model

Full derivation and sources: `references/finger-web/01-elastic-membrane-and-hole-formation.md`.
Every constant below carries its source in line, per CLAUDE.md. A companion `web/WEB-MODEL.md`
should be written as the model is built, the way `hand/PUPPET-MODEL.md` was.

### 3.1 The sheet

A **Lagrangian membrane in image space**: a triangulated material domain, built once at the
calibration frame as a regular triangulation of the rest-state hull, with the ten pins at their rest
positions. Each frame the pins move to the tracked fingertips and the sheet is solved.

- **Solver: XPBD** (Macklin, Müller & Chentanez 2016, `papers/macklin2016-xpbd.pdf`), not plain PBD.
  PBD's stiffness depends on the iteration count and the time step, so a look tuned at one solver
  setting silently changes at another. XPBD's compliance α̃ = α/Δt² makes stiffness a real material
  parameter. Dennis will ask for "stiffer" or "loppier" and the knob has to still mean that after a
  re-render.
- **Substeps, not iterations** (Macklin et al. 2019, `papers/macklin2019-small-steps-in-physics-simulation.pdf`):
  8–16 substeps per source frame, one or two iterations each, rather than one step with many
  iterations. Non-negotiable given the measured peak fingertip speed of **274 px/frame** (§3.5).
- **Pins are hard constraints**, not springs — PBD projects the position directly (Müller et al.
  2007, `papers/muller2007-position-based-dynamics.pdf`), so a fingertip snap cannot blow the sheet up.
- **Strain limiting** by clamping the singular values of each element's deformation gradient F
  (Wang, O'Brien & Ramamoorthi 2010, `papers/wang2010-multiresolution-isotropic-strain-limiting.pdf`).
  This is literally "stretched above its limit", and the SVD hands us the two principal stretches
  λ₁, λ₂ per element for free — so **J = λ₁λ₂**, the per-element areal stretch, is a by-product, not
  an extra computation.
- **2D, not 3D, for round one.** Measured tip depth (MediaPipe model z) spans only −0.02 to −0.10
  image-width units across the take, so the sheet is very nearly planar; z is worth using for shading
  and a little parallax, not for the solve. Revisit only if the flatness reads badly.

### 3.2 Why holes appear in the middle

Dennis said the holes start "in the middle". That is where the physics puts them anyway, for two
independent reasons, and it is worth saying so in the model document:

1. The pins hold the material at the boundary. All the areal change has to be accommodated by the
   interior, so **per-element J peaks farthest from any pin** — the middle.
2. Nucleation in a biaxially stretched elastomer is governed by the **hydrostatic** (dilatational)
   strength, which for natural rubber is 2.9 ± 0.5 MPa against 11.3 ± 3.7 MPa uniaxial and
   14.8 ± 6.2 MPa biaxial — about **four times lower** (López-Pamies 2024, `papers/lopezpamies2024-cavitation-jmps.pdf`,
   reviewing Gent & Lindley 1959 and Kumar & López-Pamies 2021). It is the *areal* mode that fails
   first, and that mode peaks away from the constrained boundary.

### 3.3 Dough: the material law

Model the sheet as **volume-incompressible**, so thickness h = h₀ / J. Feed J through the dough law
measured in large-deformation biaxial extension — the same deformation our sheet is in, which is why
this literature transfers (Dobraszczyk, *Baking, Extrusion and Frying* ch. 8,
`papers/dobraszczyk-baking-extrusion-frying-ch8.pdf`, Figs. 8.11–8.13):

- **σ = K·ε^b**, a J-shaped power-law: stiffness rises rapidly with inflation.
- Strain hardening "allows the expanding gas cell walls to resist failure by locally increasing
  resistance to extension **as the bubble walls become thinner**" — the self-stabilising term that
  keeps a real dough sheet from tearing the instant it is pulled.
- "Once strain hardening drops below a value of **around 1**, bubble wall stability decreases
  rapidly." **b ≈ 1 is the published stability knee**, and it is the one number here that is
  quotable. Rank whatever b we pick against it before rendering, the way the pull-up model's
  ordering is printed against Youdas 2010.

**b is Dennis's material dial**: b > 1 is bread dough that fights back and survives a big stretch,
b < 1 runs away and goes to holes early. NOT FOUND this pass: tabulated b and Hencky-failure-strain
values per flour — the primary (Dobraszczyk & Roberts 1994) is paywalled at Elsevier. Treat b as a
ranked look knob, not a measured constant, and say so in the model document.

### 3.4 Holes: three stages, three laws

**(a) Nucleation — a seeded defect field.** Holes nucleate at pre-existing defects, and the critical
stress rises sharply as the defect gets smaller (Gent & Lindley 1959 via `papers/lopezpamies2024-cavitation-jmps.pdf`).
So: scatter a **fixed-seed** random defect field over the material domain, each defect with its own
threshold J\*ᵢ drawn from a distribution. A defect opens when the local J passes its own J\*ᵢ.

This buys three things at once: holes appear **one at a time in a staggered order** instead of the
middle going porous in a single frame; the order is **repeatable**, so the render is deterministic
and the bake-once cache (`studio.cache.BakeCache`) stays valid; and the look is controlled by two
honest parameters (defect density, threshold spread) rather than by hand-placed holes.

**(b) Growth — Taylor–Culick, which gives us the rate for free.** A hole in a thin film opens at a
constant velocity v_TC = √(2γ / (ρ h₀)) (Taylor 1959, Culick 1960; stated in
`papers/villermaux2022-taylor-culick-retractions-surroundings.txt` eq. 1.1 and independently in
`papers/petit2015-holes-and-cracks-in-rigid-foam-films.txt`). With h = h₀/J from §3.3 this becomes

> **v ∝ √J**

— holes that open where the sheet is thinnest also **grow fastest**, with no art direction. One
constant (the growth scale) sets the whole behaviour.

**(c) The perimeter — a rim and radial cracks, and this is what sells it as dough.**

- "the liquid collects in a **thicker rim** at the retracting edge of the film" — a hole in a real
  film has a raised, rolled edge, never a clean cut. A rim only grows if the film's extent exceeds
  the Stokes length μ/(ρ v_TC), so the rim thickness has a physical scale rather than an arbitrary one.
- Petit et al. 2015 studied films with high **surface elasticity** — closer to dough than water is —
  and report "**crack-like patterns**" radiating during the hole opening rather than a smooth circular
  retraction. So the honest look for an elastic membrane is a hole with a **raised rim and radiating
  cracks**, which is also far more legible on a phone screen than a smooth circle.

**(d) Closing.** Griffith says a hole grows only while the elastic energy it releases exceeds the
fracture energy it costs, so when the hands relax the growth **stops**. True healing is a
viscoelastic-recovery argument, not a Griffith one — so the honest behaviour, and the one to
implement, is "holes stop growing and then slowly close", not "the tear un-tears". This matters for
the ending: at 39–46 s J decays to 0.23 and the holes should visibly close as he lets go.

### 3.5 The lines between the fingers: taut and slack

The boundary edges between consecutive hull anchors are the visible "strings". Each gets a rest
length L₀ from the calibration frame (§3.6). Per frame, with `span` the current tip-to-tip distance:

- **span ≥ L₀** — taut, straight, and the tension feeds the look (brighter, thinner, more strained).
- **span < L₀** — slack by ΔL = L₀ − span, and it **sags**.

**Do not write this from scratch.** `tools/scripts/render_puppet.py:122`, `catenary_points(A, B, L)`,
already solves the **exact** catenary for the marionette's strings — `brentq` on
2a·sinh(h/2a) = √(L² − v²), then x₀ and c from the endpoints — and it already carries the two
degenerate cases that broke it during that build (a vertical drop with h < 1e-6, and span ≤ h where
the root falls outside any bracket, both dated in its docstring). Port it, per the
`port-referenced-look-from-code` memory. The one adaptation needed: it works in world coordinates
with **z up**, and our membrane is in image space with **y down**.

Keep the parabolic closed form as the cheap sanity check on the port
(`papers/johndcook-catenary-sag-approximation.txt`; the <1% refinement is Frame 1950):

> extra length ≈ 8·sag² / (3·span)  ⟹  **sag ≈ √( 3·span·ΔL / 8 )**

It also says what the behaviour should feel like: sag grows as the **square root** of the slack, so a
line that goes slightly long drops a lot at first and then flattens — the reason a washing line
droops far more than people expect. That square root *is* the whole "looser if less stretched" half
of Dennis's request, and if the ported exact solver disagrees with it at shallow sag, the port is
wrong.

This is also precisely where the open-source prior art stops. `AadishY/Hand-Gesture-Filter` (MIT)
advertises "elastic membrane bending"; `code/aadishy-geometry.js` implements it as a **fixed 7% bow**
(`const bendFactor = 0.07;`) on quadratic Béziers — the same curve whether the hands are together or
at arm's length. Nothing in the published prior art measures tension. That gap is the video.

### 3.6 Calibration — "the first stretch is the taut reference"

Rest area A₀ = the hull area at the first sustained big stretch. Measured options and what each one
actually costs in screen time (`tools/scripts/analyze_finger_web.py`, hull_norm in palm² units):

| rest A₀ | J median | J max | frames over rest | hole time at J\*=1.15 | longest single hole run |
|---|---|---|---|---|---|
| **14.60** — run A's max (the first big stretch) | 0.88 | 2.15 | 36% | **10.6 s** | **2.93 s** |
| 12.0 — run A's p75 | 1.07 | 2.61 | 63% | 28.4 s | 21.97 s |
| 6.02 — run A's median | 2.13 | 5.20 | 73% | 35.5 s | 33.93 s |
| 3.67 — the take's p10 (fully relaxed) | 3.49 | 8.53 | 80% | — | — |

**Recommendation: A₀ = 14.60, J\* ≈ 1.15.** That is Dennis's sentence read literally — the first big
stretch is where the web is exactly taut — and it gives 10.6 s of hole time across the take with the
longest continuous run under 3 s. The holes come and go, they are *earned*, and the dough closes
again between them. The other rows leave the sheet permanently torn, which throws the beat away.

**Trap to avoid:** auto-calibrating from "the first sustained run" makes the whole look depend on the
first four seconds, so re-trimming the video silently changes it. **Calibrate once on the full take,
then write A₀ and the per-edge L₀ as literal constants into the render config**, so a re-trim or a
re-cut leaves the material alone.

## 4. The pipeline

The house pattern — extract, analyse, model, render, gate, publish — with measured costs where this
session measured them.

1. **Track.** `tools/scripts/extract_hands_mp.py` on `web/work/master.mp4`. **Done, 46 s**, output
   `web/work/hands.npz`, both hands on 89% of frames.
2. **Smooth and fill.** A **1-Euro filter** (Casiez, Roussel & Vogel 2012, `papers/casiez2012-one-euro-filter.pdf`)
   per landmark — a low-pass whose cutoff rises with speed, so it kills jitter when the hand is still
   and does not lag when it snaps. Start from the prior art's f_min = 0.06 Hz, β = 0.85 and tune
   against the measured 274 px/frame peak. Interpolate the single-frame dropout at 864 and the short
   one-hand stretches; hold a lost hand for 10 frames before dropping the sheet.
3. **Calibrate.** Compute A₀ and every edge's L₀ once (§3.6) and freeze them into the config.
4. **Simulate.** XPBD membrane, 8–16 substeps a frame, pinned at ten tips, strain-limited, with the
   seeded defect field and the hole SDF advancing at v ∝ √J. Output one record per frame: vertex
   positions, per-element J, the hole field. **Before rendering, print the model's checks** the way
   the pull-up and push-up models do: the chosen b against the b ≈ 1 stability knee; J's measured
   range against the strain limit (a sheet that clips at the limit for most of the take cannot
   breathe on screen); every pin's residual after the solve; the hole count and total hole area per
   second against the §3.6 table.
5. **Matte the hands.** So the fingers read as *holding* the sheet rather than lying under it, the
   hands must composite **on top**. **Verified this session** (`web/work/seg_classes.png`): MediaPipe's
   `selfie_multiclass_256x256.tflite` (already in `tools/models/`) class 2 = body-skin cleanly
   isolates hands and forearms and correctly cuts the gaps between spread fingers. Intersect it with
   a dilated ROI around the hand landmarks to drop the spurious blobs visible top-right at frame 1100.
   **Cost: 2.5 fps = 600 s for the full take** at full frame — cut it by running on a hand-ROI crop.
   The mask is 256×256 upsampled, so refine the edge with the guided filter the way
   `tools/scripts/extract_hand_matte.py` does, and judge it at 1:1 on the spread-finger frames.
6. **Render.** Through `studio.gl`, reusing the puppet video's machinery: the **jump-flood distance
   field** already in the library is exactly the right tool for the membrane's SDF — the sheet
   boundary, the hole boundaries, the rim band and the glow all fall out of one distance field.
   Bake once through `studio.cache.BakeCache` so look changes are composite-time, per the
   `render-iteration-cache` memory.
7. **Gate.** The house gates, no exceptions: `ffmpeg -v error -i out.mp4 -f null -`, the flicker
   check on anything composited, every burned-in line measured to its box, eyeball the first frame,
   the last frame and one card frame, one NVENC encode at a time, the 720 copy.
8. **Publish.** Caption per CLAUDE.md (one paragraph per line, LF, ≤5 hashtags, ≤2000 characters),
   the brand sting appended by `concat_copy`, the mirror script for `../dyeallpies-productions/`.

## 5. The look

Two layers, and they should be decided separately.

**The web itself** — the boundary lines, the mesh interior, the rims around the holes. The brand
foundation is in `tools/brand/BRAND.md`; the neon puppet video established violet-dominant with the
boots' hot red, and `studio.glow` does the glow in linear light. Carrying that palette over makes
this read as the same channel's work. But this take is a **bright daylit room** — cream sofa, white
wall, a red-and-yellow poster, a window blowing out on the right — not the pitch black the neon look
was built for. Research item 09 (colour salience on a light ground) and item 11 (CG realism in phone
footage) in `references/marionette/` already did that analysis for exactly this problem and should be
read before choosing; item 12's finding that bloom *collapses* Weber contrast on a light wall is the
specific trap here.

**Inside the membrane** — the filtered picture, which is the reference's whole idea. Two proposals:

- **Tie the filter to the strain.** As J rises the filter intensifies — the material "heats" as it is
  stretched. That makes the filter a readout of the physics instead of an unrelated cycling list, and
  it is a real improvement on the reference, where the filter changes on a timer.
- **The holes reveal the unfiltered frame.** Through a hole you see the real room, untouched. Dennis
  wrote "starts revealing holes"; the double reading is a gift — the holes *reveal*, and what they
  reveal is reality. It also makes the holes instantly legible on a phone at arm's length, which the
  reference's flat filters are not.

`code/aadishy-filters.js` (MIT) is a ready-made bank — halftone, dither, thermal jet, posterize,
ASCII, x-ray — to read rather than reinvent. Note the attribution requirement if any of it is ported.

## 6. Cut and length

Frames 214–1419 = **7.13–47.30 s = 40.2 s** is one continuous run once frame 864 is interpolated, and
it contains the complete arc. 40 s is long for a reel, but the pull-up format kept a full real-time
set and one of those hit 140k, so length is a judgement call, not a rule.

- **The flattest stretch is 14–20 s** (J holds between 3.4 and 4.6 with little shape). Trimming it is
  the cheapest 6 seconds.
- **Do not cut the release** (39–46 s, J → 0.23). It is the ending.
- **A mid-cut costs continuity**: the membrane's state jumps. If the cut is needed, either make it a
  deliberate beat (the dough re-forms) or re-run the sim per segment.

Recommendation to open with: the full 40.2 s continuous for the first look, then trim 14–20 s to land
near 33 s if it drags. Plus the ~2.5 s brand sting.

## 7. Reuse — what already exists

| what | where | note |
|---|---|---|
| hand tracking | `tools/scripts/extract_hands_mp.py` | used as-is, done |
| quad / web measurement | `tools/scripts/analyze_finger_quad.py`, `analyze_finger_web.py` | **written this session** |
| jump-flood distance field | `studio.gl` | the membrane SDF, rims, glow |
| bake-once cache | `studio.cache.BakeCache` | look changes at composite time |
| glow in linear light | `studio.glow` | from the neon puppet round |
| encode, gates, 720 copy, sting join | `studio.encode` | `concat_copy`, `sting_encode_args` |
| brand palette and sting | `tools/brand/BRAND.md`, `render_brand_sting.py` | `look=neon` exists |
| hand matte pattern | `tools/scripts/extract_hand_matte.py` | the guided-filter edge band |
| **exact catenary** | `tools/scripts/render_puppet.py:122` `catenary_points()` | **port it, do not rewrite it** (§3.5) |

That last row is the one to chase first: the marionette video already solved "a string that is
straight when taut and sags when slack", exactly, with both degenerate cases fixed the hard way.
Per the `port-referenced-look-from-code` memory, port it rather than approximating it.

## 8. Risks, ranked

1. **The sheet reads as a flat cartoon overlay, not as material in the room.** The biggest risk and
   the one the neon puppet round already fought. Mitigations that worked there: a dark edge by
   distance, contact shading where the fingers grip, grain matched to the plate, a little of the
   sheet's light spilling onto the hands. Read `references/marionette/11-cg-realism-in-phone-footage.md`
   before the first composite, not after.
2. **The matte fails between touching fingers.** This is the *exact* open problem left on the puppet
   video (HANDOFF "NEXT ROUND") — the wall showing through where fingers overlap. Here the background
   is a busy room, which is harder for a key but easier for a segmenter, and body-skin already cuts
   the finger gaps correctly (§4.5). Judge at 1:1 on the spread-finger frames, as the puppet round
   learned to.
3. **The holes are unreadable on a phone.** 10.6 s of hole time is plenty, but a hole a few dozen
   pixels across in a 1080-wide frame at arm's length is nothing. Set a minimum visible hole radius
   and check it against the burned-in-text measuring habit.
4. **The J signal is spiky.** Measured |dJ| p98 = 0.47 per frame but a max of 4.71 — those spikes are
   tracking glitches, not motion. Median-filter over 5 frames before anything thresholds on J,
   otherwise a single bad frame punches a hole.
5. **b has no measured value.** §3.3. Rank the choice against the b ≈ 1 knee and print the ranking.

## 9. Decisions for Dennis (nothing below is decided)

Decisions 1–7 are here; **§11.5 adds 8–12** (the scene) and **§12.5 adds 13–16** (the ending). Sixteen
in all, and §12.4 notes the one ordering constraint: the sting cannot be built before the look
(decision 2) and the scene (decision 8) are settled.

1. **The calibration.** §3.6 recommends A₀ = 14.60 / J\* = 1.15 — holes for 10.6 s of the take,
   longest run 2.9 s, earned and then healed. The alternative reading of his sentence leaves the
   sheet torn for most of the video. **Which does he mean?**
2. **The look inside the membrane.** Brand violet/red carried over from the neon puppet, or something
   dough-coloured and warm to match this bright room? (§5)
3. **Filter on a timer, like the reference, or driven by the strain?** (§5 recommends strain.)
4. **Do the holes show the unfiltered room?** (§5 recommends yes.)
5. **Length.** 40.2 s continuous, or trim the 14–20 s hold to land near 33 s? (§6)
6. **The format's name.** `web/` is provisional — "finger web", after her `#spiderman 🕸️` framing.
   If the dough side leads instead, the folder and skill should say so before anything is committed.
7. **Does the membrane ever cover his face?** It does, often — that is the reference's whole trick.
   Worth confirming he is happy with his face inside the filter.

## 10. What is already done in this session

- `web/originals/` extracted from the drive zip; `web/work/`, `web/out/`, `web/originals/` added to
  `.gitignore`.
- `web/work/master.mp4` — the upright 1080×1920 NVENC master, decode-gated.
- `web/work/hands.npz` — MediaPipe hands over the whole take (46 s, both hands on 89% of frames).
- `tools/scripts/analyze_finger_quad.py` — the reference's four-corner construction, measured on his
  take, which is what showed it does not fit (§1).
- `tools/scripts/analyze_finger_web.py` — the ten-tip membrane signals (tips, hull area, J, hand
  separation, finger spread, palm scale, depth) → `web/work/web_signals.npz`.
- `web/work/quad_check_a.png`, `quad_check_b.png` — the quad and skeletons on real frames.
- `web/work/ref1_sheet.png`, `ref2_crop_a.png`, `ref2_grid_t4.0.png`, `ref2_mesh_t6.0.png`,
  `ref2_full_t12.png`, `ref1_full_t8.png` — the reference decoded.
- `web/work/seg_classes.png` — the hand-matte route verified on three frames (§4.5).
- `web/work/ref2_content_band.png` — her scene's content band cropped to the measured 1170×1239, the
  frame §11.1's geometry was taken off.
- The scene measurements (§11): both reels' letterbox bands, her VS Code / title bar / feed split and
  its colours, recording 1's three-column layout, and the crop tests that ruled out her 4:3 window
  (65–70% of two-hand frames against a 90.6% ceiling).
- `references/finger-web/` — research item 01, 11 papers, 4 MIT-licensed source files, the numbers
  CSV, `downloads-01.md`, `DOWNLOADS.md`.

`web/work/` was built for this plan and is gitignored; the two analysis scripts are in
`tools/scripts/` on purpose, so they survive a work-folder clear.

---

## 11. The scene: make it read as the same *kind* of video (added 2026-09-18, Dennis)

Dennis wants the presentation frame to match hers, to maximise the viral read: a screen recording
with **the code showing**, his footage sitting in it **as if it were his webcam**, assembled from
screenshots taken during the Fable build session.

**The honesty rule he set, and it settles the whole question (Dennis, 2026-09-18):** *the caption is
honest that it is a scene; the video itself just maximises virality.* So — **no disclaimer on screen,
no "recreation" card, no hedging in the frame.** The video is cut for the strongest read it can get.
The caption says plainly that the desktop scene is assembled, while the code and the effect in it are
real. That split is what §11.4 is built around, and it is also why §11.4's "do not fake a result"
rule still binds: the caption can only claim the code is real if it *is*.

### 11.1 Her scene, measured

Both her reels are a **landscape/near-square screen recording letterboxed on black** into the 9:16
reel — not a full-bleed portrait video. Measured off the pixels (the reel player's own chrome
excluded):

**Recording 2** (`#spiderman`, the target) — content band **1170 x 1239**, aspect **0.944**:

| element | rows (of 1239) | share | measured colour |
|---|---|---|---|
| VS Code strip | 0-313 | **25.3%** | editor bg ~ #121113, menu bar ~ #171919, active tab ~ #D5D3D4 |
| Windows title bar (near-white) | 314-366 | **4.3%** (53 px) | ~ #F2EFF4 |
| the feed | 367-1238 | 70.4% | - |

The app window spans x 9-1160 of 1170 - essentially full width with a ~9 px inset. **The feed is
1152 x 872 = aspect 1.321, i.e. 4:3.** The colours are from a screen recording of a reel (compressed
twice), so treat them as approximate rather than as hex to match exactly.

Inside the VS Code strip, top to bottom: the menu bar (`Edit Selection View Go Run ...`, with the
`File` menu cropped off the left, then the back/forward arrows and the workspace name **`Filtros`**
in the command centre), the tab bar (`main.py` with the Python icon and an x), the breadcrumb
(`main.py > main`), then **four visible code lines with gutter numbers 9, 63, 64, 65**. The jump from
9 to 63 is **VS Code's sticky scroll** pinning `def main():` above the viewport - an authentic detail
worth reproducing.

**Recording 1** (PUZZLE-CAM) - content band **1170 x 547**, aspect **2.14**, a wide strip split into
three columns by measured column brightness: **VS Code (x 0 to ~330, dark) | the app with the webcam
(x ~360 to ~1000) | a bright white side panel (x ~1040 to 1170, her "TIRA" capture strip)**. This
matters for §11.3: **a side panel beside the feed is already inside her visual language**, not a
departure from it.

### 11.2 The collision: her window is 4:3, his footage is 9:16

Her feed is a landscape webcam. His take is a portrait phone recording in which **his hands go high
and wide** - the ten-tip bounding box is a median 764 px wide and reaches 1282 px tall in a 1080x1920
frame. Cropping him to her 4:3 window throws the effect away. Measured over the 1335 two-hand frames,
with a crop that tracks a 1 s-smoothed tip centroid, and again with the footage scaled to 91% inside
the window:

| crop | size | tracking | tracking + 10% pad |
|---|---|---|---|
| **4:3** (her window) | 1080x810 | 64.9% | 69.8% |
| 1:1 | 1080x1080 | 85.2% | 88.7% |
| **4:5** | 1080x1350 | **90.3%** | **90.6%** |
| 9:16 (native) | 1080x1920 | 90.6% | 90.6% |

**90.6% is the ceiling**: in 9.4% of two-hand frames MediaPipe predicts a fingertip *outside* the
1080x1920 frame, which no crop can recover. So a **4:5 crop is free** - it costs nothing against the
native frame - while her 4:3 loses a fingertip in about **30%** of the frames. Cropping to 4:3 is not
on the table without a re-shoot.

### 11.3 The way out, and it improves the video

Keep **her window shape** and put a **side panel** in it, which recording 1 already does:

> a **4:3 app window** (her exact proportions and title bar) containing a **4:5 tracking crop of his
> footage at 60% of the window width**, with the remaining **40% as a live telemetry panel**.

The arithmetic is exact: a 4:5 video inside a 4:3 window occupies 0.8 / 1.333 = **60%** of its width.
(A 9:16 video would take only 42%, leaving a panel bigger than the video; a 1:1 crop would give a
75/25 split but costs ~2% of the frames.)

The panel earns its 40% by carrying what this channel already prints - the stretch J against its
threshold, the per-string tension, the hole count and total hole area, the defect field. That turns
filler into the format's own dashboard DNA, and it is the honest version of the claim the video makes.

**On "as if it were my webcam":** with a portrait 4:5 feed the window reads as a **phone camera feed
in a desktop app**, which is what it actually is - we are processing a phone recording. That is still
a coding-reel scene. If the literal webcam read matters more than the hands, that is a re-shoot in
landscape, not a crop. Decision 11 in §11.5.

### 11.4 Assembling it from real screenshots

Dennis asked for the scene to be built from screenshots taken during the build session. Two routes,
and they combine:

- **Real screenshots - Dennis's to take.** Fable runs in a terminal and cannot capture Dennis's
  screen. So Fable's job is to say *exactly what should be on screen* at the moment of capture, and
  Dennis takes them (Win+Shift+S, or a short screen recording to pull frames from). Needed: the
  editor with the key source file open; the terminal with the model's printed checks; the file tree
  with the real filenames.
- **Rendered panel - Fable's to build.** The code strip can be rendered directly from our real source
  files with a syntax highlighter at exactly the target pixel size, which guarantees legibility and
  lets the visible lines be *chosen*. Pair it with one real screenshot of Dennis's VS Code chrome
  (menu bar, tab bar, breadcrumb) so the frame around it is genuinely his.

**The legibility rule, and it is the whole trick.** Her code strip is 314 px tall in a 1170-wide band
and shows **four lines**. At that size the font has to be large and the visible lines have to be the
ones that *say what the video does* - her frame shows `frame = render_portal(frame, p1, p2, p3, p4,
FILTROS[filtro_index])` and nothing else of substance. Ours must do the same: pick the single line
that names the effect (the membrane solve, or the hole nucleation test), put it in the viewport, and
measure it to its box like any other burned-in line (CLAUDE.md, memory `video-text-fit-check`). Three
to five lines, no more.

Details worth copying because they read as real: **sticky scroll** (a `def` pinned above a distant
line number, hence her 9 / 63 / 64 / 65), the workspace name in the command centre (hers `Filtros`),
and the tab showing one file, not twelve.

**Do not fake a result.** Assembling the desktop is staging and the caption will say so. The *code*
is a different matter: the lines on screen must be the lines that produced the render. Capture after
the build works, not before. If the frame shows a function, it exists in the repo and does that job -
otherwise the caption's "the code is real" becomes a lie, and that is the one claim the caption is
making.

### 11.5 Decisions this adds (numbering continues from §9)

8. **The scene at all** - full-bleed portrait like our previous reels (memory
   `reels-fullbleed-preference`: "talking video fills the frame, overlays on top, never boxed"), or
   her letterboxed screen-recording scene? **These conflict**, and her format is the one Dennis is
   asking to match. His call, explicitly, because it overrides a standing preference.
9. **The split** - the recommended 60% feed / 40% telemetry panel, or a bigger feed with a thinner
   panel?
10. **What goes in the panel** - the live stretch readout, or something closer to her recording 1's
    captured-frame strip?
11. **Webcam or phone feed** - accept that a portrait feed reads as a phone camera (free, keeps every
    frame), or re-shoot landscape for the literal webcam read (costs a re-shoot, and the hands-high
    poses would have to change)?
12. **Which source line is on screen**, and whether the terminal panel shows the model's checks.

### 11.6 The caption

Per Dennis's rule above, the caption carries the disclosure the video does not. It should say, in his
own plain voice and without apology, that **the desktop scene is put together** - the editor, the
window, the framing - and that **the effect, the code and the physics in it are real and were built
for this**. Both halves matter: the first is the honesty, the second is the thing worth bragging
about, and it is the reason the video is interesting at all.

House rules still apply (CLAUDE.md): one paragraph per line, LF endings, at most 5 hashtags on one
line, at most 2000 characters, counted with Python `len()` and checked in UTF-16 too. Credit the
model in the video if one is named, as the puppet captions do.

---

## 12. The ending: a DyeAllPies sting in this video's own theme (added 2026-09-18, Dennis)

Dennis wants a specific ending like the hands reel's, **adapted to this video's theme** rather than
reused as-is. The precedent and the rule are already set: on 2026-09-12 the puppet sting was rebuilt
so that "the video's thread extends into the logo" — the wordmark and the falling strings in the
doll's violet, the tick in the boots' red, the glow in linear light through `studio.glow`. The asset
is `tools/scripts/render_brand_sting.py`, the rules are `tools/brand/BRAND.md`, and the palette and
fonts come from `studio.brand` so the sting and the brand document cannot drift apart.

### 12.1 The existing sting's beats, which we keep

From the script's own header, at 30 fps:

| frames | beat |
|---|---|
| 0–8 | the five strings **fall** under real gravity at the puppet's scale — "the drop the reel is about" |
| 8–12 | they **snap taut** and bounce |
| 10–22 | the wordmark **lights letter by letter** as they land |
| 22–30 | PRODUCTIONS tracks in, the tick draws |
| then | the URL fades in over 6 frames and holds (`hold=1.5` s) |

Total 2.5 s, 1080×1920, silent, appended by `concat_copy` with no re-encode of the shot.

**Keep this skeleton exactly.** It is what makes it the same channel's sting rather than a new one.
Only the *thing that falls* and *how the wordmark arrives* change.

### 12.2 The adaptation, and the footage already sets it up

The take ends the right way on its own. Against the recommended rest (A₀ = 14.60):

| time | J | what happens |
|---|---|---|
| 38 s | 1.30 | the last over-stretch — holes open |
| 39–46 s | 0.67 → **0.06** | the full release: the membrane goes deeply slack, the strings sag, the holes close |
| 47–48 s | 0.38 | a small last pose |
| **48.43 s** | — | **the last hand leaves the frame** (then 1.5 s of empty room to 49.90 s) |

So the video's final event is not a tear — it is the membrane **being let go**. That is the hook:

> the hands reel's sting was the **strings dropping** and lighting the wordmark.
> This one is the **membrane dropping**, stretching across the wordmark, and **tearing open to reveal it**.

Beat for beat, against the table above:

- **0–8 — the sheet falls.** The ten anchors are gone, so the released membrane falls under the same
  real gravity the puppet's strings used. Same beat, a sheet instead of five threads.
- **8–12 — it catches and snaps taut.** It lands across the wordmark's letterforms and goes tight
  over them, replacing the strings' snap-and-bounce with the sheet's.
- **10–22 — the holes open, and the wordmark is what shows through them.** Stretched over the
  letters, the local areal stretch passes the threshold, defects trip, and DYEALLPIES is revealed
  through the holes — one opening per letter, in the letter-by-letter order the existing sting
  already lights them in. **The video's own mechanism produces the logo**, which is exactly what
  "the video's thread extends into the logo" asked for.
- **22–30 — PRODUCTIONS tracks in and the tick draws.** Draw the tick as a **tear** rather than a
  stroke: a crack propagating with the radiating-crack perimeter from Petit et al. 2015 (research
  item 01 §5c). Same shape, this video's physics.
- **then — the URL fades in and holds**, unchanged.

Each hole should carry the **raised rim** of §3.4c. At sting scale it is the one detail that keeps
the letters reading as revealed-through-dough instead of as a stencil.

### 12.3 The transition into it

The hands reel used a pull-in with a zoom blur and a dip to black over the last 18 frames
(`outro=18`, research item 13 `references/marionette/13-outro-transition.md` — the CapCut "Pull In"
/ zoom-blur move; no files were saved for it, commercial guides only).

This video's own version is **through a hole**: the last hole opens toward camera and swallows the
frame, and the sting is on the other side of it. It is the same push-in energy, and it is this
effect's own vocabulary rather than a borrowed transition. Keep `outro=N` as the knob and keep the
dip to black — the sting's `ground` must not step away from whatever the shot ends on (the reason
`ground=#000000` exists at all).

### 12.4 Colour, and what has to be decided first

The sting takes **the video's palette**, whatever §9 decision 2 settles. `render_brand_sting.py`
already exposes `look=neon accent=… core=… tick=… gain=… wall=…` and computes the glow in linear
light through `studio.glow`, so a palette change is a parameter change, not a rewrite. The orange v1
stays the script's default; this video gets its own accent the way the puppet did.

**So: the sting cannot be built before the look is chosen.** Sequence it after §9 decisions 2 and 8,
not before.

### 12.5 Decisions this adds

13. **The reveal** — the wordmark revealed *through* the holes (recommended: it is the video's own
    mechanism), or lit letter by letter as the sheet lands on it (closer to the puppet sting)?
14. **The tick as a tear**, or the existing drawn stroke?
15. **The transition** — through a hole, or the puppet reel's pull-in with zoom blur?
16. **Whether the sting's sheet carries the shot's last slack**, i.e. the membrane falls already
    sagging and deeply relaxed (J ≈ 0.06 at 46 s), which would carry the shot's final state straight
    into the logo.
