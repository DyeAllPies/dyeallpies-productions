"""The finger web's render, round one (2026-09-18): the dough membrane from web_membrane.py drawn over the
plate on the GPU, the strings on top, the hands in front of everything, the plate untouched elsewhere.

    python render_web.py <master.mp4> <membrane.npz> <matte.npy|none> <out.mp4>
        [trim=214,1480] [preview=214,330,420] [look=dough] [pattern=grid|web|none] [filt=0.85]
        [shadow=0.18] [debug=0] [string_px=5] [fps=30] [yc_mode=fade|step|dither|cornsweet] [yc_period=0.15] [yc_amp=0.25] [yc_w=0.06] [yc_step=<J>] [xmode=pinch|occlude] [xtaper=0.7] [heli=1] [heli_k=0.55] [shadow_mode=hue|fixed] [shadow_k=0.22]

The look, per fragment, in LINEAR light (studio.colour's transfer; the constants are the look's dict below):
  P       the plate under the fragment (the room, his face)
  J       the areal stretch from the model (rest = 1), clamped below at 0.02
  milk    1 - exp(-milk_k / J): the sheet's opacity from its THICKNESS h = h0 / J (volume-incompressible,
          web/PLAN.md section 3.3): a slack sheet is thick and hides the picture like a ball of dough, a
          stretched one is thin and shows it
  heat    smoothstep(heat_lo, jstar, J): the material heats as it nears the threshold (the plan's section 5
          "tie the filter to the strain"), cream -> hot
  Pf      the picture through the sheet: a posterised duotone of P's luminance between shadow_col and the
          sheet's colour (the reference's filtered portal), `levels` steps falling with the heat, blended
          in at `filt`
  colour  mix(Pf, sheet, milk), then the pattern lines (a grid or a web in REST space, so the cells stretch
          with the material), the holes (alpha 0 inside, a raised rim lit from the upper left just outside,
          dark radiating cracks: plan section 3.4c), a dark band at the outline (a thickness edge)
The holes reveal the UNFILTERED room (plan section 5). Hands: the matte (extract_skin_matte.py) composites
the plate back over everything, so the fingers hold the sheet from the front. The strings: each outline
edge drawn twice, a dark base and a core coloured by its tension (slack: dull; taut: hot), thinner as it
stretches, with a soft offset shadow; the sheet casts a soft shadow on the plate outside its outline
(item 11's ranked list: a contact shadow is the cheapest realism cue).

Every frame is independent of the others (the model carries the state), so preview=i,j,k renders those
frames straight away and a look change costs a re-render of about a minute, no bake needed.

Round three, second pass (2026-09-19 late night): the ramp gains cyan through the brand's neutral (no green hue at any sample,
`ramp_check`), the lines wear the same ramp at their stretch^2 (`stretch` from the model), and the fill pass carries the nearest drawn
colour to the outline (`ext_px`) instead of painting the gap between the mesh and the line in the crushed colour.
"""
import json, os, sys, time
import numpy as np
import cv2
import moderngl

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from studio.encode import RawWriter, decode_check, preview_720, streams, mux_audio
from studio.colour import hex_to_rgb01, srgb_to_lin
import studio.gl as sgl

