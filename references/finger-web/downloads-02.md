# Downloads — item 02, the twisted ribbon's regimes and rods with contact (2026-09-19)

Everything fetched this pass, with its URL and licence. PDFs stay local (never in the public
mirror). All downloads went through `curl -L` (the venv's Python certificate store is expired —
machine-local skill).

## Papers (`papers/`) — thread (a), the twisted ribbon's regimes

| file | url | licence | date |
|---|---|---|---|
| chopin2013-helicoids-wrinkles-loops.pdf | https://physics.clarku.edu/~akudrolli/preprints/ribbons.pdf | author's copy (Arshad Kudrolli, Clark University); *Phys. Rev. Lett.* 111, 174302 (2013); no explicit licence stated. **The arXiv ID given in the brief, 1306.1583, is wrong** — it resolves to an unrelated astrophysics paper (Lara-López et al., GAMA survey). Kudrolli's own preprint page (linked from his publications list) has no arXiv link for this title at all; this PDF is the only open copy found | 2026-09-19 |
| chopin2015-roadmap-morphological-instabilities.pdf, .txt | https://arxiv.org/pdf/1403.0267 | arXiv preprint (Chopin, Démery, Davidovitch); arXiv default licence; *J. Elasticity* 119, 137–189 (2015). arXiv ID confirmed correct | 2026-09-19 |
| chopin2016-disclinations-econes.pdf, .txt | https://arxiv.org/pdf/1601.00575 | arXiv preprint (Chopin & Kudrolli); arXiv default licence; *Soft Matter* 12, 4457–4462 (2016) | 2026-09-19 |

**NOT FOUND, full text:**
- **A. E. Green, "The elastic stability of a thin twisted strip. II", Proc. R. Soc. A 161, 197
  (1937)**, DOI 10.1098/rspa.1937.0141 — Royal Society Publishing returns HTTP 403; no open mirror
  found (pre-1950s papers are not in the Society's free-after-embargo window the way 1920s ones
  are). Its Part I (1936, DOI 10.1098/rspa.1936.0061) was not attempted either. Only a secondhand
  description survives, via its citation in `chopin2013-helicoids-wrinkles-loops.pdf` (ref. [10])
  and `chopin2015-roadmap-morphological-instabilities.pdf` (§1.1) — see
  `abstracts/green1937-elastic-stability-twisted-strip-ii.txt`.
- **E. M. Mockensturm, "The Elastic Stability of Twisted Plates", J. Appl. Mech. 68(4), 561–567
  (2001)** — paywalled at the ASME Digital Collection (HTTP 403), no open mirror found. Secondhand
  description via its citation in `chopin2013-helicoids-wrinkles-loops.pdf` (ref. [13]) and web
  search-engine summaries of the ASME abstract — see
  `abstracts/mockensturm2001-elastic-stability-twisted-plates.txt`.

**Consulted, not saved (follow-ups the brief allowed as bonus, judged not to add numbers beyond
what the three Chopin papers already give):**
- Kohn & O'Brien, "The wrinkling of a twisted ribbon" (J. Nonlinear Sci., also at
  https://math.nyu.edu/~kohn/papers/kohn-obrien-twisted-ribbon.pdf) — a rigorous
  Γ-convergence treatment of the untensioned inextensible limit; no twist-vs-tension phase
  diagram or contact numbers, so left uncited.
- Chopin, Démery et al., "Tension-dependent transverse buckles and wrinkles in twisted elastic
  sheets" (arXiv:1801.10456) and "From cylindrical to stretching ridges and wrinkles in twisted
  ribbons" (arXiv:1605.03728) — later, more specialized follow-ups on the far-from-threshold
  wrinkle pattern; the three downloaded papers already give the threshold and wavelength numbers
  the brief asked for, so these were read in search snippets only, not fetched.

## Papers (`papers/`) — thread (b), rods with contact for real-time simulation

| file | url | licence | date |
|---|---|---|---|
| kugelstadt2016-cosserat-rods.pdf, .txt | https://animation.rwth-aachen.de/media/papers/2016-SCA-Cosserat-Rods.pdf | author's copy (Tassilo Kugelstadt / Jan Bender's group, RWTH Aachen); SCA '16, Eurographics; no explicit licence stated | 2026-09-19 |
| soler2018-cosserat-rods-projective-dynamics.pdf, .txt | https://igl.ethz.ch/projects/cosserat-rods/CosseratRods-SCA2018.pdf | author's copy (Carlota Soler et al., ETH Zürich IGL group); *Computer Graphics Forum* 37(8), 2018; no explicit licence stated. **9.9 MB** — over the archive's 5 MB guideline, kept because it is the primary source for this thread | 2026-09-19 |
| umetani2014-position-based-elastic-rods.pdf, .txt | https://www.dropbox.com/s/ccq50x7vf63y1q7/2014_sca_PositionBasedElasticRod.pdf (linked from the author's own project page, https://cgenglab.github.io/en/publication/sca14_pbdrod/) | author's copy (Nobuyuki Umetani); SCA '14; no explicit licence stated. **18 MB** — over the 5 MB guideline, kept because it is the primary source; Umetani's own site (nobuyuki-umetani.com) hosts only a conference-talk slide PDF, not the paper, so the author-linked Dropbox mirror was used instead | 2026-09-19 |
| bergou2008-discrete-elastic-rods.pdf, .txt | http://www.cs.columbia.edu/cg/pdfs/143-rods.pdf | author's copy (Columbia Computer Graphics Group); ACM TOG (SIGGRAPH) 27(3), 2008; no explicit licence stated | 2026-09-19 |
| bender2017-survey-position-based-dynamics.pdf, .txt | https://animation.rwth-aachen.de/media/papers/2017-EG-CourseNotes.pdf | author's copy (Jan Bender, Matthias Müller, Miles Macklin); Eurographics '17 Tutorials; no explicit licence stated. **31 MB** — well over the 5 MB guideline (the course-notes PDF embeds many full-resolution figures over only 31 pages), kept because it is the primary requested survey and the text-extractable content is a modest 140 KB (`bender2017-survey-position-based-dynamics.txt`) | 2026-09-19 |

`papers/macklin2016-xpbd.pdf` was already in the archive from item 01 and not re-downloaded; a
`.txt` extract (`macklin2016-xpbd.txt`) was added this pass to mine its contact-compliance and
iteration-count numbers.

## Consulted, nothing saved

- `https://www.semanticscholar.org/search?...` for the Mockensturm 2001 abstract — returned no
  page content (search-only URL, not a paper page); the ASME abstract itself was not reachable.
- `https://ui.adsabs.harvard.edu/abs/1937RSPSA.161..197G/abstract` for the Green 1937 abstract —
  HTTP 405 from ADS's abstract endpoint.
- `https://cgenglab.github.io/labpage/en/publication/sca14_pbdrod/` — an old/broken path that
  redirects; the working path `https://cgenglab.github.io/en/publication/sca14_pbdrod/` carries
  the Dropbox PDF link used above.
