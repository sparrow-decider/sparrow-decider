# Sparrow Decider brand guide

Version 0.2.0 (launch). Owned by the Sparrow Decider contributors.
Assets in this folder: `tokens.css`, `logo-mark.svg`, `logo-wordmark.svg`, `logo-wordmark-light.svg`,
`favicon.svg`, `og-image.svg`, PNG renders in `previews/`.

Every number used in brand or marketing material must come from `site/facts.json`. If a sentence
needs a number that is not there, rewrite the sentence.

---

## 1. Positioning

**Positioning statement**

> For developers building agents, robots and embedded products who need a quick, reliable call on
> "what happens next", Sparrow Decider is a family of tiny decision models that answer yes/no,
> pick-one and score questions with calibrated probabilities. Unlike a large model behind an API,
> Sparrow runs where the decision is made: from a 47 MB model on a laptop down to a ~2 KB compiled
> model that decides in 9.3 µs on a $10 ESP32-S3. No GPU, no network, no model server.

**One-line description**

> Sparrow Decider: tiny decision models, from 47 MB on a laptop to ~2 KB on a microcontroller.

**Short description (about 40 words)**

> Sparrow Decider is a family of decision models that answer yes/no, pick-one and score questions
> about a state, with calibrated probabilities, in the same shapes as Strands Decider. Python needs
> only numpy. The C99 runtime uses no malloc and runs on an ESP32-S3.

**Name rules**

- Full name: **Sparrow Decider**. Short form after first mention: **Sparrow**.
- Model IDs are always lowercase code: `sparrow-pico-rover-v1.1`, `sparrow-nano-robot-v1.1`.
- Tier names are lowercase words in prose: pico, nano, micro, tiny, small.
- Never "SparrowDecider", "Sparrow AI", "Sparrow LLM".
- Always pair public material with the disclaimer:
  **"Unofficial community project. Not an AWS or Strands product."**
- Credit the work to "the Sparrow Decider contributors". No individual names.

---

## 2. Messaging pillars

### Pillar 1. Small enough to live where the decision happens
The family spans a 47 MB model on a laptop to a ~2 KB-per-question compiled model (501 parameters)
on any microcontroller. The decision runs inside your agent, your robot or your chip.
*Proof:* 9.3 µs per decision on a $10 ESP32-S3 (pico). 3.8 ms per text decision on the same chip (nano).
Board: ESP32-S3, 240 MHz, 16 MB flash, 8 MB PSRAM.

### Pillar 2. Measured, not promised
Every number is a measurement, and the limits are published next to the wins.
*Proof:* The C runtime matches the Python runtime to within 1e-5 on the host; on the ESP32-S3, int8 builds agree with the host on 150-155 of 155 decisions. A 1.37 MB nano-robot v1.0 scores
40 / 55 on RobotBench, the same as the public 2B Strands Decider. pico matches its spec's rules
94.0% of the time (its 2B teacher: 94.2%). Honest limits: open-ended language is well behind the 2B;
JevBench yes/no is near chance at every tier.

### Pillar 3. Boring to install, easy to ship
`pip install sparrow-decider`. Python needs numpy only. The C99 runtime has no malloc and reads
the model from flash (ESP-IDF component). The sparrow-pico compiler turns a device spec into a C header.
Same question shapes as Strands Decider, so prompts and schemas carry over.

---

## 3. Voice and tone

Confident, precise, playful-but-engineered. Short sentences. Numbers do the bragging.
We sound like a careful engineer who is quietly delighted that the thing fits.

| Do | Don't |
|---|---|
| Lead with a measured number and its condition: "9.3 µs per decision on a $10 ESP32-S3." | Strip the condition: "9.3 µs decisions." |
| Name the model and the hardware. | Say "blazing fast", "lightning", "instant" as a claim. |
| Put limits next to wins. | Hide JevBench or MASSIVE results. |
| Use plain verbs: decides, answers, runs, fits, ships. | Use "revolutionary", "game-changer", "disrupt", "unleash", "supercharge", "magic". |
| Use one light bird reference per page, at most. | Pun on birds in every heading. |
| Write "the public 2B Strands Decider" when comparing. | Imply endorsement by AWS or Strands. |
| Use "you" and the imperative: "Compile a decision for your device." | Talk about "our users" or "customers" (we have no figures for either). |
| Use µs and ms with a space: "9.3 µs", "3.8 ms". | Round, combine or extrapolate: no "N times faster", no rounded values, no device or user counts. |