LOOKS = {
    # round one (2026-09-18): dough in a daylit room. Item 09's rule for a bright plate: luminance contrast, no
    # bloom; the lines are dark and the heat is a saturated warm hue that still reads against the cream wall.
    "dough": dict(cream="#F2E3C6", warm="#FFB347", hot="#FF4E1A", shadow_col="#6B4226", line_col="#4A2E1B", rim_light="#FFF4DC",
                  milk_k=0.5, milk_max=0.8, heat_lo=0.85, levels_lo=5.0, levels_hi=2.0, grid_spacing=0.3, line_w=0.02, line_alpha=0.32,
                  rim_w=0.08, crack_w=0.012, crack_len=0.7, edge_px=6.0, back_col="#F2E3C6", back_mul=1.0, string_px=5.0,
                  string_dull="#6B4A2E", string_hot="#FF3B00", string_dark="#231F20"),
    # round two (2026-09-19, Dennis: "more vivid, violet again", the neon puppet's violet-dominant look with its hot red):
    # the values are the puppet's own (render_puppet.py LOOKS["violet-mix"], linear BGR -> sRGB; memory
    # port-referenced-look-from-code): the trunk's electric violet (1.00, 0.00, 0.28) = #8F00FF as the front face, the
    # limbs' blue-violet (1.00, 0.00, 0.14) = #6900FF as the BACK face of the twisted ribbon, the upper arms' magenta
    # (0.75, 0.00, 1.00) = #FF00E1 as the warming and the boots' pure red #FF0000 as the hot end and the taut strings, the
    # strings' pale tube (1.00, 0.35, 0.60) = #CBA0FF as the tear rims' light. On the daylit room item 09 still binds: no
    # bloom, luminance contrast, so the edges and the duotone's shadow are DARK violets (assumed, judged on his screen)
    # and the shadow is not near-black (round one's lesson: #3A2415 painted his shirt as blobs). The ribbon's edge is
    # thick (string_px 12: "a very thick ribbon") and the outline band is 8 px.
    "violet": dict(cream="#8F00FF", warm="#FF00E1", hot="#FF0000", shadow_col="#3C1478", line_col="#2A0A55", rim_light="#CBA0FF",
                   milk_k=0.5, milk_max=0.8, heat_lo=0.85, levels_lo=5.0, levels_hi=2.0, grid_spacing=0.3, line_w=0.02, line_alpha=0.32,
                   rim_w=0.08, crack_w=0.012, crack_len=0.7, edge_px=8.0, back_col="#6900FF", back_mul=0.62, string_px=12.0,
                   string_dull="#6900FF", string_hot="#FF0000", string_dark="#231F20"),
    # round three (2026-09-19, Dennis's verdict on round two, HANDOFF item 1): the strain colouring follows the VISIBLE SPECTRUM'S order,
    # red at the lowest strain and violet at the highest, with ZERO green at every stop (the line of purples is the only green-free path
    # from red to violet). `ramp` is the sheet's colour over the areal stretch J: crushed (J -> 0) red, magenta at half the rest area,
    # the rest (J = 1) a red-violet, the tear threshold J* the brand's electric violet #8F00FF, the take's largest stretch (J* + 0.6:
    # the local J peaks at 1.57 on this take) blue-violet. The back face of the twisted ribbon is the same ramp read at |J| and darkened
    # (`back_mode` 1); the tear rims are lit in the highest stop mixed with magenta (rim_light #FF00FF: no green in the highlight either);
    # the strings run red when slack to blue-violet when taut; the crushed fill is the ramp's low end. The dark violets for the edges and
    # the duotone's shadow keep item 09's rule on the daylit wall (dark edges, no bloom) and lose their green channel too. The fire's ramp
    # (web_fire.RAMP) is temperature, not strain, and is unchanged. All stops assumed on the spectrum's order; judged on his screen.
    # 2026-09-19 late night, his note on the export: orange, yellow and blue as the middle tones between the red and violet ends (the
    # first spectrum version ran red -> magenta -> violet with no green channel anywhere; the orange and yellow stops now carry one by
    # necessity, but no stop is green and the only grey-green is the short yellow -> blue mix between J 1.0 and J*). Rest (J = 1) is
    # yellow, a crushed or slack band orange to red, the threshold blue, the take's largest stretch (J* + 0.6) the brand's violet.
    # 2026-09-19 late night, second pass, his note: "red orange yellow cyan (cyan only if possible with no green) blue violet". Cyan sits
    # between green and blue in the spectrum, and any mix from yellow (hue 60) to cyan (hue 190) passes through green (hue 120) unless it
    # goes through the achromatic axis: so the ramp crosses from yellow to cyan THROUGH THE BRAND'S NEUTRAL (#F2F0EA, off-white) at
    # J* - 0.1, a pale band a tenth of a stretch wide, and no sample of the ramp is a green hue (ramp_check samples it at 400 points and
    # prints the verdict; the shader mixes in linear light and ramp_rgb does the same, so the panel and the sheet agree). The band from
    # yellow to blue is now 1.0 -> J* + 0.25 (was 1.0 -> J*: the whole band flipped blue -> yellow over two frames at source 1010, the
    # round-three gate's one real colour flash); violet at J* + 0.45 = 1.65, the take's largest local stretch (1.57 at frame 789).
    # Later the same night, his note on that export: no white either, "make the yellow transition directly to the next colour without
    # white (green)". So the ramp STEPS from yellow to cyan: two stops at the same J (J* - 0.1), yellow then cyan, and both the shader
    # and ramp_rgb read a zero-width segment as a hard edge (a posterised isoline sweeps the sheet where J crosses it). Yellow holds
    # from the rest to the step; cyan -> blue -> violet mix as before. `ramp_check` prints the step.
    # 2026-09-22, his verdict on the r4 export ("at second twelve it clearly shows cyan versus yellow without a gradient"; then, on the
    # dark-seam idea, "don't put a dark part between cyan and yellow, just make it a gradient like you would a button that fades from
    # one colour to the other"; and "No green!" as the standing rule for the STOPS): the ramp is a plain FADE again, yellow at the rest
    # (J 1.0) to cyan at J*, mixed in linear light like every other segment. No stop is green; the fade's middle is a pale mint by the
    # physics of the two lights (ramp_check prints how many samples of the band exceed the hue-and-saturation rule, and the shipped
    # export is judged on his screen). The step, the stripes and the Cornsweet cusp stay as `yc_mode=` knobs: ramp_stops inserts the
    # step into this fade when a mode asks for one.
    "spectrum": dict(ramp=[(0.0, "#FF0000"), (0.5, "#FF7F00"), (1.0, "#FFE000"), ("J*", "#00D8FF"), ("J*+0.25", "#0040FF"), ("J*+0.45", "#8F00FF")],
                     cream="#FFE000", warm="#0040FF", hot="#8F00FF", fill="#FF0000", shadow_col="#3C0078", line_col="#2A0055", rim_light="#FF00FF",
                     milk_k=0.5, milk_max=0.8, heat_lo=0.85, levels_lo=5.0, levels_hi=2.0, grid_spacing=0.3, line_w=0.02, line_alpha=0.32,
                     rim_w=0.08, crack_w=0.012, crack_len=0.7, edge_px=8.0, back_col="#B400FF", back_mul=0.62, back_mode=1, string_px=12.0,
                     string_dull="#FF0000", string_hot="#4B00FF", string_dark="#231F20",
                     # ROUND SIX (2026-09-22, Dennis on the r5 export: "the red-orange is good, but yellow isn't, violet is good too";
                     # seconds 15 and 19 - the saturated cyan and blue on the twist - "have the prettiest colours"). Measured on the r5
                     # file: the rest yellow's interior was (209, 186, 92), a mustard at saturation 0.57, while the stop is #FFE000. Two
                     # leaks: the duotone mixed the FIXED dark-violet shadow (#3C0078) into every stop wherever the plate's posterised
                     # luminance is below 1 (the wall reads 0.6), and yellow is the one stop a violet shadow turns to mud (red, cyan, blue
                     # and violet keep their hue against it); and filt 0.75 let a quarter of the plate's white light through the sheet,
                     # which desaturates the brightest stop most (yellow at J 1 sits at milk 0.41). Now: the shadow is the sheet's own
                     # colour darkened (`shadow_mode=hue`, `shadow_k` 0.22 in linear light: the dark of a yellow gel is a dark gold, of a
                     # cyan gel a deep teal), and the plate enters only through its posterised luminance (`filt` 1.0). The look's
                     # constants are assumed, judged on his screen at seconds 12, 15, 19 and 32.
                     shadow_mode="hue", shadow_k=0.22, filt=1.0),
}


def ramp_stops(look, jstar, step_at=None):
    """The look's strain ramp as [(J, hex)], the stops written 'J*' or 'J*+0.6' resolved against the model's threshold. A look without
    a `ramp` (dough, violet: rounds one and two) is expressed as its cream -> warm heat ramp (smoothstep(heat_lo, J* + 0.8) in the shader
    was cream to warm; the piecewise-linear ramp below is the same two colours at the same ends)."""
    if "ramp" not in look: return [(0.0, look["cream"]), (look["heat_lo"], look["cream"]), (jstar + 0.8, look["warm"])]
    out = []
    for j, c in look["ramp"]:
        if isinstance(j, str): j = jstar + float(j[2:] or 0) if j.startswith("J*") else float(j)
        out.append((float(j), c))
    if step_at is not None:
        # round four's step modes (step | dither | cornsweet): a hard step INSERTED into the fade at `step_at`: the stop below it holds
        # its colour up to the step and the stop above starts there (two stops at one J; the shader and ramp_rgb read a zero-width
        # segment as an edge). A ramp that already carries a step has it moved instead. With no step_at the ramp is the plain fade
        # (2026-09-22, the shipped state).
        ks = [k for k in range(len(out) - 1) if abs(out[k + 1][0] - out[k][0]) < 1e-9 and out[k][1] != out[k + 1][1]]
        if ks:
            for k in ks: out[k] = (float(step_at), out[k][1]); out[k + 1] = (float(step_at), out[k + 1][1])
        else:
            k = max([k for k in range(len(out) - 1) if out[k][0] < step_at <= out[k + 1][0]] or [0])
            out = out[:k + 1] + [(float(step_at), out[k][1]), (float(step_at), out[k + 1][1])] + out[k + 1:]
    return out


def ramp_step(stops):
    """(J, hex_before, hex_after) of the ramp's first hard step, or None."""
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        if abs(b - a) < 1e-9 and ca != cb: return a, ca, cb
    return None


def _lin_to_srgb(c):
    c = np.clip(c, 0.0, 1.0); return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def ramp_rgb(stops, J):
    """The ramp's sRGB colour (r, g, b) 0..255 at J, piecewise-linear between the stops IN LINEAR LIGHT (as the shader mixes them),
    clamped at the ends (for the panel and the strings)."""
    cols = [srgb_to_lin(np.array(hex_to_rgb01(c))) for _, c in stops]; js = [j for j, _ in stops]
    if J <= js[0]: c = cols[0]
    else:
        c = cols[-1]
        for (a, ca), (b, cb) in zip(zip(js[:-1], cols[:-1]), zip(js[1:], cols[1:])):
            if a <= J <= b: u = (J - a) / max(b - a, 1e-9); c = ca * (1 - u) + cb * u; break
    return tuple(int(round(v)) for v in _lin_to_srgb(c) * 255)


