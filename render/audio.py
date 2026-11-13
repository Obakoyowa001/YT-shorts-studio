"""Audio for Shorts: narrator TTS, character vocal FX, CC0 sound effects, synthesised
ambiences and a music bed, mixed with ducking under the voice."""
import asyncio
import glob
import os
import re
import subprocess
import wave
from functools import lru_cache

import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
SFX_DIR = os.path.join(HERE, "sfx")

# name -> (file globs, default gain dB). Random variant picked per cue (seeded).
LIB = {
    "hammer": (["impactWood_medium_*"], -6),
    "knock": (["impactWood_light_*"], -6),
    "plank": (["impactPlank_medium_*"], -6),
    "press": (["impactMetal_heavy_*"], -10),
    "metal": (["impactMetal_light_*"], -8),
    "glass": (["impactGlass_light_*"], -8),
    "step_grass": (["footstep_grass_*"], -12),
    "step_wood": (["footstep_wood_*"], -10),
    "stamp": (["impactPunch_heavy_000"], -4),
    "thud": (["impactSoft_heavy_000"], -4),
    "squelch": (["impactSoft_medium_*"], -4),
    "door_open": (["doorOpen_1"], -6),
    "door_close": (["doorClose_1"], -4),
    "book_open": (["bookOpen"], -2),
    "book_flip": (["bookFlip*"], -4),
    "book_place": (["bookPlace1"], -2),
    "chop": (["chop"], -4),
    "coins": (["handleCoins*"], -4),
    "clink": (["chips-collide-*", "chip-lay-1"], -8),
    "latch": (["metalLatch", "metalClick"], -6),
    "creak": (["creak1"], -8),
    "cloth": (["cloth*"], -10),
    "paper": (["card-slide-*", "card-place-1"], -6),
    "pop": (["pluck_*"], -10),
    "drop": (["drop_001"], -10),
    "ding": (["confirmation_002"], -8),
    "huh": (["question_001"], -10),
    "bark": (["dog_bark"], -6),
    "growl": (["dog_growl"], -6),
    "meow": (["cat_meow"], -8),
    "snip": (["knifeSlice", "knifeSlice2"], -8),
    "bell": (["impactBell_heavy_000"], -16),
    "whip": (["drawKnife1"], -10),
}


# ---------------------------------------------------------------- io
def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


@lru_cache(maxsize=256)
def _sample(path):
    return decode(path)


def lib_files(name):
    pats, _ = LIB[name]
    out = []
    for p in pats:
        out += sorted(glob.glob(os.path.join(SFX_DIR, p + ".ogg")))
    return out


def norm(w):
    return re.sub(r"[^a-z0-9$¢]", "", w.lower())


# ---------------------------------------------------------------- TTS
def tts_edge(text, mp3_path, voice, rate="+0%", pitch="+0Hz"):
    import edge_tts

    async def run():
        try:
            comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                        boundary="WordBoundary")
        except TypeError:
            comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        words = []
        with open(mp3_path, "wb") as f:
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    st = ch["offset"] / 1e7
                    words.append((st, st + ch["duration"] / 1e7, ch["text"]))
        return words

    return asyncio.run(run())


