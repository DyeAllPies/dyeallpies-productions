# Item 02 — the twisted ribbon's regimes, and rods with contact

Context: the violet ribbon (item 01, round two/three) is currently drawn from a kinematic model —
each long edge a straight segment when taut, an exact catenary when slack, 12 px wide. When a hand
flips, the projected ribbon becomes a bow-tie and the near edge is drawn over the far one by a
z-order hack, not a physical contact. The next round gives the edges a body: each long edge a
chain of particles with distance constraints, gravity, endpoints pinned to the fingertips, and a
rod–rod contact constraint of radius one thickness, solved with XPBD substeps. Where the two edges
come within a thickness of each other they meet at a point and the ribbon's width goes to zero
there — the fold. This item asks two questions of the literature: (a) when a *real* twisted ribbon
brings its own edges into contact — so the render's fold threshold has a physical answer rather
than an art-directed one — and (b) how the graphics literature solves rods-with-contact fast enough
for XPBD, with the actual constants people ship.

Every number below is attributed to a file in `papers/` or to
`data/02-twisted-ribbon-and-rod-contact.csv`. **NOT FOUND** marks something the brief wanted that
this pass could not source. `downloads-02.md` lists every URL and licence fetched, including one
correction to the brief: the arXiv ID it gave for Chopin & Kudrolli 2013 (1306.1583) is wrong —
it resolves to an unrelated GAMA-survey astrophysics paper. The correct PDF was found on Arshad
Kudrolli's own site instead.

---

## 1. The controlling experiment: Chopin & Kudrolli 2013, "Helicoids, Wrinkles, and Loops in Twisted Ribbons"

(`papers/chopin2013-helicoids-wrinkles-loops.pdf`, *Phys. Rev. Lett.* 111, 174302.) This is the
paper the brief points at, and it earns it: a ribbon of length L, width W, thickness h is held at
tension F and twisted by angle φ about its long axis. Two dimensionless control parameters
organize everything else:

> **θ = φ·W/L** (normalized twist) and **T = F/(E·h·W)** (normalized tension)

Measuring the critical θ at which each shape appears, for a range of T, produces a **phase diagram
in the (T, θ) plane** with three regimes meeting at a single triple point (T\*, θ\*):

- **Below T\*: longitudinal buckling.** The ribbon first buckles along its own length (a
  compressive stress builds symmetrically about the centerline as twist rises). In the
  vanishing-thickness limit the threshold is exactly **θ₀ = √(24·T)** — a closed form, no fit
  parameters. Real ribbons buckle a bit later, offset linearly by their finite thickness:
  θ_L − θ₀ ≈ **9.3·(h/W)**. Past threshold the buckle wavelength shrinks as twist grows,
  λ_L ≈ **3.8·√(hW/θ₀)** (eq. 6, numerical prefactor from their Fig. 2f) — thinner or narrower
  ribbons wrinkle at a finer pitch. Twisted further, the buckle **localizes into a self-creased
  helicoid**: the curvature focuses onto the sides of a triangle repeated down the ribbon,
  origami-like, and the crease gets sharper as tension drops.
- **Above T\*: transverse buckling.** Above the triple point the first instability is a buckle
  *across* the ribbon's width instead, at a threshold **θ_T = 4.4·√(h/W)** that (surprisingly)
  does not depend on T or L in their "ribbon regime" (L/W large) — a single geometric ratio sets
  it.
- **The triple point** falls out of setting θ_L(T\*) = θ_T(T\*) in the thin-ribbon limit:
  **T\* ≈ 0.8·(h/W)**. For their reference ribbon (L=45 cm, W=25.4 mm, h=127 μm) that predicts
  T\* ≈ 4×10⁻³, matching the measured phase diagram.
- **Loops with self-contact — the number we actually need.** Twisted further still, in *both*
  regimes, the ribbon snaps into a **loop where the two edges touch themselves**, a discontinuous,
  hysteretic transition. The two paths to it are qualitatively different, which matters for the
  round: **above T\*** (higher tension), the loop follows the transverse buckle directly, with "no
  significant hysteresis" — twist a little more than θ_T and it self-contacts. **Below T\*** (lower
  tension, longitudinal/creased regime) the behaviour is *anomalous compared with a twisted rod*:
  the critical loop angle **decreases linearly as T rises** — i.e. a slacker-but-more-twisted
  ribbon self-contacts *more* easily than a tenser one, because the creases formed by the
  longitudinal buckling self-rigidify the ribbon and change the energetics. Once looped, decreasing
  twist again does not immediately undo the contact (hysteresis) — the ribbon stays self-touching
  until twist drops well back below the forming threshold.