def ramp_check(stops, n=400, sat_min=0.2, green=(75.0, 165.0)):
    """The rule "no green" made a check: the ramp sampled at n points from its first stop to its last, each sample's hue (degrees) and
    saturation; a sample is green when its hue is inside `green` and its saturation is above `sat_min` (a pale or grey sample has no
    hue to speak of). Returns (n_green, [(J, hex)] of the green samples); prints the verdict."""
    import colorsys
    js = np.linspace(stops[0][0], stops[-1][0], n); bad = []; pale = []
    for J in js:
        r, g, b = ramp_rgb(stops, float(J)); h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if green[0] <= 360 * h <= green[1] and s > sat_min: bad.append((float(J), f"#{r:02X}{g:02X}{b:02X}", s))
        elif s <= sat_min and v > 0.85: pale.append((float(J), f"#{r:02X}{g:02X}{b:02X}"))     # a white band (his note on the neutral bridge, 2026-09-19)
    print("strain ramp (J -> colour): " + ", ".join(f"{j:.2f} {c}" for j, c in stops))
    steps = [(a, ca, cb) for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]) if abs(b - a) < 1e-9 and ca != cb]
    if steps: print("  hard steps (no mix): " + ", ".join(f"{ca} -> {cb} at J {a:.2f}" for a, ca, cb in steps))
    if bad:
        smax = max(x[2] for x in bad)
        print(f"  green-hued samples on the ramp: {len(bad)} of {n}, J {bad[0][0]:.3f}..{bad[-1][0]:.3f} (e.g. {bad[0][1]}; saturation at most {smax:.2f}): "
              + ("the yellow -> cyan fade's middle (no stop is green; the mix of the two lights is)" if not steps else "fix the stops"))
    else: print(f"  no green hue on the ramp ({n} samples, hue {green[0]:.0f}-{green[1]:.0f} deg at saturation > {sat_min} counts as green)")
    if pale: print(f"  pale samples on the ramp (saturation <= {sat_min} at value > 0.85): {len(pale)} of {n}, J {pale[0][0]:.3f}..{pale[-1][0]:.3f} (e.g. {pale[0][1]}): "
                   + ("the fade's middle, where the two lights cancel" if not steps else "a white stop: fix the stops"))
    else: print("  no white on the ramp (saturation <= 0.2 at value > 0.85)")
    return len(bad), bad

VS = """
#version 330
uniform vec2 size;
in vec2 in_pos; in vec2 in_uv; in float in_J;
out vec2 v_uv; out float v_J;
void main() {
    v_uv = in_uv; v_J = in_J;
    gl_Position = vec4(2.0 * in_pos.x / size.x - 1.0, 2.0 * in_pos.y / size.y - 1.0, 0.0, 1.0);   // row 0 = image top (studio.gl's convention)
}
"""

