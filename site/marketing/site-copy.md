# Sparrow Decider: website copy

For the web team. All copy is final unless marked *(optional)*. Every number here is from
`site/facts.json` (version noted below). If facts.json changes, update the number, not the sentence shape.
Styling notes in *italics* refer to `site/brand/BRAND.md` and `site/brand/tokens.css`.

- Facts version used: facts.json `_updated` 2026-10-23 (nano-general 3.8 ms on ESP32-S3; nano-robot v1.1 7.6 ms).
- Units: always a space before the unit (`9.3 µs`, `3.8 ms`, `2.2 MB`). Set numbers in Inter, never Sora (Sora has no µ).
- Links:
  - GitHub: https://github.com/sparrow-decider/sparrow-decider
  - Releases (Download models): https://github.com/sparrow-decider/sparrow-decider/releases
  - Docs: https://github.com/sparrow-decider/sparrow-decider/tree/main/docs/quickstart *(swap for the docs site if one ships)*
  - Issues: https://github.com/sparrow-decider/sparrow-decider/issues
  - Discussions: https://github.com/sparrow-decider/sparrow-decider/discussions

---

## Global

### Page titles and meta

| Page | `<title>` | Meta description |
|---|---|---|
| Home | Sparrow Decider: decisions that fit on a chip | Tiny decision models for agents, robots and microcontrollers. From 47 MB on a laptop to ~2 KB on a chip. 9.3 µs per decision on a $10 ESP32-S3. |
| Models | Models · Sparrow Decider | Decision models from 47 MB to ~2 KB per question. Pick by input, hardware and time budget. |
| Architecture | Architecture · Sparrow Decider | Distillation from a 4B Strands Decider, static embeddings with number pooling, and a compiler that turns a device spec into C. |
| Benchmarks | Benchmarks · Sparrow Decider | Measured timings on an ESP32-S3 and a laptop, quality against the public 2B Strands Decider, and the limits we know about. |
| Contact | Contact · Sparrow Decider | Questions, bugs and results from your hardware: GitHub Discussions and Issues. |
| 404 | Not found · Sparrow Decider | |

`og:image`: `previews/og-image.png` (1200 x 630). `og:title`: "Sparrow Decider". `og:description`: "Decisions that fit on a chip. 9.3 µs per decision on a $10 ESP32-S3."

### Navigation

- Logo (links home), aria-label: "Sparrow Decider home"
- Models
- Architecture
- Benchmarks
- Contact
- Button (ghost): **GitHub**
- Theme toggle, aria-label: "Switch to light theme" / "Switch to dark theme"
- Mobile menu button, aria-label: "Open menu" / "Close menu"
- Skip link: "Skip to content"

### Footer

**Column: Sparrow Decider**
Decisions that fit on a chip.
v0.2.0 · Apache-2.0

**Column: Product**
Models · Architecture · Benchmarks · Download models

**Column: Developers**
Read the docs · Python · ESP32-S3 · sparrow-pico · C library

**Column: Community**
GitHub · Discussions · Report an issue · Contact

**Bottom line (required, always visible):**
Unofficial community project. Not an AWS or Strands product.

**Second line:**
Built by the Sparrow Decider contributors. Code under Apache-2.0; model weights derived from MIT-licensed potion-base-8M and Ettin encoders. Strands Decider is referenced for compatibility and comparison only.

**Third line (small):**
No cookies, no tracking.

---

## Home

### Hero

**Eyebrow:** v0.2.0 · open source

**Headline:** Decisions that fit *on a chip.*
*("on a chip." in `.sd-gradient-text`; Sora 700, `--sd-text-hero`)*

**Subhead:** Tiny decision models for agents, robots and microcontrollers. From 47 MB on a laptop to ~2 KB on a chip, with calibrated answers in the same shapes as Strands Decider.