Ribbons in the experiment are biaxially-oriented PET (Mylar), **E ≈ 3.4 GPa**, in the geometric
regime **L > 10W > 500h** that defines a "ribbon" as opposed to a rod (h ~ W) or a plate (L ~ W).
Above θ ≈ 0.5 plastic deformation appears at the edges and the elastic theory in the paper stops
applying cleanly.

## 2. The general framework: Chopin, Démery & Davidovitch 2015, "Roadmap to the Morphological Instabilities of a Stretched Twisted Ribbon"

(`papers/chopin2015-roadmap-morphological-instabilities.pdf`, *J. Elasticity* 119, 137–189,
arXiv:1403.0267 — this arXiv ID **is** correct, unlike the brief's ID for the 2013 paper.) This is
the theory paper behind §1's numbers: a covariant Föppl–von Kármán treatment of the helicoidal
state that reproduces both θ₀ = √(24T) and the transverse threshold, and explains *why* the three
curves meet at one triple point rather than crossing pairwise (§1.2 (C) of the paper) — it is not
a coincidence but the intersection of exactly two curves, θ_tr(T) and θ_lon = √(24T), in the
(T, θ) plane. Its most useful addition for us is a **general scaling for the transverse
threshold, θ_tr ∼ t/√T**, valid on both sides of the triple point with different numerical
prefactors (consistent with §1's θ_T ∝ √(h/W) at leading order once T-dependence is folded in
near T\*). It also draws a length-dependence line we should note: a **short** ribbon (our case —
finger to finger, L/W not large) buckles into a single localized fold; a **long** ribbon
(L⁻² ≪ t) instead wrinkles into a spread-out transverse pattern. This is reassuring — the round's
ribbon, short and stubby between two fingertips, sits in the single-fold regime the render already
wants, not the multi-wrinkle regime that would need a much finer discretization to show.

## 3. Deep past threshold: Chopin & Kudrolli 2016, "Disclinations, e-cones, and their interactions in extensible sheets"

(`papers/chopin2016-disclinations-econes.pdf`, *Soft Matter* 12, 4457, arXiv:1601.00575 — also
correct.) This is the brief's speculative "check" reference, and it does exist and is on-topic: far
past the buckling threshold, the wrinkled zone's defects (negative disclinations, "e-cones") settle
into a **triangular lattice** of vertices joined by stretched ridges, which self-rigidifies the
sheet — the same self-rigidity effect that §1 uses to explain the anomalous below-T\* loop
transition. It also reports a **regime crossover in the wrinkle wavelength**: near threshold the
wavelength is set by the ribbon's geometry (§1's λ_L formula); far past threshold it crosses over
to being set by the ratio of tension to elastic modulus × cross-section instead. This is a second
confirmation, independent of §1–2, that "how far past its own threshold" a ribbon is twisted
changes its *qualitative* behaviour, not just a number — which is the same texture the round wants
(a ribbon that starts smooth, then buckles, then folds on itself, are three different looks, not
one look scaled up).

