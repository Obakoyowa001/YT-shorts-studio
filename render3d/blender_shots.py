"""Render this shard's shots to PNG frames (runs inside Blender).

blender -b --python render3d/blender_shots.py -- PLAN.json SHARD OUT_DIR WIDTH HEIGHT SAMPLES
"""
import importlib
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
plan = json.load(open(argv[0]))
shard = int(argv[1])
out_dir, W, H, samples = argv[2], int(argv[3]), int(argv[4]), int(argv[5])
only = {int(x) for x in argv[6].split(",")} if len(argv) > 6 and argv[6] else None
scenes = importlib.import_module(f"scenes.{plan['short']}")
fps = plan["fps"]

for sh in plan["shots"]:
    if sh["shard"] != shard and shard >= 0:
        continue
    if only is not None and sh["idx"] not in only:
        continue
    t0 = time.time()
    lib.reset()
    d = (sh["f1"] - sh["f0"]) / fps
    update = scenes.SHOTS[sh["idx"]](d)
    lib.setup_render(W, H, samples)
    folder = os.path.join(out_dir, "shot%02d" % sh["idx"])
    os.makedirs(folder, exist_ok=True)
    step = int(os.environ.get("FRAME_STEP", "1"))
    frames = range(sh["f0"], sh["f1"], step)
    if os.environ.get("STILLS") == "1":   # one frame per shot, 60% of the way in
        frames = [sh["f0"] + int((sh["f1"] - sh["f0"]) * 0.6)]
    for f in frames:
        t = (f - sh["f0"]) / fps
        update(t)
        bpy.context.view_layer.update()
        bpy.context.scene.render.filepath = os.path.join(folder, "%05d.png" % (f - sh["f0"]))
        bpy.ops.render.render(write_still=True)
    n = len(frames)
    print(f"SHOT {sh['idx']:02d}: {n} frames in {time.time() - t0:.0f}s "
          f"({(time.time() - t0) / max(1, n):.1f}s/frame)", flush=True)
