"""Render a Short in three stages so the heavy video part can run on parallel cloud jobs.

  prep      voice (TTS) + word timings + full sound mix + shot plan     -> work/plan.json, mix.wav
  shots     render this shard's shots to MP4 segments (4K60 by default) -> work/shotNN.mp4
  assemble  join segments, add the mix, loudness-normalise             -> final MP4
  all       run everything locally

  python render/render.py all --short s001 --width 540 --height 960 --fps 30 --out out/p.mp4
"""
import argparse
import importlib
import json
import math
import multiprocessing as mp
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio as A  # noqa: E402

AMBIENCE = {  # bg -> list of (generator, gain dB)
    "day": [("wind", -36)],
    "forest": [("wind", -34)],
    "night": [("crickets", -30), ("wind", -42)],
    "interior": [("room", -44)],
    "shop": [("room", -44)],
    "modern": [("room", -46)],
    "sunrise": [("wind", -38)],
    "sepia": [("wind", -40), ("room", -46)],
}


# ---------------------------------------------------------------- prep
def segment_starts(segments, words):
    counts = [len([w for w in seg["text"].split() if A.norm(w)]) for seg in segments]
    total = sum(counts)
    if total != len(words):
        print(f"[warn] script has {total} words, TTS returned {len(words)}; scaling")
    starts, cum = [], 0
    for n in counts:
        idx = min(len(words) - 1, round(cum * len(words) / total))
        starts.append(words[idx][0])
        cum += n
    starts[0] = 0.0
    for i in range(1, len(starts)):
        starts[i] = max(starts[i] - 0.05, starts[i - 1] + 0.4)
    return starts