**Primary CTA (gradient button):** Download models
**Secondary CTA (ghost button):** View on GitHub
**Install block:** `pip install sparrow-decider` with copy button
**Tertiary link:** Read the docs →

**Proof line under CTAs:** 9.3 µs per decision on a $10 ESP32-S3. No GPU, no network, no model server.

### Live demo panel

*Animated state -> question -> answer. Show final state immediately under reduced motion.*

**Panel title:** One decision, start to finish
**Tabs:** Robot · Agent · Microcontroller

**Robot tab**
- State: `battery: 6%   front_obstacle_m: 7.0   path: clear`
- Question: What should the robot do next?
- Options: continue · slow · stop · dock · replan
- Answer: **dock**
- Caption: sparrow-nano-robot · text with sensor readings

**Agent tab**
- State: `User: I was charged twice for order 1182`
- Question: What does the user want?
- Options: refund · cancel · status
- Answer: **refund**
- Caption: sparrow-nano-general · pick-one, yes/no and score in one call

**Microcontroller tab**
- State: `sensors, flags and enums from your device`
- Question: compiled into the firmware
- Answer: one of the answers in your spec
- Caption: sparrow-pico · 9.3 µs per decision on an ESP32-S3

**Demo footnote:** Illustrative example. Probabilities shown in the demo are for illustration only; timings are measured, see Benchmarks.

*Web team: do not display made-up probability values as if measured. Either omit the probability bar values or label them "illustrative" as above.*

### Numbers band

**Section heading:** Numbers first.
**Intro:** Measured on an ESP32-S3 at 240 MHz and on a laptop. Every figure is on the Benchmarks page with its conditions.

| Value | Label |
|---|---|
| 9.3 µs | per decision on a $10 ESP32-S3 (sparrow-pico) |
| 3.8 ms | per text decision on the same chip (sparrow-nano-general) |
| 40 / 55 | robot decisions right: a 1.37 MB nano-robot v1.0 ties the public 2-billion-parameter Strands Decider |
| numpy only | Python install; C99 runtime with no malloc |
| ~2 KB | per compiled question (sparrow-pico, 501 parameters) |

**Link:** See every benchmark →

### What it does

**Heading:** Small questions. Calibrated answers.
**Body:** Most decisions in an agent or a robot have a short list of answers. Sparrow answers them about a state you give it, with calibrated probabilities, in the same shapes as Strands Decider.

**Three cards:**
1. **Yes / no** — "Is the user upset?" A probability you can threshold.
2. **Pick one** — "Which skill should run?" A choice from your list, with a probability for each option.
3. **Score** — "How urgent is this?" A rating on the scale you define.

### Tiers

**Heading:** From laptop to microcontroller.
**Body:** Pick the smallest model that fits your input and your hardware.

| Card | Title | Line 1 | Line 2 | Line 3 |
|---|---|---|---|---|
| pico | **pico** | ~2 KB per question | sensor numbers, flags, enums | 9.3 µs on an ESP32-S3 |
| nano | **nano** | 1.19 MB to 2.2 MB | text, or text with sensor readings | 3.8 ms (general) / 7.6 ms (robot) on an ESP32-S3 |
| micro | **micro** | 7.6 MB | text | 0.22 ms on a laptop (C) |
| tiny | **tiny** | 17.9 MB | text | 23 ms on a laptop (numpy) |
| small | **small** | 47 MB | text | 64 ms on a laptop (numpy) |

**Link:** Compare all models →

### Runs where you build

**Heading:** Three runtimes. Nothing extra.
- **Python** — `pip install sparrow-decider`. numpy only.
- **C99** — no malloc, model read from flash. Ships as an ESP-IDF component.
- **sparrow-pico compiler** — write a device spec, get a C header.

### Honest limits teaser

**Heading:** What it is not.
**Body:** Sparrow is for fixed-answer decisions about a known kind of state. It is well behind the 2B on open-ended language it never trained on, and yes/no judgement on JevBench is near chance at every tier. We publish the misses next to the wins.
**Link:** Read the limits →

