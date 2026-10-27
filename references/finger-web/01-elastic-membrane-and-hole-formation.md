# Item 01 — the finger web: an elastic dough membrane between ten fingertips, and how holes open in it

Context: Dennis brought a 50 s phone take (`web/originals/IMG_6268.MOV`, 2026-09-18) and two
screen recordings of another creator's reels (`mishu.ksv`). Her effect draws a quadrilateral
between the thumb and index fingertips of both hands and replaces the picture inside it with a
filtered version. Ours is to be the same *idea* with two departures Dennis named:

1. **elasticity** — the lines between the fingers get tighter or looser with how far he pushes
   them, with a calibration where the first stretch is the taut reference and anything less than
   that goes slack;
2. **dough, not a rigid frame** — the surface behaves like a sheet of dough, and when it is
   stretched past its limit it starts **opening holes in the middle**.

This item collects (a) what the reference actually does, read off the code visible in her screen
recording; (b) the open-source prior art and precisely where it stops; (c) the physics that makes
an elastic sheet thin, tear and heal, with the numbers. It is written for Fable to weigh — several
sections end with a "what this buys us / what it costs" note rather than a decision.

Every number below is attributed to a file in `papers/`, `code/`, `abstracts/` or to
`data/01-membrane-numbers.csv`. **NOT FOUND** marks something the brief wanted that this pass could
not source. `downloads-01.md` lists every URL and licence fetched.

---

## 1. What the reference reel actually does (decoded from the screen recordings)

Both recordings are of Instagram reels by **`mishu.ksv`**, screen-captured on 2026-09-18 at 1170×2532,
60 fps. Both are *coding* reels: the phone shows her editor and her running program side by side, so
the implementation is legible in the frame.

**Recording 2** (`ScreenRecording_09-18-2026 15-15-54_1.mp4`, 19.2 s, caption
`#spiderman #python #software 🕷️🕸️`, 33.7K likes) is the one Dennis is pointing at. Visible in
`main.py`:

```
 63     filtro_index = (filtro_index + 1) % len(FILTROS)
 65     frame = render_portal(frame, p1, p2, p3, p4, FILTROS[filtro_index...
```

So: four points `p1..p4` from the hands, one call that renders a "portal", and a filter index that
cycles through a list. Sampling the reel at 2 fps (`web/work/ref2_crop_a.png`) shows four filters in
19 s — a crimson halftone, a plain white perspective **grid**, an orange/magenta two-tone posterize,
and a black-and-white halftone — plus a jet/thermal colormap at t≈12 s (`web/work/ref2_full_t12.png`).
The grid frame (`web/work/ref2_grid_t4.0.png`) is the clearest read of the geometry: a regular
grid drawn in the quad's own parameter space and warped to the four fingertips, so the cells are
perspective-foreshortened. Her hashtag is the giveaway for the intent — `#spiderman 🕸️` — the quad
edges read as web.

Three things about her version matter for ours:

- **The corners are the thumb tip and index tip of each hand.** Her hands are held in the
  "director's frame" pose, so those four points are far apart and make a usable rectangle.
- **The quad is a hard polygon.** Its edges are straight lines between fingertips; nothing about it
  responds to how far apart her hands are, beyond getting bigger.
- **The content inside is warped, not just masked.** At `web/work/ref2_mesh_t6.0.png` the face inside
  the portal is larger than the face outside it, so the region is rectified, filtered and mapped back
  through the quad's homography.

**Recording 1** (`ScreenRecording_09-18-2026 15-15-20_1.mp4`, 21.2 s, caption "Making coding fun 🧑‍💻",
59.9K likes) is a different reel — a browser app at `127.0.0.1:5500` titled **PUZZLE·CAM — HAND-FRAME
CAPTURE**. Visible in `app.js`: `applyBWInsideBox(lastSeenFrame.box)`, `drawLiveFrameOverlay(...)`,
`drawCountdownOverlay(puzzle.boardBox)`, `isPinching(lm)`, `handleDragForHand(label, pinching, indexPx)`,
and an `appState` machine with `"countdown"` and `"puzzle"` states. Its on-screen legend reads
`pinch ambas manos → congelar y capturar (1s)` / `pinch una mano sobre pieza → arrastrar` /
`puño cerrado → guardar y reset`. It is the same hand-frame idea driving a photo-strip puzzle
("TIRA"), and it is **not** what Dennis is asking for — but its gesture vocabulary (pinch both hands
to commit, one hand to drag, fist to reset) is a proven, readable way to let the hands trigger state,
and is worth borrowing if ours ever needs a trigger.