def prep(args):
    short = importlib.import_module(f"shorts.{args.short}")
    work = args.work
    os.makedirs(work, exist_ok=True)
    text = " ".join(s["text"] for s in short.SEGMENTS)

    voice = None
    pref = os.environ.get("TTS_ENGINE", "auto")
    if pref in ("auto", "edge"):
        try:
            mp3 = os.path.join(work, "voice.mp3")
            words = A.tts_edge(text, mp3, short.VOICE, short.RATE)
            voice = A.decode(mp3)
            print("tts: edge")
        except Exception as e:  # noqa: BLE001
            if pref == "edge":
                raise
            print(f"[warn] edge-tts failed ({type(e).__name__}: {e}); using Piper")
    if pref == "fake":  # silent placeholder voice for local testing without network
        words, t = [], 0.3
        for w in text.split():
            words.append((t, t + 0.22, w))
            t += 0.27 + (0.12 if w[-1] in ",.?!" else 0)
        voice = np.zeros(int((t + 0.3) * A.SR), np.float32)
    if voice is None:
        model = os.environ.get("PIPER_MODEL", os.path.join(A.HERE, "voices",
                                                           "en_US-ryan-high.onnx"))
        voice, words = A.tts_piper(short.SEGMENTS, work, model,
                                   float(getattr(short, "PIPER_LENGTH_SCALE", 0.8)))
        print("tts: piper")
    vdur = len(voice) / A.SR
    print(f"voice: {vdur:.1f}s, {len(words)} words, {len(words) / vdur * 60:.0f} WPM")

    starts = segment_starts(short.SEGMENTS, words)
    total = vdur + 0.7
    ends = starts[1:] + [total]

    # sound effects + ambience
    m = A.Mixer(total)
    m.whoosh = A.whoosh()
    m.chime = A.chime()
    m.squeak, m.tick, m.stretch = A.squeak(), A.tick(), A.stretch()
    m.vox = {}
    for tag, (txt, v, rate, pitch) in getattr(short, "VOCALS", {}).items():
        m.vox[tag] = A.vocal(txt, v, work, tag, rate, pitch)
    gens = {"wind": A.wind, "crickets": A.crickets, "room": A.room}
    for seg, a, b in zip(short.SEGMENTS, starts, ends):
        d = b - a
        for name, g in AMBIENCE.get(seg.get("bg", "day"), []):
            x = gens[name](d + 0.1)
            fade = min(len(x) // 2, int(0.05 * A.SR))
            x[:fade] *= np.linspace(0, 1, fade)
            x[-fade:] *= np.linspace(1, 0, fade)
            m.add(x, a, g)
        if seg.get("audio"):
            seg["audio"](m, a, d)
    for st in starts[1:]:
        m.add(m.whoosh, st - 0.08, -32)
    sfx = m.buf[: int(total * A.SR)]

    if getattr(short, "MUSIC", True):
        bed = A.music(total)[: len(sfx)] * 10 ** (-21 / 20)
    else:
        bed = np.zeros(len(sfx), np.float32)
    vpad = np.zeros(len(sfx), np.float32)
    vpad[: min(len(voice), len(vpad))] = voice[: len(vpad)]
    bed = A.duck(bed, vpad, -8)
    mix = vpad + sfx + bed
    mix /= max(1.0, float(np.max(np.abs(mix))) / 0.89)
    A.write_wav(os.path.join(work, "mix.wav"), mix)

    fps = args.fps
    shots = []
    for i, (a, b) in enumerate(zip(starts, ends)):
        f0, f1 = round(a * fps), round(b * fps)
        shots.append(dict(idx=i, f0=f0, f1=f1))
    # split long shots into chunks (3D renders), then balance across shards (greedy)
    units = []
    for sh in shots:
        if args.chunk:
            n = max(1, math.ceil((sh["f1"] - sh["f0"]) / args.chunk))
            size = math.ceil((sh["f1"] - sh["f0"]) / n)
            for p in range(n):
                a = sh["f0"] + p * size
                units.append(dict(idx=sh["idx"], part=p, f0=a, f1=min(sh["f1"], a + size)))
        else:
            units.append(sh)
    loads = [0] * args.shards
    for u in sorted(units, key=lambda s: s["f1"] - s["f0"], reverse=True):
        k = loads.index(min(loads))
        u["shard"] = k
        loads[k] += u["f1"] - u["f0"]
    plan = dict(short=args.short, fps=fps, width=args.width, height=args.height,
                shards=args.shards, shots=shots, words=words, total=total)
    if args.chunk:
        plan["chunks"] = units
    json.dump(plan, open(os.path.join(work, "plan.json"), "w"))
    print(f"plan: {len(shots)} shots, {round(total * fps)} frames @ {fps} fps, "
          f"shard loads {loads}")


# ---------------------------------------------------------------- shots
def _render_shot(job):
    import cairo

    import engine as E
    plan, sh, out = job
    short = importlib.import_module(f"shorts.{plan['short']}")
    seg = short.SEGMENTS[sh["idx"]]
    W, H, fps = plan["width"], plan["height"], plan["fps"]
    S = W / E.BASE_W
    t_start, t_end = sh["f0"] / fps, sh["f1"] / fps
    dur = t_end - t_start
    words = plan["words"]
    gold_words = set(getattr(short, "GOLD_WORDS", []))
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264",
         "-preset", os.environ.get("X264_PRESET", "fast"), "-crf", "17",
         "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    wi = 0
    for f in range(sh["f0"], sh["f1"]):
        tg = f / fps
        tl = tg - t_start
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c = E.Canvas(surf, S, W, H, tl)
        E.sky(c, seg.get("bg", "day"))
        seg["draw"](c, tl, dur)
        E.finish(c)
        while wi + 1 < len(words) and words[wi + 1][0] <= tg:
            wi += 1
        if words and words[wi][0] <= tg:
            nxt = words[wi + 1][0] if wi + 1 < len(words) else words[wi][1] + 0.5
            if tg < max(nxt, words[wi][1] + 0.15) or tg < words[wi][0] + 0.6:
                raw = words[wi][2]
                txt = re.sub(r"^[\"'(]+|[\"'),.!?;:]+$", "", raw)
                gold = (A.norm(raw) in gold_words or any(ch.isdigit() for ch in raw)
                        or "$" in raw)
                E.draw_caption(c, txt, tg - words[wi][0], gold)
        surf.flush()
        ff.stdin.write(surf.get_data())
    ff.stdin.close()
    ff.wait()
    if ff.returncode:
        raise RuntimeError(f"ffmpeg failed on {out}")
    return out


def shots(args):
    plan = json.load(open(os.path.join(args.work, "plan.json")))
    if args.width:
        plan["width"], plan["height"] = args.width, args.height
    mine = [s for s in plan["shots"] if args.shard is None or s["shard"] == args.shard]
    jobs = [(plan, s, os.path.join(args.work, f"shot{s['idx']:02d}.mp4")) for s in mine]
    jobs.sort(key=lambda j: j[1]["f1"] - j[1]["f0"], reverse=True)
    with mp.get_context("spawn").Pool(args.jobs) as pool:
        for done in pool.imap_unordered(_render_shot, jobs):
            print("rendered", os.path.basename(done), flush=True)


# ---------------------------------------------------------------- assemble
def assemble(args):
    plan = json.load(open(os.path.join(args.work, "plan.json")))
    lst = os.path.join(args.work, "shots.txt")
    with open(lst, "w") as f:
        units = plan.get("chunks") or plan["shots"]
        for s in units:
            name = ("shot%02d_p%02d.mp4" % (s["idx"], s["part"])) if "part" in s else \
                ("shot%02d.mp4" % s["idx"])
            seg_path = os.path.abspath(os.path.join(args.work, name))
            f.write("file '%s'\n" % seg_path)
    silent = os.path.join(args.work, "video.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", silent], check=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent,
                    "-i", os.path.join(args.work, "mix.wav"), "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-movflags", "+faststart", "-shortest", args.out],
                   check=True)
    print("done:", args.out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["prep", "shots", "assemble", "all"])
    ap.add_argument("--short", default="s001")
    ap.add_argument("--width", type=int, default=2160)
    ap.add_argument("--height", type=int, default=3840)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--shard", type=int, default=None)
    ap.add_argument("--chunk", type=int, default=0, help="max frames per render unit (3D)")
    ap.add_argument("--work", default="out/work")
    ap.add_argument("--out", default="out/short.mp4")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()
    if args.stage in ("prep", "all"):
        prep(args)
    if args.stage in ("shots", "all"):
        if args.stage == "shots" and "--width" not in sys.argv:
            args.width = args.height = None
        shots(args)
    if args.stage in ("assemble", "all"):
        assemble(args)


if __name__ == "__main__":
    main()