**Approved word bank:** tiny, small, fits, on-chip, measured, calibrated, compiled, no malloc,
numpy only, offline, local, deterministic runtime, per decision, per question.

**Playfulness budget:** one wink per surface (a 404 page, a tooltip, a closing line). Never in numbers,
limits, licensing or the disclaimer.

---

## 4. Tagline

### Final tagline

# Decisions that fit on a chip.

Why: it is literally true (pico is ~2 KB per question and nano runs text decisions on an ESP32-S3),
it names the differentiator nobody else in the decider space can claim, it is short enough for a
favicon tooltip, and it sets up the proof line without needing it.

**Standard support line:** "From 47 MB on a laptop to ~2 KB on a microcontroller."
**Numeric support line:** "9.3 µs per decision on a $10 ESP32-S3."

### Ten alternatives, ranked

| # | Tagline | Rationale |
|---|---|---|
| 1 | Tiny models. Fast decisions. | Clean rhythm and broad; loses the chip, which is our sharpest edge. |
| 2 | From 47 MB to 2 KB. | Shows the range in numbers; reads as a spec, better as a support line. Use "~2 KB" in body copy. |
| 3 | Decide in microseconds. | Punchy and true for pico (9.3 µs), but text tiers decide in milliseconds, so it overreaches as a family line. |
| 4 | The decider that fits on a chip. | Close to the winner; "the decider" sounds like a single model, not a family. |
| 5 | Small bird. Quick calls. | Charming brand tie-in; too cute for embedded engineers as the primary line. |
| 6 | Know what to do next, on-device. | Explains the job well; generic against other on-device ML. |
| 7 | Calibrated decisions, down to the microcontroller. | Accurate and complete; too long for hero and social. |
| 8 | Same question. Smaller model. | Speaks to Strands Decider users; needs context for everyone else. |
| 9 | Decisions without a model server. | True and useful in docs; defined by what it lacks. |
| 10 | Decisions at the speed of a heartbeat. | Memorable, but imprecise: a heartbeat is far slower than 9.3 µs, which undersells and confuses. |

---

## 5. Color system

Vibrant, smooth gradients on deep ink. Color carries energy; ink carries trust. Gradients are for
the mark, hero highlights and one primary button per view. Everything else is ink, paper and one cyan accent.

### Core palette

| Token | Hex | Role |
|---|---|---|
| Amber | `#FFB547` | Gradient start, inline numbers on dark |
| Coral | `#FF6B4A` | Gradient |
| Pink | `#FF3D8B` | Gradient, glow |
| Violet | `#8B5CF6` | Gradient end (not for small text on dark: 4.47:1) |
| Violet 300 | `#A78BFA` | Violet for text on dark |
| Cyan | `#22D3EE` | Accent: links, focus rings, "live" signals, code prompts |
| Ink 900 | `#0B1020` | Dark background, text on light |
| Ink 800 | `#111832` | Dark surface |
| Ink 700 | `#182046` | Dark raised surface |
| Ink 600 | `#2A3560` | Dark border |
| Paper | `#F5F7FF` | Text on dark |

### Theme tokens

| Token | Dark (default) | Light |
|---|---|---|
| `--sd-bg` | `#0B1020` | `#FAFBFF` |
| `--sd-surface` | `#111832` | `#FFFFFF` |
| `--sd-surface-2` | `#182046` | `#F1F3FB` |
| `--sd-border` | `#2A3560` | `#DDE2F2` |
| `--sd-border-strong` | `#3A4777` | `#C9D0E6` |
| `--sd-text` | `#F5F7FF` | `#0B1020` |
| `--sd-text-muted` | `#A9B3D6` | `#3B4468` |
| `--sd-text-subtle` | `#8C96BD` | `#5A6389` |
| `--sd-accent` (links, focus) | `#22D3EE` | `#0E7490` |
| `--sd-highlight` (inline numbers) | `#FFB547` | `#B45309` |
| `--sd-violet-text` | `#A78BFA` | `#6D28D9` |
| `--sd-success` | `#34D399` | `#047857` |
| `--sd-danger` | `#FF5D73` | `#BE123C` |
| `--sd-on-cta` (text on CTA gradient) | `#0B1020` | `#0B1020` |
| `--sd-code-bg` | `#0E1430` | `#0B1020` (code stays dark) |

### Gradients

