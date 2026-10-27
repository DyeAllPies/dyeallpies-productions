"""The finger web's fire (round two, 2026-09-19, Dennis): a violet flame out of each thumb at the thumbs-up, in the
video's palette, and the sting in the video's own style: the two flames leave the thumbs, meet, and light the
DyeAllPies wordmark letter by letter, then PRODUCTIONS and the URL as in the brand sting's beats (tools/brand/BRAND.md,
render_brand_sting.py: the layout and the neon composite are imported from there, so the two stings cannot drift).

The flame is a 2-D particle system in the SCENE's pixels (render_web_scene.py draws it over the composed frame, so it
can rise out of the app window), deterministic from its seed. Per frame each emitter spawns `rate` particles in a
small disc, each with an upward speed, a lifetime, and a size; every step adds buoyancy (hot air rises: a constant
upward acceleration), a lateral turbulence (a sine field drifting with time, the cheap stand-in for curl noise), and
drag. A particle's temperature is its remaining life: hot and small at the base, cool and large at the tip. The
particles are splatted as Gaussians into a density map and a temperature-weighted map at quarter resolution; the
colour is a ramp over the temperature in the puppet's violet palette (render_web.LOOKS["violet"], ported from
render_puppet.py: blue-violet #6900FF at the cool tip, electric violet #8F00FF, magenta #FF00E1, and the strings' pale
#CBA0FF as the hot core), the opacity 1 - exp(-k density).

On the daylit room the flame is composited by ALPHA (a saturated violet darker than the wall: luminance contrast,
item 09's rule, no bloom); on the black ground of the sting the same flame is added as emission with studio.glow's
bloom (BRAND.md: the glow stays on the dark ground).

The tail (`Sting`): frame j of the tail after the effect's last frame:
  0-14   the scene dips to black (a 15-frame fade; the puppet's outro precedent) while the two emitters fly from the
         thumbs to the wordmark's left end (ease-out), merging on the way
  15-27  the merged flame sweeps left to right along the wordmark's cap height and each letter lights as it passes
         (the brand's 10-22 beat: 4 frames per letter, 1.2 apart, with the white flash), the flame's rate fading to
         nothing over the last letters
  27-35  PRODUCTIONS tracks in and the tick draws in the boots' red (the brand's 22-30 beat)
  35-41  the URL fades in; then the hold to `n_tail` (default 90 frames, 3.0 s: the brand's 2.5 s plus the flight)
The wordmark sits at the brand's y = 900, inside the 270-1250 safe band; the black band above the app window (y < 393)
is under the platforms' UI, so the logo does not go there.

All numbers here are look choices (assumed), judged on Dennis's screen; the palette and the layout are ported.
"""
import os, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import render_brand_sting as bs
from studio import brand
from studio import glow as sglow
from studio.colour import srgb8_to_lin, lin_to_srgb8, hex_to_bgr8

# the ramp over temperature (0 = the tip, 1 = the base): the puppet's violets (render_web.LOOKS["violet"])
RAMP = [(0.00, "#3A0090"), (0.30, "#6900FF"), (0.55, "#8F00FF"), (0.80, "#FF00E1"), (1.00, "#CBA0FF")]
DOWN = 4                      # the splat maps' downsampling (quarter resolution: a 26 px particle is 6.5 texels)


def ramp_lut():
    lut = np.zeros((256, 3), np.float32)
    for k in range(256):
        t = k / 255
        for (a, ca), (b, cb) in zip(RAMP[:-1], RAMP[1:]):
            if a <= t <= b:
                u = (t - a) / (b - a); c0 = np.array(hex_to_bgr8(ca), np.float32); c1 = np.array(hex_to_bgr8(cb), np.float32)
                lut[k] = c0 * (1 - u) + c1 * u; break
    return lut


