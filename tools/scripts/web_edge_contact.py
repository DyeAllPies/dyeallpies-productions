"""Where the finger web's two long edges touch (2026-09-19 late night, Dennis's note for round four: "the top and bottom lines
might spatially touch each other when bending, which should trigger an extra twist where the lines touch"; HANDOFF).

    python web_edge_contact.py <membrane.npz> [offset=214] [thick=12] [near=24]

Per frame: the minimum image distance (px) between the polylines of the two long edges of the ring (the edges whose anchors are on
different hands: thumb -> thumb and index -> index), from `strings_px`; the two short edges (inside one hand) are not strings and
are left out. Printed per export second (min over the second, `*` where the outline is the bow-tie), then the runs under `near` px
WITHOUT a bow-tie (a bending approach, the flip's exit, the pinch, or the line state where the edges coincide by construction),
each with its closest frame and the image point of contact. `thick` is a drawn line's width: under it the edges overlap on screen.
Measured on the take (membrane6.npz): contact at the flips (2-9 px), 14-21 px at a flip's exit, 6 px at 30.0 and 31.1 s, 1-2 px at
the pinch; the sag alone reaches 67 px at 28 s and 29 px at 29 s.
"""
import json, sys
import numpy as np


def main():
    M = np.load(sys.argv[1]); kw = dict(a.split("=", 1) for a in sys.argv[2:])
    offset = int(kw.get("offset", 214)); thick = float(kw.get("thick", 12)); near = float(kw.get("near", 24))
    S = M["strings_px"]; nh = M["n_hull"]; hi = M["hull_idx"]; valid = M["valid"]; tw = M["twisted"]
    names = json.loads(str(M["params"]))["names"]; fps = float(json.loads(str(M["params"])).get("fps", 30))
    n = len(valid); dmin = np.full(n, np.nan); where = np.full((n, 2), np.nan)
    for i in range(n):
        if not valid[i] or nh[i] != 4: continue
        ring = hi[i, :4]; longs = [k for k in range(4) if names[ring[k]][1] != names[ring[(k + 1) % 4]][1]]
        if len(longs) != 2: continue
        a = S[i, longs[0]]; b = S[i, longs[1]]
        if np.isnan(a).any() or np.isnan(b).any(): continue
        d = np.linalg.norm(a[:, None] - b[None], axis=-1); k = np.unravel_index(d.argmin(), d.shape)
        dmin[i] = d[k]; where[i] = (a[k[0]] + b[k[1]]) / 2
    print(f"min distance between the two long edges (px; a drawn line is {thick:.0f} px), per export second [source frame], * = a bow-tie in that second:")
    row = []
    for t in range(int((n - offset) // fps) + 1):
        s = offset + int(t * fps); v = dmin[s:s + int(fps)]; v = v[~np.isnan(v)]
        if v.size: row.append(f"{t}s[{s}] {v.min():.0f}" + ("*" if tw[s:s + int(fps)].any() else ""))
    print("  " + "  ".join(row))
    close = np.flatnonzero((dmin < near) & ~tw); runs = []
    for i in close:
        if runs and i == runs[-1][1] + 1: runs[-1][1] = int(i)
        else: runs.append([int(i), int(i)])
    print(f"under {near:.0f} px WITHOUT a bow-tie (source a-b [export s], the closest frame, the contact point):")
    for a, b in runs:
        k = a + int(np.nanargmin(dmin[a:b + 1]))
        print(f"  {a}-{b} [{(a - offset) / fps:.1f}-{(b - offset) / fps:.1f} s] min {dmin[k]:.0f} px at frame {k}, x {where[k, 0]:.0f} y {where[k, 1]:.0f}")
    tr = np.flatnonzero(tw); groups = np.split(tr, np.flatnonzero(np.diff(tr) > 1) + 1) if tr.size else []
    print("bow-tie runs (source): " + ", ".join(f"{g[0]}-{g[-1]}" for g in groups))
    print(f"frames with the edges under one thickness ({thick:.0f} px): {int((dmin < thick).sum())} of {int(np.isfinite(dmin).sum())} four-tip frames, "
          f"{int(((dmin < thick) & ~tw).sum())} of them outside a bow-tie")


if __name__ == "__main__":
    main()