def _trim(a, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    return a[max(0, idx[0] - int(0.02 * SR)): idx[-1] + int(0.05 * SR)]


def tts_piper(segments, work, model, length_scale):
    """Offline neural TTS fallback; word times spread over each segment by word length."""
    from piper import PiperVoice

    pv = PiperVoice.load(model)
    gap = np.zeros(int(0.07 * SR), np.float32)
    parts, words, t = [], [], 0.0
    for i, seg in enumerate(segments):
        p = os.path.join(work, f"seg{i:02d}.wav")
        with wave.open(p, "wb") as wf:
            try:
                from piper import SynthesisConfig
                pv.synthesize_wav(seg["text"], wf,
                                  syn_config=SynthesisConfig(length_scale=length_scale))
            except ImportError:
                pv.synthesize(seg["text"], wf, length_scale=length_scale)
        a = _trim(decode(p))
        dur = len(a) / SR
        toks = [w for w in seg["text"].split() if norm(w)]
        wts = [len(norm(w)) + 2 + (3 if w[-1] in ",.?!" else 0) for w in toks]
        tot = float(sum(wts))
        acc = 0.0
        for w, k in zip(toks, wts):
            st = t + dur * acc / tot
            acc += k
            words.append((st, t + dur * acc / tot, w))
        parts += [a, gap]
        t += dur + len(gap) / SR
    return np.concatenate(parts).astype(np.float32), words


def vocal(text, voice, work, tag, rate="+0%", pitch="+0Hz"):
    """Short character line (laugh, chant). Returns samples or None if TTS is unavailable."""
    path = os.path.join(work, f"vox_{tag}.mp3")
    try:
        tts_edge(text, path, voice, rate, pitch)
        return _trim(decode(path))
    except Exception as e:  # noqa: BLE001
        print(f"[warn] vocal '{tag}' skipped ({type(e).__name__})")
        return None


# ---------------------------------------------------------------- synthesis
def _rng(seed):
    return np.random.default_rng(seed)


def lowpass_fast(x, width):
    k = np.ones(int(max(1, width))) / max(1, width)
    return np.convolve(x, k, mode="same")


def whoosh(dur=0.28, seed=3):
    n = int(dur * SR)
    x = _rng(seed).normal(0, 1, n).astype(np.float32)
    x = lowpass_fast(x, 24) - lowpass_fast(x, 220)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return (x * env / (np.max(np.abs(x)) + 1e-9)).astype(np.float32)


def chime(dur=0.9, base=1760.0):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for k, f in enumerate((base, base * 1.5, base * 2.0, base * 2.67)):
        out += np.sin(2 * np.pi * f * t) * np.exp(-t * (5 + k * 2)) * (0.6 ** k) * \
            (t >= k * 0.06)
    return (out / (np.max(np.abs(out)) + 1e-9)).astype(np.float32)


def wind(dur, seed=5):
    n = int(dur * SR)
    x = _rng(seed).normal(0, 1, n).astype(np.float32)
    x = lowpass_fast(x, 60)
    lfo = 0.6 + 0.4 * np.sin(np.linspace(0, dur * 0.7, n) * 2 * np.pi + 1)
    return (x * lfo / (np.max(np.abs(x)) + 1e-9)).astype(np.float32)


def squeak(dur=0.25, f0=1800, f1=2600):
    """Rusty wheel squeak: a short pitch-swept tone with rough edges."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = np.linspace(f0, f1, n) + np.sin(t * 2 * np.pi * 37) * 80
    ph = np.cumsum(2 * np.pi * f / SR)
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    x = (np.sin(ph) + 0.3 * np.sign(np.sin(ph * 2))) * env
    return (x / (np.max(np.abs(x)) + 1e-9)).astype(np.float32)


def tick(dur=0.03):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 260)
    return x.astype(np.float32)


def stretch(dur=1.2):
    """Balloon / rubber stretch: low wobbling tone rising in pitch."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 140 + 260 * (t / dur) ** 1.5 + np.sin(t * 2 * np.pi * 9) * 18
    ph = np.cumsum(2 * np.pi * f / SR)
    x = (np.sin(ph) + 0.4 * np.sin(ph * 2.01)) * np.minimum(1, t / 0.05) * np.minimum(1, (dur - t) / 0.1)
    return (x / (np.max(np.abs(x)) + 1e-9)).astype(np.float32)


def crickets(dur, seed=9):
    out = np.zeros(int(dur * SR), np.float32)
    rng = _rng(seed)
    t = 0.0
    while t < dur - 0.3:
        f = rng.uniform(4200, 4800)
        for k in range(3):
            st = int((t + k * 0.045) * SR)
            n = int(0.03 * SR)
            tt = np.arange(n) / SR
            out[st:st + n] += np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / 0.03) * 0.5
        t += rng.uniform(0.35, 0.9)
    return out


def room(dur, seed=11):
    n = int(dur * SR)
    x = _rng(seed).normal(0, 1, n).astype(np.float32)
    x = lowpass_fast(x, 140)
    return x / (np.max(np.abs(x)) + 1e-9)


