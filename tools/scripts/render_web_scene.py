"""The finger web's scene, round one (2026-09-18, web/PLAN.md section 11): the effect export letterboxed into
the frame of a screen recording, the way the reference reels present theirs, so the video reads as the same
kind of video. A 4:3 app window (the reference's proportions, measured in the plan's 11.1) holds a 4:5 crop of
his footage that tracks the hands, at 60 % of the window's width (0.8 / 1.333: the plan's 11.3), and a live
telemetry panel in the other 40 % drawn from the membrane model's own state; above the window the VS Code
strip with the real source lines of the model, then the Windows title bar; black above and below (the
reference is letterboxed too).

    python render_web_scene.py <effect.mp4> <membrane.npz> <out.mp4> [offset=214] [preview=330,652,...]
        [title=web-ribbon] [workspace=DyeAllPies-Productions] [file=tools/scripts/web_membrane.py] [lines=608,610]
        [sticky=auto] [cursor=525] [chrome=<png>] [split=0.6] [smooth=0.4] [cov=web/work/scene_cov.npy]
        [look=spectrum] [fire=auto] [sting=1] [n_tail=90] [fps=30] [p720=1]

Round three, second pass (2026-09-19 late night, his notes on the export): the panel redrawn (the comment above `class Panel` says
what changed and why: the ramp meter under the hero figure, the map clipped to its lines, one row per edge with its stretch on the
ramp, hairlines, one type scale), the panel's lines on the same ramp as the effect's (the model's `stretch`).

Round three (2026-09-19, Dennis's verdict on round two, HANDOFF items 1, 6 and 8): the panel's strain LUT, its J value and bar and
its strings are coloured by the effect's strain ramp (render_web.ramp_stops: the spectrum's order, red -> violet, no green); the
fire starts at the model's thumbs-up settle (`fire=auto` reads params["fire_frame"]); and NO SLOT ON THE PANEL PRINTS A CONSTANT:
the J* number next to the value (the tick on the bar stays), the "· 16 defects" in the field's label are gone, and the report at
the end counts the distinct strings every slot printed over the export and names any VALUE slot that printed one string on every
frame (a label slot is allowed to). The rule from now on: a slot that prints the same string on every frame of the export is
removed before delivery; that check is this script's last line.

Round two (2026-09-19, Dennis's verdict on round one): the panel's map is DYNAMIC (the band's current shape in image
space with its strain field, as the renderer draws it, not the rest outline), the strings widget is the ring's four
edges (two coincide in the line state), the workspace reads DyeAllPies-Productions, the panel's marks come from the
effect's look (`look=`, render_web.LOOKS), a violet flame rises from each thumb from source frame `fire` (the
thumbs-up; web_fire.py, drawn over the composed frame so it can leave the app window), and with `sting=1` the tail is
appended: the two flames leave the thumbs, meet and write the wordmark, then PRODUCTIONS and the URL (the brand's
beats, the sting's neon composite; the scene dips to black under them, since the black band above the window is under
the platforms' UI and the brand's safe band is y 270-1250). The tail is silent; the shot's audio ends with the shot.

The crop: full width, the height that fills the feed's aspect (1350 px for 4:5), its vertical position
tracking the centre of the tips' and strings' extent smoothed by a Gaussian of `smooth` seconds (the plan's
11.2 measured that a 4:5 crop tracking the hands keeps every frame the native 9:16 keeps, 90.6 %, while the
reference's 4:3 loses a fingertip in 30 %). The printed check repeats that measurement on the path used.

The panel (the plan's 11.3: "what this channel already prints"): the hull's areal stretch J against the hole
threshold J* with its last six seconds, the strain field on the rest sheet with the sixteen seeded defects
and the open holes, the outline's strings by tension or slack, the hole count and area, the tracking state.
Every value is read from membrane.npz at the SOURCE frame (export frame + `offset`); nothing is invented.

The chrome (menu bar, tab, breadcrumb, title bar) is a stand-in drawn here in VS Code's Dark Modern and
Windows 11's light title bar; Dennis's own screenshot replaces it (`chrome=`: a PNG of his VS Code's top strip,
scaled to the band's width). The code rows are rendered from the real file at every build with the real
line numbers and VS Code's sticky scroll (the enclosing def pinned above the viewport), so the lines on
screen are the lines that produced the render (plan 11.4: do not fake a result). Every text is measured to
its box (memory video-text-fit-check); the report at the end lists any that had to shrink.

Every frame is independent: the panel reads the model's arrays, the crop path is computed once from the
tips. A change to the panel or the chrome is a re-compose of about a minute, no re-render of the effect.
`preview=` takes SOURCE frame indices, like render_web.py.
"""
import io, json, keyword, os, sys, time, tokenize
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from studio.encode import RawWriter, decode_check, preview_720, streams, mux_audio
from studio.colour import hex_to_rgb8
import studio.brand as brand
from render_web import LOOKS, ramp_stops, ramp_rgb
import web_fire

# ---- the frame (plan 11.1: the reference's content band, 1170 x 1239, measured; scaled to 1080 wide) ----
REEL_W, REEL_H = 1080, 1920
STRIP_H = 289            # the VS Code strip: 314 of the reference's 1239 rows (25.3 %)
TITLE_H = 49             # the Windows title bar: 53 rows
INSET = 10               # the app window's inset from the band's edge: ~9 px of 1170
WIN_W = REEL_W - 2 * INSET                    # 1060
WIN_H = int(round(WIN_W * 3 / 4))             # 795: the reference's 4:3 window
BAND_H = STRIP_H + TITLE_H + WIN_H            # 1133 of 1920; black above and below
BAND_Y0 = (REEL_H - BAND_H) // 2              # 393
TITLE_Y0 = BAND_Y0 + STRIP_H
WIN_Y0 = TITLE_Y0 + TITLE_H

# VS Code Dark Modern (the default theme's values; his screenshot replaces the chrome, the code rows keep `editor`)
VSC = dict(title="#181818", tabs="#181818", tab_active="#1F1F1F", editor="#1F1F1F", border="#2B2B2B", text="#CCCCCC",
           text_dim="#9D9D9D", accent="#0078D4", gutter="#6E7681", gutter_active="#CCCCCC", guide="#404040",
           cur_line="#282828", cc_bg="#242424", cc_border="#303030", run="#89D185", icon="#22A4F2")
# Dark+ Python syntax colours
SYN = dict(kw="#569CD6", kw2="#C586C0", func="#DCDCAA", var="#9CDCFE", mod="#4EC9B0", const="#4FC1FF", number="#B5CEA8",
           string="#CE9178", comment="#6A9955", op="#D4D4D4", text="#D4D4D4")
CONTROL = {"for", "if", "else", "elif", "while", "return", "break", "continue", "try", "except", "finally", "with", "yield",
           "in", "and", "or", "not", "is", "raise", "pass", "as", "import", "from"}
# the Windows 11 light title bar: the background measured off the reference (plan 11.1, ~#F2EFF4)
WIN = dict(bg="#F2EFF4", text="#1B1B1B", border="#8A8A8A")
# the panel: the brand's ground and neutral (studio.brand), the marks in this video's own palette (render_web.LOOKS[look])
PANEL = dict(bg=brand.MAIN, text=brand.NEUTRAL, muted="#A39E97", track="#3B3536")