| Name | Definition | Use |
|---|---|---|
| Sunrise | `linear-gradient(120deg, #FFB547 0%, #FF6B4A 35%, #FF3D8B 68%, #8B5CF6 100%)` | Hero accents, dividers, large decorative fills |
| CTA | `linear-gradient(120deg, #FFB547 0%, #FF6B4A 50%, #FF3D8B 100%)` | The single primary button. Ink text only. |
| Mark | `linear-gradient(45deg, #8B5CF6 0%, #FF3D8B 40%, #FF6B4A 72%, #FFB547 100%)` | Logo (violet tail, amber head) |
| Signal | `linear-gradient(120deg, #22D3EE 0%, #8B5CF6 100%)` | Live demo, terminal, "decision made" states |
| Gradient text, dark | `linear-gradient(100deg, #FFB547, #FF6B4A 35%, #FF3D8B 68%, #A78BFA)` | Headline highlight words on dark |
| Gradient text, light | `linear-gradient(100deg, #C2410C, #BE185D 55%, #6D28D9)` | Headline highlight words on light |
| Ambient glow | radial pink at top right, amber at right, cyan at bottom left (`--sd-glow`) | Page backgrounds, hero; low opacity |

### Contrast (WCAG 2.x, computed)

Ratios were computed with the WCAG relative-luminance formula. AA needs 4.5:1 for body text and
3:1 for large text (24 px, or 18.66 px bold) and UI components.

**Dark theme**

| Foreground | on `#0B1020` bg | on `#111832` surface | on `#182046` surface-2 | Verdict |
|---|---|---|---|---|
| Text `#F5F7FF` | 17.70 | 16.35 | 14.72 | AAA |
| Muted `#A9B3D6` | 9.11 | 8.42 | 7.58 | AAA |
| Subtle `#8C96BD` | 6.50 | 6.01 | 5.41 | AA |
| Cyan `#22D3EE` | 10.48 | 9.68 | 8.71 | AAA |
| Amber `#FFB547` | 10.78 | 9.96 | 8.96 | AAA |
| Coral `#FF6B4A` | 6.72 | 6.21 | 5.59 | AA |
| Pink `#FF3D8B` | 5.67 | 5.24 | 4.72 | AA |
| Violet `#8B5CF6` | **4.47** | 4.13 | 3.72 | Large text only. Use `#A78BFA` (6.96) for text. |
| Violet 300 `#A78BFA` | 6.96 | 6.43 | 5.79 | AA |
| Success `#34D399` | 9.85 | 9.10 | 8.19 | AAA |
| Danger `#FF5D73` | 6.37 | 5.89 | 5.30 | AA |

**Light theme**

| Foreground | on `#FAFBFF` bg | on `#FFFFFF` surface | on `#F1F3FB` surface-2 | Verdict |
|---|---|---|---|---|
| Text `#0B1020` | 18.31 | 18.93 | 17.09 | AAA |
| Muted `#3B4468` | 9.18 | 9.49 | 8.57 | AAA |
| Subtle `#5A6389` | 5.67 | 5.86 | 5.29 | AA |
| Accent `#0E7490` | 5.18 | 5.36 | 4.84 | AA |
| Highlight `#B45309` | 4.86 | 5.02 | 4.53 | AA |
| Coral ink `#C2410C` | 5.01 | 5.18 | 4.67 | AA |
| Pink ink `#BE185D` | 5.84 | 6.04 | 5.45 | AA |
| Violet ink `#6D28D9` | 6.87 | 7.10 | 6.41 | AA |
| Success `#047857` | 5.30 | 5.48 | 4.95 | AA |
| Danger `#BE123C` | 6.08 | 6.29 | 5.67 | AA |

**Buttons and fills**

- Ink `#0B1020` on CTA gradient stops: amber 10.78, coral 6.72, pink 5.67. Passes AA everywhere.
- White on the sunrise stops: 1.76 / 2.82 / 3.34 / 4.23. **Never put white text on the gradient.**
- Ink on cyan: 10.48. White on `#0E7490`: 5.36.
- Cyan `#22D3EE` on white is about 1.6:1: never use raw cyan as text in light mode; use `#0E7490`.
- Borders (`#2A3560` on ink 1.6:1, `#DDE2F2` on paper 1.25:1) are decorative. Inputs and focus states
  must use `--sd-border-strong` plus the focus ring, never border colour alone.

---

## 6. Typography

All from Google Fonts. One stylesheet request:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

