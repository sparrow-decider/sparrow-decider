# Sparrow Decider press kit

**Unofficial community project. Not an AWS or Strands product.**

Contact: [GitHub Discussions](https://github.com/sparrow-decider/sparrow-decider/discussions) ·
[GitHub Issues](https://github.com/sparrow-decider/sparrow-decider/issues)
Repository: https://github.com/sparrow-decider/sparrow-decider
Current version: 0.2.0

---

## Boilerplate

**Short (25 words)**
Sparrow Decider is an open-source family of tiny decision models, from 47 MB on a laptop to ~2 KB on
a microcontroller, built by the Sparrow Decider contributors.

**Standard (about 80 words)**
Sparrow Decider is an open-source family of decision models that answer yes/no, pick-one and score
questions about a state, with calibrated probabilities, in the same shapes as Strands Decider. The
family ranges from a 47 MB model on a laptop down to a ~2 KB compiled model on a microcontroller,
which decides in 9.3 µs on a $10 ESP32-S3. Python needs only numpy; the C99 runtime uses no malloc.
Sparrow Decider is built by the Sparrow Decider contributors and released under Apache-2.0.
Unofficial community project. Not an AWS or Strands product.

---

## Key facts

| | |
|---|---|
| Name | Sparrow Decider (short form: Sparrow) |
| Tagline | Decisions that fit on a chip. |
| Version | 0.2.0 |
| What | Decision models for yes/no, pick-one and score questions about a state, with calibrated probabilities, in the same shapes as Strands Decider |
| Range | 47 MB (laptop) to ~2 KB per question (microcontroller) |
| Install | `pip install sparrow-decider` (Python, numpy only) |
| Runtimes | Python (numpy only); C99 with no malloc, model read from flash (ESP-IDF component); sparrow-pico compiler (device spec to C header) |
| License | Apache-2.0 (code); model weights derived from MIT-licensed potion-base-8M and Ettin encoders |
| Built by | The Sparrow Decider contributors |
| Affiliation | None. Unofficial community project. Not an AWS or Strands product. |

### Headline numbers

All on-chip figures measured on an ESP32-S3 (QFN56 rev0.2), 240 MHz, 16 MB flash, 8 MB PSRAM.

| Value | Meaning |
|---|---|
| **9.3 µs** | per decision on a $10 ESP32-S3 (sparrow-pico) |
| **3.8 ms** | per text decision on the same chip (sparrow-nano-general) |
| **40 / 55** | robot decisions right: a 1.37 MB nano-robot v1.0 ties the public 2-billion-parameter Strands Decider |
| **numpy only** | Python install; C99 runtime with no malloc |
| **~2 KB** | per compiled question (sparrow-pico, 501 parameters) |

Parity: The C runtime matches the Python runtime to within 1e-5 on the host; on the ESP32-S3, int8 builds agree with the host on 150-155 of 155 decisions.

### The family

| Tier | Model ID | Size | Input | Runs on | Measured time | Quality |
|---|---|---|---|---|---|---|
| pico | sparrow-pico-rover-v1.1 | ~2 KB per question (501 parameters) | sensor numbers, flags, enums | any microcontroller | 9.3 µs (ESP32-S3); 0.18 µs (laptop) | 94.0% vs the spec's rules (its 2B teacher: 94.2%) |
| nano | sparrow-nano-general-v1.1 | 2.2 MB | text | ESP32-S3, Raspberry Pi, laptop | 3.8 ms (ESP32-S3); 0.06 ms (laptop, C) | JevBench 122/231, MASSIVE intent 0.59 |
| nano | sparrow-nano-robot-v1.1 | 1.19 MB | text with sensor readings | ESP32-S3, Pi, laptop | 7.6 ms (ESP32-S3); 0.09 ms (laptop, C) | RobotBench 38/55; navigation from sensor numbers 10/10 (public 2B: 3/10) |
| micro | sparrow-micro-general-v1.1 | 7.6 MB | text | Pi, laptop | 0.22 ms (laptop, C) | |
| tiny | sparrow-tiny-general-v1.0 | 17.9 MB | text | laptop, Pi | 23 ms (laptop, numpy) | |
| small | sparrow-small-general-v1.0 | 47 MB | text | laptop, Pi, Jetson | 64 ms (laptop, numpy) | |

Earlier model `sparrow-nano-robot-v1.0` (1.37 MB): RobotBench 40/55, same as the public Strands Decider 2B (40/55).

### Optimisation history on the ESP32-S3

- nano-general: 9.6 ms -> 3.8 ms
- nano-robot: 73.5 ms (first run) -> 13.2 ms (v1.0) -> 7.6 ms (v1.1)
- pico: 42.9 µs -> 9.3 µs

### How it works (one paragraph)

A full Strands Decider (4B) teaches the text tiers through distillation on ~430k decisions. The nano
tier uses static embeddings, a pruned 8-16k vocabulary at 128 dimensions, and key-value number pooling
that reads "battery: 6%" as a value. For pico, a developer writes a spec of sensors, rules and questions;
the public Strands Decider 2B labels sampled states; the compiler writes one tiny MLP per question as C.
On the ESP32-S3, inference uses int8 SIMD on the vector unit (ESP-NN kernel) with weights in PSRAM or internal RAM.

### Known limits

- Open-ended language it never trained on: well behind the 2B (MASSIVE domain routing 0.52-0.67 vs 0.86).
- Yes/no judgement on JevBench is near chance at every tier.
- pico answers only the questions it was compiled for.

### Credits

potion-base-8M (MinishLab, MIT) · Ettin encoders (JHU CLSP, MIT) · Strands Decider (Apache-2.0) ·
ESP-NN (Espressif, Apache-2.0) · Amazon MASSIVE (CC BY 4.0, evaluation only) · JevBench (MIT, evaluation only)

---

## Assets

All in `site/brand/`. SVG is the master; PNG renders are in `site/brand/previews/`.

| Asset | File | Notes |
|---|---|---|
| Logo mark | `logo-mark.svg` | Transparent, gradient. PNG: `previews/logo-mark-512-dark.png`, `previews/logo-mark-512-light.png` |
| Wordmark, dark backgrounds | `logo-wordmark.svg` | PNG: `previews/logo-wordmark.png` |
| Wordmark, light backgrounds | `logo-wordmark-light.svg` | PNG: `previews/logo-wordmark-light.png` |
| App icon / favicon | `favicon.svg` | Ink tile. PNG: `previews/favicon-512.png`, `-32`, `-16` |
| Social card 1200 x 630 | `og-image.svg` | PNG: `previews/og-image.png` |
| Colours, type, usage | `BRAND.md`, `tokens.css` | |

Colours: ink `#0B1020`, sunrise gradient `#FFB547` -> `#FF6B4A` -> `#FF3D8B` -> `#8B5CF6`, cyan accent `#22D3EE`, paper `#F5F7FF`.
Fonts: Sora (display), Inter (body), JetBrains Mono (code). All Google Fonts.

Please do not recolour, rotate or redraw the mark, and do not place it beside AWS or Strands logos in a
way that suggests endorsement.

---

## Style notes for writers

- Write "Sparrow Decider" on first mention, then "Sparrow".
- Always state the hardware with a timing: "9.3 µs per decision on an ESP32-S3", not "9.3 µs decisions".
- Comparisons are with "the public 2B Strands Decider" (2 billion parameters).
- There are no customer, user, download or star figures to quote. Please do not estimate any.
- Please include: "Unofficial community project. Not an AWS or Strands product."