class Flame:
    """A particle flame in scene pixels. `emit(pos, strength)` per frame per emitter, then `step()`, then `render()`."""

    def __init__(self, W, H, seed=11, rate=110, life=(10, 22), speed=(3.0, 9.0), spread=6.0, size=(7.0, 14.0),
                 buoy=0.3, turb=2.8, drag=0.965, k_alpha=0.045, elong=2.6, wander=0.7, flicker=0.4):
        self.W, self.H = W, H; self.rng = np.random.default_rng(seed)
        self.rate, self.life, self.speed, self.spread, self.size = rate, life, speed, spread, size
        self.buoy, self.turb, self.drag, self.k_alpha = buoy, turb, drag, k_alpha
        self.elong, self.wander, self.flicker = elong, wander, flicker     # the splat's vertical stretch; a per-particle random walk; the rate's flutter
        self.pos = np.zeros((0, 2), np.float32); self.vel = np.zeros((0, 2), np.float32)
        self.age = np.zeros(0, np.float32); self.lifev = np.zeros(0, np.float32); self.sz = np.zeros(0, np.float32); self.phase = np.zeros(0, np.float32)
        self.t = 0; self.lut = ramp_lut()
        w, h = W // DOWN, H // DOWN
        self.yy, self.xx = np.mgrid[0:h, 0:w].astype(np.float32)

    def emit(self, pos, strength=1.0):
        r = self.rng
        n = int(round(self.rate * strength * r.uniform(1 - self.flicker, 1 + self.flicker)))   # a flame flutters: the feed is never steady
        if n <= 0: return
        ang = r.uniform(0, 2 * np.pi, n); rad = self.spread * np.sqrt(r.uniform(0, 1, n))
        p = np.stack([pos[0] + rad * np.cos(ang), pos[1] + rad * np.sin(ang) * 0.5], 1).astype(np.float32)
        v = np.stack([r.normal(0, 1.1, n), -r.uniform(*self.speed, n)], 1).astype(np.float32)
        self.pos = np.concatenate([self.pos, p]); self.vel = np.concatenate([self.vel, v])
        self.age = np.concatenate([self.age, np.zeros(n, np.float32)]); self.lifev = np.concatenate([self.lifev, r.uniform(*self.life, n).astype(np.float32)])
        self.sz = np.concatenate([self.sz, r.uniform(*self.size, n).astype(np.float32)]); self.phase = np.concatenate([self.phase, r.uniform(0, 6.28, n).astype(np.float32)])

    def step(self):
        if len(self.pos):
            self.vel[:, 1] -= self.buoy
            self.vel[:, 0] += self.turb * np.sin(self.pos[:, 1] * 0.035 + self.t * 0.9 + self.phase) * (self.age / self.lifev + 0.2)
            self.vel[:, 0] += self.rng.normal(0, self.wander, len(self.pos))       # the tongues separate: each particle wanders on its own
            self.vel *= self.drag
            self.pos += self.vel; self.age += 1
            keep = self.age < self.lifev
            self.pos, self.vel, self.age, self.lifev, self.sz, self.phase = (a[keep] for a in (self.pos, self.vel, self.age, self.lifev, self.sz, self.phase))
        self.t += 1

    def maps(self):
        """Density and temperature-weighted density at quarter resolution (float32)."""
        h, w = self.yy.shape
        dens = np.zeros((h, w), np.float32); temp = np.zeros((h, w), np.float32)
        for k in range(len(self.pos)):
            T = 1.0 - self.age[k] / self.lifev[k]
            x, y = self.pos[k] / DOWN; s = self.sz[k] / DOWN * (0.5 + 0.7 * T)      # a tongue tapers: the particle shrinks as it rises and cools
            sy = s * self.elong
            r = int(np.ceil(2.5 * sy)); x0, x1 = int(x) - r, int(x) + r + 1; y0, y1 = int(y) - r, int(y) + r + 1
            if x1 <= 0 or y1 <= 0 or x0 >= w or y0 >= h: continue
            cx0, cx1, cy0, cy1 = max(x0, 0), min(x1, w), max(y0, 0), min(y1, h)
            g = np.exp(-0.5 * (((self.xx[cy0:cy1, cx0:cx1] - x) / s) ** 2 + ((self.yy[cy0:cy1, cx0:cx1] - y) / sy) ** 2)) * (0.4 + 0.6 * T)
            dens[cy0:cy1, cx0:cx1] += g; temp[cy0:cy1, cx0:cx1] += g * T
        return dens, temp

    def render(self):
        """(colour BGR uint8 at full resolution, alpha float32 (H, W)) of the flame; both zero where there is no flame."""
        dens, temp = self.maps()
        T = temp / np.maximum(dens, 1e-6)
        T = np.clip(T ** 1.6 * 1.05 + 0.2 * np.clip(dens / 14.0, 0, 1), 0, 1)     # the hot core stays near the base; the thick middle a little hotter
        col = self.lut[(T * 255).astype(np.uint8)]
        a = 1.0 - np.exp(-self.k_alpha * dens)
        col = cv2.resize(col, (self.W, self.H), interpolation=cv2.INTER_LINEAR)
        a = cv2.resize(a, (self.W, self.H), interpolation=cv2.INTER_LINEAR)
        return col.astype(np.uint8), a.astype(np.float32)


def over(img, col, a):
    """Alpha composite (the daylit room: no bloom)."""
    return (img.astype(np.float32) * (1 - a[..., None]) + col.astype(np.float32) * a[..., None] + 0.5).astype(np.uint8)


