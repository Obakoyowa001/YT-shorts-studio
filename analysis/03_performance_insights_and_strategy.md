# Performance Insights, Topic Strategy & Automation Plan

This document builds on the original formula analysis and shot-by-shot breakdowns (docs 01 and 02, kept in the owner's private research repo because they quote the reference channel's scripts). The formula itself is summarised in [`CLAUDE.md`](../CLAUDE.md). It adds:

- an independent re-check of the core metrics
- what the performance data says about **which topics** to make
- a topic backlog and an automation pipeline for producing our own variation

---

## 1. Independent Verification of the Metrics (2026-11-12)

All three Shorts were re-downloaded with `yt-dlp` and re-measured with `ffmpeg`. Results agree with docs 01/02, with these notes:

| Metric | Value | Notes |
| :--- | :--- | :--- |
| Views / likes / comments | Matches doc 01 | The 2026-11-12 snapshot is slightly higher (e.g. `IdSsAquESBE` 1,717,308 views / 53,907 likes / 413 comments). That's normal growth since the first snapshot. Doc 01's table remains the baseline. |
| Word count | 237 / 193 / 231 words | Counted from the clean transcripts (private research repo). Doc 01, README and `CLAUDE.md` have been updated to these figures. |
| Speaking rate | **209 / 218 / 227 WPM** (3.5–3.8 words/sec) | Faster than normal speech (~150 WPM). This is a key part of the format's "relentless" feel (CLAUDE.md Rule 2). |
| Hard cuts | 24 / 21 / 24 → **~2.4–2.7 s per shot** | Stable across ffmpeg scene thresholds 0.1–0.3. Continuous camera moves and props popping in within each shot mean the screen still changes every ~1.5–2 s (CLAUDE.md Rule 4). |
| Format | 608×1080 delivered, 30 fps, 9:16 | Audio mastered loud: mean ≈ −17 dB, peaks ≈ −0.7 dB. |
| Metadata | Empty description, zero tags, `People & Blogs` | Confirms doc 01: distribution is driven by the content, not SEO. |

---

## 2. What the Performance Data Tells Us

### 2.1 Views come from the Shorts feed, not subscribers
The channel had only **~7,230 subscribers** at the time of analysis. Each Short still reached **0.66M–1.7M views** within days of upload, and all three went up within about two weeks. That's roughly 90–235 views per subscriber. **Implication:** a brand-new channel using this format does not need an existing audience. Retention and rewatch rate are what matter (see doc 01, Section 1).

### 2.2 "Forbidden money" topics beat "clever business" topics roughly 2:1
| Topic type | Video | Views | Like rate | Comments |
| :--- | :--- | :--- | :--- | :--- |
| Illicit (money laundering) | `IdSsAquESBE` | 1.71M | 3.1% | 409 |
| Illicit (money laundering) | `uiIKhYWuO50` | 1.10M | 2.9% | 109 |
| Legal grey-area retail | `NrVzNpmNZ3s` | 0.66M | 1.7% | 53 |

Both laundering videos beat the phone-shop video on views, like rate and comments. This matches CLAUDE.md Rule 1 (Pattern A: shady/grey hustle). **When choosing topics, lean toward the "secret/shady" end of the spectrum**, framed as explanation, never as instruction.

### 2.3 Winning topics can be re-run with a new metaphor
The channel covered **money laundering twice in 11 days** (casino + laundromat → gym bag + car wash). The second version did ~55% more views. The concept (placement → layering → integration) stayed the same. Only the front business, gags and Timmy's payoff changed. **Implication:** when one of our Shorts over-performs, remake the topic 1–3 weeks later with a fresh setting rather than moving on.

### 2.4 The closing line drives rewatches
Two of the three end with *"And that's basically how every ___ works."* (Act V in doc 01). It generalizes the lesson and sets up a clean loop back into the hook. Keep it as the default sign-off.

---

## 3. Making It "Our Own Variation" — Originality Guardrails

The goal is to reuse the **formula** (5-Act structure, pacing, diegetic text, caption style), not the channel's **assets**. To protect monetization (YouTube's reused/inauthentic-content policy) and avoid copyright claims:

- **Scripts:** always write new scripts and new gags. Never re-voice or lightly reword a Wobbly Business script.
- **Characters:** keep the four **roles** from CLAUDE.md Rule 3 (the Boss, the naive fall guy, the shady middleman, the authority figure). Give them **our own names and visual designs** rather than reproducing Timmy, Tony or the Tax Man as drawn by Wobbly Business.
- **Branding:** use our own channel name/logo as the in-world shop sign (as they do with `WOBBLY BUSINESS`). Keep parody brands like `ORBIT` instead of real trademarks.
- **Footage:** never upload or re-cut their video files. Their video files live only in the private research repo, for reference.

---

## 4. Topic Backlog (Fits the Proven Pattern)

Ranked "shady/secret" first, per Section 2.2. Each includes the real term the video would teach (CLAUDE.md Rule 2).

| # | Working Title | Term(s) Taught | Angle |
| :--- | :--- | :--- | :--- |
| 1 | How Ponzi Schemes Actually Collapse | Ponzi scheme, liquidity | Illicit |
| 2 | How Pyramid Schemes Get You In | MLM, downline | Grey |
| 3 | How Casinos Make Sure You Lose | House edge, comps | Grey |
| 4 | How Scammers Hide Crypto Money | Mixing, chain-hopping (explained, not instructed) | Illicit |
| 5 | How Gyms Profit From People Who Never Go | Breakage, overselling | Grey |
| 6 | How Car Dealers Really Make Money | F&I, dealer holdback | Grey |
| 7 | How Credit Cards Profit From You | Interchange, APR | Legal |
| 8 | How Cinemas Actually Make Money | Concession margin | Legal |
| 9 | How "Free" Apps Make Money | Data brokerage, freemium | Legal |
| 10 | How Airlines Make Money (It's Not Tickets) | Loyalty points, ancillary revenue | Legal |

---

## 5. Automation Pipeline

1. **Topic → script:** feed a topic from Section 4 to Claude with `CLAUDE.md`. Output follows Rule 7 (titles, script with word count, storyboard, scene prompts). Target 190–240 words.
2. **Voiceover:** TTS (e.g. ElevenLabs) in a warm, deadpan American male voice, rate tuned to ~210–230 WPM, long pauses trimmed (doc 01, Section 5).
3. **Visuals:** build reusable 3D scene templates for our own cast (Blender/Unreal), or use AI image/video tools with locked character reference sheets. Aim for a hard cut every ~2.5 s with constant camera motion.
4. **Captions:** get word-level timestamps with Whisper, then burn in single-word captions per CLAUDE.md Rule 6 (white + black stroke, gold for dollar amounts and key words).
5. **Music/SFX:** quiet caper music (−22 to −26 dB under the voice) plus an SFX hit every 1.5–2 s (doc 01, Section 5). Master to around −17 dB mean / −1 dB peak.
6. **Publish & learn:** upload once a day with no tags or description needed. Track views in the first 24 h. Re-run any topic that beats the channel median, using a new metaphor (Section 2.3).