**NOT FOUND, full text:** **A. E. Green 1937** ("The elastic stability of a thin twisted
strip. II", *Proc. R. Soc. A* 161, 197) is the seminal 1937 analysis all three papers above cite
as their starting point — Green showed a tensioned ribbon is twist-unstable because twist alone
produces a nonuniform compressive stress across the width, and derived the vanishing-thickness
helicoid-buckling threshold that Chopin & Kudrolli's θ₀ = √(24T) reproduces and extends to finite
thickness. Paywalled at the Royal Society (HTTP 403), no open mirror found; see
`abstracts/green1937-elastic-stability-twisted-strip-ii.txt` for the secondhand description.
**E. M. Mockensturm 2001** ("The Elastic Stability of Twisted Plates", *J. Appl. Mech.* 68(4),
561) is one of the numerical-simulation sources Chopin & Kudrolli 2013 cites for finite-tension
transverse buckling; paywalled at ASME (HTTP 403), no open mirror found — see
`abstracts/mockensturm2001-elastic-stability-twisted-plates.txt`.

## 4. Regime table

| regime | condition | edge behaviour | source |
|---|---|---|---|
| flat helicoid | θ < θ₀ = √(24T) | edges straight, ribbon a minimal helicoid, no self-contact | Chopin & Kudrolli 2013 |
| longitudinal buckle | T < T\*, θ₀ < θ < θ_loop(T) | edges develop a symmetric in-plane wave about the centerline | Chopin & Kudrolli 2013 eq. 1–6 |
| creased helicoid | T < T\*, twist well past θ₀ | curvature focuses onto a repeating triangular crease pattern; the ribbon self-rigidifies | Chopin & Kudrolli 2013; 2016 |
| **loop / self-contact, low tension** | T < T\*, θ ≥ θ_loop(T), **θ_loop falls as T rises** | ribbon snaps discontinuously into a loop where the two edges touch; hysteretic on untwisting | Chopin & Kudrolli 2013 Fig. 4 |
| transverse buckle | T > T\*, θ₀ < θ < θ_T = 4.4√(h/W) | edges develop a wave across the width instead of along the length | Chopin & Kudrolli 2013 Fig. 3 |
| **loop / self-contact, high tension** | T > T\*, θ ≥ θ_T (roughly), **not hysteretic** | self-contact follows the transverse buckle almost immediately on further twist | Chopin & Kudrolli 2013 Fig. 4 |

## 5. Rods with contact, for real-time simulation

The membrane literature in item 01 (Müller 2007 PBD, Macklin 2016 XPBD, Macklin 2019 substeps) is
the base this round reuses; the additions here are specific to giving a **1D edge** — not a 2D
sheet — bending and twisting stiffness, and letting two such edges collide with each other.

**Bergou, Wardetzky, Robinson, Audoly & Grinspun 2008, "Discrete Elastic Rods"**
(`papers/bergou2008-discrete-elastic-rods.pdf`, SIGGRAPH '08) is the formulation everything below
either wraps or competes with: a discrete adapted framed curve (Bishop frame + angular deviation),
force-based, with an implicit/quasistatic treatment of the twisting and stretching modes because
they are the stiff ones. It is not itself a PBD/XPBD method — it needs small time steps or an
implicit solve — which is exactly the "main performance bottleneck" every position-based follow-up
below cites as its reason to exist.

**Umetani, Schmidt & Stam 2014, "Position-based Elastic Rods"**
(`papers/umetani2014-position-based-elastic-rods.pdf`, SCA '14) is the first to fold a Cosserat rod
into PBD, by adding a **ghost point** off each edge so the material frame is still representable as
positions (PBD constraints only know how to act on positions). Shipped in Autodesk Maya's Nucleus
solver; reported **200 strands × 20 edges at interactive rate**. This is the direct ancestor both
of the next two papers, and of what "PBD rod" means in this literature.

**Kugelstadt & Schömer 2016, "Position and Orientation Based Cosserat Rods"**
(`papers/kugelstadt2016-cosserat-rods.pdf`, SCA '16) replaces the ghost point with a **quaternion
per edge**, constrained directly (unit-quaternion PBD constraints for stretch-shear and
bend-twist), which needs only **2 constraints per rod element** against Umetani's 4, and reports
being "more than one order of magnitude faster" at matched visual quality — **60–70×** in their
own benchmark. Concretely: their Slinky demo (1000 discrete elements, 50 curls) ran at **50 solver
iterations**, 7 ms/frame without collision, on one CPU core; a 30-element rod matched against
Umetani's own PBER numbers at **10 solver iterations**, 1.1 ms/frame. Fixed **time step 10 ms**
throughout (unconditionally stable, so a large step is fine). This is the paper the brief names
first for rod contact, and it is the most directly reusable of the five: a chain of particles +
per-edge orientation is exactly what "each long edge as a chain of particles with distance
constraints" plus bend/twist stiffness needs.

**Soler, Martin & Sorkine-Hornung 2018, "Cosserat Rods with Projective Dynamics"**
(`papers/soler2018-cosserat-rods-projective-dynamics.pdf`, CGF 2018) swaps the solver family:
Projective Dynamics instead of PBD/XPBD, which converges to a true implicit-Euler solution (their
Fig. 9 validates directly against an Abaqus FEM reference) rather than PBD's iteration-and-step
dependent approximation. It converges to a mesh-independent result from about **10 iterations**
on, with usable results from as few as **2**; PD is compared against Kugelstadt's PBD method at
matched compute budget, not raw speed — PD's advantage is that refining the mesh does not change
the answer, where PBD's does unless iteration count is retuned per resolution. Their reported
per-experiment time steps (Table 1) fall in the **1–11 ms** range. **This is the accuracy
benchmark, not the round's solver** — XPBD is still the better fit for a real-time, "no constant
printed on screen" render, but Soler's convergence numbers (2–10 iterations) are a useful sanity
check for how many XPBD iterations-per-substep the round needs before the look stops changing.

**Bender, Müller & Macklin 2017, "A Survey on Position Based Dynamics"**
(`papers/bender2017-survey-position-based-dynamics.pdf`, Eurographics tutorial) is the one place
that writes out the **generic contact constraint** in closed form (eq. 26):

> C(xᵢ, xⱼ) = |xᵢ − xⱼ| − (rᵢ + rⱼ) ≥ 0

for two spheres of radius rᵢ, rⱼ. This is exactly the **capsule–capsule / rod–rod contact
constraint** the brief asks for, once xᵢ, xⱼ are taken as the **closest points on the two
segments** rather than fixed particle centers: compute the closest-point pair between the two
edges' line segments each substep, treat each as a sphere of radius = half the ribbon's thickness
(so their sum is one full thickness — matching the brief's "contact constraint of radius one
thickness"), and push both points apart along the connecting normal by the constraint's violation,
exactly like any other PBD/XPBD distance-type constraint. Also from this source: the **friction**
model appended after the contact solve is a *position-level* tangential correction (eq. 27,
citing Macklin et al. 2014's Unified Particle Physics), not a velocity-level damping force —
needed because velocity-level friction (Müller 2007's original scheme) cannot hold static
contact, it only slows sliding.

**Macklin, Müller & Chentanez 2016, XPBD** (already in the archive,
`papers/macklin2016-xpbd.pdf`; new this pass is a `.txt` mining extract) states the contact-specific
convention directly: **"we assume zero compliance in contact"** — even in a scene where the
elastic constraints carry real, tunable compliance (their harmonic-oscillator validation case uses
α = 0.001), the collision/contact constraints are solved as **hard, infinitely-stiff constraints**.
For iteration counts: their FEM cantilever-beam validation matches a Newton reference at **20
XPBD iterations**; a 20-particle hanging chain is shown converged at **50**.

## 6. The numbers, at a glance

(Full table: `data/02-twisted-ribbon-and-rod-contact.csv`.)

| quantity | value | source |
|---|---|---|
| longitudinal buckling threshold (θ vs T) | θ₀ = √(24T) | Chopin & Kudrolli 2013 |
| transverse buckling threshold | θ_T = 4.4·(h/W)^0.5 | Chopin & Kudrolli 2013 |
| triple-point tension | T\* ≈ 0.8·(h/W) | Chopin & Kudrolli 2013 |
| longitudinal wrinkle wavelength | λ_L ≈ 3.8·√(hW/θ₀) | Chopin & Kudrolli 2013 |
| self-contact below T\* | θ_loop falls linearly with T, hysteretic | Chopin & Kudrolli 2013 |
| self-contact above T\* | follows θ_T with no hysteresis | Chopin & Kudrolli 2013 |
| XPBD contact compliance | 0 (rigid) | Macklin et al. 2016 |
| Kugelstadt substeps/iterations | dt = 10 ms fixed; 10–50 solver iterations | Kugelstadt & Schömer 2016 |
| Soler PD convergence | mesh-independent by ~10 iterations | Soler et al. 2018 |
| capsule/rod contact constraint | C = \|xᵢ−xⱼ\| − (rᵢ+rⱼ) ≥ 0, closest points on segments | Bender, Müller & Macklin 2017 |

## 7. What this says for the round

**When a real ribbon folds on itself.** The physical answer is not "when the near and far edges
happen to overlap in the camera's 2D projection" (the current bow-tie hack) — it is a function of
**how much twist relative to tension**, θ vs T, and it happens in two qualitatively different ways
depending which side of the triple point the ribbon sits on. A hand-driven ribbon at finger
tension is closer to the **low-tension / below-T\*** regime than the taut lab strips in these
papers (Dennis's hands go slack far more than a clamped 25 mm PET ribbon ever does) — which is the
regime where **more twist at lower tension folds *more* easily**, not less. That is good news for
the render: it means the "twists half a turn when a hand flips, snaps into the second touch" beat
already described in the finger-web skill is, physically, exactly backwards from a taut rod's
intuition and exactly right for a slack ribbon's — the fold should get *easier*, not harder, as
the ribbon goes slack mid-twist. The simplest way to carry that into the sim without modeling the
full (T, θ) phase diagram: use the **contact constraint itself** as the fold trigger (§5's
capsule–capsule constraint), and bias its target gap or its effective radius down slightly as the
local tension (already computed for the catenary/taut switch in round one) drops — a slacker
ribbon should need less twist to bring its edges together, matching Chopin & Kudrolli's
below-T\* line without needing the ribbon's actual Young's modulus or a real phase-diagram lookup.

**The simplest XPBD recipe, with constants pulled from §5–6:**

1. **Discretize** each long edge as a chain of particles connected by **distance constraints**
   (rest length = chain segment length at the first-stretch calibration, per item 01 §6);
   endpoints **pinned** to the tracked fingertip positions every frame (a hard/zero-compliance
   position constraint, same as item 01's pinned membrane anchors).
2. **Substep**, not iterate — per item 01 §3 (Macklin et al. 2019) and confirmed by every rod
   paper here reporting substep-scale time steps (Kugelstadt's fixed **10 ms**, Soler's **1–11
   ms** range): at 30 fps source, **8–16 substeps/frame** carries over directly; each substep
   applies gravity, then solves the distance/bend constraints, then the contact constraint, once
   (XPBD substepping, not many Gauss-Seidel passes per step).
3. **Contact**: each substep, find the **closest points on the two edge polylines** (segment vs.
   segment, standard closest-point-between-two-line-segments), and apply
   **C = |xᵢ−xⱼ| − 2r ≥ 0** with r = half the ribbon's rendered thickness (so the pair separates
   at exactly **one thickness**, per the brief), **compliance = 0** (Macklin et al. 2016's
   explicit convention — contact should feel rigid even while the distance/bend constraints carry
   real, tunable compliance). Where this constraint is active, the local ribbon width should be
   driven to zero over a few substeps (not snapped instantly), reading as the fold closing rather
   than the edges teleporting together.
4. **Iteration budget**: 1 solver pass per substep is enough per Kugelstadt (2016) and Soler
   (2018) — both converge visually within **2–10 iterations total**, and XPBD's substep model
   already spends the budget as substeps rather than iterations (item 01 §3). No need to chase
   Soler's FEM-exact convergence; this is a phone-video render, not an engineering sim.
5. **Friction**, only if the folded edges visibly slide against each other in a way that reads as
   wrong: apply the **position-level tangential correction** (Bender/Müller/Macklin 2017 eq. 27)
   after the contact solve, not a velocity-level damping term, since a velocity-level term cannot
   hold two folded edges genuinely still against each other.
6. **Orientation/twist stiffness**: if the edges need visible bending/twisting resistance beyond
   plain distance constraints (e.g. so the ribbon doesn't kink sharply at the fold), Kugelstadt &
   Schömer's quaternion-per-edge bend-twist constraint is the lightest-weight option found (2
   constraints/element) — but note this is an *upgrade path*, not required for the fold itself,
   which only needs the distance-constraint chain plus the contact constraint above.

## 8. What was not found this pass

- **Full text of A. E. Green 1937** ("The elastic stability of a thin twisted strip. II") —
  paywalled at the Royal Society, no open mirror. §1, §3 above only.
- **Full text of E. M. Mockensturm 2001** ("The Elastic Stability of Twisted Plates") — paywalled
  at ASME, no open mirror.
- **A correct arXiv ID for Chopin & Kudrolli 2013 in the brief's own text** — 1306.1583 is wrong
  (see `downloads-02.md`); resolved by using the author's own PDF instead of chasing the arXiv
  copy further (the paper may simply never have been posted to arXiv — Kudrolli's own preprints
  page links only the direct PDF, not an arXiv abstract page, for this title).
- **A single numeric "contact stiffness" or "penalty" convention across the rod papers** — every
  method that reports it (Macklin 2016, and implicitly Kugelstadt 2016 and Soler 2018, which both
  treat contact as a hard non-penetration constraint rather than a tunable spring) uses **zero
  compliance / a hard constraint** for contact, so there is no spring constant to report — the
  "constant" is the absence of one, which is itself the answer §6–7 uses.
- **Clean values out of Soler et al.'s Table 1** — `pdftotext` mangles the table's column
  alignment (numbers land out of row/column order); the **1–11 ms** time-step range quoted in §5
  is read off the visible `h` row by eye and should be treated as approximate, not a verified
  per-experiment value. Re-extracting from the PDF's actual table structure (not a bare
  `pdftotext` dump) would sharpen this if it turns out to matter.