FS = """
#version 330
uniform sampler2D plate;      // BGR8 of the frame, row 0 = image top
uniform sampler2D sdf;        // R32F at half resolution: signed distance to the outline in px (+ inside)
uniform vec2 size;
uniform int n_holes;
uniform vec4 holes[32];       // rest cx, cy, radius (palms), seed
uniform vec3 cream, warm, hot, shadow_col, line_col, rim_light, back_col;
uniform float milk_k, milk_max, heat_lo, jstar, levels_lo, levels_hi, filt, grid_spacing, line_w, line_alpha, rim_w, crack_w, crack_len, edge_px, back_mul;
uniform int pattern, debug, front;   // front: 1 = only front-facing triangles draw (a folded-over layer is discarded), 0 = the reverse, -1 = both
uniform vec3 rcol[8]; uniform float rj[8]; uniform int n_ramp;   // the strain ramp (round three): the sheet's colour over J, piecewise-linear in linear light
uniform int back_mode;               // 0: the back face is back_col; 1: the ramp read at |J| (the underside carries its own stretch's colour)
uniform float fade;                  // the snap's fade (round three): multiplies the sheet's alpha
// yellow -> cyan with no green and no white (round four, 2026-09-19, Dennis: "try forcing an illusory gradient for yellow cyan"):
//   yc_mode 0  the ramp's hard step (two stops at one J)
//   yc_mode 1  STRIPES in rest space between yc_lo and yc_hi: bands of yc_period palms across the ribbon, the cyan share of each band
//              running 0 -> 1 with J, so the eye reads the yellow bars thinning into cyan as a gradient while every pixel is yellow or
//              cyan. The bands are COARSE on purpose: fine stripes fuse (in the eye, in the 720 downscale and in the encoder's 4:2:0
//              chroma average) to the additive mix of yellow and cyan, which IS green; only a visible grating is not
//   yc_mode 2  the step with a Cornsweet cusp: within yc_w of the step the yellow side darkens and the cyan side brightens by yc_amp,
//              the luminance ramp the eye reads as a gradient across the edge (Craik-O'Brien-Cornsweet); a scaled colour keeps its hue
uniform int yc_mode; uniform float yc_lo, yc_hi, yc_period, yc_amp, yc_w; uniform vec3 yc_a, yc_b;
uniform int shadow_mode; uniform float shadow_k;   // round six: 1 = the duotone's dark is the sheet's own colour x shadow_k (a coloured gel), 0 = shadow_col
// round six: the twisted ribbon SHADED as a helicoid. The model gives each hand's angle out of the image plane (heli_th); the width
// vector rotates uniformly along the length, so the face's normal at rest-space position s along the ribbon's axis makes the angle
// theta(s) = th0 + s (th1 - th0) with the view; a matte surface lit from the camera's side is bright face-on and dark edge-on
// (Lambert: |cos theta|). The lobes darken into the crossing and brighten again toward the flipped hand: the depth cue the
// projection alone lacks (round-four brief item 4). heli_k is the shading's depth (0 = off); the ends are the tips exactly.
uniform int heli_on; uniform float heli_th0, heli_th1, heli_k, heli_L; uniform vec2 heli_o, heli_ax;
in vec2 v_uv; in float v_J;
out vec4 o;

vec3 s2l(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 l2s(vec3 c) { c = clamp(c, 0.0, 1.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }
float hash1(float x) { return fract(sin(x * 127.1) * 43758.5453); }
vec3 ramp(float J) {
    if (J <= rj[0]) return rcol[0];
    for (int i = 1; i < n_ramp; i++) if (J <= rj[i]) return mix(rcol[i - 1], rcol[i], (J - rj[i - 1]) / max(rj[i] - rj[i - 1], 1e-6));
    return rcol[n_ramp - 1];
}
vec3 sheet_col(float J, float aa) {                       // the ramp, then the yellow -> cyan mode on top (aa: rest units per pixel)
    vec3 c = ramp(J);
    if (yc_mode == 1 && J > yc_lo && J < yc_hi) {
        float t = (J - yc_lo) / (yc_hi - yc_lo);              // the cyan duty cycle of the band under this fragment
        float sc = fract(v_uv.x / yc_period);                 // the band coordinate: lines of constant rest u, across the ribbon's length
        float e = max(aa / yc_period, 1e-4);                  // one pixel of anti-aliasing at the yellow | cyan boundary inside a band
        c = mix(yc_a, yc_b, smoothstep(1.0 - t - e, 1.0 - t + e, sc));
    } else if (yc_mode == 2) {
        float d = J - yc_hi;                                  // yc_hi is the step's J in this mode
        float k = 1.0 - smoothstep(0.0, yc_w, abs(d));
        c *= 1.0 + yc_amp * k * (d < 0.0 ? -1.0 : 1.0);
    }
    return c;
}

void main() {
    if (front >= 0 && (gl_FrontFacing != (front == 1))) discard;   // the folded-over layer of the mesh (2026-09-18: sawtooth slivers at a pinched hand)
    vec2 fc = gl_FragCoord.xy / size;
    vec3 P = s2l(texture(plate, fc).bgr);
    float d_out = texture(sdf, fc).r;                       // px, + inside the outline
    float cov = smoothstep(-1.0, 1.0, d_out);
    if (cov <= 0.0) { o = vec4(l2s(P), 1.0); return; }
    float Jc = clamp(v_J, -10.0, 10.0);                     // the model writes finite values; a fold gives J < 0, which reads as crushed
    float J = max(Jc, 0.02);
    float aa = length(fwidth(v_uv));                        // rest units per pixel: the anti-aliasing width in uv space
    float milk = 0.10 + milk_max * (1.0 - exp(-milk_k / J));   // capped: a crushed sheet is folds and air, not a wall (it hid his face at the
                                                                 // thumbs-up); floored: the thinnest dough still has a body of its own
    float heat = smoothstep(heat_lo, jstar + 0.8, Jc);       // the strain as a 0..1 scalar: drives the posterisation's levels and the pattern's fade
    float bk = 1.0 - smoothstep(-0.10, 0.0, Jc);            // the folded region of the map IS the ribbon's back face (round two, 2026-09-19: a hand
    vec3 front_c = sheet_col(J, aa);                         // flip reverses one end of the rest quad and the sheet twists half a turn); soft across the
    vec3 back_c = back_mode == 1 ? sheet_col(abs(Jc), aa) : back_col; // fold line, where the ribbon is edge-on, and off where J only wobbles about 0 (the line state).
    vec3 sheet = mix(front_c, back_c, bk);                   // The colour is the strain ramp (round three: the spectrum's order, red -> violet, no green)
    float lum = dot(P, vec3(0.2126, 0.7152, 0.0722));
    float levels = mix(levels_lo, levels_hi, heat);
    float q = floor(pow(lum, 0.8) * levels + 0.5) / levels;
    vec3 shcol = shadow_mode == 1 ? sheet * shadow_k : shadow_col;   // round six: the shadow keeps the sheet's hue
    vec3 duo = mix(shcol, sheet * 1.05, q);
    vec3 Pf = mix(P, duo, filt);
    vec3 col = mix(Pf, sheet, milk);
    // the pattern in rest space: the cells stretch with the material; lines thin as the sheet thins
    float lw = line_w / sqrt(max(J, 0.25));
    float line = 0.0;
    if (pattern == 1) {
        vec2 g = abs(fract(v_uv / grid_spacing) - 0.5) * grid_spacing;
        float d = min(g.x, g.y);
        line = 1.0 - smoothstep(0.5 * lw, 0.5 * lw + aa, d);
    } else if (pattern == 2) {
        float rho = length(v_uv); float th = atan(v_uv.y, v_uv.x);
        float dth = 6.2831853 / 16.0; float a = mod(th, dth) - 0.5 * dth;
        float ds = abs(rho * sin(a)); float dr = abs(fract(rho / grid_spacing) - 0.5) * grid_spacing;
        line = max(1.0 - smoothstep(0.5 * lw, 0.5 * lw + aa, ds), 1.0 - smoothstep(0.5 * lw, 0.5 * lw + aa, dr));
    }
    col = mix(col, line_col, line * line_alpha * (1.0 - 0.5 * heat) * smoothstep(0.25, 0.6, J));   // the lines fade where the material is crushed
    // holes: nearest hole edge in rest space, a noisy radius, the rim, the cracks
    float dmin = 1e9; vec2 nrm = vec2(0.0, -1.0); float crack = 0.0;
    for (int i = 0; i < n_holes; i++) {
        vec4 h = holes[i];
        if (h.z <= 0.0) continue;
        vec2 rel = v_uv - h.xy; float rho = length(rel); float th = atan(rel.y, rel.x);
        float rr = h.z * (1.0 + 0.10 * sin(5.0 * th + h.w) + 0.05 * sin(9.0 * th + 2.0 * h.w));
        float d = rho - rr;
        if (d < dmin) { dmin = d; nrm = rel / max(rho, 1e-6); }
        // cracks: 4 radial creases from the rim outward, their length a fraction of the radius, fading to the tip
        for (int k = 0; k < 4; k++) {
            float ak = h.w + 1.5707963 * float(k) + 0.6 * (hash1(h.w + float(k)) - 0.5);
            float perp = abs(rho * sin(th - ak));
            float along = rho - rr;                             // distance beyond the rim along the crease
            float len = crack_len * h.z + 0.05;
            float t = along / len;
            if (t > -0.15 && t < 1.0 && cos(th - ak) > 0.0) {
                float w = crack_w * (1.0 - 0.6 * max(t, 0.0));
                crack = max(crack, (1.0 - smoothstep(0.5 * w, 0.5 * w + aa, perp)) * (1.0 - max(t, 0.0)));
            }
        }
    }
    float hole = 0.0, rim = 0.0;
    if (n_holes > 0 && dmin < 1e8) {
        hole = 1.0 - smoothstep(0.0, aa, dmin);
        rim = (1.0 - smoothstep(0.0, rim_w, dmin)) * step(0.0, dmin);
        float shade = 0.5 + 0.5 * dot(nrm, normalize(vec2(-0.5, -0.85)));   // lit from the upper left (y down)
        vec3 rimcol = mix(hot, rim_light, 0.35) * (0.7 + 0.6 * shade);      // the tear's rolled edge: hot, lit on top
        col = mix(col, rimcol, rim * (0.6 + 0.4 * milk));
    }
    col *= 1.0 - 0.55 * crack;
    col *= mix(1.0, back_mul, bk);                           // the underside, in the room's light, is darker (assumed, judged on his screen)
    if (heli_on == 1) {                                      // round six: the helicoid's Lambert shading along the ribbon's rest axis
        float sN = clamp(dot(v_uv - heli_o, heli_ax) / heli_L, 0.0, 1.0);
        float thN = heli_th0 + sN * (heli_th1 - heli_th0);
        col *= mix(1.0, abs(cos(thN)), heli_k);
    }
    float edge = 1.0 - smoothstep(0.0, edge_px, d_out);
    col *= 1.0 - 0.22 * edge;
    if (debug == 1) {                                        // the strain field: blue (compressed) -> grey (rest) -> red (stretched)
        vec3 dc = v_J < 1.0 ? mix(vec3(0.1, 0.2, 0.9), vec3(0.5), clamp(v_J, 0.0, 1.0)) : mix(vec3(0.5), vec3(0.95, 0.1, 0.05), clamp((v_J - 1.0) / 1.0, 0.0, 1.0));
        vec2 g = abs(fract(v_uv / 0.25) - 0.5) * 0.25; float gline = 1.0 - smoothstep(0.008, 0.008 + aa, min(g.x, g.y));
        col = mix(dc, vec3(0.0), gline * 0.8);
    }
    float alpha = cov * (1.0 - hole) * fade;
    o = vec4(l2s(mix(P, col, alpha)), 1.0);
}
"""

BLIT_VS = """
#version 330
in vec2 in_pos; out vec2 v_t;
void main() { v_t = 0.5 * in_pos + 0.5; gl_Position = vec4(in_pos, 0.0, 1.0); }
"""
BLIT_FS = """
#version 330
uniform sampler2D plate; in vec2 v_t; out vec4 o;
void main() { o = vec4(texture(plate, v_t).bgr, 0.0); }      // alpha 0 = nothing drawn here yet (the fill pass reads it)
"""

