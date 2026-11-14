"""Turn rendered PNG frames into captioned, upscaled MP4 shot segments.

python render3d/post.py PLAN.json SHARD FRAMES_DIR WORK_DIR
"""
import importlib
import json
import os
import re
import subprocess
import sys

import cairo
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "render"))
import audio as A  # noqa: E402
import engine as E  # noqa: E402

plan_path, shard, frames_dir, work = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
plan = json.load(open(plan_path))
story = importlib.import_module(f"shorts.{plan['short']}")
W, H, fps = plan["width"], plan["height"], plan["fps"]
S = W / E.BASE_W
words = plan["words"]
gold_words = set(getattr(story, "GOLD_WORDS", []))
step = int(os.environ.get("FRAME_STEP", "1"))

shots = {s["idx"]: s for s in plan["shots"]}
for sh in plan.get("chunks") or plan["shots"]:
    if sh["shard"] != shard and shard >= 0:
        continue
    full = shots[sh["idx"]]
    folder = os.path.join(frames_dir, "shot%02d" % sh["idx"])
    if not os.path.isdir(folder):
        continue
    seg = story.SEGMENTS[sh["idx"]]
    out = os.path.join(work, ("shot%02d_p%02d.mp4" % (sh["idx"], sh["part"])) if "part" in sh
                       else "shot%02d.mp4" % sh["idx"])
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264",
                           "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p", out],
                          stdin=subprocess.PIPE)
    wi = 0
    last = None
    for f in range(sh["f0"], sh["f1"]):
        k = f - full["f0"]
        src = os.path.join(folder, "%05d.png" % (k - k % step))
        if os.path.exists(src):
            last = src
        img = Image.open(last).convert("RGBA")
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        buf = bytearray(img.tobytes("raw", "BGRA"))
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, W, H, W * 4)
        tg = f / fps
        tl = tg - full["f0"] / fps
        c = E.Canvas(surf, S, W, H, tl)
        c.cam(drift=0)
        if seg.get("badge"):
            E.badge(c, tl, seg["badge"][0], seg["badge"][1])
        while wi + 1 < len(words) and words[wi + 1][0] <= tg:
            wi += 1
        if words and words[wi][0] <= tg:
            nxt = words[wi + 1][0] if wi + 1 < len(words) else words[wi][1] + 0.5
            if tg < max(nxt, words[wi][1] + 0.15) or tg < words[wi][0] + 0.6:
                raw = words[wi][2]
                txt = re.sub(r"^[\"'(]+|[\"'),.!?;:]+$", "", raw)
                gold = A.norm(raw) in gold_words or any(ch.isdigit() for ch in raw) or "$" in raw
                E.draw_caption(c, txt, tg - words[wi][0], gold)
        surf.flush()
        ff.stdin.write(bytes(buf))
    ff.stdin.close()
    ff.wait()
    print("encoded", os.path.basename(out), flush=True)