### Closing CTA band

**Heading:** Give your device a decider.
**Body:** Install in one line, or flash a model to a $10 board.
**Buttons:** Download models · View on GitHub
**Install block:** `pip install sparrow-decider`

---

## Models

### Header

**Eyebrow:** Models
**Heading:** Pick the smallest bird that does the job.
**Subhead:** Every model answers yes/no, pick-one and score questions with calibrated probabilities. They differ in input, size and where they run.

### Comparison table

**Table caption:** The Sparrow Decider family. Timings are measured; blank cells were not measured.

| Tier | Model ID | Size | Input | Runs on | ESP32-S3 | Laptop | Quality |
|---|---|---|---|---|---|---|---|
| pico | `sparrow-pico-rover-v1.1` | ~2 KB per question (501 parameters) | sensor numbers, flags, enums | any microcontroller | 9.3 µs | 0.18 µs | 94.0% vs the spec's rules (its 2B teacher: 94.2%) |
| nano | `sparrow-nano-general-v1.1` | 2.2 MB | text | ESP32-S3, Raspberry Pi, laptop | 3.8 ms | 0.06 ms (C) | JevBench 122/231, MASSIVE intent 0.59 |
| nano | `sparrow-nano-robot-v1.1` | 1.19 MB | text with sensor readings | ESP32-S3, Pi, laptop | 7.6 ms | 0.09 ms (C) | RobotBench 38/55; navigation from sensor numbers 10/10 (public 2B: 3/10) |
| micro | `sparrow-micro-general-v1.1` | 7.6 MB | text | Pi, laptop | | 0.22 ms (C) | |
| tiny | `sparrow-tiny-general-v1.0` | 17.9 MB | text | laptop, Pi | | 23 ms (numpy) | |
| small | `sparrow-small-general-v1.0` | 47 MB | text | laptop, Pi, Jetson | | 64 ms (numpy) | |

### Model cards (body copy)

**pico: compiled for your device**
Numbers in, decision out. You write a spec of sensors, flags, enums, rules and questions, and the compiler writes one tiny MLP per question as a C header. The rover example is 501 parameters, ~2 KB per question, and takes 9.3 µs per decision on an ESP32-S3. It answers only the questions it was compiled for.
*Buttons:* Read the pico guide · Download

**nano-general: text on a microcontroller**
2.2 MB. Reads text and answers in 3.8 ms on an ESP32-S3, or 0.06 ms on a laptop in C. Good for routing and gating inside an agent when you want no network call.
*Buttons:* Read the ESP32-S3 guide · Download

**nano-robot: text with sensor readings**
1.19 MB. Reads states like `battery: 6%` as values, not words. 7.6 ms per decision on an ESP32-S3. v1.1 gets navigation from sensor numbers right 10/10 (the public 2B: 3/10) and scores 38/55 on RobotBench. The earlier v1.0 (1.37 MB) scores 40/55, the same as the public 2B. Choose v1.1 for navigation, v1.0 for the broader benchmark.
*Buttons:* Read the robot guide · Download

**micro, tiny, small: more room, more reach**
7.6 MB, 17.9 MB and 47 MB text models for a Raspberry Pi, a laptop or a Jetson.
*Buttons:* Read the Python guide · Download

### How to choose

**Heading:** Which one?
- Your input is sensor numbers and the questions never change → **pico**
- Your input is text and the device is an ESP32-S3 → **nano-general**
- Your input mixes text and sensor readings → **nano-robot**
- You have a Pi, a laptop or a Jetson and want more headroom → **micro**, **tiny** or **small**

**Note:** License: Apache-2.0 (code); model weights derived from MIT-licensed potion-base-8M and Ettin encoders.

---

## Architecture

### Header

**Eyebrow:** Architecture
**Heading:** Big teacher. Small student. Plain C.
**Subhead:** How a 4B decider's judgement ends up in a few KB of firmware.

