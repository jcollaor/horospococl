"""Genera los Reels (mp4) y memes (jpg) de diciembre 2026 para @horospococl.
Uso: python3 render.py [id ...]   (sin argumentos genera todo)
"""
import os, sys, math, subprocess, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from content import POSTS_ALL as POSTS, SIGNS, SYM

W, H, FPS, SR = 1080, 1920, 30, 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_R = os.path.join(ROOT, "reels"); OUT_M = os.path.join(ROOT, "memes")
GF = "/usr/share/fonts/truetype/google-fonts/"
BOLD, MED = GF + "Poppins-Bold.ttf", GF + "Poppins-Medium.ttf"
SYMF = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
GOLD, WHITE, LAV = (245, 194, 107), (255, 255, 255), (214, 200, 255)

_fc = {}
def F(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def text_block(d, text, font, y, color, maxw=900, lh=1.18, x=None, anchor="ma"):
    lines = wrap(text, font, maxw)
    step = int(font.size * lh)
    for ln in lines:
        d.text((W // 2 if x is None else x, y), ln, font=font, fill=color, anchor=anchor)
        y += step
    return y

def block_h(text, font, maxw=900, lh=1.18):
    return len(wrap(text, font, maxw)) * int(font.size * lh)

# ---------- fondo ----------
def make_background(w, h, seed):
    y = np.linspace(0, 1, h)[:, None]
    top, mid, bot = np.array([18, 10, 46]), np.array([46, 16, 88]), np.array([10, 6, 30])
    t1 = np.clip(y / 0.55, 0, 1); t2 = np.clip((y - 0.55) / 0.45, 0, 1)
    col = np.where((y < 0.55)[..., None], top + (mid - top) * t1[..., None], mid + (bot - mid) * t2[..., None])
    bg = np.broadcast_to(col, (h, w, 3)).astype(np.float32).copy()
    yy, xx = np.mgrid[0:h, 0:w]
    glow = np.exp(-(((xx - w * 0.5) / (w * 0.55)) ** 2 + ((yy - h * 0.42) / (h * 0.28)) ** 2))
    bg += glow[..., None] * np.array([70, 30, 90], np.float32) * 0.6
    rng = np.random.default_rng(seed)
    layers = []
    for k in range(3):
        img = Image.new("L", (w, h), 0); d = ImageDraw.Draw(img)
        for _ in range(70):
            sx, sy = rng.uniform(0, w), rng.uniform(0, h)
            r = rng.choice([1.2, 1.6, 2.2, 3.0], p=[.45, .3, .17, .08])
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=int(rng.uniform(150, 255)))
        layers.append(np.asarray(img, np.float32)[..., None] / 255.0)
    return bg, layers

# ---------- escenas (capas RGBA) ----------
def new_layer():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)

def sc_hook(text):
    im, d = new_layer()
    d.text((W // 2, 560), "  ".join(SYM[s] for s in SIGNS[:6]), font=F(SYMF, 44), fill=GOLD, anchor="ma")
    f = F(BOLD, 88); hh = block_h(text, f)
    text_block(d, text, f, 900 - hh // 2, WHITE)
    d.text((W // 2, 1250), "  ".join(SYM[s] for s in SIGNS[6:]), font=F(SYMF, 44), fill=GOLD, anchor="ma")
    return im

def sc_top(rank, sign, reason):
    im, d = new_layer()
    d.text((W // 2, 470), f"#{rank}", font=F(BOLD, 70), fill=GOLD, anchor="ma")
    d.text((W // 2, 580), SYM[sign], font=F(SYMF, 230), fill=GOLD, anchor="ma")
    d.text((W // 2, 870), sign, font=F(BOLD, 110), fill=WHITE, anchor="ma")
    text_block(d, reason, F(MED, 62), 1040, LAV, maxw=880)
    return im

def sc_trait(sign, n, text):
    im, d = new_layer()
    d.text((W // 2, 470), SYM[sign], font=F(SYMF, 170), fill=GOLD, anchor="ma")
    d.text((W // 2, 700), f"{sign.upper()}  ·  {n}/3", font=F(BOLD, 46), fill=GOLD, anchor="ma")
    f = F(BOLD, 80); hh = block_h(text, f, 880)
    text_block(d, text, f, 1010 - hh // 2, WHITE, maxw=880)
    return im

def sc_compat(pair, label, text):
    im, d = new_layer()
    d.text((W // 2, 470), f"{SYM[pair[0]]}  +  {SYM[pair[1]]}", font=F(SYMF, 150), fill=GOLD, anchor="ma")
    d.text((W // 2, 720), label.upper(), font=F(BOLD, 66), fill=GOLD, anchor="ma")
    f = F(BOLD, 80); hh = block_h(text, f, 880)
    text_block(d, text, f, 1040 - hh // 2, WHITE, maxw=880)
    return im

def sc_grid(title, signs, values):
    im, d = new_layer()
    text_block(d, title, F(BOLD, 50), 330, GOLD, maxw=900)
    y = 520
    for s in signs:
        d.text((150, y + 12), SYM[s], font=F(SYMF, 112), fill=GOLD, anchor="ma")
        d.text((270, y), s, font=F(BOLD, 60), fill=WHITE, anchor="la")
        text_block(d, values[s], F(MED, 54), y + 78, LAV, maxw=720, lh=1.12, x=270, anchor="la")
        y += 265
    return im

def sc_element(name, signs, text):
    im, d = new_layer()
    d.text((W // 2, 450), name.upper(), font=F(BOLD, 104), fill=GOLD, anchor="ma")
    d.text((W // 2, 610), "   ".join(SYM[s] for s in signs), font=F(SYMF, 130), fill=GOLD, anchor="ma")
    d.text((W // 2, 800), " · ".join(signs), font=F(MED, 50), fill=LAV, anchor="ma")
    f = F(BOLD, 82); hh = block_h(text, f, 880)
    text_block(d, text, f, 1080 - hh // 2, WHITE, maxw=880)
    return im

def sc_cta(text):
    im, d = new_layer()
    f = F(BOLD, 84); hh = block_h(text, f)
    text_block(d, text, f, 800 - hh // 2, WHITE)
    d.text((W // 2, 1100), "Síguenos para tu horóscopo diario", font=F(MED, 48), fill=LAV, anchor="ma")
    d.text((W // 2, 1180), "@horospococl", font=F(BOLD, 72), fill=GOLD, anchor="ma")
    return im

def footer():
    im, d = new_layer()
    d.text((W // 2, 1560), "@horospococl", font=F(BOLD, 40), fill=(245, 194, 107, 200), anchor="ma")
    return np.asarray(im, np.float32) / 255.0

def scenes_for(p):
    k = p["kind"]; S = [(sc_hook(p["hook"]), 3.0)]
    if k == "top3":
        for i, (s, r) in enumerate(p["items"]):
            S.append((sc_top(3 - i, s, r), 3.3))
    elif k == "sign":
        for i, t in enumerate(p["items"]):
            S.append((sc_trait(p["sign"], i + 1, t), 3.3))
    elif k == "compat":
        for lab, t in p["items"]:
            S.append((sc_compat(p["pair"], lab, t), 3.4))
    elif k == "grid12":
        for i in range(3):
            S.append((sc_grid(p["hook"], SIGNS[i * 4:i * 4 + 4], p["items"]), 4.3))
    elif k == "elements":
        for name, signs, t in p["items"]:
            S.append((sc_element(name, signs, t), 3.6))
    S.append((sc_cta(p["cta"]), 3.0))
    return S

# ---------- audio ----------
def make_audio(dur, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    shift = int(rng.integers(-3, 3))
    hz = lambda m: 440 * 2 ** ((m - 69 + shift) / 12)
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    cl = 2.4; out = np.zeros_like(t)
    for ci in range(int(math.ceil(dur / cl))):
        ch = prog[ci % 4]; t0 = ci * cl
        m = (t >= t0) & (t < t0 + cl + 1.0); tt = t[m] - t0
        env = np.minimum(1, tt / 0.6) * np.exp(-np.maximum(0, tt - cl) * 4)
        sig = np.zeros_like(tt)
        for n in ch:
            for det in (-0.12, 0.12):
                sig += np.sin(2 * np.pi * hz(n + 12) * (1 + det / 100) * tt) * 0.06
        sig += np.sin(2 * np.pi * hz(ch[0] - 12) * tt) * 0.10
        out[m] += sig * env
        for j in range(8):  # arpegio suave
            n = ch[[0, 1, 2, 1][j % 4]] + 24 + (12 if j == 6 else 0)
            ts = t0 + j * cl / 8; mm = (t >= ts) & (t < ts + 1.2); u = t[mm] - ts
            out[mm] += np.sin(2 * np.pi * hz(n) * u) * np.exp(-u * 5) * 0.05
    out *= np.minimum(1, t / 0.5) * np.minimum(1, (dur - t) / 1.2)
    out = out / (np.abs(out).max() + 1e-9) * 0.5
    return np.repeat((out * 32767).astype(np.int16)[:, None], 2, axis=1)

# ---------- video ----------
def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def render_reel(p):
    os.makedirs(OUT_R, exist_ok=True)
    seed = int(hashlib.md5(p["id"].encode()).hexdigest()[:8], 16)
    bg, stars = make_background(W, H, seed)
    foot = footer()
    S = [(np.asarray(im, np.float32) / 255.0, d) for im, d in scenes_for(p)]
    dur = sum(d for _, d in S)
    wav = f"/tmp/{p['id']}.wav"
    import wave
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(make_audio(dur, seed).tobytes())
    out = os.path.join(OUT_R, f"{p['id']}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-shortest", "-movflags", "+faststart", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nf = int(round(dur * FPS)); starts = np.cumsum([0] + [d for _, d in S])
    for fi in range(nf):
        t = fi / FPS
        frame = bg.copy()
        for k, L in enumerate(stars):
            a = 0.55 + 0.45 * math.sin(t * (1.3 + k * 0.7) + k * 2.1)
            frame += L * (255 * a)
        si = int(np.searchsorted(starts, t, side="right") - 1); si = min(si, len(S) - 1)
        lay, d = S[si]; lt = t - starts[si]
        a_in = ease(lt / 0.4) if si > 0 or lt < 0.4 else 1
        a_out = 1 if si == len(S) - 1 else min(1, max(0, (d - lt) / 0.25))
        alpha = a_in * a_out; dy = int((1 - ease(lt / 0.4)) * 40)
        L = lay if dy == 0 else np.concatenate([np.zeros((dy, W, 4), np.float32), lay[:-dy]], axis=0)
        aa = L[..., 3:4] * alpha
        frame = frame * (1 - aa) + L[..., :3] * 255 * aa
        fa = foot[..., 3:4]; frame = frame * (1 - fa) + foot[..., :3] * 255 * fa
        pr.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    pr.stdin.close(); pr.wait()
    return out, dur

# ---------- memes ----------
MW, MH = 1080, 1350
def render_meme(p):
    os.makedirs(OUT_M, exist_ok=True)
    seed = int(hashlib.md5(p["id"].encode()).hexdigest()[:8], 16)
    bg, stars = make_background(MW, MH, seed)
    base = np.clip(bg + sum(L * 200 for L in stars), 0, 255).astype(np.uint8)
    files = []
    for slide in range(4):
        im = Image.fromarray(base).convert("RGBA"); d = ImageDraw.Draw(im)
        if slide == 0:
            d.text((MW // 2, 250), "  ".join(SYM[s] for s in SIGNS[:6]), font=F(SYMF, 50), fill=GOLD, anchor="ma")
            f = F(BOLD, 92); hh = block_h(p["hook"], f, 900)
            text_block(d, p["hook"], f, 640 - hh // 2, WHITE)
            d.text((MW // 2, 1000), "  ".join(SYM[s] for s in SIGNS[6:]), font=F(SYMF, 50), fill=GOLD, anchor="ma")
            d.text((MW // 2, 1120), "Desliza y busca tu signo  »", font=F(MED, 46), fill=LAV, anchor="ma")
        else:
            y = 90
            for s in SIGNS[(slide - 1) * 4:(slide - 1) * 4 + 4]:
                d.text((140, y + 14), SYM[s], font=F(SYMF, 110), fill=GOLD, anchor="ma")
                d.text((255, y), s, font=F(BOLD, 58), fill=WHITE, anchor="la")
                text_block(d, p["items"][s], F(MED, 48), y + 76, LAV, maxw=740, lh=1.15, x=255, anchor="la")
                y += 285
        d.text((MW // 2, MH - 80), "@horospococl", font=F(BOLD, 38), fill=GOLD, anchor="ma")
        fn = os.path.join(OUT_M, f"{p['id']}_{slide + 1}.jpg")
        im.convert("RGB").save(fn, quality=92); files.append(fn)
    return files

if __name__ == "__main__":
    ids = set(sys.argv[1:])
    for p in POSTS:
        if ids and p["id"] not in ids: continue
        if p["kind"] == "meme": print(p["id"], render_meme(p))
        else: print(p["id"], *render_reel(p))