# the fill pass: a pixel inside the outline that no front-facing triangle covered is material that folded away
# or bunched (a pinched hand crushes a palm of rest sheet onto one point): paint it as crushed dough.
# 2026-09-19 late night (Dennis: "some inside doesn't touch the lines"): the MLS interior is pinned to the tips and to six samples of
# every string, so between the samples its boundary falls short of the drawn string by a few pixels, and the fill painted that gap in
# the crushed colour (a red seam along a yellow or blue sheet). Now an uncovered pixel inside the outline takes the colour of the
# NEAREST drawn pixel within `ext_px` (16 rings of 8 samples), so the material reaches the line in its own colour; only where nothing
# is drawn within that radius (the crushed pinch) does the crushed colour paint.
FILL_FS = """
#version 330
uniform sampler2D color; uniform sampler2D plate; uniform sampler2D sdf;
uniform vec3 cream; uniform float edge_px; uniform float fade; uniform float ext_px;
in vec2 v_t; out vec4 o;
vec3 s2l(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 l2s(vec3 c) { c = clamp(c, 0.0, 1.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }
void main() {
    vec4 c = texture(color, v_t);
    if (c.a > 0.5) { o = vec4(c.rgb, 1.0); return; }
    float d = texture(sdf, v_t).r; float cov = smoothstep(-1.0, 1.0, d) * fade;
    if (cov <= 0.0) { o = vec4(c.rgb, 1.0); return; }
    vec2 px = 1.0 / vec2(textureSize(color, 0));
    vec3 near = vec3(-1.0);
    for (int r = 1; r <= 16 && near.x < 0.0; r++) {
        float rr = ext_px * float(r) / 16.0;
        for (int k = 0; k < 8; k++) {
            float a = 0.7853982 * float(k) + 0.3926991 * float(r % 2);
            vec4 s = texture(color, v_t + rr * vec2(cos(a), sin(a)) * px);
            if (s.a > 0.5) { near = s.rgb; break; }
        }
    }
    vec3 Ps = texture(plate, v_t).bgr;
    if (near.x >= 0.0) { o = vec4(mix(Ps, near, cov), 1.0); return; }      // the material's own colour, carried to the line
    vec3 P = s2l(Ps);
    vec3 col = mix(P, cream, 0.72) * (1.0 - 0.22 * (1.0 - smoothstep(0.0, edge_px, d)));
    o = vec4(l2s(mix(P, col, cov)), 1.0);
}
"""


def lin(hexcol):
    return tuple(float(x) for x in srgb_to_lin(np.array(hex_to_rgb01(hexcol))))