### Section 1: Distillation

**Heading:** Taught by a full Strands Decider
**Body:** A full Strands Decider (4B) teaches the text tiers through distillation on ~430k decisions. The students keep the same question shapes, so a schema written for Strands Decider works here.

### Section 2: nano

**Heading:** Static embeddings that can read a number
**Body:** nano uses static embeddings over a pruned 8-16k vocabulary at 128 dimensions. Key-value number pooling reads `battery: 6%` as a value, so sensor readings in text are not just tokens.
*Diagram labels:* text in → tokens → static embeddings (128-d) → number pooling → decision head → probabilities

### Section 3: pico

**Heading:** A compiler, not a model download
**Body:** You write a spec: sensors, rules and questions. The public Strands Decider 2B labels sampled states. The compiler writes one tiny MLP per question as C. Your firmware includes the header and calls a function.
*Diagram labels:* device spec → sampled states → labels from the public 2B → one MLP per question → C header → your firmware

### Section 4: On the chip

**Heading:** Built for the ESP32-S3
**Body:** int8 SIMD on the vector unit through the ESP-NN kernel, with weights in PSRAM or internal RAM. The C99 runtime has no malloc and reads the model from flash. The C runtime matches the Python runtime to within 1e-5 on the host; on the ESP32-S3, int8 builds agree with the host on 150-155 of 155 decisions.
**Spec line:** ESP32-S3 (QFN56 rev0.2) · 240 MHz · 16 MB flash · 8 MB PSRAM

### Section 5: Runtimes

| Runtime | What you get |
|---|---|
| Python | numpy only |
| C99 | no malloc, model read from flash, ESP-IDF component |
| sparrow-pico compiler | device spec in, C header out |

---

## Benchmarks

### Header

**Eyebrow:** Benchmarks
**Heading:** Measured, with the conditions attached.
**Subhead:** On-chip timings are from an ESP32-S3 (QFN56 rev0.2), 240 MHz, 16 MB flash, 8 MB PSRAM. Laptop timings name the runtime.

### Section 1: Speed on the chip

**Heading:** Time per decision on an ESP32-S3
| Model | Time |
|---|---|
| sparrow-pico-rover-v1.1 | 9.3 µs |
| sparrow-nano-general-v1.1 | 3.8 ms |
| sparrow-nano-robot-v1.1 | 7.6 ms |

**Chart note:** pico is in µs and nano in ms; plot them on separate charts (or a log scale) and label the units on every bar.

### Section 2: How we got there

**Heading:** Every release got faster
- nano-general: 9.6 ms → 3.8 ms
- nano-robot: 73.5 ms (first run) → 13.2 ms (v1.0) → 7.6 ms (v1.1)
- pico: 42.9 µs → 9.3 µs

### Section 3: Speed on a laptop

| Model | Time |
|---|---|
| sparrow-pico-rover-v1.1 | 0.18 µs |
| sparrow-nano-general-v1.1 | 0.06 ms (C) |
| sparrow-nano-robot-v1.1 | 0.09 ms (C) |
| sparrow-micro-general-v1.1 | 0.22 ms (C) |
| sparrow-tiny-general-v1.0 | 23 ms (numpy) |
| sparrow-small-general-v1.0 | 64 ms (numpy) |

### Section 4: Quality

**Heading:** Against the public 2B
- **Robot decisions (RobotBench):** nano-robot v1.0 (1.37 MB) 40/55, the same as the public 2B Strands Decider (40/55). nano-robot v1.1 (1.19 MB) 38/55.
- **Navigation from sensor numbers:** nano-robot v1.1 10/10; public 2B 3/10.
- **pico vs its spec's rules:** 94.0%; its 2B teacher 94.2%.
- **General text (nano-general v1.1):** JevBench 122/231, MASSIVE intent 0.59.

### Section 5: Correctness on the chip