def panel_palette(look):
    """The panel's marks from the effect's look: the sheet's colours, the strings', the fold (the back face) and the thick dough."""
    L = LOOKS[look]
    return dict(PANEL, look=look, cream=L["cream"], warm=L["warm"], hot=L["hot"], dull=L["string_dull"], string_hot=L["string_hot"],
                fold=L["back_col"] if look != "dough" else "#2A2224", thick="#8C6A4A" if look == "dough" else L["back_col"], back_mul=L.get("back_mul", 1.0))
TRACE_S = 6.0            # seconds of J history in the trace
J_AXIS = 2.0             # the bar's and the trace's full scale (the hull's J tops out at 1.40 in this take; J* 1.4; local J to 1.6)
R_VIS = 0.04             # a hole counts as open above this radius (palms), as web_membrane.py's printed checks count them

CODE_FONT = "C:/Windows/Fonts/CascadiaMono.ttf"; UI_FONT = "C:/Windows/Fonts/segoeui.ttf"; ICON_FONT = "C:/Windows/Fonts/SegoeIcons.ttf"
CODE_PX, CODE_ADV, ROW_H = 28, 16, 46          # Cascadia Mono 28 px advances 16 px: 61 columns in the code area
TB, TABS, BC = 34, 38, 24                      # the VS Code title/menu bar, the tab bar, the breadcrumb
GUTTER_X, CODE_X = 84, 100                     # line numbers right-aligned at GUTTER_X; code from CODE_X

_FC = {}


def font(path, size):
    return _FC.get((path, size)) or _FC.setdefault((path, size), ImageFont.truetype(path, size))


def rgb(h):
    return tuple(hex_to_rgb8(h))


def lerp(a, b, t):
    t = float(np.clip(t, 0, 1)); return tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3))


class Fits:
    """Every burned-in line measured to its box: the worst case per slot is printed at the end. Round three: every slot also counts
    the distinct strings it printed; a VALUE slot (kind="value", the default) that printed one string on every frame is a constant
    and is named at the end (the rule: it is removed before delivery); a LABEL slot (kind="label") may be constant."""

    def __init__(self): self.worst = {}; self.seen = {}; self.kind = {}; self.frames = 0

    def text(self, d, slot, xy, s, fnt, fill, maxw, anchor="ls", kind="value"):
        w = d.textlength(s, font=fnt); size = fnt.size; path = fnt.path
        while w > maxw and size > 10:
            size -= 1; fnt = font(path, size); w = d.textlength(s, font=fnt)
        prev = self.worst.get(slot)
        if prev is None or w / maxw > prev[0] / prev[3]: self.worst[slot] = (w, s, size, maxw)
        self.seen.setdefault(slot, set()).add(s); self.kind[slot] = kind
        d.text(xy, s, font=fnt, fill=fill, anchor=anchor)
        return w

    def report(self):
        print("text fit (worst case per slot: width / box, size used; distinct strings over the run):")
        for slot, (w, s, size, maxw) in sorted(self.worst.items()):
            flag = "  SHRUNK" if size < int(slot.split("@")[1]) else ""
            print(f"  {slot:28s} {w:6.0f} / {maxw:4.0f}  {size:3d} px{flag}  {len(self.seen[slot]):5d} distinct ({self.kind[slot]})  '{s}'")
        const = [slot for slot in self.seen if self.kind[slot] == "value" and len(self.seen[slot]) == 1]
        print("constant VALUE slots (printed one string on every frame; remove before delivery): " + (", ".join(sorted(const)) if const else "none"))


FITS = Fits()


# ---- the code strip ----------------------------------------------------------------------------------------------
def tokens(line):
    """(column, text, kind) per token of one source line, Dark+'s classes approximated from Python's own tokenizer."""
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(line + "\n").readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return [(0, line, "text")]
    skip = {tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING}
    toks = [t for t in toks if t.type not in skip]
    out = []
    for k, t in enumerate(toks):
        s = t.string; prev = toks[k - 1].string if k else ""; nxt = toks[k + 1].string if k + 1 < len(toks) else ""
        if t.type == tokenize.COMMENT: kind = "comment"
        elif t.type == tokenize.STRING: kind = "string"
        elif t.type == tokenize.NUMBER: kind = "number"
        elif t.type == tokenize.NAME:
            if keyword.iskeyword(s): kind = "kw2" if s in CONTROL else "kw"
            elif prev in ("def", "class") or nxt == "(": kind = "func"
            elif nxt == ".": kind = "mod"
            elif s.isupper() and len(s) > 1: kind = "const"
            else: kind = "var"
        else: kind = "op"
        out.append((t.start[1], s, kind))
    return out


def sticky_lines(src, first):
    """VS Code's sticky scroll with the outline model: the enclosing def/class lines of the viewport's first line."""
    pins = []; ind = len(src[first - 1]) - len(src[first - 1].lstrip())
    for ln in range(first - 1, 0, -1):
        s = src[ln - 1]
        if not s.strip(): continue
        k = len(s) - len(s.lstrip())
        if k < ind:
            if s.lstrip().startswith(("def ", "class ", "async def ")): pins.append(ln)
            ind = k
        if ind == 0: break
    return pins[::-1][:5]