**What this buys us:** the reference is a 2D image-space effect with no simulation in it at all. Our
departure is not cosmetic — it is the whole difference between the two videos.

## 2. The open-source prior art, and exactly where it stops

**`AadishY/Hand-Gesture-Filter`** (GitHub, MIT per `package.json` and the README badge — note there
is **no `LICENSE` file in the repo**, a caveat recorded in `downloads-01.md`) is the closest published
implementation of the reference effect. Vanilla JS + MediaPipe Hands + Canvas2D/WebGL. Saved:
`code/aadishy-geometry.js`, `code/aadishy-tracking.js`, `code/aadishy-filters.js`,
`code/aadishy-hand-gesture-filter-README.md`.

Its quad is the same four landmarks (index and thumb tips of both hands). Its README advertises
"elastic membrane bending". **That phrase is cosmetic.** `code/aadishy-geometry.js`,
`buildPortalPath()`:

```js
const bendFactor = 0.07;
const cpTop = { x: (x1+x3)/2 + (center.x - (x1+x3)/2) * bendFactor, ... };
const cpRight = { x: (x3+x4)/2 + ((x3+x4)/2 - center.x) * (bendFactor * 0.4), ... };
```

The four edges are quadratic Béziers whose control points are pulled toward (top/bottom) or away
from (left/right) the centre by a **fixed 7%** — the same bow whether the hands are together or at
arm's length. Nothing measures tension. (The function also has a real typo at the first
`quadraticCurveTo(cpTop.x, cpTop.y, x3, x3.y || y3)` — `x3` is a number, so `x3.y` is `undefined`
and it falls through to `y3`; the result is right by accident.)

Useful numbers it *does* carry, all from the README (`code/aadishy-hand-gesture-filter-README.md`):

| quantity | value | our use |
|---|---|---|
| 1-Euro filter min cutoff | 0.06 Hz | starting point for landmark smoothing |
| 1-Euro filter β | 0.85 | speed coefficient |
| jitter deadband | < 1 px | matches our measured 0.7 px floor (§7) |
| temporal grace | 10 frames | how long to hold a lost hand |
| gesture debounce | 350 ms | filter-change trigger |
| foreshortening border gain | 1.4× | thickness when the plane tilts |
| yaw / pitch from palm scale | ±60° / ±45° | depth from relative palm size |

Its filter list — Crimson Noir, Liquid Chrome, Crystal Ice Glass, Matrix Void ASCII, Vintage Manga,
Medical X-Ray, HD ASCII Matrix, Retro Dither, **Thermal JET**, **Rosa Halftone** — is an almost exact
match for the filters visible in `mishu.ksv`'s reel, which suggests a common lineage. Either way
`code/aadishy-filters.js` is a ready-made, MIT-licensed bank of image filters to read rather than
reinvent.

**What this buys us:** a working reference for the tracking→quad→filter plumbing and its constants,
and a clear statement of the ceiling: *nobody in the prior art simulates the membrane.* The elasticity
and the holes are ours to build.

## 3. Simulating the sheet: Position Based Dynamics and its descendants

The sheet must be pinned at ten moving anchors, solve fast, and never explode when a hand snaps
(we measured tip speeds up to 274 px/frame, §7). That is precisely the problem PBD was designed for.

**Müller, Heidelberger, Hennix & Ratcliff 2007, "Position Based Dynamics"**
(`papers/muller2007-position-based-dynamics.pdf`). Positions are projected directly onto constraints
instead of integrating forces, so attachment constraints are exact and unconditionally stable —
a pinned vertex is simply moved to the fingertip, with no spring stiffness to tune or blow up.

