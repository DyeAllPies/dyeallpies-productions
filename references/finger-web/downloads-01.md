# Downloads — item 01, the finger web (2026-09-18)

Everything fetched this pass, with its URL and licence. PDFs stay local (never in the public mirror).
All downloads went through `curl` (the venv's Python certificate store is expired — machine-local skill).

## Papers (`papers/`)

| file | url | licence | date |
|---|---|---|---|
| muller2007-position-based-dynamics.pdf | https://matthias-research.github.io/pages/publications/posBasedDyn.pdf | author's copy on the author's own site (Matthias Müller, NVIDIA); JVCA 2007, no explicit licence stated | 2026-09-18 |
| macklin2016-xpbd.pdf | https://matthias-research.github.io/pages/publications/XPBD.pdf | author's copy; MIG '16, ACM, no explicit licence stated | 2026-09-18 |
| macklin2019-small-steps-in-physics-simulation.pdf | https://matthias-research.github.io/pages/publications/smallsteps.pdf | author's copy; SCA '19, no explicit licence stated | 2026-09-18 |
| pfaff2014-adaptive-tearing-thin-sheets.pdf | http://graphics.berkeley.edu/papers/Pfaff-ATC-2014-07/Pfaff-ATC-2014-07.pdf | author's copy, U.C. Berkeley Computer Graphics; ACM TOG 33(4), July 2014; no explicit licence stated. **18 MB** — over the archive's usual 5 MB guideline, kept because it is the primary tearing reference | 2026-09-18 |
| wang2010-multiresolution-isotropic-strain-limiting.pdf | http://graphics.berkeley.edu/papers/Wang-MRI-2010-12/Wang-MRI-2010-12.pdf | author's copy, U.C. Berkeley; ACM TOG 29(6), Dec 2010; no explicit licence stated. **12 MB**. (The `Wang-MIS-…` path in search results 404s to an HTML error page — the correct slug is `Wang-MRI-`) | 2026-09-18 |
| obrien1999-brittle-fracture.pdf | http://graphics.berkeley.edu/papers/Obrien-GMA-1999-08/Obrien-GMA-1999-08.pdf | author's copy, U.C. Berkeley; SIGGRAPH '99; no explicit licence stated | 2026-09-18 |
| casiez2012-one-euro-filter.pdf | https://cristal.univ-lille.fr/~casiez/publications/CHI2012-casiez.pdf | author's copy (Géry Casiez, Université de Lille); CHI '12, DOI 10.1145/2207676.2208639. The HAL mirrors (`inria.hal.science` / `hal.inria.fr` `/hal-00670496/document`) returned an HTML shell, not the PDF | 2026-09-18 |
| villermaux2022-taylor-culick-retractions-surroundings.pdf, .txt | https://arxiv.org/pdf/2202.13400 | arXiv preprint (Sanjay, Lohse et al.), "Taylor-Culick retractions and the influence of the surroundings"; arXiv default licence. **12 MB**; `.txt` is pages 1–6 only | 2026-09-18 |
| petit2015-holes-and-cracks-in-rigid-foam-films.pdf, .txt | https://arxiv.org/pdf/1503.06197 | arXiv preprint (Petit et al.), "Holes and cracks in rigid foam films"; arXiv default licence | 2026-09-18 |
| lopezpamies2024-cavitation-jmps.pdf, .txt | https://pamies.cee.illinois.edu/assets/pdf/JMPS2024b.pdf | author's copy (Oscar Lopez-Pamies, UIUC); J. Mech. Phys. Solids 188 (2024) 105683; no explicit licence stated. `.txt` is pages 1–8 only | 2026-09-18 |
| dobraszczyk-baking-extrusion-frying-ch8.pdf, .txt | https://nscpolteksby.ac.id/ebook/files/Ebook/Hospitality/Food%20Processing%20(2011)/8%20-%20Baking-Extrusion%20and%20Frying.pdf | chapter 8 of *Food Processing Handbook* (Dobraszczyk, Ainsworth, Ibanoglu, Bouchon), mirrored on a polytechnic's course-material server; **no licence stated, mirror of a copyrighted Wiley-VCH chapter** — cited for facts and figures only, never redistributed | 2026-09-18 |
| johndcook-catenary-sag-approximation.html, .txt | https://www.johndcook.com/blog/2024/03/09/catenary-sag-approx/ | personal blog (John D. Cook), all rights reserved by the author; cited for the Frame 1950 approximation and the sag/extra-length relation. **The formula itself is rendered as an image on the page and could not be read from the text**; the parabolic form in the item comes from the corroborating search summary of standard cable-sag references | 2026-09-18 |

## Code (`code/`) — `AadishY/Hand-Gesture-Filter`

MIT licence declared in `package.json` (`"license": "MIT"`) and by the README badge. **There is no
`LICENSE` file in the repository** (`raw.githubusercontent.com/.../main/LICENSE` → 404), so the
declaration is second-hand; treat the code as MIT but attribute it if any of it is ported.

| file | url | date |
|---|---|---|
| aadishy-hand-gesture-filter-README.md | https://raw.githubusercontent.com/AadishY/Hand-Gesture-Filter/main/README.md | 2026-09-18 |
| aadishy-geometry.js | https://raw.githubusercontent.com/AadishY/Hand-Gesture-Filter/main/js/geometry.js | 2026-09-18 |
| aadishy-tracking.js | https://raw.githubusercontent.com/AadishY/Hand-Gesture-Filter/main/js/tracking.js | 2026-09-18 |
| aadishy-filters.js | https://raw.githubusercontent.com/AadishY/Hand-Gesture-Filter/main/js/filters.js | 2026-09-18 |

Repo file listing taken from the GitHub trees API; `js/app.js` (33 KB) and `index.html` (22 KB) were
**not** fetched — the three saved modules carry the geometry, the tracking constants and the filters,
which is what item 01 cites.

## Consulted, nothing saved

- `https://www.intechopen.com/chapters/84168` — IntechOpen, CC BY 3.0, "Biaxial Extensional Viscosity
  in Wheat Doughs". Read and **discarded**: discusses strain hardening only qualitatively, carries no
  numerical values for the strain hardening index, Hencky failure strain, viscosity or strain rate.
- `https://github.com/AadishY/Hand-Gesture-Filter` (rendered page) — read for the technical summary
  quoted in item 01 §2.
- Dobraszczyk & Roberts 1994, *J. Cereal Sci.* 20(3):265–274, "Strain Hardening and Dough Gas Cell-wall
  Failure in Biaxial Extension" — the primary source for §4's numbers. **Paywalled at Elsevier
  (S0733521084710666); no open mirror found.** Abstract not saved: ScienceDirect blocks the fetch.

## Source material read (not downloads — Dennis's own drop)

`web/originals/` from `drive-download-20260918T194605Z-1-001.zip`, extracted 2026-09-18:

| file | what it is |
|---|---|
| IMG_6268.MOV | Dennis's take. iPhone 14, HEVC, 1920×1080 with rotation=90 (so 1080×1920 upright), 30 fps, 49.90 s, 1497 frames, audio effectively silent (mean −53 dB, peak −24.7 dB) |
| ScreenRecording_09-18-2026 15-15-20_1.mp4 | `mishu.ksv` reel "Making coding fun 🧑‍💻" — PUZZLE·CAM. 1170×2532, 59.94 fps, 21.2 s |
| ScreenRecording_09-18-2026 15-15-54_1.mp4 | `mishu.ksv` reel "#spiderman #python #software 🕷️🕸️" — `render_portal`. 1170×2532, 60 fps, 19.2 s. **This is the reference.** |