def code_strip(path, lines, sticky, cursor, workspace, chrome_png):
    src = open(path, encoding="utf-8").read().split("\n")
    lo, hi = lines; view = list(range(lo, hi + 1))
    pins = sticky_lines(src, lo) if sticky == "auto" else ([int(x) for x in sticky.split(",")] if sticky else [])
    rows = [(ln, True) for ln in pins] + [(ln, False) for ln in view]
    img = Image.new("RGB", (REEL_W, STRIP_H), rgb(VSC["editor"])); d = ImageDraw.Draw(img)
    ui, ui_s, ui_m, ico = font(UI_FONT, 17), font(UI_FONT, 15), font(UI_FONT, 14), font(ICON_FONT, 10)
    # VS Code's title bar: the icon, the menu, the command centre with the workspace, the window controls
    d.rectangle((0, 0, REEL_W, TB), fill=rgb(VSC["title"]))
    d.rounded_rectangle((12, 9, 28, 25), radius=3, fill=rgb(VSC["icon"])); d.rectangle((16, 13, 24, 21), fill=rgb(VSC["title"]))
    x = 40
    for item in ("File", "Edit", "Selection", "View", "Go", "Run", "Terminal", "Help"):
        d.text((x, 22), item, font=ui_m, fill=rgb(VSC["text"]), anchor="ls"); x += d.textlength(item, font=ui_m) + 12
    cw = 320; cx0 = int(x) + 66                                   # the command centre sits right of the menu, its arrows just before it
    d.text((cx0 - 52, 22), "\u2190", font=ui_m, fill=rgb(VSC["text_dim"]), anchor="ls"); d.text((cx0 - 28, 22), "\u2192", font=ui_m, fill=rgb(VSC["text_dim"]), anchor="ls")
    d.rounded_rectangle((cx0, 5, cx0 + cw, TB - 5), radius=6, fill=rgb(VSC["cc_bg"]), outline=rgb(VSC["cc_border"]))
    tw = d.textlength(workspace, font=ui_s); gx = cx0 + cw / 2 - tw / 2 - 14
    d.ellipse((gx - 6, 12, gx + 3, 21), outline=rgb(VSC["text_dim"]), width=2); d.line((gx + 2, 20, gx + 6, 24), fill=rgb(VSC["text_dim"]), width=2)
    FITS.text(d, "cc.workspace@15", (cx0 + cw / 2 + 4, 23), workspace, ui_s, rgb(VSC["text"]), cw - 60, anchor="ms", kind="label")
    for k, g in enumerate(("\uE921", "\uE922", "\uE8BB")):
        d.text((REEL_W - 46 * (3 - k) + 23, TB / 2), g, font=ico, fill=rgb(VSC["text"]), anchor="mm")
    # the tab bar: one tab, the file; the run button at the right
    d.rectangle((0, TB, REEL_W, TB + TABS), fill=rgb(VSC["tabs"]))
    name = os.path.basename(path); tw = d.textlength(name, font=ui); tab_w = int(tw) + 74
    d.rectangle((0, TB, tab_w, TB + TABS), fill=rgb(VSC["tab_active"])); d.line((0, TB, tab_w, TB), fill=rgb(VSC["accent"]), width=2)
    d.line((tab_w, TB, tab_w, TB + TABS), fill=rgb(VSC["border"]))
    py = TB + TABS / 2
    d.rounded_rectangle((14, py - 8, 24, py + 1), radius=2, fill=(55, 118, 171)); d.rounded_rectangle((20, py - 1, 30, py + 8), radius=2, fill=(255, 212, 59))
    d.text((40, py), name, font=ui, fill=(255, 255, 255), anchor="lm"); d.text((tab_w - 18, py), "\u00D7", font=ui, fill=rgb(VSC["text"]), anchor="mm")
    d.polygon([(REEL_W - 92, py - 7), (REEL_W - 92, py + 7), (REEL_W - 80, py)], fill=rgb(VSC["run"]))
    for k in range(3): d.ellipse((REEL_W - 52 + 8 * k, py - 1.5, REEL_W - 49 + 8 * k, py + 1.5), fill=rgb(VSC["text"]))   # "more actions"
    d.line((0, TB + TABS, REEL_W, TB + TABS), fill=rgb(VSC["border"]))
    # the breadcrumb: the path inside the workspace, then the symbol
    rel = os.path.relpath(path, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")).replace("\\", "/").split("/")
    sym = src[pins[-1] - 1].strip().split(" ")[1].split("(")[0] if pins else ""
    crumb = "  \u203A  ".join(rel + ([sym] if sym else []))
    FITS.text(d, "breadcrumb@15", (16, TB + TABS + BC - 6), crumb, ui_s, rgb(VSC["text_dim"]), REEL_W - 32, kind="label")
    # the code rows: sticky pins first (with VS Code's shadow under them), then the viewport
    code = font(CODE_FONT, CODE_PX); y = TB + TABS + BC
    for r, (ln, pinned) in enumerate(rows):
        s = src[ln - 1] if ln - 1 < len(src) else ""; ry = y + r * ROW_H
        if ln == cursor: d.rectangle((CODE_X - 6, ry, REEL_W - 1, ry + ROW_H - 1), outline=rgb(VSC["cur_line"]), width=2)
        ind = len(s) - len(s.lstrip())
        for k in range(ind // 4): d.line((CODE_X + 4 * k * CODE_ADV, ry, CODE_X + 4 * k * CODE_ADV, ry + ROW_H), fill=rgb(VSC["guide"]))
        d.text((GUTTER_X, ry + ROW_H / 2), str(ln), font=code, fill=rgb(VSC["gutter_active"] if ln == cursor else VSC["gutter"]), anchor="rm")
        for col, tok, kind in tokens(s):
            x = CODE_X + col * CODE_ADV
            if x >= REEL_W: break
            d.text((x, ry + ROW_H / 2), tok, font=code, fill=rgb(SYN[kind]), anchor="lm")
        if pinned and r == len(pins) - 1:
            for k in range(6): d.line((0, ry + ROW_H + k, REEL_W, ry + ROW_H + k), fill=lerp(rgb(VSC["editor"]), (0, 0, 0), 0.5 * (1 - k / 6)))
    vis_cols = (REEL_W - CODE_X) // CODE_ADV
    for ln, pinned in rows:
        s = src[ln - 1].rstrip()
        note = f"clipped at column {vis_cols} of {len(s)}" if len(s) > vis_cols else "fits"
        print(f"  code row {ln:4d}{' (sticky)' if pinned else ''}: {note}: {s.strip()[:70]}")
    if chrome_png:
        top = Image.open(chrome_png).convert("RGB").resize((REEL_W, TB + TABS + BC), Image.LANCZOS); img.paste(top, (0, 0))
    return np.asarray(img)[:, :, ::-1].copy()


# ---- the template: black, the strip, the Windows title bar, the window border, the panel's ground ---------------------
def template(strip_bgr, title):
    img = Image.new("RGB", (REEL_W, REEL_H), (0, 0, 0)); d = ImageDraw.Draw(img)
    d.rectangle((INSET - 1, TITLE_Y0 - 1, REEL_W - INSET, WIN_Y0 + WIN_H), outline=rgb(WIN["border"]))
    d.rectangle((INSET, TITLE_Y0, REEL_W - INSET - 1, WIN_Y0 - 1), fill=rgb(WIN["bg"]))
    ui, ico = font(UI_FONT, 17), font(ICON_FONT, 10); cy = TITLE_Y0 + TITLE_H / 2
    d.rectangle((INSET + 12, cy - 7, INSET + 28, cy + 7), fill=(255, 255, 255), outline=(110, 110, 110)); d.rectangle((INSET + 12, cy - 7, INSET + 28, cy - 4), fill=(70, 120, 200))
    FITS.text(d, "window.title@17", (INSET + 40, cy), title, ui, rgb(WIN["text"]), 500, anchor="lm", kind="label")
    for k, g in enumerate(("\uE921", "\uE922", "\uE8BB")):
        d.text((REEL_W - INSET - 46 * (3 - k) + 23, cy), g, font=ico, fill=rgb(WIN["text"]), anchor="mm")
    out = np.asarray(img)[:, :, ::-1].copy()
    out[BAND_Y0:BAND_Y0 + STRIP_H] = strip_bgr
    return out


# ---- the crop path ----------------------------------------------------------------------------------------------
def crop_path(M, fps, crop_h, H, smooth_s):
    """Per source frame, the crop's top row: the centre of the tips' (and, while the sheet hangs, the strings')
    vertical extent, Gaussian-smoothed over `smooth_s` seconds, clamped to the frame. Gaps interpolated, ends held."""
    tips = M["tips_px"]; strings = M["strings_px"]; valid = M["valid"]; released = M["released"]; n_hull = M["n_hull"]; n = len(valid)
    cy = np.full(n, np.nan)
    for i in range(n):
        pts = tips[i][np.isfinite(tips[i][:, 1])]
        if valid[i] and not released[i]:
            sp = strings[i, :n_hull[i]].reshape(-1, 2); sp = sp[np.isfinite(sp[:, 1])]
            if len(sp): pts = np.concatenate([pts, sp], 0) if len(pts) else sp
        if len(pts): cy[i] = 0.5 * (pts[:, 1].min() + pts[:, 1].max())
    ok = np.isfinite(cy)
    if not ok.any(): return np.full(n, (H - crop_h) // 2, int)
    idx = np.arange(n); cyf = np.interp(idx, idx[ok], cy[ok])
    sig = max(smooth_s * fps, 1e-3); k = int(3 * sig) + 1
    g = np.exp(-0.5 * (np.arange(-k, k + 1) / sig) ** 2); g /= g.sum()
    cys = np.convolve(np.pad(cyf, k, mode="edge"), g, mode="valid")
    return np.clip(np.round(cys - crop_h / 2), 0, H - crop_h).astype(int)


def path_report(M, y0, crop_h, t0, t1):
    tips = M["tips_px"][t0:t1]; y = y0[t0:t1]; K = tips.shape[1]
    ten = np.isfinite(tips[..., 1]).sum(1) == K
    inside = ((tips[..., 1] >= y[:, None]) & (tips[..., 1] < (y + crop_h)[:, None]) & (tips[..., 0] >= 0) & (tips[..., 0] < REEL_W)).all(1)
    native = ((tips[..., 1] >= 0) & (tips[..., 1] < REEL_H) & (tips[..., 0] >= 0) & (tips[..., 0] < REEL_W)).all(1)
    step = np.abs(np.diff(y0)).max()
    print(f"crop path: all {K} tips inside the {REEL_W}x{crop_h} crop on {100 * inside[ten].mean():.1f} % of the {ten.sum()} {K}-tip frames "
          f"(inside the native frame: {100 * native[ten].mean():.1f} %, the ceiling); top row {y0[t0:t1].min()}..{y0[t0:t1].max()}; "
          f"largest step {step} px/frame")


# ---- the panel ---------------------------------------------------------------------------------------------------
# Second pass (2026-09-19 late night, Dennis: the panel "doesn't look like something Fable would do"; the strain field "isn't neat,
# some inside doesn't touch the lines or goes over the lines"). What changed, and the rule behind each:
#   - one type scale (Inter for labels, JetBrains Mono for every number), hairlines between the sections, a 22 px gutter, the brand's
#     one accent as a 6 px mark beside the heading and nowhere else; text wears the text tokens, a coloured mark beside it carries
#     the value's colour (dataviz: text never wears the series colour, except the hero figure, which IS the mark here);
#   - the meter under the hero figure is the strain ramp itself: full colour up to the current J, the rest of the ramp dimmed, the
#     J* tick on it (a meter whose track is a lighter step of the same ramp doubles as the legend of the sheet's colour);
#   - the map: every grid cell with any corner inside the rest sheet is rasterised, then the field is CLIPPED to the polygon of the
#     strings themselves and every pixel of that polygon the cells left bare takes its nearest rasterised colour (scipy's EDT with
#     indices), so the fill ends exactly at the line, neither short of it nor past it; the map is framed by a hairline;
#   - the edges: one row per outline edge (name, a bar of its linear stretch lambda coloured by the ramp at lambda^2 with the rest
#     tick at lambda = 1, and the value: "slack 0.41", "+12 %" or "rest"), the same scale the lines wear on screen; the up/down
#     bars stay for an outline with more than six edges (the ten-tip dough);
#   - nothing prints a constant (Fits still checks; the edges' names are labels).
class Panel:
    def __init__(self, M, W, H, fps, offset, jstar, palette, crop_y0=None, crop_h=None, src_w=REEL_W):
        self.M = M; self.W, self.H, self.fps, self.jstar = W, H, fps, jstar; self.P = palette
        self.J = M["J_global"]; self.gJ = M["grid_J"]; self.inside = M["inside"]; self.uv = M["grid_uv"]; self.gpx = M["grid_px"]
        self.valid = M["valid"]; self.released = M["released"]; self.n_hull = M["n_hull"]; self.tension = M["tension"]; self.slack = M["slack"]
        self.holes = M["holes_r"]; self.defects = M["defects"]; self.tips = M["tips_px"]; self.fall = M["fall_dy"]; self.strings = M["strings_px"]
        self.hull_idx = M["hull_idx"] if "hull_idx" in M.files else None
        self.snap_f = M["snap_f"] if "snap_f" in M.files else np.ones(len(self.valid), np.float32)
        if "stretch" in M.files: self.stretch = M["stretch"]
        else:
            with np.errstate(all="ignore"): st = np.where(self.slack > 1e-6, M["span"] / np.maximum(M["span"] + self.slack, 1e-9), 1.0 + self.tension)
            self.stretch = np.clip(np.nan_to_num(st, nan=1.0), 0, 10).astype(np.float32)
        self.K = self.tips.shape[1]; self.names = json.loads(str(M["params"])).get("names", [f"t{k}" for k in range(self.K)])
        self.bg = rgb(palette["bg"]); self.text = rgb(palette["text"]); self.muted = rgb(palette["muted"]); self.track = rgb(palette["track"])
        self.accent = rgb(brand.SECONDARY)
        self.cream, self.warm, self.hot = rgb(palette["cream"]), rgb(palette["warm"]), rgb(palette["hot"])
        self.dull, self.shot = rgb(palette["dull"]), rgb(palette["string_hot"])
        self.pad = 22; self.iw = W - 2 * self.pad
        # the strain LUT over J in [-0.5, jstar + 0.8]: the effect's own strain ramp (render_web.ramp_stops; round three: the spectrum's
        # order) for J >= 0, and the fold (the back face: the rest colour darkened as the renderer darkens it) for J < 0
        self.stops = ramp_stops(LOOKS[palette["look"]], jstar) if "look" in palette else [(0.0, palette["cream"]), (jstar, palette["warm"]), (jstar + 0.8, palette["hot"])]
        self.on_ramp = "look" in palette and "ramp" in LOOKS[palette["look"]]          # the lines wear the ramp at stretch^2 (render_web.draw_strings)
        self.fold = tuple(int(round(v * palette.get("back_mul", 1.0))) for v in ramp_rgb(self.stops, 1.0)) if palette.get("look") != "dough" else rgb(palette["fold"])
        self.j_lo, self.j_hi = -0.5, jstar + 0.8
        self.j_axis = max(J_AXIS, self.stops[-1][0] + 0.15)                              # the meter's and the trace's full scale: past the ramp's last stop
        lut = np.zeros((256, 3), np.uint8)
        for k in range(256):
            J = self.j_lo + (self.j_hi - self.j_lo) * k / 255
            lut[k] = self.fold if J < -0.05 else (lerp(self.fold, ramp_rgb(self.stops, 0.0), (J + 0.05) / 0.05) if J < 0 else ramp_rgb(self.stops, J))
        self.lut = lut
        u = self.uv[..., 0]; v = self.uv[..., 1]; self.u0, self.u1, self.v0, self.v1 = u.min(), u.max(), v.min(), v.max()
        # the map: round one drew the REST sheet (Dennis asked why the form on the right had that shape); round two draws the band's
        # CURRENT shape in image space, as the renderer draws it: a window of the tracking crop's width centred on the crop's centre
        self.dynamic = crop_y0 is not None
        self.crop_y0 = crop_y0; self.crop_h = crop_h; self.src_w = src_w
        self.map_w = self.iw
        if self.dynamic:
            # the scale is the height over 640 image px, so the open quad (610 px tall at 514) fits, centred horizontally
            self.map_h = int(round(self.iw * 0.46)); self.map_scale = self.map_h / 640.0; self.map_x0 = (self.map_w - src_w * self.map_scale) / 2
        else:
            self.map_h = int(round(self.iw * (self.v1 - self.v0) / (self.u1 - self.u0)))
            poly = np.array([self.uv_to_map(p) for p in M["rest_poly"]], np.float32) - [self.pad, 0]    # the rest outline, anti-aliased
            m = np.zeros((self.map_h, self.map_w), np.uint8); cv2.fillPoly(m, [np.round(poly * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
            self.mask = (m.astype(np.float32) / 255.0)[..., None]
        self.f_label = brand.font("sub", 20); self.f_big = brand.font("mono", 76); self.f_mid = brand.font("mono", 54)
        self.f_mono = brand.font("mono", 18); self.f_mono_s = brand.font("mono", 13); self.f_head = brand.font("sub", 21); self.f_row = brand.font("sub", 18)
        self.f_mono_v = brand.font("mono", 16)                                       # the edge rows' values ("slack 0.81" fits its 104 px box at 16)
        self.ground = lerp(self.bg, self.track, 0.5)
        # the edges' names: both anchors thumbs -> "thumbs", both index -> "index", else the hand (0 = the image-left hand)
        self.edge_names = None
        if self.hull_idx is not None and self.K <= 6:
            self.edge_names = {}
            for i in np.flatnonzero(self.valid):
                key = tuple(int(x) for x in self.hull_idx[i, :int(self.n_hull[i])])
                if key in self.edge_names: continue
                rows = []
                for k in range(len(key)):
                    a, b = self.names[key[k]], self.names[key[(k + 1) % len(key)]]
                    word = "thumbs" if a[0] == b[0] == "t" else ("index" if a[0] == b[0] == "i" else ("left hand" if a[1] == "0" else "right hand"))
                    rows.append((word, f"{a}–{b}"))
                self.edge_names[key] = rows

    def img_to_map(self, p, i):
        """Image px -> map px for the dynamic map: the crop's centre row maps to the map's centre."""
        cy = self.crop_y0[i] + self.crop_h / 2
        return np.stack([p[..., 0] * self.map_scale + self.map_x0, (p[..., 1] - cy) * self.map_scale + self.map_h / 2], -1)

    def edge_colour(self, i, k):
        """The colour of outline edge k on frame i: the ramp at its stretch^2 (as the renderer draws it), else the tension lerp."""
        if self.on_ramp: return ramp_rgb(self.stops, float(self.stretch[i, k]) ** 2)
        t = float(self.tension[i, k]); return lerp(self.dull, self.shot, t / 0.5) if t > 0 else lerp(self.dull, self.bg, 0.3)

    def draw_dynamic_map(self, i, live):
        """The band as the renderer draws it, in miniature: the grid cells filled with their strain colour (the back face in the fold
        colour), clipped to the polygon of the strings and carried to it where the cells fall short, the ring's strings by stretch,
        the open holes at their image positions, the tracked tips as dots."""
        h, w = self.map_h, self.map_w
        m = np.zeros((h, w, 3), np.uint8); m[:] = self.ground[::-1]
        if live:
            G = self.img_to_map(self.gpx[i], i); Jf = self.gJ[i]; ins = self.inside
            step = 2; Gy, Gx = Jf.shape
            field = np.zeros((h, w, 3), np.uint8); covered = np.zeros((h, w), np.uint8)
            for y in range(0, Gy - step, step):
                for x in range(0, Gx - step, step):
                    if not (ins[y, x] or ins[y + step, x + step] or ins[y, x + step] or ins[y + step, x]): continue
                    q = np.array([G[y, x], G[y, x + step], G[y + step, x + step], G[y + step, x]], np.float32)
                    if not np.isfinite(q).all() or (np.abs(q) > 1e4).any(): continue
                    Jc = float(Jf[y:y + step + 1, x:x + step + 1].mean())
                    c = self.lut[int(np.clip((Jc - self.j_lo) / (self.j_hi - self.j_lo) * 255, 0, 255))]
                    qi = np.round(q * 16).astype(np.int32)
                    cv2.fillConvexPoly(field, qi, tuple(int(v) for v in c[::-1]), cv2.LINE_8, shift=4); cv2.fillConvexPoly(covered, qi, 255, cv2.LINE_8, shift=4)
            n = int(self.n_hull[i])
            poly = self.strings[i, :n].reshape(-1, 2); poly = poly[np.isfinite(poly[:, 0])]
            if len(poly) >= 3:
                mask = np.zeros((h, w), np.uint8)
                cv2.fillPoly(mask, [np.round(self.img_to_map(poly, i) * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
                bare = (mask > 0) & (covered == 0)
                if bare.any() and covered.any():
                    from scipy.ndimage import distance_transform_edt
                    _, (iy, ix) = distance_transform_edt(covered == 0, return_indices=True)
                    field[bare] = field[iy[bare], ix[bare]]
                a = (mask.astype(np.float32) / 255.0)[..., None]
                m = (field * a + m * (1 - a) + 0.5).astype(np.uint8)
            for k in range(n):                                                    # each line on a 1 px ground of the panel's own colour, so a
                s = self.strings[i, k]; s = s[np.isfinite(s[:, 0])]                 # line at rest still reads against a sheet at rest (both yellow)
                if len(s) < 2: continue
                q = [np.round(self.img_to_map(s, i) * 16).astype(np.int32)]
                cv2.polylines(m, q, False, self.bg[::-1], 5, cv2.LINE_AA, shift=4); cv2.polylines(m, q, False, self.edge_colour(i, k)[::-1], 3, cv2.LINE_AA, shift=4)
            ppx = float(self.M["scale"][i]) * self.map_scale                   # map px per palm
            for k, p in enumerate(self.defects):
                r = float(self.holes[i, k]) * ppx
                if r > R_VIS * ppx:
                    c = self.img_to_map(self.uv_to_img(p, i), i)
                    if np.isfinite(c).all(): cv2.circle(m, (int(c[0]), int(c[1])), int(r), self.bg[::-1], -1, cv2.LINE_AA); cv2.circle(m, (int(c[0]), int(c[1])), int(r), self.hot[::-1], 2, cv2.LINE_AA)
        tp = self.tips[i]
        for k in range(self.K):
            if np.isfinite(tp[k]).all():
                c = self.img_to_map(tp[k], i)
                if 0 <= c[0] < w and 0 <= c[1] < h: cv2.circle(m, (int(c[0]), int(c[1])), 4, self.text[::-1], -1, cv2.LINE_AA)
        cv2.rectangle(m, (0, 0), (w - 1, h - 1), self.track[::-1], 1)          # the hairline frame
        return Image.fromarray(m[:, :, ::-1])

    def uv_to_img(self, p, i):
        """A rest position (palm units) -> image px through the frame's grid (bilinear)."""
        Gy, Gx = self.gJ.shape[1:]
        fx = (p[0] - self.u0) / (self.u1 - self.u0) * (Gx - 1); fy = (p[1] - self.v0) / (self.v1 - self.v0) * (Gy - 1)
        x0 = int(np.clip(np.floor(fx), 0, Gx - 2)); y0 = int(np.clip(np.floor(fy), 0, Gy - 2)); ax, ay = fx - x0, fy - y0
        G = self.gpx[i]
        return (G[y0, x0] * (1 - ax) * (1 - ay) + G[y0, x0 + 1] * ax * (1 - ay) + G[y0 + 1, x0] * (1 - ax) * ay + G[y0 + 1, x0 + 1] * ax * ay)

    def heat(self, J):
        """The J value's and bar's colour: the strain ramp at J (round three), muted when there is no value."""
        if not np.isfinite(J): return self.muted
        return ramp_rgb(self.stops, max(J, 0.0))

    def uv_to_map(self, p):
        return (self.pad + (p[0] - self.u0) / (self.u1 - self.u0) * self.map_w, (p[1] - self.v0) / (self.v1 - self.v0) * self.map_h)

    def hairline(self, d, y):
        d.line((self.pad, y, self.pad + self.iw, y), fill=self.track, width=1)

    def meter(self, d, x0, y0, w, h, J):
        """The ramp as the meter's track: full colour up to J, dimmed beyond it; the J* tick; the marker at J."""
        for x in range(w):
            Jx = self.j_axis * x / (w - 1); c = ramp_rgb(self.stops, Jx)
            if not (np.isfinite(J) and Jx <= J): c = lerp(c, self.bg, 0.72)
            d.line((x0 + x, y0, x0 + x, y0 + h - 1), fill=c)
        tx = x0 + int(round(w * self.jstar / self.j_axis))
        d.rectangle((tx - 1, y0 - 4, tx, y0 + h + 3), fill=self.text)
        FITS.text(d, "meter.jstar@13", (tx, y0 - 8), "J*", self.f_mono_s, self.muted, 30, anchor="ms", kind="label")
        if np.isfinite(J):
            mx = x0 + int(round(w * min(max(J, 0.0), self.j_axis) / self.j_axis))
            d.polygon([(mx - 5, y0 + h + 2), (mx + 5, y0 + h + 2), (mx, y0 + h - 4)], fill=self.text)

    def draw(self, i):
        W, H, pad, iw = self.W, self.H, self.pad, self.iw
        img = Image.new("RGB", (W, H), self.bg); d = ImageDraw.Draw(img)
        live = bool(self.valid[i]) or bool(self.released[i]); rel = bool(self.released[i])
        # the heading: the accent mark, the tracked name, the frame clock
        d.rectangle((pad, 31, pad + 6, 37), fill=self.accent)
        x = pad + 16
        for ch in "MEMBRANE":
            d.text((x, 42), ch, font=self.f_head, fill=self.text, anchor="ls"); x += d.textlength(ch, font=self.f_head) + 3
        FITS.text(d, "hdr.frame@18", (W - pad, 42), f"f {i:04d}  {i / self.fps:5.1f} s", self.f_mono, self.muted, iw - 170, anchor="rs")
        self.hairline(d, 60)
        # 1. the hull's areal stretch: the hero figure in the ramp's colour, the ramp meter with the J* tick, the last six seconds
        y = 92
        FITS.text(d, "J.label@20", (pad, y), "areal stretch  J", self.f_label, self.muted, iw, kind="label")
        J = float(self.J[i]) if i < len(self.J) else np.nan; hc = self.heat(J)
        FITS.text(d, "J.value@76", (pad - 2, y + 80), f"{J:.2f}" if np.isfinite(J) else "—", self.f_big, hc, 220)
        FITS.text(d, "J.unit@13", (pad + 200, y + 80), "hull area / rest area", self.f_mono_s, self.muted, iw - 200, kind="label")
        by = y + 104; bh = 12
        self.meter(d, pad, by, iw, bh, J)
        ty0 = by + bh + 22; th = 52; n_tr = int(TRACE_S * self.fps)
        d.rectangle((pad, ty0, pad + iw, ty0 + th), fill=self.ground)
        yy = ty0 + th - th * self.jstar / self.j_axis
        for xx in range(pad, pad + iw, 10): d.line((xx, yy, xx + 5, yy), fill=lerp(self.ground, self.text, 0.35))
        seg = []; k0 = max(0, i - n_tr + 1)
        for k in range(k0, i + 1):
            Jk = self.J[k] if k < len(self.J) else np.nan
            if np.isfinite(Jk): seg.append((pad + iw * (k - (i - n_tr + 1)) / (n_tr - 1), ty0 + th - th * min(Jk, self.j_axis) / self.j_axis))
            elif len(seg) > 1: d.line(seg, fill=self.text, width=2); seg = []
            else: seg = []
        if len(seg) > 1: d.line(seg, fill=self.text, width=2)
        if seg: d.ellipse((seg[-1][0] - 4, seg[-1][1] - 4, seg[-1][0] + 4, seg[-1][1] + 4), fill=hc, outline=self.bg)
        FITS.text(d, "trace.span@13", (pad, ty0 + th + 16), f"last {TRACE_S:.0f} s", self.f_mono_s, self.muted, 120, kind="label")
        self.hairline(d, ty0 + th + 30)
        # 2. the strain field: the band as drawn, clipped to its lines
        y = ty0 + th + 60
        n_open = int((self.holes[i] > R_VIS).sum()) if live else 0
        FITS.text(d, "field.label@20", (pad, y), "strain field", self.f_label, self.muted, iw, kind="label")
        my0 = y + 14
        if self.dynamic:
            img.paste(self.draw_dynamic_map(i, live), (pad, my0)); d = ImageDraw.Draw(img)
        elif live:
            idx = np.clip((self.gJ[i] - self.j_lo) / (self.j_hi - self.j_lo) * 255, 0, 255).astype(np.uint8)
            fld = cv2.resize(self.lut[idx], (self.map_w, self.map_h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
            fld = (fld * self.mask + np.array(self.bg, np.float32) * (1 - self.mask) + 0.5).astype(np.uint8)
            img.paste(Image.fromarray(fld), (pad, my0)); d = ImageDraw.Draw(img)
            ppx = self.map_w / (self.u1 - self.u0)                       # map px per palm
            for k, p in enumerate(self.defects):
                cx, cy = self.uv_to_map(p); cy += my0; r = float(self.holes[i, k]) * ppx
                if r > R_VIS * ppx: d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=self.bg, outline=self.hot, width=2)
                else: d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), outline=lerp(self.bg, self.text, 0.55), width=1)
        else:
            d.rectangle((pad, my0, pad + iw, my0 + self.map_h), fill=self.ground, outline=self.track)
        self.hairline(d, my0 + self.map_h + 24)
        # 3. the edges: one row each, the stretch on the ramp
        y = my0 + self.map_h + 54
        n = int(self.n_hull[i]) if live else 0
        taut = int((self.tension[i, :n] > 5e-3).sum()); slk = int((self.slack[i, :n] > 1e-3).sum())   # the rows' own thresholds ("rest" under them)
        FITS.text(d, "edges.label@20", (pad, y), f"edges  ·  {taut} taut  {slk} slack" if live else "edges", self.f_label, self.muted, iw)
        key = tuple(int(x) for x in self.hull_idx[i, :n]) if (self.hull_idx is not None and n) else None
        rows = self.edge_names.get(key) if (self.edge_names is not None and key is not None) else None
        if rows is not None:
            rh = 36; y0 = y + 18; bx0 = pad + 160; bx1 = W - pad - 112; lam_axis = 1.6
            for k in range(n):
                ry = y0 + k * rh; lam = float(self.stretch[i, k]); s = float(self.slack[i, k]); t = float(self.tension[i, k]); col = self.edge_colour(i, k)
                FITS.text(d, f"edge.{k}.name@18", (pad, ry + 23), rows[k][0], self.f_row, self.text, 96, kind="label")
                FITS.text(d, f"edge.{k}.pair@13", (pad + 102, ry + 23), rows[k][1], self.f_mono_s, self.muted, 52, kind="label")
                d.rounded_rectangle((bx0, ry + 12, bx1, ry + 22), radius=3, fill=self.track)
                fx = bx0 + int(round((bx1 - bx0) * min(lam, lam_axis) / lam_axis))
                if fx > bx0 + 2: d.rounded_rectangle((bx0, ry + 12, fx, ry + 22), radius=3, fill=col)
                tx = bx0 + int(round((bx1 - bx0) / lam_axis)); d.rectangle((tx, ry + 9, tx, ry + 25), fill=self.text)   # the rest tick, lambda = 1
                # a short edge (inside one hand) never sags: below the rest spread its value is the spread's shortfall (2026-09-22)
                val = f"slack {s:.2f}" if s > 1e-3 else (f"+{100 * t:.0f} %" if t > 5e-3 else (f"-{100 * (1 - lam):.0f} %" if lam < 0.995 else "rest"))
                FITS.text(d, f"edge.{k}.value@16", (W - pad, ry + 23), val, self.f_mono_v, self.text, 104, anchor="rs")
        elif n:
            base = y + 56; amp = 36; slot = iw / n
            d.line((pad, base, pad + iw, base), fill=self.track, width=1)
            for k in range(n):
                x0 = pad + k * slot + 3; x1 = x0 + slot - 6; t = float(self.tension[i, k]); s = float(self.slack[i, k])
                if t > 0: h = max(3, min(t / 0.6, 1.0) * amp); d.rectangle((x0, base - h, x1, base), fill=self.edge_colour(i, k))
                else: h = max(3, min(s / 2.0, 1.0) * amp); d.rectangle((x0, base, x1, base + h), fill=lerp(self.bg, self.edge_colour(i, k), 0.75))
        # the holes: absent when the model has no defects (2026-09-19 late night: the holes effect removed, and with it its mention)
        if len(self.defects):
            y = H - 96
            FITS.text(d, "holes.label@20", (pad, y), "holes", self.f_label, self.muted, 120, kind="label")
            area = float((np.pi * self.holes[i] ** 2).sum()) if live else 0.0
            FITS.text(d, "holes.area@18", (W - pad, y), f"area {area:.2f} palm²", self.f_mono, self.text, iw - 130, anchor="rs")
            FITS.text(d, "holes.count@54", (pad - 1, y + 54), str(n_open), self.f_mid, self.hot if n_open else self.text, 90)
            FITS.text(d, "holes.open@20", (pad + 66, y + 54), "open", self.f_label, self.muted, 80, kind="label")
        # the state line
        n_tips = int(np.isfinite(self.tips[i][:, 1]).sum())
        snapped = self.K == 4 and not live and bool(self.valid[:i].any())         # round two: after the snap the sheet is gone for good
        if rel:
            state = "released  ·  sheet gone" if float(self.fall[i]) > self.H else f"released  ·  falling"
        elif live and float(self.snap_f[i]) < 1.0: state = f"{n_tips} tips  ·  snapping"
        elif live: state = f"{n_tips} tips  ·  {n} edges" + ("  ·  twisted" if "twisted" in self.M.files and self.M["twisted"][i] else "")
        elif snapped: state = f"{n_tips} tips  ·  snapped"
        else: state = f"{n_tips} tips  ·  no sheet"
        self.hairline(d, H - 44)
        FITS.text(d, "state@18", (pad, H - 18), state, self.f_mono, self.muted, iw)
        return np.asarray(img)[:, :, ::-1]


# ---- main ---------------------------------------------------------------------------------------------------------
def main():
    effect, mem_npz, out = sys.argv[1:4]
    kw = dict(a.split("=", 1) for a in sys.argv[4:])
    offset = int(kw.get("offset", 214)); fps = float(kw.get("fps", 30)); split = float(kw.get("split", 0.6)); smooth = float(kw.get("smooth", 0.4))
    title = kw.get("title", "web-ribbon"); workspace = kw.get("workspace", "DyeAllPies-Productions")   # his spelling of the label (2026-09-19)
    src_file = kw.get("file", os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_membrane.py"))
    lines = tuple(int(x) for x in kw.get("lines", "608,610").split(",")); sticky = kw.get("sticky", "auto"); cursor = int(kw.get("cursor", lines[0]))   # the bow-tie lines: grep "hv = ring; m = K"
    chrome = kw.get("chrome"); cov_path = kw.get("cov", os.path.join("web", "work", "scene_cov.npy"))
    look = kw.get("look", "spectrum"); sting = kw.get("sting", "1") == "1"; n_tail = int(kw.get("n_tail", 90))
    M = np.load(mem_npz); params = json.loads(str(M["params"])); jstar = float(params["jstar"])
    fire_kw = kw.get("fire", "auto")                                          # round three: the model's thumbs-up settle, else a frame
    if fire_kw == "none": fire_from = 10 ** 9              # no fire in the shot (2026-09-19: the export ends at the snap, the thumbs-up is cut); the tail's
    else:                                                   # flames still start at the tips' last tracked position, i.e. the touch point where the sheet vanished
        fire_from = int(params.get("fire_frame", -1)) if fire_kw == "auto" else int(fire_kw)
        if fire_from < 0: fire_from = 1409; print("fire: the model has no settle frame; falling back to source 1409 (round two's first thumbs-up frame)")
    feed_w = int(round(WIN_W * split)); feed_h = WIN_H; panel_w = WIN_W - feed_w
    crop_h = int(round(REEL_W * feed_h / feed_w))
    cap = cv2.VideoCapture(effect); W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); nv = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    assert (W, H) == (REEL_W, REEL_H), f"the effect export is {W}x{H}; the scene is laid out for {REEL_W}x{REEL_H}"
    print(f"scene: band {REEL_W}x{BAND_H} at y {BAND_Y0} (strip {STRIP_H}, title {TITLE_H}, window {WIN_W}x{WIN_H}); feed {feed_w}x{feed_h} "
          f"({100 * split:.0f} %) from a {REEL_W}x{crop_h} crop; panel {panel_w}x{WIN_H}; {nv} effect frames from source {offset}; look {look}; "
          f"{'no fire in the shot' if fire_from >= 10 ** 9 else f'fire from source {fire_from}'}; tail {n_tail if sting else 0} frames")
    print("code strip:")
    strip = code_strip(src_file, lines, sticky, cursor, workspace, chrome)
    tmpl = template(strip, title)
    path = crop_path(M, fps, crop_h, H, smooth); path_report(M, path, crop_h, offset, min(offset + nv, len(path)))
    panel = Panel(M, panel_w, WIN_H, fps, offset, jstar, panel_palette(look), crop_y0=path, crop_h=crop_h, src_w=W)
    fx0, fy0 = INSET, WIN_Y0; px0 = INSET + feed_w
    # the thumbs in scene px, per source frame (the fire's emitters): the tips through the crop, held across gaps and past the last
    # tracked frame (the four-tip tracking drops out at 1451-1465 of this take while the thumbs stay up)
    tips = M["tips_px"]; K = tips.shape[1]; thumb_idx = [0, K // 2]
    thumbs = np.full((len(path), 2, 2), np.nan, np.float32)
    for i in range(len(path)):
        for j, t in enumerate(thumb_idx):
            p = tips[i, t]
            if np.isfinite(p).all(): thumbs[i, j] = [fx0 + p[0] * feed_w / W, fy0 + (p[1] - path[i]) * feed_h / crop_h]
            elif i > 0: thumbs[i, j] = thumbs[i - 1, j]
    flame = web_fire.Flame(W, H) if fire_from >= 0 else None
    fire_state = [-1]                                                          # the last source frame the flame was advanced to

    def compose(k, fr, with_fire=True):
        i = min(k + offset, len(path) - 1); y0 = int(path[i])
        img = tmpl.copy()
        img[fy0:fy0 + feed_h, fx0:fx0 + feed_w] = cv2.resize(fr[y0:y0 + crop_h], (feed_w, feed_h), interpolation=cv2.INTER_AREA)
        img[fy0:fy0 + WIN_H, px0:px0 + panel_w] = panel.draw(i)
        if with_fire and flame is not None and i >= fire_from:
            if fire_state[0] != i - 1:                                         # a preview: replay the flame from its first frame (deterministic)
                flame.__init__(W, H)
                for s in range(fire_from, i):
                    for th in thumbs[s]:
                        if np.isfinite(th).all(): flame.emit((th[0], th[1] - 6), min(1.0, (s - fire_from + 1) / 8))
                    flame.step()
            for th in thumbs[i]:
                if np.isfinite(th).all(): flame.emit((th[0], th[1] - 6), min(1.0, (i - fire_from + 1) / 8))   # the flame catches over 8 frames
            flame.step(); fire_state[0] = i
            fcol, fa = flame.render(); img = web_fire.over(img, fcol, fa)
        return img

    # the tail's wordmark in the effect's own colours (2026-09-22): the ramp's stops, from the same function the panel's meter reads
    ramp_hex = [c for _, c in ramp_stops(LOOKS[look], jstar)] if look in LOOKS and "ramp" in LOOKS[look] else None
    tail = web_fire.Sting(W, H, n_tail=n_tail, ramp=ramp_hex) if sting else None

    def tail_frame(j, last_scene):
        i = min(offset + nv - 1, len(path) - 1)
        return tail.frame(j, last_scene, flame, [th for th in thumbs[i] if np.isfinite(th).all()])

    if "preview" in kw:
        idx = [x for x in kw["preview"].split(",")]; tiles = []; last_scene = None; tail_done = 0
        for s in idx:
            if s.startswith("t"):                                              # tN: frame N of the tail (after the effect's last frame)
                j = int(s[1:])
                if last_scene is None:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, nv - 1); ok, fr = cap.read(); last_scene = compose(nv - 1, fr, with_fire=False)
                if j < tail_done:                                              # the flame is stateful: replay the tail from its first frame
                    flame.__init__(W, H); tail.__init__(W, H, n_tail=n_tail, ramp=ramp_hex); tail_done = 0
                for jj in range(tail_done, j): tail_frame(jj, last_scene)
                t0 = time.time(); img = tail_frame(j, last_scene); dt = time.time() - t0; label = f"tail {j}"; tail_done = j + 1
                p = out.replace(".mp4", f"_t{j:03d}.png")
            else:
                i = int(s); k = i - offset; cap.set(cv2.CAP_PROP_POS_FRAMES, k); ok, fr = cap.read()
                if not ok: print(f"  source frame {i} is outside the export"); continue
                t0 = time.time(); img = compose(k, fr); dt = time.time() - t0; label = f"{i} {i / fps:.1f}s"
                p = out.replace(".mp4", f"_f{i:04d}.png")
            cv2.imwrite(p, img); print(f"  {label}: {dt * 1000:.0f} ms -> {p}")
            t = cv2.resize(img, (W // 3, H // 3)); cv2.putText(t, label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3); tiles.append(t)
        rows = [np.hstack(tiles[j:j + 3]) for j in range(0, len(tiles), 3)]
        w = max(r.shape[1] for r in rows)
        rows = [np.hstack([r, np.zeros((r.shape[0], w - r.shape[1], 3), np.uint8)]) if r.shape[1] < w else r for r in rows]
        cv2.imwrite(out.replace(".mp4", "_sheet.png"), np.vstack(rows)); FITS.report(); print("preview written"); return

    enc = RawWriter(out, W, H, int(fps)); t0 = time.time(); k = 0    # video only; the audio is muxed from the original below (audio=), never
                                                                     # copied from the effect with -shortest, which cut the last frame (2026-09-18)
    n_all = nv + (n_tail if sting else 0)
    cov = np.zeros((n_all, H // 8, W // 8, 1), np.uint8); cov[:nv, fy0 // 8:(fy0 + feed_h) // 8, fx0 // 8:(fx0 + feed_w) // 8] = 255   # the tail's dip is deliberate: not gated
    last_scene = None
    while True:
        ok, fr = cap.read()
        if not ok or k >= nv: break
        img = compose(k, fr); enc.write(img); k += 1
        if k == nv: last_scene = compose(nv - 1, fr, with_fire=False)
        if k % 200 == 0: print(f"  frame {k}/{nv} {(time.time() - t0) / k:.3f} s/frame", flush=True)
    if sting:
        for j in range(n_tail): enc.write(tail_frame(j, last_scene))
        print(f"  tail: {n_tail} frames ({n_tail / fps:.1f} s): the dip, the flight, the wordmark, PRODUCTIONS, the URL, the hold")
    rc = enc.close(); print(f"wrote {out} ffmpeg exit {rc}: {enc.n} frames ({nv} shot + {enc.n - nv} tail) in {time.time() - t0:.1f} s")
    if "audio" in kw:                                   # the shot's own audio from the ORIGINAL at the export's offset (audio=web/originals/IMG_6268.MOV);
        tmp = out.replace(".mp4", ".mux.mp4"); mux_audio(out, kw["audio"], tmp, start=offset / fps, duration=nv / fps); os.replace(tmp, out)   # the tail stays silent
    FITS.report()
    ok, err = decode_check(out); print("decode gate:", "OK" if ok else "FAILED " + err, "|", streams(out))
    np.save(cov_path, cov); print(f"gate matte (the feed's rectangle on the shot's frames, nothing on the tail) -> {cov_path} {cov.shape}; run check_flicker.py on it with offset=0")
    if kw.get("p720", "1") == "1":
        p = out.replace(".mp4", "-720.mp4"); preview_720(out, p); print("720 copy:", p)


if __name__ == "__main__":
    main()
