# CLAUDE.md — Shorts Script & Render Engine

This is the production repo for our faceless YouTube Shorts channel. It holds the formula (below), our scripts, and the code that renders the videos in the cloud. The format was reverse-engineered from the Shorts channel **Wobbly Business** (`@wobblybusiness`); we reuse the *formula*, never their assets. The raw research (their downloaded videos, transcripts and shot-by-shot breakdowns) is kept in the owner's private research repo, not here.

---

## 1. Repository Structure

- [`README.md`](./README.md) — What's here and how to render a video.
- [`analysis/03_performance_insights_and_strategy.md`](./analysis/03_performance_insights_and_strategy.md) — Verified metrics of the reference Shorts, which topics perform best, originality guardrails, topic backlog, and the production pipeline.
- [`scripts/`](./scripts/) — Our scripts, storyboards and fact-check notes, one file per Short.
- [`render/`](./render/) — 2.5D cloud renderer (Cairo) used for Short #001.
- [`render3d/`](./render3d/) — 3D cloud renderer (Blender) used from Short #002 on.

---

## 2. Core Formula When Writing New Videos

Whenever asked to brainstorm topics, write a script, or build a storyboard/prompt list for a new Short, strictly adhere to these **7 Golden Rules** derived from the data:

> **Originality first (see [`analysis/03_performance_insights_and_strategy.md`](./analysis/03_performance_insights_and_strategy.md), Section 3):** reuse the *formula*, never the channel's *assets*. Every script, gag, character design, and name must be our own. Never reuse the reference channel's lines verbatim or lightly reworded.

### Rule 1: The "You + Absurd Premise + Congratulations" Hook (0.0s – 8.0s)
Every video opens in **second person ("You")** throwing the viewer straight into a shady, grey-area, or counter-intuitive business operation, punctuated by a deadpan **"Congratulations."**
- *Pattern A (Illicit/Grey Hustle):* `"If you [do shady/clever business move], congratulations—you're in the [X] business."`
- *Pattern B (Sudden Windfall Problem):* `"You just [came into a pile of money in an awkward way]. Congratulations. You [can't actually use it]."`
- *Pattern C (Hypothetical / History):* `"If you [did X in a past era / Imagine everyone could X], congratulations. [Absurd consequence]."`
- Immediately follow with the **Core Conflict / Paradox** (why the obvious move fails or how the hidden margin actually works).
- **Topic choice:** prefer "secret/shady money" topics. They pulled ~2x the views of legal-retail topics. Frame them as explanation, never as instructions. When a video over-performs, re-run the same topic 1–3 weeks later with a new setting/metaphor (doc 03, Sections 2.2–2.3 and topic backlog in Section 4).

### Rule 2: Relentless Pacing & Reading Level (50–68 Seconds, ~3.5–3.8 Words/Sec)
- **Target Word Count:** 190 to 240 words (for a 53–68 second Short; ~210–230 WPM).
- **Reading Grade:** 4th–5th grade vocabulary. Zero jargon without an immediate physical joke explaining it.
- **Sentence Length:** Short, punchy declarative sentences (6–12 words average).
- **Named Business Concepts:** Always teach 1 to 3 real economic/financial terms (`placement`, `layering`, `integration`, `gray import`, `loss leader`), introduced *after* showing the physical action:
  > Pattern: show the silly physical action in one or two short sentences, give the fall guy a beat, then name it: ***"This is called [term]."***

### Rule 3: The Recurring Character Cast (Our Own Characters, Same Four Roles)
Use a consistent cast of recurring characters so viewers build parasocial familiarity across episodes. Keep the four **roles** that make the reference channel work, but use **our own names and visual designs**. Do **not** reproduce the reference channel's characters (Timmy, Tony, the bowler-hat Tax Man) or their looks.

| Role | What the role does | Our character |
| :--- | :--- | :--- |
| **1. The Boss ("You")** | Calm, calculating operator who runs the scheme; stands in for the viewer. | **The Boss**: short, round banker, emerald-green waistcoat, gold watch chain, slicked side-part. |
| **2. The Fall Guy** | Lovable, naive customer/accomplice who gets used and never notices. Delivers the comedic payoff in Act IV and appears in every episode. | **Gus**: huge gentle lumberjack, red beanie, red plaid shirt, brown beard, usually barefoot. |
| **3. The Middleman** | Shady dealer/partner who asks pointed questions or helps move the money. | **Mo**: skinny, huge handlebar mustache, purple coat, rides a tiny pony. |
| **4. The Authority** | Inspector/tax man/banker who "does the math" and catches the scheme. | **Inspector Pike**: very tall and thin, grey long coat, top hat, giant magnifying glass. |

Design guidance: pick a visual style and silhouettes clearly different from the reference channel's (different art style, palette, proportions, signature outfits). Use these names in every script.

### Rule 4: Visual Gags & Diegetic Props (Show, Don't Just Tell)
Hard-cut to a new shot roughly every 2.5 seconds (22–25 shots per Short), and keep the camera moving / new props or text popping in every ~1.5–2 seconds within each shot, so every beat lands on a new physical gag or close-up prop with **huge, readable in-world text**:
- Never show complex spreadsheets. Show a whiteboard where a hand physically sticks a green `0` onto `$5,000` to make `$50,000`.
- Show a literal yellow sponge wiping a phone screen to "wipe" a trade-in phone.
- Show a machine with its power cord lying unplugged when the line says nothing is really happening.
- Turn abstract ideas into literal props: "the money is legit now" becomes cash sitting next to receipts and an appointment card.

### Rule 5: The Twist / Ironic Payoff Ending (48s – 65s)
End with a humorous escalation featuring **our Fall Guy** (Rule 3), then the signature closing line *"And that's basically how every ___ works."* It generalizes the lesson and loops cleanly back to the hook. Payoff patterns that work:
- **Reveal the real product:** the cheap thing was never the product; the fall guy was.
- **Ironic leftover:** the fall guy's tiny honest payment is the only real money in the whole scheme.
- **Consequence lands on the fall guy:** the authority does the math, and the fall guy is the one left holding the bag.

### Rule 6: On-Screen Caption Specification
- **Style:** Single-word (1 word at a time) karaoke pop-in at the center/lower-middle of the 9:16 frame (`align: center`, ~55%–60% down from top).
- **Font:** Extra-bold rounded sans-serif (e.g., Montserrat Black / Rubik Mono / Komika Axis), white fill with thick black outline + subtle drop shadow.
- **Color Emphasis:** Switch word color to **Bright Yellow/Gold (`#FFD700`)** on dollar amounts (`$100,000`, `$200`, `$0.50`, `$30`, `$8`), key nouns (`Cash`, `Gym`, `Charger`), or punchwords (`Cheaper`).

### Rule 7: Output Format When Generating New Videos
When the user asks you to create a new video, provide:
1. **3 High-CTR Title Options** (4–6 words, Title Case, curiosity gap around how a business/scheme works).
2. **Full Voiceover Script** with word count, estimated duration, and `[emphasis/pause]` markers.
3. **Shot-by-Shot Storyboard Table** (Timestamp | Shot Duration | Spoken Line | 3D Visual Scene & Camera Move | In-World Prop Text | SFXCue).
4. **AI Video / 3D Scene Generation Prompts** (ready to paste into image/video generators or Blender/3D pipelines).