**Heading:** How closely the chip matches the host
**Body:** The C runtime matches the Python runtime to within 1e-5 on the host; on the ESP32-S3, int8 builds agree with the host on 150-155 of 155 decisions.

### Section 6: Honest limits

**Heading:** Where it falls short
- Open-ended language it never trained on: well behind the 2B (MASSIVE domain routing 0.52-0.67 vs 0.86).
- Yes/no judgement on JevBench is near chance at every tier.
- pico answers only the questions it was compiled for.

**Closing line:** Run it on your hardware and tell us what you measure.
**Button:** Share your results (links to Discussions)

**Evaluation data credit:** Amazon MASSIVE (CC BY 4.0, evaluation only) · JevBench (MIT, evaluation only)

---

## Contact

**Eyebrow:** Contact
**Heading:** Talk to the flock.
**Subhead:** Sparrow Decider is built in the open by the Sparrow Decider contributors. GitHub is the best place to reach us.

**Card 1: Questions and ideas**
Ask how to fit a decision to your device, share what you built, or post benchmark results from your hardware.
*Button:* Open Discussions

**Card 2: Bugs and requests**
Something wrong or missing? File an issue with your model ID, runtime and hardware.
*Button:* Open an issue

**Card 3: Contribute**
Code is Apache-2.0. Read the contributing guide on GitHub before opening a pull request.
*Button:* View on GitHub

**Note:** We do not offer paid support, and we do not collect email addresses on this site.

**Disclaimer block:** Unofficial community project. Not an AWS or Strands product. For questions about Strands Decider itself, please use that project's own channels.

---

## Microcopy

### Buttons

| Context | Label |
|---|---|
| Primary download | Download models |
| GitHub | View on GitHub |
| Docs | Read the docs |
| Copy install | Copy |
| Copy success | Copied |
| Copy failure | Press Ctrl+C to copy (or Cmd+C) |
| Model card download | Download |
| Guide link | Read the guide |
| Demo replay | Run again |
| Back to top | Back to top |
| Share results | Share your results |

### Tooltips

| Element | Tooltip |
|---|---|
| Copy button | Copy install command |
| Theme toggle | Switch theme |
| "~2 KB per question" | Size of one compiled pico question for the rover example (501 parameters). |
| "9.3 µs" | sparrow-pico-rover-v1.1 on an ESP32-S3 at 240 MHz. |
| "3.8 ms" | sparrow-nano-general-v1.1 on an ESP32-S3 at 240 MHz. |
| "40 / 55" | RobotBench, sparrow-nano-robot-v1.0 (1.37 MB). The public 2B Strands Decider also scores 40/55. |
| "150-155 of 155" | int8 builds on the ESP32-S3 compared with the host; differences come from int8 rounding near ties. |
| "numpy only" | The Python package's only dependency. |
| "calibrated" | The probability reflects how often the answer is right, so you can set a threshold. |
| "public 2B" | The public 2-billion-parameter Strands Decider, used for comparison. |
| "no malloc" | The C99 runtime allocates no heap memory; the model is read from flash. |
| Blank table cell | Not measured. |

### Status and empty states

- Demo loading: Thinking small…
- Demo reduced-motion label: Showing the final answer. Animation is off because your system prefers reduced motion.
- JavaScript off (noscript): The demo needs JavaScript. Everything else on this site works without it.
- Copy unavailable: Select the command and copy it.

### Accessibility labels

- Logo image alt: "Sparrow Decider"
- OG / hero art alt: "Sparrow Decider logo: a geometric sparrow in a sunrise gradient"
- Stat group: aria-label "Headline measurements"
- Demo region: aria-live="polite", label "Decision demo"

---

## 404

**Heading:** This branch was never compiled.
**Body:** sparrow-pico only answers the questions it was built for, and this page was not one of them.
**Buttons:** Back to home · Browse models
**Small:** Think a link is broken? Open an issue.