class WebRenderer:
    def __init__(self, W, H, look, pattern, filt, debug, front=1, jstar=1.15, yc=None, shadow_mode="fixed", shadow_k=0.22):
        """yc: the yellow -> cyan mode (round four): dict(mode=step|dither|cornsweet, period=<palms>, amp, w, lo, step) or None (= step)."""
        self.W, self.H = W, H; self.look = look; yc = dict(yc or {}); mode = yc.get("mode", "fade")   # fade (2026-09-22, shipped) | step | dither | cornsweet
        self.gl = sgl.GL(); ctx = self.gl.ctx
        self.prog = ctx.program(vertex_shader=VS, fragment_shader=FS)
        self.blit = ctx.program(vertex_shader=BLIT_VS, fragment_shader=BLIT_FS)
        self.blit_vao = self.gl.fullscreen_vao(self.blit)
        self.fill = ctx.program(vertex_shader=BLIT_VS, fragment_shader=FILL_FS)
        self.fill_vao = self.gl.fullscreen_vao(self.fill)
        self.plate = ctx.texture((W, H), 3, dtype="f1"); self.plate.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.sdf = ctx.texture((W // 2, H // 2), 1, dtype="f4"); self.sdf.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.color = ctx.texture((W, H), 4, dtype="f1"); self.fbo = ctx.framebuffer(color_attachments=[self.color])
        self.color2 = ctx.texture((W, H), 4, dtype="f1"); self.fbo2 = ctx.framebuffer(color_attachments=[self.color2])
        self.vbo = None; self.ibo = None; self.vao = None
        self.prog["size"].value = (float(W), float(H)); self.prog["plate"].value = 0; self.prog["sdf"].value = 1; self.blit["plate"].value = 0
        self.front = int(front); self.prog["front"].value = self.front
        self.fill["color"].value = 2; self.fill["plate"].value = 0; self.fill["sdf"].value = 1; self.fill["cream"].value = lin(look.get("fill", look["cream"])); self.fill["edge_px"].value = float(look["edge_px"])
        def setu(k, v):                                                    # a uniform the compiler optimised out (cream, warm: replaced by the ramp) is absent
            try: self.prog[k].value = v
            except KeyError: pass
        for k in ("cream", "warm", "hot", "shadow_col", "line_col", "rim_light", "back_col"): setu(k, lin(look[k]))
        for k in ("milk_k", "milk_max", "heat_lo", "levels_lo", "levels_hi", "grid_spacing", "line_w", "line_alpha", "rim_w", "crack_w", "crack_len", "edge_px", "back_mul"):
            setu(k, float(look[k]))
        self.prog["filt"].value = float(filt); self.prog["pattern"].value = {"none": 0, "grid": 1, "web": 2}[pattern]; self.prog["debug"].value = int(debug)
        setu("shadow_mode", 1 if shadow_mode == "hue" else 0); setu("shadow_k", float(shadow_k))   # round six
        setu("heli_on", 0); setu("heli_k", 0.0); self.setu = setu
        print(f"  the duotone's shadow: {'the sheet''s own colour x ' + format(shadow_k, '.2f') + ' (a coloured gel)' if shadow_mode == 'hue' else 'the fixed ' + look['shadow_col']}; "
              f"the plate's light through the sheet: {100 * (1 - filt):.0f} % (filt {filt})")
        # the stripe mode ends its zone at the step: the step moves to J* so the zone yc_lo (the yellow stop) .. J* is the handoff's
        # "duty cycle 1 -> 0 over J 1.0 -> J*"; the other modes keep the look's step (J* - 0.1)
        # the fade (the default) takes the look's ramp as it is; the step modes insert their step at yc_step= (default J* - 0.1, round
        # four's value; the stripe mode's step sits at J* so its zone runs from the yellow stop to J*)
        step_at = float(yc["step"]) if "step" in yc else (jstar if mode == "dither" else (jstar - 0.1 if mode in ("step", "cornsweet") else None))
        stops = ramp_stops(look, jstar, step_at); self.stops = stops; st = ramp_step(stops)
        assert len(stops) <= 8, "the shader holds 8 ramp stops"
        self.yc = dict(mode=mode, lo=float(yc.get("lo", 1.0)), hi=(st[0] if st else jstar), period=float(yc.get("period", 0.15)), amp=float(yc.get("amp", 0.25)), w=float(yc.get("w", 0.06)))
        setu("yc_mode", {"fade": 0, "step": 0, "dither": 1, "cornsweet": 2}[mode]); setu("yc_lo", self.yc["lo"]); setu("yc_hi", self.yc["hi"])
        setu("yc_period", self.yc["period"]); setu("yc_amp", self.yc["amp"]); setu("yc_w", self.yc["w"])
        if st: setu("yc_a", lin(st[1])); setu("yc_b", lin(st[2]))
        rc = np.zeros((8, 3), np.float32); rjv = np.zeros(8, np.float32)
        for k, (j, c) in enumerate(stops[:8]): rc[k] = lin(c); rjv[k] = j
        self.prog["rcol"].write(rc.tobytes()); self.prog["rj"].write(rjv.tobytes()); self.prog["n_ramp"].value = min(len(stops), 8)
        self.prog["back_mode"].value = int(look.get("back_mode", 0)); self.prog["fade"].value = 1.0; self.fill["fade"].value = 1.0
        self.fill["ext_px"].value = float(look.get("ext_px", 40.0))
        ramp_check(stops)
        if mode == "dither": print(f"  yellow -> cyan by STRIPES in rest space: zone J {self.yc['lo']:.2f} -> {self.yc['hi']:.2f} (cyan duty 0 -> 1), period {self.yc['period']:.3f} palm")
        elif mode == "cornsweet": print(f"  yellow -> cyan by a Cornsweet cusp at J {self.yc['hi']:.2f}: amplitude {self.yc['amp']:.2f} over {self.yc['w']:.2f} J on each side")
        elif mode == "step": print(f"  yellow -> cyan by the hard step at J {self.yc['hi']:.2f}")
        else: print("  yellow -> cyan by the plain fade (linear light) between their stops")
        if "ramp" in look:                                  # the one scale, read twice (2026-09-22, his "looser, further down until red; tighter, further up until violet")
            print("  the same ramp on the sheet and on the lines: " + ", ".join(f"{c} at J {j:.2f} = line stretch {np.sqrt(max(j, 0)):.2f}" for j, c in stops))

    def mesh(self, Gy, Gx):
        idx = []
        for y in range(Gy - 1):
            for x in range(Gx - 1):
                a = y * Gx + x; b = a + 1; c = a + Gx; d = c + 1
                idx += [a, b, c, b, d, c]
        self.ibo = self.gl.ctx.buffer(np.array(idx, np.int32).tobytes())
        self.vbo = self.gl.ctx.buffer(reserve=Gy * Gx * 5 * 4)
        self.vao = self.gl.ctx.vertex_array(self.prog, [(self.vbo, "2f 2f 1f", "in_pos", "in_uv", "in_J")], self.ibo)

    def render(self, frame_bgr, verts, sdf_half, holes, jstar, fade=1.0, heli=None):
        """frame_bgr (H, W, 3) uint8; verts (Gy*Gx, 5) float32 [x, y, u, v, J]; sdf_half (H/2, W/2) float32 px; holes (N, 4); fade the sheet's alpha;
        heli (th0, th1, k, o, ax, L) the helicoid's shading for this frame (round six) or None."""
        self.gl.make_current(); ctx = self.gl.ctx
        if heli is None: self.setu("heli_on", 0)
        else:
            th0, th1, k, o, ax, L = heli
            self.setu("heli_on", 1); self.setu("heli_th0", float(th0)); self.setu("heli_th1", float(th1)); self.setu("heli_k", float(k))
            self.setu("heli_o", (float(o[0]), float(o[1]))); self.setu("heli_ax", (float(ax[0]), float(ax[1]))); self.setu("heli_L", float(L))
        self.plate.write(np.ascontiguousarray(frame_bgr).tobytes()); self.sdf.write(np.ascontiguousarray(sdf_half, np.float32).tobytes())
        self.fbo.use(); ctx.disable(moderngl.DEPTH_TEST); ctx.disable(moderngl.BLEND)
        self.plate.use(0); self.sdf.use(1)
        self.blit_vao.render(moderngl.TRIANGLES)
        self.vbo.write(np.ascontiguousarray(verts, np.float32).tobytes())
        h = np.zeros((32, 4), np.float32); n = min(len(holes), 32); h[:n] = holes[:n]
        self.prog["holes"].write(h.tobytes()); self.prog["n_holes"].value = n; self.prog["jstar"].value = float(jstar)
        self.prog["fade"].value = float(fade); self.fill["fade"].value = float(fade)
        if self.front < 0:
            self.prog["front"].value = -1; self.vao.render(moderngl.TRIANGLES)
        else:                                                    # the folded layer first, the facing layer over it: where the mesh
            self.prog["front"].value = 1 - self.front; self.vao.render(moderngl.TRIANGLES)     # accordions at a pinch the facing layer wins
            self.prog["front"].value = self.front; self.vao.render(moderngl.TRIANGLES)         # wherever it exists and the other fills its gaps
                                                                                               # (culling alone left cream/amber stripes, 2026-09-18)
        self.fbo2.use(); self.color.use(2); self.plate.use(0); self.sdf.use(1)    # the fill pass: crushed dough where the outline is not covered
        self.fill_vao.render(moderngl.TRIANGLES)
        buf = self.fbo2.read(components=3, dtype="f1")
        return np.frombuffer(buf, np.uint8).reshape(self.H, self.W, 3)[..., ::-1].copy()     # the fbo holds RGB; back to BGR


def outline_sdf(poly_px, W, H):
    """Signed distance (px, + inside) to the closed outline polyline, at half resolution."""
    m = np.zeros((H // 2, W // 2), np.uint8)
    cv2.fillPoly(m, [np.round(np.clip(poly_px / 2.0, -4000, 4000)).astype(np.int32)], 255)
    if not m.any(): return np.full(m.shape, -1e4, np.float32), m               # the sheet is off screen (fallen): no coverage anywhere
    inside = cv2.distanceTransform(m, cv2.DIST_L2, 5); outside = cv2.distanceTransform(255 - m, cv2.DIST_L2, 5)
    return np.clip(inside - outside, -1e4, 1e4) * 2.0, m


def polyline_crossing(a, b):
    """The image point where polylines a and b (m, 2) cross (their first segment pair that intersects), or None."""
    for i in range(len(a) - 1):
        p, r = a[i], a[i + 1] - a[i]
        for j in range(len(b) - 1):
            q, s = b[j], b[j + 1] - b[j]
            den = r[0] * s[1] - r[1] * s[0]
            if abs(den) < 1e-9: continue
            qp = q - p; t = (qp[0] * s[1] - qp[1] * s[0]) / den; u = (qp[0] * r[1] - qp[1] * r[0]) / den
            if 0 <= t <= 1 and 0 <= u <= 1: return p + t * r
    return None


def draw_strings(img, strings, tension, n_hull, look, string_px, shadow, near=-1, fade=1.0, xsig=60.0, xgain=0.12, stretch=None, stops=None, xmode="pinch", xtaper=0.7):
    """The outline's edges: a soft offset shadow, a dark base, a core coloured by tension and thinner as it stretches.
    Round three: at a crossing (`near` = the ring index of the nearer long edge, from the model) the far edge is drawn first, then the
    near edge with its own shadow over it, so the two never pass through each other; the near edge widens and the far one narrows by
    `xgain` within a Gaussian of `xsig` px of the crossing (the ribbon is edge-on there: one edge is a ribbon's width nearer the camera,
    the perspective of that depth; assumed). `fade` blends the whole drawing over the image (the snap).
    Second pass (2026-09-19 late night): with `stretch` (the edge's linear stretch lambda = span / rest, from the model) and `stops`
    (the look's ramp) the core is the SHEET'S ramp read at lambda^2, so a slack line is red -> orange, a line at rest yellow, a taut one
    cyan -> blue -> violet, the same scale the material beside it wears; without them the round-two dull -> hot lerp over tension."""
    dull = np.array(hex_to_rgb01(look["string_dull"])[::-1]) * 255; hot = np.array(hex_to_rgb01(look["string_hot"])[::-1]) * 255
    dark = tuple(int(x) for x in np.array(hex_to_rgb01(look["string_dark"])[::-1]) * 255)
    polys = []
    for k in range(n_hull):
        p = strings[k]
        if np.isnan(p).any(): continue
        t = float(np.clip(tension[k] / 0.5, 0, 1))
        w = string_px - 2.0 * t
        if stretch is not None and stops is not None: col = tuple(int(x) for x in ramp_rgb(stops, float(stretch[k]) ** 2)[::-1])
        else: col = tuple(int(x) for x in dull * (1 - t) + hot * t)
        polys.append((k, p.astype(np.float64), w, col))
    if not polys: return img
    src = img
    img = img.copy() if fade < 1.0 else img
    far = (near + 2) % n_hull if near >= 0 and n_hull == 4 else -1
    x = None
    if near >= 0 and far >= 0:
        pn = [p for k, p, _, _ in polys if k == near]; pf = [p for k, p, _, _ in polys if k == far]
        if pn and pf: x = polyline_crossing(pn[0], pf[0])
    # ROUND FOUR (2026-09-19, Dennis: "the crossing is a pinch point, not one line drawn over the other"): xmode="pinch" makes the two long
    # edges (ring edges 0 and 2) MEET at their crossing or at their closest approach when it is under 1.5 widths (the model's contact fold
    # brings them to one point there): both taper by `xtaper` within `xsig` px of that point and are drawn in ring order with one shadow,
    # so the rods converge into the point as a ribbon's edges do where it is edge-on. xmode="occlude" is round three's near-over-far draw.
    taper = None
    if xmode == "pinch" and n_hull == 4:
        lp = {k: p for k, p, _, _ in polys if k in (0, 2)}
        if len(lp) == 2:
            xc = polyline_crossing(lp[0], lp[2])
            if xc is None:
                d = np.linalg.norm(lp[0][:, None] - lp[2][None], axis=-1); ka, kb = np.unravel_index(d.argmin(), d.shape)
                if d[ka, kb] < 1.5 * string_px: xc = 0.5 * (lp[0][ka] + lp[2][kb])
            if xc is not None: taper = xc; near = -1; far = -1; x = None

    def pieces(k, p, w):
        """(int polyline, width) pieces of one edge: a single piece, or split at the crossing into widths modulated by the depth cue."""
        if taper is not None and k in (0, 2):
            d = np.linalg.norm(p - taper, axis=1); g = -xtaper * np.exp(-0.5 * (d / xsig) ** 2)
            return [(np.round(p[i:i + 2]).astype(np.int32).reshape(-1, 1, 2), max(int(round(w * (1 + 0.5 * (g[i] + g[i + 1])))), 1)) for i in range(len(p) - 1)]
        if x is None or k not in (near, far): return [(np.round(p).astype(np.int32).reshape(-1, 1, 2), int(round(w)))]
        d = np.linalg.norm(p - x, axis=1); g = np.exp(-0.5 * (d / xsig) ** 2) * (xgain if k == near else -xgain)
        out = []
        for i in range(len(p) - 1):
            wi = w * (1 + 0.5 * (g[i] + g[i + 1]))
            out.append((np.round(p[i:i + 2]).astype(np.int32).reshape(-1, 1, 2), max(int(round(wi)), 1)))
        return out

    def shade(target, sel):
        sh = np.zeros(target.shape[:2], np.uint8)
        for k, p, w, _ in sel:
            for q, wi in pieces(k, p, w): cv2.polylines(sh, [q + np.array([3, 4])], False, 255, wi + 2, cv2.LINE_AA)
        sh = cv2.GaussianBlur(sh, (0, 0), 2.5).astype(np.float32) / 255.0 * shadow * 1.6
        return (target * (1 - sh[..., None])).astype(np.uint8)

    def stroke(target, sel):
        for k, p, w, _ in sel:
            for q, wi in pieces(k, p, w): cv2.polylines(target, [q], False, dark, wi + 2, cv2.LINE_AA)
        for k, p, w, col in sel:
            for q, wi in pieces(k, p, w): cv2.polylines(target, [q], False, col, wi, cv2.LINE_AA)
        return target

    first = [e for e in polys if e[0] != near]; last = [e for e in polys if e[0] == near]
    if shadow > 0: img = shade(img, polys)
    img = stroke(img, first)
    if last:
        if shadow > 0 and x is not None: img = shade(img, last)      # the near edge's shadow falls on the far edge at the crossing
        img = stroke(img, last)
    if fade < 1.0: img = (src.astype(np.float32) * (1 - fade) + img.astype(np.float32) * fade + 0.5).astype(np.uint8)
    return img


def sheet_shadow(img, mask_half, shadow, offset=(14, 22), sigma=10):
    """The sheet's soft shadow on the plate outside its outline (a translucent sheet: 0.6 of `shadow`)."""
    if shadow <= 0: return img
    H, W = img.shape[:2]
    m = np.zeros_like(mask_half); dy, dx = offset[1] // 2, offset[0] // 2
    m[dy:, dx:] = mask_half[:mask_half.shape[0] - dy, :mask_half.shape[1] - dx]
    m = cv2.GaussianBlur(m.astype(np.float32) / 255.0, (0, 0), sigma / 2.0) * (1 - mask_half.astype(np.float32) / 255.0)
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR) * (0.6 * shadow)
    return (img * (1 - m[..., None])).astype(np.uint8)


def main():
    video, mem_npz, matte_path, out = sys.argv[1:5]
    kw = dict(a.split("=", 1) for a in sys.argv[5:])
    look = LOOKS[kw.get("look", "dough")]; pattern = kw.get("pattern", "grid"); filt = float(kw.get("filt", look.get("filt", 0.75)))
    shadow_mode = kw.get("shadow_mode", look.get("shadow_mode", "fixed")); shadow_k = float(kw.get("shadow_k", look.get("shadow_k", 0.22)))   # round six
    heli_k = float(kw.get("heli_k", 0.55)) if int(kw.get("heli", 1)) else 0.0                                                             # round six
    shadow = float(kw.get("shadow", 0.18)); debug = int(kw.get("debug", 0)); string_px = float(kw.get("string_px", look["string_px"])); fps = float(kw.get("fps", 30))
    front = int(kw.get("front", 1))                    # which facing of the mesh draws (1 front, 0 back, -1 both): see FS
    xmode = kw.get("xmode", "pinch"); xtaper = float(kw.get("xtaper", 0.7))   # round four: the crossing as a pinch point (both edges taper into it) | occlude
    yc = {k[3:]: v for k, v in kw.items() if k.startswith("yc_")}   # yc_mode=step|dither|cornsweet yc_period=<palms> yc_amp= yc_w= yc_step= (round four)
    M = np.load(mem_npz); params = json.loads(str(M["params"])); jstar = params["jstar"]
    valid = M["valid"]; released = M["released"]; grid_px = M["grid_px"]; grid_J = M["grid_J"]; grid_uv = M["grid_uv"]
    n_hull = M["n_hull"]; strings = M["strings_px"]; tension = M["tension"]; holes_r = M["holes_r"]; defects = M["defects"]; thr = M["thr"]
    snap_f = M["snap_f"] if "snap_f" in M.files else np.ones(len(valid), np.float32)   # round two: the snap's contraction thins the edge with the sheet
    snap_mode = params.get("snap_mode", "contract")                                  # round three: `fade` makes snap_f the sheet's and the strings' alpha
    near_edge = M["near_edge"] if "near_edge" in M.files else np.full(len(valid), -1, np.int8)   # round three: the nearer long edge at a crossing
    if "stretch" in M.files: stretch = M["stretch"]                                          # second pass: the edges' linear stretch (the lines' colour)
    else:
        with np.errstate(all="ignore"): stretch = np.where(M["slack"] > 1e-6, M["span"] / np.maximum(M["span"] + M["slack"], 1e-9), 1.0 + tension)
        stretch = np.clip(np.nan_to_num(stretch, nan=1.0), 0, 10).astype(np.float32)
    lines_on_ramp = "ramp" in look                                                             # the lines wear the sheet's ramp when the look has one
    n, Gy, Gx = grid_J.shape
    cap = cv2.VideoCapture(video); W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); nv = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    matte = None if matte_path == "none" else np.load(matte_path, mmap_mode="r")
    R = WebRenderer(W, H, look, pattern, filt, debug, front, jstar, yc, shadow_mode, shadow_k); R.mesh(Gy, Gx)
    # round six: the helicoid's shading needs the ribbon's axis in REST space (from hand 0's tips to hand 1's) and each hand's angle per frame
    heli_axis = None
    if heli_k > 0 and "heli_th" in M.files and params.get("twist", "none") == "helicoid":
        heli_th = M["heli_th"]; nm = params["names"]; RT = M["rest_tips"]
        m0 = 0.5 * (RT[nm.index("t0")] + RT[nm.index("i0")]); m1 = 0.5 * (RT[nm.index("t1")] + RT[nm.index("i1")])
        L_ = float(np.linalg.norm(m1 - m0)); heli_axis = (m0, (m1 - m0) / max(L_, 1e-9), L_)
        okf = np.isfinite(heli_th).all(1)
        print(f"  helicoid shading: depth {heli_k:.2f} (|cos theta| at the edge-on point), the rest axis {L_:.2f} palm long, angles on {int(okf.sum())} frames "
              f"(the darkest point on a bow-tie frame is {100 * (1 - heli_k):.0f} % of the face-on brightness)")
    elif heli_k > 0: print("  helicoid shading: off (no heli_th in the model file, or twist != helicoid)")
    if R.yc["mode"] == "dither":                        # the stripes' period on screen: must survive the 720 copy (x 2/3) and 4:2:0 (x 1/2) as a visible grating
        sc = float(np.nanmedian(M["scale"][valid])); print(f"  stripe period at the median scale ({sc:.0f} px/palm): {R.yc['period'] * sc:.0f} px at 1080, {R.yc['period'] * sc * 720 / W:.0f} px on the 720 copy")
    uv = grid_uv.reshape(-1, 2)
    seeds = np.random.default_rng(params["seed"]).uniform(0, 6.28, len(defects)).astype(np.float32)
    print(f"look {kw.get('look', 'dough')}, pattern {pattern}, filt {filt}, shadow {shadow}, strings {string_px} px, jstar {jstar}, snap {snap_mode}; {n} model frames, {nv} video frames, matte {'yes' if matte is not None else 'no'}; "
          f"crossings with a near edge on {int((near_edge >= 0).sum())} frames; the lines coloured by {'the ramp at stretch^2' if lines_on_ramp else 'tension (dull -> hot)'}")

    def frame(i, fr):
        if not (valid[i] or released[i]): return fr
        poly = strings[i, :n_hull[i]].reshape(-1, 2); poly = poly[~np.isnan(poly[:, 0])]
        if len(poly) < 3: return fr
        sdf, mask_half = outline_sdf(poly, W, H)
        verts = np.concatenate([grid_px[i].reshape(-1, 2), uv, grid_J[i].reshape(-1, 1)], 1).astype(np.float32)
        holes = np.stack([defects[:, 0], defects[:, 1], holes_r[i], seeds], 1)
        fade = float(snap_f[i]) if snap_mode == "fade" else 1.0
        heli = None
        if heli_axis is not None and np.isfinite(heli_th[i]).all():
            heli = (heli_th[i][0], heli_th[i][1], heli_k, heli_axis[0], heli_axis[1], heli_axis[2])
        img = R.render(fr, verts, sdf, holes, jstar, fade, heli=heli)
        img = sheet_shadow(img, mask_half, shadow * fade)
        img = draw_strings(img, strings[i], tension[i], int(n_hull[i]), look, string_px if snap_mode == "fade" else max(string_px * float(snap_f[i]), 2.0), shadow,
                           near=int(near_edge[i]), fade=fade, stretch=stretch[i] if lines_on_ramp else None, stops=R.stops if lines_on_ramp else None,
                           xmode=xmode, xtaper=xtaper)
        if matte is not None:
            a = np.asarray(matte[i]).astype(np.float32)[..., None] * (1 / 255.0)
            img = (img * (1 - a) + fr * a + 0.5).astype(np.uint8)
        return img

    if "preview" in kw:
        idx = [int(x) for x in kw["preview"].split(",")]; tiles = []
        for i in idx:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, fr = cap.read()
            t0 = time.time(); img = frame(i, fr); dt = time.time() - t0
            cv2.imwrite(out.replace(".mp4", f"_f{i:04d}.png"), img)
            t = cv2.resize(img, (W // 3, H // 3)); cv2.putText(t, f"{i} {i / fps:.1f}s J{M['J_global'][i]:.2f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3); tiles.append(t)
            print(f"  frame {i}: {dt * 1000:.0f} ms, holes open {(holes_r[i] > 0.04).sum()}, outline {n_hull[i]} tips")
        rows = [np.hstack(tiles[j:j + 4]) for j in range(0, len(tiles), 4)]
        w = max(r.shape[1] for r in rows)
        rows = [np.hstack([r, np.zeros((r.shape[0], w - r.shape[1], 3), np.uint8)]) if r.shape[1] < w else r for r in rows]
        cv2.imwrite(out.replace(".mp4", "_sheet.png"), np.vstack(rows)); print("preview written"); return

    t0_, t1_ = (int(x) for x in kw.get("trim", "214,1480").split(",")); t1_ = min(t1_, nv)
    enc = RawWriter(out, W, H, int(fps))                # video only: the upright master carries no audio track (made without one, 2026-09-18)
    cap.set(cv2.CAP_PROP_POS_FRAMES, t0_); t0 = time.time()
    for i in range(t0_, t1_):
        ok, fr = cap.read()
        if not ok: break
        enc.write(frame(i, fr))
        if (i - t0_) % 100 == 0: print(f"  frame {i} {(time.time() - t0) / (i - t0_ + 1):.3f} s/frame", flush=True)
    rc = enc.close(); print(f"wrote {out} ffmpeg exit {rc}: {enc.n} frames in {time.time() - t0:.1f} s")
    if "audio" in kw:                                   # the shot's own audio from the ORIGINAL, aligned to the trim (audio=web/originals/IMG_6268.MOV)
        tmp = out.replace(".mp4", ".mux.mp4"); mux_audio(out, kw["audio"], tmp, start=t0_ / fps, duration=enc.n / fps); os.replace(tmp, out)
    ok, err = decode_check(out); print("decode gate:", "OK" if ok else "FAILED " + err, "|", streams(out))   # a silent export passes the decode gate
    if kw.get("p720", "1") == "1":
        p = out.replace(".mp4", "-720.mp4"); preview_720(out, p); print("720 copy:", p)


if __name__ == "__main__":
    main()