class Sting:
    """The tail: the wordmark written by the flame over the dipped scene. `frame(j, last_scene, flame, thumbs)` returns the
    tail's frame j; the flame object is the scene's (its particles carry over from the thumbs)."""

    def __init__(self, W, H, n_tail=90, dip=15, sweep=(15, 27), t_sub=27, t_url=35, accent="#8F00FF", core="#CBA0FF", tick="#FF0000", ramp=None):
        """`ramp`: the effect's strain ramp as a list of hex stops (2026-09-22, Dennis: the logo's writing in the predominant colours of
        the animation, the ground black). The wordmark's letters take the stops in order, left to right (red at D, violet at s, each
        letter the stop nearest its position on the ramp, no mixing between letters: the mix of yellow and cyan would be green), the
        tick is the ramp's stops as segments (the meter under the wordmark), PRODUCTIONS wears the rest colour (the sheet's own,
        yellow), the URL and the tube cores the brand's neutral. Without a ramp: the puppet video's violet neon."""
        self.W, self.H, self.n = W, H, n_tail; self.dip = dip; self.sweep = sweep; self.t_sub = t_sub; self.t_url = t_url
        self.accent = brand.bgr(accent); self.core = brand.bgr(core); self.tick = brand.bgr(tick)
        self.letter_cols = self.tick_cols = self.sub_col = None
        if ramp:
            cols = [brand.bgr(c) for c in ramp]; nl = len(bs.WORD)
            self.letter_cols = [cols[int(round(k * (len(cols) - 1) / (nl - 1)))] for k in range(nl)]
            self.tick_cols = cols; self.sub_col = brand.bgr(ramp[min(2, len(ramp) - 1)]); self.core = brand.bgr(brand.NEUTRAL)
            print("  sting: the wordmark on the ramp's stops: " + " ".join(f"{ch}={ramp[int(round(k * (len(cols) - 1) / (nl - 1)))]}" for k, ch in enumerate(bs.WORD))
                  + f"; the tick {len(cols)} segments; PRODUCTIONS {ramp[min(2, len(ramp) - 1)]}; the URL and the cores {brand.NEUTRAL}")
        pil = Image.new("RGB", (W, H)); dr = ImageDraw.Draw(pil); self.L = bs.layout(dr)
        L = self.L; self.y_cap = L["y_word"] + (L["bbox"][1] + L["bbox"][3]) / 2       # the wordmark's mid cap height
        self.x0 = L["xs"][0][0] - 30; self.x1 = L["xs"][-1][1] + 30

    def emitters(self, j, thumbs):
        """The two flames' positions during the flight (j < sweep[0]) or the one flame's during the sweep; (pos, strength) list."""
        s0, s1 = self.sweep
        if j < s0:
            u = bs.ease_out(j / s0); target = np.array([self.x0, self.y_cap])
            out = []
            for k, th in enumerate(thumbs):
                p = np.array(th, np.float32) * (1 - u) + target * u
                out.append((p, 1.0))
            return out
        u = min((j - s0) / (s1 - s0), 1.0)
        x = self.x0 + (self.x1 - self.x0) * u
        strength = 1.0 if j <= s1 else max(0.0, 1.0 - (j - s1) / 6.0)              # dies out after the last letter
        return [((x, self.y_cap - 10), strength)]

    def frame(self, j, last_scene, flame, thumbs):
        W, H = self.W, self.H
        # the ground: the last scene frame dipping to black over `dip` frames, then black
        a_dip = bs.ease_out(j / self.dip) if self.dip > 0 else 1.0
        ground = (last_scene.astype(np.float32) * (1 - a_dip) + 0.5).astype(np.uint8)
        # the flame
        for pos, strength in self.emitters(j, thumbs): flame.emit(pos, strength)
        flame.step(); fcol, fa = flame.render()
        # the marks: the wordmark's letters light as the flame passes them (the brand's per-letter beat, timed to the sweep)
        lit = np.zeros((H, W, 3), np.uint8); hot = np.zeros((H, W, 3), np.uint8)
        pil = Image.new("RGB", (W, H)); dr = ImageDraw.Draw(pil); pil_word = Image.new("RGB", (W, H)); dr_word = ImageDraw.Draw(pil_word)
        s0, s1 = self.sweep; per = (s1 - s0) / (len(bs.WORD) - 1)
        bs.draw_marks(j, dr, dr_word, self.L, hot, lit, t_word=s0 - 1, per_letter=per, t_sub=self.t_sub, t_url=self.t_url,
                      accent=self.accent, neutral=self.core, tick=self.tick, neon=True,
                      letter_cols=self.letter_cols, tick_cols=self.tick_cols, sub_col=self.sub_col)
        text = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR); word = cv2.cvtColor(np.array(pil_word), cv2.COLOR_RGB2BGR)
        bs.tube_core(word, self.core)
        lit = np.maximum(lit, np.maximum(text, word))
        # the flame on the dark ground is emission too: its colour times its alpha goes into the glow
        fl = (fcol.astype(np.float32) * fa[..., None] * a_dip).astype(np.uint8)
        out = bs.neon_composite(ground, np.maximum(lit, fl), hot)
        # over the not-yet-black scene the flame is composited by alpha (as in the shot), fading to the emission read as the ground dips
        if a_dip < 1.0: out = over(out, fcol, fa * (1 - a_dip))
        return out