**Macklin, Müller & Chentanez 2016, "XPBD"** (`papers/macklin2016-xpbd.pdf`). Plain PBD's stiffness
depends on the iteration count and the time step, which means a look tuned at one solver setting
changes when the settings change. XPBD adds a compliance term (α̃ = α/Δt²) that makes stiffness a
real material parameter, independent of iterations. **For this format that is not optional:** Dennis
will ask for "stiffer" or "loppier" and the knob has to mean the same thing after a re-render.

**Macklin, Storey, Lu, Terdiman, Chentanez, Jeschke & Müller 2019, "Small Steps in Physics
Simulation"** (`papers/macklin2019-small-steps-in-physics-simulation.pdf`): spending the budget on
more substeps rather than more solver iterations per step converges better for the same cost. The
practical reading for us: at 30 fps source, substep the membrane (e.g. 8–16 substeps a frame) rather
than iterating a single step.

**Wang, O'Brien & Ramamoorthi 2010, "Multi-Resolution Isotropic Strain Limiting"**
(`papers/wang2010-multiresolution-isotropic-strain-limiting.pdf`). Strain limiting clamps the
singular values of each element's deformation gradient, coordinate-invariantly. This is the direct
mechanism for "the web only stretches so far": it gives a **hard limit** that is separate from the
elastic response, which is exactly the shape of the thing Dennis described ("stretched above its
limit"). The SVD of the deformation gradient F also hands us, for free, the two principal stretches
λ₁, λ₂ per element — and therefore the areal stretch **J = λ₁λ₂**, which is the quantity everything
in §4 and §5 keys off.

## 4. Why dough, specifically: the J-curve and thinning

Dough is not an arbitrary choice of material — it is the one whose failure mode *is* "holes appear
when you over-stretch it", and it has a measurement literature because bread depends on it.

**Dobraszczyk, in *Baking, Extrusion and Frying* ch. 8** (`papers/dobraszczyk-baking-extrusion-frying-ch8.pdf`,
`.txt` lines 370–440) is the compact statement:

- Dough in large-deformation **biaxial** extension gives a **J-shaped stress–Hencky-strain curve**
  (Fig. 8.11): stiffness rises rapidly with inflation. The fit is a power law, σ = K·ε^b, with **b the
  strain hardening index**.
- "Strain hardening allows the expanding gas cell walls to **resist failure by locally increasing
  resistance to extension as the bubble walls become thinner**" — i.e. the material fights back
  exactly where it is thinnest. This is the self-stabilising term that stops a real dough sheet from
  tearing the instant it is pulled.
- "Once strain hardening drops below a value of **around 1**, bubble wall stability decreases rapidly"
  (Fig. 8.13, Hencky failure strain vs strain hardening). **b ≈ 1 is the published stability knee.**

The design reading: model the sheet as **incompressible in volume**, so areal stretch J implies
thickness h = h₀/J. Feed J through a hardening law with exponent b; at b > 1 the sheet resists and
survives large J, at b < 1 it runs away and fails. Dennis gets one physically-meaningful dial —
**b** — that moves the whole character of the material from "cling film" to "good bread dough".

Biaxial extension is also the right *kind* of deformation for our case: a sheet pulled outward by
ten anchors in its own plane is biaxial, not uniaxial, which is why this literature transfers and
the (much larger) uniaxial-tensile-test literature does not.

**NOT FOUND this pass:** numerical values of b and of the Hencky failure strain for named flours.
The chapter presents Figs. 8.11–8.13 as plots without tabulated values, and the primary sources
(Dobraszczyk & Roberts 1994, *J. Cereal Sci.*, "Strain Hardening and Dough Gas Cell-wall Failure in
Biaxial Extension"; Dobraszczyk & Morgenstern 2003) are paywalled at Elsevier with no open mirror
found. Only the **b ≈ 1 stability knee** is quotable as a number. Fable should treat b as a look
knob ranked against that knee, not as a measured constant.

## 5. How a hole opens: nucleation, then propagation, then the rim

Three separate physical stages, three separate sources, and they map cleanly onto three stages of
the effect.

**(a) Nucleation is a strength threshold at a defect, not a global event.** Gent & Lindley's 1959
poker-chip experiments are the origin of the field; the classical reading was a critical hydrostatic
stress of ≈ 5E/6. The modern account, in the open-access
`papers/lopezpamies2024-cavitation-jmps.pdf` (López-Pamies, *JMPS* 2024, reviewing Lefèvre et al. 2015
and Kumar & López-Pamies 2021), is sharper and more useful:

> "the nucleation of cracks in the poker-chip experiments of Gent and Lindley (1959) on natural rubber
> is governed by the strength — in particular, the hydrostatic strength — of the rubber, while the
> propagation of the nucleated cracks is governed by the Griffith competition between the bulk elastic
> energy of the rubber and its intrinsic fracture energy"

with the numbers, for that vulcanizate: uniaxial strength 11.3 ± 3.7 MPa, biaxial 14.8 ± 6.2 MPa,
**hydrostatic strength 2.9 ± 0.5 MPa — about four times smaller**. Cavitation is "first and foremost a
fracture process, and not a purely elastic one as conjectured for decades."

Design consequences, and they are strong ones:
- Holes nucleate **at pre-existing defects**, so seed a fixed random defect field over the sheet with
  varying local strengths. The holes then appear in a **repeatable, staggered order** — one, then
  another, then a third — instead of the whole middle going porous in one frame. Fixed seed = a
  deterministic render, which this repo needs for its bake-once cache.
- A membrane pulled biaxially fails at a much lower load in the **hydrostatic/dilatational** mode than
  in tension. In our terms: it is the *areal* stretch J, not the stretch along any one direction, that
  should trip the threshold. That agrees with §3's J = λ₁λ₂.

**(b) Propagation is an energy competition, so holes stop — and can close.** The Griffith half of the
statement above means a hole grows only while the elastic energy it releases exceeds the fracture
energy it costs. Relax the hands and the driving energy falls; growth halts. This is what licenses
the "dough heals when he brings his hands back" behaviour as physics rather than as a cheat —
though true healing is a plasticity/viscoelastic-recovery argument, not a Griffith one, so the honest
framing on screen is "holes stop growing and slowly close", not "the tear un-tears".

**(c) Once open, a hole opens at a constant speed set by thickness, and grows a rim.** For a thin film
this is the **Taylor–Culick** result (Taylor 1959, Culick 1960), stated in
`papers/villermaux2022-taylor-culick-retractions-surroundings.txt` (Sanjay, Lohse et al., arXiv
2202.13400) eq. 1.1 and independently in `papers/petit2015-holes-and-cracks-in-rigid-foam-films.txt`
(Petit et al., arXiv 1503.06197):

> v_TC = √( 2γ / (ρ h₀) )

constant after an initial transient, with γ the surface tension, ρ the density and **h₀ the film
thickness**. The dependence is the point: **the thinner the sheet, the faster the hole opens** — so
holes that nucleate where the membrane is most stretched (thinnest) also *grow fastest*, with no extra
art direction needed. Also from the same sources:

- "the liquid collects in a **thicker rim** at the retracting edge of the film" — a hole in a real
  film is bordered by a raised, rolled edge, not a clean cut. That rim is the single detail that will
  sell the material as dough rather than as a cut-out mask.
- A rim only grows if the film's radial extent exceeds the **Stokes length** μ/(ρ v_TC); below that,
  no rim. So rim thickness has a physical scale rather than an arbitrary one.
- Petit et al. 2015 studied films with high **surface elasticity** (i.e. closer to dough than water
  is) and report "**crack-like patterns**" radiating during the hole opening, not a smooth circular
  retraction. For an elastic membrane, the honest look is a hole with **radiating cracks at its
  perimeter**, which is also far more legible on a phone screen than a smooth circle.

**What this buys us:** a three-stage recipe — seeded defects trip on J, the hole opens at a rate set
by local thinness, the perimeter carries a raised rim and radial cracks — every stage of which has a
citation and a knob.

## 6. Slack lines: the catenary, for "looser if less stretched"

When the anchors come closer than the line's rest length, the line goes slack and must *sag*, or it
will read as a rubber band that has simply gone limp. The classical relation between the extra length
and the sag, in the parabolic approximation (accurate to ~1% for shallow sags; the refinement is
J. S. Frame, "An approximation for the dip of a catenary", *Pi Mu Epsilon Journal* 1(2), April 1950,
pp. 44–46, via `papers/johndcook-catenary-sag-approximation.txt`):

> extra length ≈ 8·sag² / (3·span)  ⟹  **sag ≈ √( 3·span·ΔL / 8 )**

with ΔL = L₀ − span the slack. That is a closed form, evaluated per line per frame at no cost, and it
has the right feel: sag grows as the **square root** of the slack, so a line that goes 5% slack drops
a lot at first and then flattens out — which is why a slightly long net or washing line droops so
much more than people expect (the article's own comment thread makes exactly this observation about
pickleball nets: ~1/3″ of extra length gives ~4″ of sag).

**What this buys us:** the "looser" half of Dennis's request is one square root, not a simulation.

**In-repo already:** `tools/scripts/render_puppet.py:122`, `catenary_points(A, B, L)`, solves the
**exact** catenary for the marionette's strings (`brentq` on 2a·sinh(h/2a) = √(L² − v²)), with both
degenerate cases already fixed in place. The parabolic form above is therefore the *check* on a port,
not the implementation to write.

## 7. Tracking: how clean is the source, and how much smoothing does it need

Measured on Dennis's own take, upright master 1080×1920 @ 30 fps, MediaPipe Hand Landmarker in VIDEO
mode (`tools/scripts/extract_hands_mp.py`, `tools/scripts/analyze_finger_web.py`; numbers in
`data/01-membrane-numbers.csv`):

| quantity | value |
|---|---|
| frames with both hands | 1335 / 1497 = **89%** |
| fingertip jitter floor (std over the quietest 15-frame hold) | **0.5–1.4 px**, mean 0.7 px |
| fingertip speed, median / p95 / max | 4.2 / 42 / **274 px per frame** |
| fingertip acceleration, median / p99 | 2.7 / 92.7 px per frame² |
| palm width (index MCP → pinky MCP) | 78–160 px, median 129 px |

The jitter floor (0.7 px) sits well below the median real motion (4.2 px/frame), which is a
comfortable margin — this take is clean. It also lands **exactly on the prior art's < 1 px deadband**
(§2), an independent corroboration of that constant.

**Casiez, Roussel & Vogel 2012, "1 € Filter"** (CHI '12,
`papers/casiez2012-one-euro-filter.pdf`) is the right smoother: a first-order low-pass whose cutoff
rises with speed, so it kills jitter when the hand is still and does not lag when the hand snaps.
Given a 0.7 px floor and 274 px/frame peaks, that speed-adaptive behaviour is not a nicety. Start from
the prior art's f_min = 0.06 Hz, β = 0.85 and tune against the 274 px/frame snap.

## 8. What was not found this pass

- **Numerical b and Hencky failure strain for dough** (§4) — paywalled, see the NOT FOUND note there.
- **Any prior implementation that drives the membrane from measured hand tension.** Searched
  MediaPipe + cloth/elastic/PBD across GitHub topics and the graphics literature; the hand-tracking
  demos found are sphere-dragging, particle fields and the fixed-bow quad of §2. If one exists it was
  not surfaced by these queries.
- **The reference reel's own source.** `mishu.ksv`'s `main.py` is only partially legible in the screen
  recording (two lines); no repo was found for it.
- **A licence file for `AadishY/Hand-Gesture-Filter`** — MIT is declared in `package.json` and the
  README badge, but `LICENSE` 404s.