| Role | Family | Weights | Notes |
|---|---|---|---|
| Display | **Sora** | 600, 700 (400 for the "Decider" half of the wordmark) | Geometric, wide apertures, holds up at hero size. Tracking -0.025em, leading 1.05. Headlines and section titles only. |
| Body / UI | **Inter** | 400, 500, 600, 700 | Body 16-18 px, leading 1.6. Big numbers (stat tiles) use Inter 700 with `font-variant-numeric: tabular-nums` so values line up. Inter has a proper µ. |
| Code / data | **JetBrains Mono** | 400, 500 | Install commands, model IDs, inline code, tables of timings. |

Rules:
- Sora does not include a Greek mu. Never set "µs" in Sora; set numbers with units in Inter.
- Sentence case for every heading and button. No all-caps except small eyebrow labels
  (Inter 600, 12 px, tracking 0.08em).
- Keep hero headlines to two lines at desktop width.
- Always a space between number and unit: `9.3 µs`, `2.2 MB`, `3.8 ms`.

---

## 7. Logo

The mark is a geometric sparrow built from one continuous silhouette: a round head, a short beak
and a long tail that points down and back. One clean cut splits back from wing. The cut and the eye
are true transparency (an SVG mask), so the mark works on any background. The fill is the Mark
gradient: violet at the tail, amber at the head, like a bird flying into sunrise.

| File | Use |
|---|---|
| `logo-mark.svg` | Mark alone, transparent, 64-unit grid. 24 px and up. |
| `favicon.svg` | Mark on an ink rounded tile with a wider cut and eye. 16-48 px, app icons, avatars. |
| `logo-wordmark.svg` | Mark + "Sparrow Decider", for dark backgrounds (paper text). |
| `logo-wordmark-light.svg` | Same, for light backgrounds (ink text). |
| `og-image.svg` | 1200 x 630 social card. Use `previews/og-image.png` for `og:image`. |

The wordmark text is converted to outlines (Sora 650 "Sparrow" + Sora 400 "Decider"), so it renders
identically without fonts installed.

**Usage rules**

- Clear space: at least the height of the mark's head (one quarter of the mark height) on every side.
- Minimum size: mark 24 px (use `favicon.svg` below that); wordmark 120 px wide.
- Use the dark wordmark on ink or photography darker than `#2A3560`; use the light wordmark on paper or white.
- Single-colour fallback (print, engraving): solid `#0B1020` or solid `#F5F7FF`. Replace the
  gradient fill in the SVG with that colour; keep the mask.
- Do not: recolour the gradient, rotate or flip the bird, add strokes or drop shadows, put the
  gradient mark on a busy gradient background, stretch the wordmark, retype the wordmark in another font,
  or add "AI", "by AWS" or any third-party logo next to it.
- The mark may stand alone (avatars, favicons, stickers). The name may stand alone in running text.

---

## 8. Motion

Motion explains state change: a question goes in, a decision comes out. It never decorates for its own sake.

| Principle | Practice |
|---|---|
| Fast like the product | UI transitions 90-240 ms. Nothing that blocks reading lasts longer than 480 ms. |
| Arrive and settle | Default easing `cubic-bezier(0.22, 1, 0.36, 1)` (`--sd-ease-out`). |
| One hero moment per page | Home: the demo shows state -> question -> answer with a probability bar filling. Others: a gentle fade-up of sections (12 px, 480 ms). |
| Ambient, not busy | Background glow may drift slowly (`--sd-dur-ambient`, 18 s loop). No parallax, no autoplaying video. |
| Numbers count honestly | Stat values may fade in, but never count up through values we did not measure. Show the final value immediately for screen readers. |
| Respect the user | Under `prefers-reduced-motion: reduce` all durations become 0 (handled in `tokens.css`); ambient loops stop; the demo shows its final state. |
| Feedback is tiny | Copy button: icon swaps to a check with a 160 ms spring pop, label "Copied". |

---

## 9. Imagery and layout

- Background: ink with `--sd-glow` and an optional faint dot grid (7% paper dots, 28 px pitch), as in `og-image.svg`.
- Cards: `--sd-surface`, 1 px `--sd-border`, radius 18 px, `--sd-shadow-md`. Stat cards may use a gradient border at low opacity.
- Code blocks are always dark, in both themes.
- Use real hardware photos only if the contributors took them. No stock photography, no AI-generated
  boards or robots, no third-party logos.
- Charts: ink grid lines, one gradient colour per series family (warm for Sparrow tiers, neutral grey
  for reference models such as the public 2B). Always label units.