def pluck(freq, dur, amp=1.0):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 7.0) * np.minimum(1, t / 0.004)
    sig = sum(np.sin(2 * np.pi * freq * h * t) / h ** 1.3 for h in range(1, 6))
    return (sig * env * amp).astype(np.float32)


def music(duration, bpm=128):
    out = np.zeros(int((duration + 2) * SR), np.float32)
    eighth = 60 / bpm / 2
    chords = [(196.0, 246.9, 293.7, 392.0), (261.6, 329.6, 392.0, 523.3),
              (293.7, 370.0, 440.0, 587.3), (196.0, 246.9, 293.7, 392.0)]
    bass = [98.0, 130.8, 146.8, 98.0]
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]
    t, bar = 0.0, 0
    while t < duration + 1:
        ch = chords[bar % 4]
        for i in range(8):
            st = int((t + i * eighth) * SR)
            n = pluck(ch[pattern[i]], 0.6, 0.35 if i % 2 else 0.5)
            out[st:st + len(n)] += n[: max(0, len(out) - st)]
            if i % 4 == 0:
                b = pluck(bass[bar % 4] if i == 0 else bass[bar % 4] * 1.5, 0.9, 0.8)
                out[st:st + len(b)] += b[: max(0, len(out) - st)]
        t += 8 * eighth
        bar += 1
    return out / (np.max(np.abs(out)) + 1e-9)


def resample(x, rate):
    """Speed/pitch change by `rate` (1.0 = unchanged)."""
    if abs(rate - 1.0) < 1e-3:
        return x
    n = int(len(x) / rate)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


# ---------------------------------------------------------------- mixing
class Mixer:
    def __init__(self, dur):
        self.buf = np.zeros(int((dur + 1) * SR), np.float32)
        self.rng = _rng(42)

    def add(self, x, t, gain_db=0.0):
        if x is None or t < 0:
            return
        i = int(t * SR)
        if i >= len(self.buf):
            return
        seg = x[: len(self.buf) - i] * 10 ** (gain_db / 20)
        self.buf[i:i + len(seg)] += seg

    def sfx(self, name, t, gain=None, rate=None):
        files = lib_files(name)
        if not files:
            print(f"[warn] missing sfx {name}")
            return
        x = _sample(files[int(self.rng.integers(len(files)))])
        r = rate if rate is not None else float(self.rng.uniform(0.94, 1.06))
        self.add(resample(x, r), t, LIB[name][1] + (gain or 0))

    def steps(self, t0, t1, interval=0.32, surface="grass", gain=0):
        t = t0
        while t < t1:
            self.sfx("step_" + surface, t, gain)
            t += interval

    def gallop(self, t0, t1, gain=0, speed=1.0):
        """Three-beat canter: da-da-DUM, from wood impacts."""
        t = t0
        beat = 0.42 / speed
        while t < t1:
            for k, (dt, g) in enumerate(((0, -6), (0.09, -4), (0.2, 0))):
                self.sfx("knock", t + dt / speed, gain + g, rate=0.7 + k * 0.05)
            t += beat


def duck(music_bed, voice, depth_db=-9, attack=0.05, release=0.35):
    """Lower the music while the narrator speaks."""
    env = np.abs(voice)
    win = int(0.03 * SR)
    env = np.convolve(env, np.ones(win) / win, mode="same")
    active = (env > 0.02).astype(np.float32)
    g = np.ones(len(music_bed), np.float32)
    cur = 1.0
    target_low = 10 ** (depth_db / 20)
    a_up = 1 / (release * SR)
    a_dn = 1 / (attack * SR)
    act = np.zeros(len(music_bed), np.float32)
    act[: min(len(active), len(act))] = active[: len(act)]
    # vectorised enough: process in blocks of 1 ms
    blk = int(SR / 1000)
    for i in range(0, len(g), blk):
        tgt = target_low if act[i] > 0 else 1.0
        step = a_dn * blk if tgt < cur else a_up * blk
        cur = max(tgt, cur - step) if tgt < cur else min(tgt, cur + step)
        g[i:i + blk] = cur
    return music_bed * g
