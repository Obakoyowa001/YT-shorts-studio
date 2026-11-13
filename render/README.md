# Short renderer (2.5D, 4K60, cloud)

Renders a Short from code on GitHub Actions. Nothing renders on your own computer.

## How a render runs

1. **Prep** (1 job): narrator voice (Microsoft Edge neural voice, falling back to an offline Piper voice), word timings, character vocal effects, sound effects, ambience and the music bed → `mix.wav` plus a shot plan.
2. **Shots** (8 parallel jobs): each job renders its share of the shots at **2160×3840, 60 fps**.
3. **Assemble** (1 job): joins the shots, adds the audio, normalises loudness to −14 LUFS, and uploads:
   - `s001-video`: the full-quality MP4
   - `s001-preview`: a 540p preview and a sheet of frame thumbnails

## Triggering

- **Automatic:** any push that changes `render/**` renders in 4K60.
- **Quick check:** put `[preview]` in the commit message to get a 540×960 / 30 fps render (about 4 min).
- **Manual:** use Actions → *Render Short* → *Run workflow*. This only works once the workflow is on `main`.

Download the result from the run page under **Artifacts**. Artifacts are kept for 30 days.

## Making a new Short

Copy `shorts/s001.py` to `shorts/s002.py`. Each entry in `SEGMENTS` is one shot:

```python
dict(text="narration for this shot", bg="forest", draw=draw_fn, audio=audio_fn)
```

- `draw_fn(c, t, d)` draws frame time `t` (seconds into the shot) of a shot lasting `d`. Use `c.cam(...)` for the camera and `with c.layer(k, blur=...)` for depth (k<1 far, k>1 foreground).
- `audio_fn(m, T, d)` cues sounds at absolute time `T + offset`: `m.sfx("coins", T + 0.4)`, `m.steps(...)`, `m.gallop(...)`, `m.add(m.vox["laugh"], ...)`.

Sound effect names are listed in `audio.py` (`LIB`); credits are in `sfx/CREDITS.md`.

## Local testing (tiny resolution)

```bash
TTS_ENGINE=fake python render/render.py all --width 270 --height 480 --fps 30 --out out/test.mp4
```

This needs `pycairo`, `pillow`, `numpy` and `ffmpeg`. `TTS_ENGINE=fake` skips the voice so it runs offline.
