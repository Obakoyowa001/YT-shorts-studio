# Ask Gus — Shorts Studio

Production repo for **Ask Gus**, our faceless YouTube Shorts channel: short, funny explainers about how money really works, starring our own cast (the Boss, Gus, Mo and Inspector Pike). Every video is scripted here and rendered in the cloud by GitHub Actions, so nothing renders on a personal computer.

## What's here

| Path | What it is |
| :--- | :--- |
| [`CLAUDE.md`](./CLAUDE.md) | The 7 rules every script follows (hook, pacing, cast, visual gags, payoff, captions, output format). |
| [`analysis/03_performance_insights_and_strategy.md`](./analysis/03_performance_insights_and_strategy.md) | Which topics perform best, originality guardrails, topic backlog, production pipeline. |
| [`scripts/`](./scripts/) | One file per Short: titles, voiceover, shot list, sound design, fact-check notes. |
| [`render/`](./render/) | 2.5D renderer (Cairo, 4K60) used for Short #001. See [`render/README.md`](./render/README.md). |
| [`render3d/`](./render3d/) | 3D renderer (Blender) used from Short #002 on. |
| [`render/sfx/`](./render/sfx/) | CC0 sound effects, with [credits](./render/sfx/CREDITS.md). |

## Shorts

1. **If You Opened a Bank in 1837**: [script](./scripts/001_wildcat_banks_1837.md), 2.5D
2. **What If Everyone Printed Money?**: [script](./scripts/002_everyone_prints_money.md), 3D (in production)

## Rendering

Renders run in the **Actions** tab. Each run's finished video and a small preview are attached to the run under **Artifacts** for 30 days.

## Licensing

The sound effects are CC0 (see credits). The fonts and the backup voice model are downloaded at render time under their own open licences. The research material that inspired the format (third-party videos and transcripts) is deliberately not stored in this public repo.
