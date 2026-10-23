# Home page spec

File: `site/www/index.html`. Scripts: `assets/js/site.js` (shared), `assets/js/hero.js`, `assets/js/charts.js`
(all `defer`). Tokens, easings and breakpoints referenced here (`--ease-out`, `--dur-m`, `md`, ...) are defined in
`interaction.md`.

Sections, in order:

| # | id | Section | Purpose |
|---|---|---|---|
| 1 | `#top` | Hero + decision-trace animation | Say what it is, prove the speed, get the install |
| 2 | `#numbers` | Headline numbers band | Five verified numbers, nothing else |
| 3 | `#tiers` | Pick your tier | Map the family to the reader's hardware |
| 4 | `#code` | Code tabs | Show it is real and small to use |
| 5 | `#pico-or-nano` | pico or nano? | Remove the one real choice-paralysis point |
| 6 | `#on-chip` | On-chip speedup story | The engineering brag, as a chart |
| 7 | `#limits` | Honest limits | Earn trust; tell people when not to use it |
| 8 | `#get-started` | Final CTA band | Convert |

Global layout: 12-column grid, max content width 1200 px, column gap 24 px (desktop), 20 px (tablet),
16 px side gutters and single column (mobile). Section vertical padding: 128 px desktop, 96 px tablet,
72 px mobile. Each section after the hero gets an eyebrow (mono, 12 px, uppercase, letter-spacing 0.08em,
cyan accent) + H2 (display face) + optional one-sentence lede (muted, 18 px, max 60ch).

---

## 1. Hero (`#top`)

### Purpose
In under five seconds: what it is (tiny decision models), the proof (9.3 µs on a $10 chip), and the next
action (`pip install`).

### Content

- **Eyebrow chip** (pill, mono 12 px): `v0.1.0 · Apache-2.0 · numpy only`
  (version from `facts.version`; licence from `facts.license`; "numpy only" from `facts.headline_numbers`).
- **H1** (brand team may swap from the shortlist in BRIEF.md; layout must fit any of them in two lines at
  desktop): **"Decide in microseconds."** The word "microseconds" gets the sunrise gradient text fill
  (dark theme) / deep gradient (light theme, see interaction.md 1.1, `--sunrise`).
- **Subhead** (20 px desktop / 18 px mobile, muted, max 54ch):
  "Sparrow Decider is a family of tiny decision models. They answer yes/no, pick-one and score questions
  about a state, with calibrated probabilities, in the same shapes as Strands Decider. From a 47 MB model on a
  laptop down to a ~2 KB compiled model on a microcontroller."
  (Paraphrase of `facts.what`; do not add numbers.)
- **Proof line** (mono 14 px, off-white, with a 6 px pulsing cyan dot before it):
  `9.3 µs per decision on a $10 ESP32-S3`
- **Primary CTA: install command block** (component `copy-command`, large):
  ```
  $ pip install sparrow-decider            [Copy]
  ```
  - Whole block is one `<div>` with the command in `<code>` and a `<button>` "Copy".
  - The `$ ` prompt is `aria-hidden` and excluded from the copied text and from selection (`user-select: none`).
  - Copies exactly `pip install sparrow-decider` (from `facts.install`).
  - States: idle (copy icon + "Copy"), success (check icon + "Copied", cyan, 1600 ms then revert), failure
    (fallback: select the command text and show "Press Ctrl/Cmd+C").
  - Announce via a visually hidden `aria-live="polite"` region: "Copied pip install sparrow-decider".
- **Secondary CTAs** (row of buttons, below the install block):
  1. `Download models` -> `releases` (secondary button style: 1 px gradient border, transparent fill).
  2. `View on GitHub` -> `repo` (ghost button with GitHub mark).
  3. `Docs` -> `docs` (text link with arrow).
- **Hero foot-note** (13 px muted, below CTAs): "Unofficial community project. Not an AWS or Strands product."

### Layout

- **Desktop (>= 1024 px):** two columns. Text column spans 6 of 12 columns, trace visual spans 6 columns,
  vertically centred. Hero min-height `min(88vh, 860px)`; content top padding 96 px below the header.
  Background: ink with two large blurred radial gradients (amber-coral at top-left, violet-pink at
  bottom-right), each 40% opacity, plus a 1 px dot grid at 6% opacity masked to fade out at the edges.
  All background art is CSS only (no images).
- **Tablet (768-1023 px):** single column. Text first (left-aligned, max-width 640 px), then the
  trace visual full-width below, max-width 640 px.
- **Mobile (< 768 px):** single column. H1 40-44 px (clamp, see type scale). Install block is full width, the
  Copy button stays on the same line (command may scroll horizontally inside the block, never wraps).
  Secondary CTAs: `Download models` and `View on GitHub` side by side at 50% each; `Docs` link below.
  Trace visual below the CTAs, full width, its typography drops one step.

### Hero visual: "Decision trace" animation

A terminal-style card that replays real decisions from the ESP32-S3 example firmware
(`c/examples/esp32s3_robot/main/main.c`, output shown in `docs/quickstart/esp32.md`), slowed down so the eye
can follow, with a latency counter that shows real units.

**Card anatomy** (top to bottom; card is surface colour, 16 px radius, 1 px hairline border, subtle
inner glow from the sunrise gradient along the top edge):

1. **Title bar:** three neutral dots (decorative) + mono label left `esp32-s3 · 240 MHz` (from `facts.board`)
   and right a model chip, e.g. `sparrow-pico` or `sparrow-nano-robot`.
2. **State block:** label `state` (mono 12 px, muted) then key-value lines, mono 14 px, each line
   `key: value` with the value in off-white and the key in muted.
3. **Question line:** label `question` + the question text in body font 16 px.
4. **Options + probability strip:** options rendered as chips in a row (wrap allowed). Under them, a single
   horizontal **probability strip** (full width, 10 px high, 5 px radius).
5. **Answer line:** label `answer`, the winning option name in display face 22 px with gradient fill.
6. **Latency counter** (bottom-right, mono 28 px tabular numerals): counts in the scene's real unit.
   Beneath it, 11 px muted: the slow-down label, e.g. `replayed 250,000x slower`.

**Scenes** (loop A -> B -> A -> ...):

| Scene | Chip | State | Question | Options | Winner | Counter end value |
|---|---|---|---|---|---|---|
| A | `sparrow-pico` | `battery: 6%` `front_obstacle_m: 7.0` `goal_m: 30` `path: clear` `carrying_load: no` | What should the robot do next? | continue, slow, stop, dock, replan | dock | `9.3 µs` |
| B | `sparrow-nano-robot` | `operator: grab that blue bottle` | Which skill should the robot run? | pick, place, navigate, speak, stop | pick | `13.2 ms` |

States, questions, options and winners are copied from the example firmware. Counter end values are from
`facts.tiers` (`esp32s3` field for pico and nano-robot).

**Probability values in the strip.** The example log in `docs/quickstart/esp32.md` shows the winner's
probability (scene A: `dock (p=0.81)`; scene B: `pick (confidence 0.93)`). These are **not in facts.json**.
- If the lead adds them to facts.json (proposed key `hero_trace`, see "Facts requests" at the end), the strip
  shows a gradient segment of that width labelled `dock 0.81`, and a neutral hatched remainder segment
  labelled `other options 0.19`. Never split the remainder among the other options (we do not have those
  values).
- If not added, the strip shows the winner segment at a fixed visual 80% width with **no numeric label**, and
  the card caption reads "Probabilities illustrative." Either way, no invented per-option values.

**Slow-down labels** (exact arithmetic, display these strings):
- Scene A: animation resolve phase lasts 2,325 ms for 9.3 µs -> `replayed 250,000x slower`.
- Scene B: resolve phase lasts 2,640 ms for 13.2 ms -> `replayed 200x slower`.
The contrast between the two labels is the story: same chip, text model in milliseconds, compiled model in
microseconds.

**Timeline per scene** (t = 0 at scene start; all easings defined in interaction.md 2):

| t (ms) | Event | Motion |
|---|---|---|
| 0 | Card content cross-fades from previous scene | outgoing fade 160 ms `--ease-in`; incoming 240 ms `--ease-out` |
| 0-480 | State lines type in, one line per 120 ms | each line: opacity 0 -> 1, translateY 4 px -> 0, 200 ms `--ease-out` |
| 480-720 | Question line appears | same as above |
| 720-960 | Option chips pop in, 40 ms stagger | scale 0.96 -> 1 + opacity, 180 ms `--ease-out` |
| 960 | Counter starts at `0.0` (unit fixed: µs or ms) | |
| 960-(960+R) | **Resolve phase** (R = 2,325 ms scene A, 2,640 ms scene B). A thin cyan scan line sweeps the chips left to right twice. Counter counts up linearly in real units (linear easing on purpose: it is a clock). Strip segment grows from 0 to its width with `--ease-in-out`. | counter updates every animation frame, formatted to one decimal place; final value snaps to the exact facts string |
| end of R | Winner chip lights: gradient border + glow, 220 ms `--ease-spring`; other chips dim to 45% opacity. Answer line types the winner name. Counter gets a 1-frame cyan flash. | |
| +1,800 hold | Hold the resolved frame | |
| then | Next scene | |

Total loop A + B: about 4.0 s + 4.4 s + holds = ~12 s.

**Controls:**
- A small icon button top-right of the card: pause/play (`aria-label="Pause animation"` / `"Play animation"`,
  `aria-pressed`). WCAG 2.2.2 requires this because the loop runs longer than 5 s.
- Animation pauses when the card is off-screen (IntersectionObserver, threshold 0.1) and when
  `document.hidden`.
- Hovering the card does not pause (avoids accidental freezes); focus on the pause button shows its focus ring.

**Accessibility:**
- The card is a `<figure>` (not `role="img"`) with a visually hidden `<figcaption>`:
  "Example decisions from the ESP32-S3 example firmware. sparrow-pico: battery 6%, clear path, answer dock,
  9.3 microseconds. sparrow-nano-robot: 'operator: grab that blue bottle', answer pick, 13.2 milliseconds."
- Animated text nodes are `aria-hidden="true"`; the figcaption carries the meaning. No live-region chatter.

**Reduced motion (`prefers-reduced-motion: reduce`) fallback:**
- No loop, no typing, no scan line, no counter animation.
- Render scene A fully resolved (all lines, winner highlighted, counter showing `9.3 µs`), and below the
  card a two-button segmented control `pico | nano-robot` that swaps to scene B's resolved frame instantly.
- The pause button is hidden (nothing moves).

**No-JS fallback:** the HTML contains scene A fully resolved (static markup). JS enhances it into the loop.

**Implementation notes:** pure DOM + CSS transitions driven by a `requestAnimationFrame` clock in `hero.js`
(< 6 KB minified). No canvas, no library. Use `font-variant-numeric: tabular-nums` on the counter so digits do
not jitter. Counter width reserved with `min-width: 7ch`.

---

## 2. Headline numbers band (`#numbers`)

### Purpose
Five numbers that do the bragging. Verbatim from `facts.headline_numbers`, in that order.

### Content

| Value | Label |
|---|---|
| `9.3 µs` | per decision on a $10 ESP32-S3 (sparrow-pico) |
| `4.4 ms` | per text decision on the same chip (sparrow-nano) |
| `1.37 MB` | nano-robot ties the public 2B decider on robot decisions (40/55) |
| `numpy only` | Python install; C99 runtime with no malloc |
| `155 / 155` | on-chip answers identical to the host runtime |

### Layout
- A full-bleed band with surface background and top + bottom hairlines. No section heading visible
  (use a visually hidden H2 "Sparrow Decider in numbers").
- **Desktop:** 5 equal columns, separated by 1 px vertical dividers. Value: display face 44 px, weight 600,
  gradient text for the first item only (the hero number), off-white for the rest. Label: 14 px muted,
  max 24ch, below the value.
- **Tablet:** 3 + 2 grid (second row centred).
- **Mobile:** 2-column grid; first item spans both columns (it is the hero number). Value 34 px.

### Interaction / animation
- Count-up starts when the band is 35% in view (once only).
- `9.3`: 0.0 -> 9.3, one decimal. `4.4`: 0.0 -> 4.4. `1.37`: 0.00 -> 1.37, two decimals. `155 / 155`:
  numerator counts 0 -> 155 (integer), denominator static. Units (`µs`, `ms`, `MB`) are static text, not counted.
- `numpy only`: no counting; the text reveals with a left-to-right clip-path wipe, 600 ms `--ease-out`.
- Duration 1,200 ms, easing `--ease-out-expo`, 90 ms stagger left to right.
- The final rendered text must equal the facts string exactly (set `textContent` to the facts string on the
  last frame).
- Screen readers: each value is real text in the HTML; JS only animates a visual copy marked `aria-hidden`,
  with the real value in a visually hidden span. Reduced motion: no count-up, values shown immediately.

---

## 3. Pick your tier (`#tiers`)

### Purpose
Answer "which one runs on my thing?" in one interaction.

### Content
Eyebrow `THE FAMILY`. H2: "From 47 MB to ~2 KB. Pick your tier." Lede: "Same question format at every size.
Smaller tiers trade breadth for speed and footprint."

Tier data (from `facts.tiers`; display only fields that exist; never fill gaps):

| Tab | Model ID(s) | Size | Input | Where it runs | ESP32-S3 | Laptop | Quality note |
|---|---|---|---|---|---|---|---|
| pico | sparrow-pico-rover-v1.1 | ~2 KB per question (501 parameters) | sensor numbers, flags, enums | any microcontroller | 9.3 µs per decision | 0.18 µs | 94.0% vs the spec's rules (its 2B teacher: 94.2%) |
| nano · general | sparrow-nano-general-v1.1 | 2.2 MB | text | ESP32-S3, Raspberry Pi, laptop | 4.4 ms per decision | (omit) | general text decisions |
| nano · robot | sparrow-nano-robot-v1.0 | 1.37 MB | text with sensor readings | ESP32-S3, Pi, laptop | 13.2 ms per decision | 0.12 ms (C) | RobotBench 40/55, same as the public Strands Decider 2B (40/55) |
| micro | sparrow-micro-general-v1.1 | 7.6 MB | text | Pi, laptop | (omit) | 0.22 ms (C) | (omit) |
| tiny | sparrow-tiny-general-v1.0 | 17.9 MB | text | laptop, Pi | (omit) | 23 ms (numpy) | (omit) |
| small | sparrow-small-general-v1.0 | 47 MB | text | laptop, Pi, Jetson | (omit) | 64 ms (numpy) | (omit) |

"(omit)" means the row of the spec sheet is not rendered at all, not rendered as "n/a" or "-".

Per-tier action link:
- pico: "Compile your own" -> `guide.pico`
- nano: "pip install, then `Decider.load()`" -> `guide.python`
- micro / tiny / small: "Download from releases" -> `releases`

### Layout

```
[ pico ][ nano ][ micro ][ tiny ][ small ]           <- segmented tabs (role=tablist)

  size ruler (log scale, 1 KB ... 100 MB)
  |----*-----------------------------------------|   <- marker slides to the tier

  +-------------------------+  +-----------------+
  | sparrow-pico-rover-v1.1 |  |  where it runs  |
  | Size      ~2 KB ...     |  |  [chip icon]    |
  | Input     sensor ...    |  |  any micro-     |
  | ESP32-S3  9.3 µs ...    |  |  controller     |
  | Laptop    0.18 µs       |  +-----------------+
  | Quality   94.0% vs ...  |
  | [Compile your own ->]   |
  +-------------------------+
```

- **Segmented tabs:** 5 tabs, equal width, pill container 48 px tall. Selected tab: surface-raised fill +
  gradient 2 px bottom bar. Under "nano" a secondary 2-option toggle appears inside the panel:
  `general | robot` (default `robot`, because it carries the RobotBench and 13.2 ms facts).
- **Size ruler:** full-width SVG, 48 px tall. Log-scale axis from 1 KB to 100 MB with ticks at 1 KB, 10 KB,
  100 KB, 1 MB, 10 MB, 100 MB (labels mono 11 px). A dot for every model at its size (positions:
  2 KB, 1.37 MB, 2.2 MB, 7.6 MB, 17.9 MB, 47 MB) in muted colour; the selected tier's dot grows to 12 px, takes
  the gradient fill, and a label above it shows the size string from facts. Purpose: make "47 MB to 2 KB"
  physically visible.
- **Spec sheet panel:** two columns on desktop: left (8 cols) a definition list (`<dl>`) with mono values;
  right (4 cols) a "where it runs" tile with simple line icons (MCU chip, Pi board, laptop, Jetson module:
  generic outline icons, no vendor logos) highlighting the hardware listed in `where`.
- **Tablet:** same, "where it runs" tile moves under the spec sheet.
- **Mobile:** tabs become a horizontally scrollable row of pills (scroll-snap, the selected one scrolled into
  view). Ruler keeps full width but shows only 1 KB / 1 MB / 100 MB labels. Spec sheet single column.

### Interaction
- ARIA tabs pattern: Left/Right arrows move and activate, Home/End jump, Tab moves into the panel.
- Panel content swaps with a 180 ms cross-fade; ruler marker slides with 420 ms `--ease-in-out`.
- Default selected tab: **pico** (it is the headline story).
- URL hash sync is not used (avoid scroll jumps).
- Reduced motion: no slide, instant swap.
- No-JS: all tiers render as stacked cards (the panels are visible; tabs hidden via the `.js` class).

---

## 4. Code tabs (`#code`)

### Purpose
Show it is real, small, and the same API everywhere.

### Content
Eyebrow `USE IT`. H2: "Three question types. Five ways in." Lede: "`noul` for yes/no, `choice` to pick one,
`score` to rate on a scale. Same shapes as Strands Decider."

Tabs: `Python` · `CLI` · `C` · `ESP32-S3` · `pico spec`. Snippets below are copied from the docs; keep them
verbatim except where noted. Each panel: code block, then a footer row with "Copy" button and
"Full guide ->" link.

**Python** (from `docs/quickstart/python.md`; the inline comment naming a model version is removed because
the docs and facts.json differ on the bundled version) -> link `guide.python`
```python
from sparrow_decider import Decider

d = Decider.load()   # bundled nano model

answers = d.ask(
    "User: I was charged twice for order 1182 and nobody replied to my email.",
    {
        "intent":  {"type": "choice", "instructions": "What does the user want?",
                    "criteria": {"refund": "money back for a charge", "cancel": "stop an order",
                                 "status": "where is my order"}},
        "upset":   {"type": "noul",   "instructions": "Is the user upset?"},
        "urgency": {"type": "score",  "instructions": "How urgent is this?",
                    "criteria": ["can wait", "today", "right now"]},
    },
)
print(answers["intent"]["choice"], answers["intent"]["confidence"])
```

**CLI** (from `docs/quickstart/python.md`) -> link `guide.python`
```bash
pip install sparrow-decider
sparrow-decider models
sparrow-decider ask "battery: 6%\nfront_obstacle_m: 7.0" --model nano-robot \
    --choice "What next?" -o "continue=keep going" -o "dock=go charge" -o "stop=halt"
sparrow-decider serve --port 8000        # POST /v1/systemone
```

**C** (from `docs/quickstart/c.md`) -> link `guide.c`
```c
#include "sparrow.h"
static sparrow_model m;
static sparrow_ctx ctx;   /* working memory; keep it static */

sparrow_load(&m, blob, blob_len);
float p_true = sparrow_noul(&m, &ctx, "motor_temp_c: 96\nmax_temp_c: 80", "Is the motor overheating?");
float conf;
int k = sparrow_choice(&m, &ctx, state, "Which skill?", opts, n_opts, &conf);
float level = sparrow_score(&m, &ctx, state, "How urgent?", levels, n_levels, &conf);
```

**ESP32-S3** (from `docs/quickstart/esp32.md`) -> link `guide.esp32`
```c
#include "sparrow.h"

extern const uint8_t model_start[] asm("_binary_model_spb_start");
extern const uint8_t model_end[]   asm("_binary_model_spb_end");
static sparrow_model model;
static sparrow_ctx ctx;

void app_main(void) {
    sparrow_load(&model, model_start, model_end - model_start);
    sparrow_option opts[] = {{"pick", "pick up an object"}, {"navigate", "move somewhere"},
                             {"speak", "answer the person"}};
    float conf;
    int k = sparrow_choice(&model, &ctx, "operator: bring me the red mug", "Which skill?", opts, 3, &conf);
}
```

**pico spec** (from `docs/quickstart/pico.md`). This panel is split: left the spec JSON, right the generated
C usage, joined by a small arrow labelled `pico_compile.py build`. On mobile they stack. -> link `guide.pico`
```json
{
  "name": "greenhouse",
  "context": "open vents when it is above 30 C; water when soil moisture is below 25%; never water and vent at the same time in frost.",
  "features": [
    {"name": "temp_c",        "type": "number", "min": -10, "max": 50},
    {"name": "soil_moisture", "type": "number", "min": 0,   "max": 100, "unit": "%"},
    {"name": "raining",       "type": "bool"},
    {"name": "time_of_day",   "type": "enum", "values": ["night", "morning", "afternoon", "evening"]}
  ],
  "questions": {
    "action":   {"type": "choice", "instructions": "What should the controller do now?",
                 "criteria": {"nothing": "no change", "water": "start watering",
                              "vent": "open the vents", "heat": "turn on the heater"}},
    "alert":    {"type": "noul", "instructions": "Should the grower be alerted?"},
    "stress":   {"type": "score", "instructions": "How stressed are the plants?",
                 "criteria": ["fine", "mild", "severe"]}
  }
}
```
```c
#include "sparrow_pico_greenhouse.h"

greenhouse_state s = {.temp_c = 34.0f, .soil_moisture = 40.0f, .raining = 0,
                      .time_of_day = GREENHOUSE_TIME_OF_DAY_AFTERNOON};
float p[GREENHOUSE_ACTION_N];
greenhouse_action(&s, p);                  /* probabilities over the options */
```

### Layout
- **Desktop:** tabs on top of a single code card (max 920 px wide, centred). Code card: ink-deep background
  (`#070B17` dark, `#0B1020` in light theme too: code stays dark in both themes), 14 px JetBrains Mono,
  line-height 1.6, 24 px padding, horizontal scroll inside the card (never wrap code), max-height 520 px with
  vertical scroll for the pico panel.
- Left of the code card on >= 1200 px only: a 3-item vertical list explaining the question types with a tiny
  shape glyph each (noul: toggle; choice: radio dots; score: 4-step bar).
- **Mobile:** tabs as scrollable pills; code font 13 px; copy button stays top-right inside the card.

### Interaction
- ARIA tabs (same keyboard model as section 3). Default tab: Python.
- Syntax highlighting: hand-written tiny tokenizer is **not** required; instead ship pre-highlighted HTML
  (spans with classes `.k` keyword, `.s` string, `.c` comment, `.n` number, `.f` function) written into the
  page source. Zero runtime cost.
- Copy button copies the raw snippet (store raw text in a `<template>` or `data-copy` on the panel; never copy
  the highlighted HTML). Same success/failure/live-region behaviour as the hero.
- Tab switch: 150 ms cross-fade, code card height animates with 220 ms `--ease-out` (use `grid-template-rows`
  0fr/1fr trick or measured height). Reduced motion: instant.

---

## 5. pico or nano? (`#pico-or-nano`)

### Purpose
The one real choice people get stuck on. Make the site itself decide, on-brand.

### Content
Eyebrow `CHOOSING`. H2: "pico or nano?" Lede: "nano reads text and answers any question you pose at runtime.
pico has no text and no vocabulary: you describe your device's sensors and questions, and get C."

**Mini decider widget** (two questions, mirrors the README flowchart):

1. Q1: "Are your inputs sensor values, and are the questions known at build time?" `[Yes] [No]`
2. If Yes -> result **sparrow-pico**: "Compile a spec into C. ~2 KB per question. 9.3 µs per decision on an
   ESP32-S3. Runs on any microcontroller." CTA "Compile your own" -> `guide.pico`.
3. If No -> Q2: "Do decisions hinge on numbers like `battery: 6%`?" `[Yes] [No]`
   - Yes -> **sparrow-nano-robot**: "1.37 MB. Reads `key: number` pairs as values. 13.2 ms per decision on an
     ESP32-S3." CTA -> `guide.python`.
   - No -> **sparrow-nano-general**: "2.2 MB. General text decisions. 4.4 ms per decision on an ESP32-S3."
     CTA -> `guide.python`. Secondary line: "Need more breadth and have the RAM? Try micro, tiny or small." ->
     `#tiers` (scrolls up and selects micro).
- Below the widget, one line: "Many devices use both: pico in the control loop, nano for anything said or
  written." (from README).
- "Start over" text button resets.

### Layout
- **Desktop:** two columns. Left (5 cols): the widget as a stacked card mimicking the hero trace styling
  (`question` label, option chips as the buttons, `answer` line for the result). Right (7 cols): the static
  flowchart as inline SVG, with the path taken highlighted (gradient stroke) as the user answers.
- **Tablet/Mobile:** widget only; the flowchart is hidden (`display:none` below 1024 px) because the widget
  carries the same logic. No-JS: show the flowchart at all widths and hide the widget.

**Flowchart SVG** (viewBox 0 0 640 360): diamond D1 at (40,140)-(240,220) with Q1 text; arrow right "yes" to
rounded box P at (320,40) w 280 h 72 "sparrow-pico / ~2 KB · 9.3 µs · any MCU"; arrow down "no" to diamond D2
at (40,250)-(240,330); from D2 "yes" to box NR (320,160) "sparrow-nano-robot / 1.37 MB"; "no" to box NG
(320,260) "sparrow-nano-general / 2.2 MB". Stroke 1.5 px muted; boxes surface fill with hairline; text 13 px.
Text in SVG uses `<text>` (selectable), `font-family: inherit`.

### Interaction
- Answer buttons are real `<button>`s. After answering, focus moves to the next question's heading or the
  result heading (`tabindex="-1"`), announced by `aria-live="polite"` on the result container.
- Each step slides in: translateX 12 px -> 0 + fade, 240 ms `--ease-out`. Flowchart path stroke draws with
  `stroke-dashoffset` over 400 ms. Reduced motion: no slide/draw, instant highlight.

---

## 6. On-chip speedup story (`#on-chip`)

### Purpose
Show the engineering: same chip, same model, much faster after optimisation.

### Content
Eyebrow `ON THE CHIP`. H2: "Same $10 chip. Much faster." Lede: "On the ESP32-S3: int8 SIMD on the vector unit
(ESP-NN kernel), weights in PSRAM / internal RAM." (from `facts.how_it_works[3]`). Board line (mono 13 px,
muted): `ESP32-S3 (QFN56 rev0.2), 240 MHz, 16 MB flash, 8 MB PSRAM` (from `facts.board`).

Chart data (from `facts.speedups_on_esp32s3`):

| Row | Before | After |
|---|---|---|
| sparrow-nano-robot (text with sensor readings) | 73.5 ms | 13.2 ms |
| sparrow-nano-general (text) | 9.6 ms | 4.4 ms |
| sparrow-pico (compiled) | 42.9 µs | 9.3 µs |

Legend: "Before: baseline build" (neutral, hatched bar) / "After: optimised build" (sunrise gradient bar).
No speedup multipliers are printed (they are not in facts.json).

### Chart design (inline SVG, built by `charts.js` from a JSON island in the page)

- **Small multiples**, one row per model, each row with its **own scale** because units differ (ms vs µs).
  The row's "before" bar spans 100% of the track; "after" spans `after/before` of the track (computed only
  for drawing geometry, never printed). A row-level unit label at the right edge makes the separate scales
  explicit: `scale: 0-73.5 ms`, etc. A one-line note under the chart: "Each row has its own scale."
- Row layout: label column 220 px (model name, 15 px, plus 12 px muted input type), track 1fr, value labels
  at bar ends (mono 14 px; after-value in off-white bold, before-value muted).
- Bars 14 px tall, 4 px radius, 8 px gap between before/after; 32 px between rows.
- Mobile: label above the track (label column collapses), track full width.

### Animation
- Triggered at 40% in view, once.
- Per row (rows staggered 180 ms): before bar grows 0 -> 100% over 600 ms `--ease-out`; then after a 120 ms beat,
  the after bar grows to its width over 700 ms `--ease-out-expo`, while the after-value label counts down
  from the before value to the after value (same unit, one decimal), finishing on the exact facts string.
- Reduced motion: bars and labels rendered at final state.
- Accessibility: the SVG is `aria-hidden="true"`; a real `<table>` with the same data sits beside it inside a
  `<details>` "Show as table" (closed by default) and is also the no-JS rendering. The `<figure>` has a
  `<figcaption>` summarising: "On the ESP32-S3, sparrow-nano-robot went from 73.5 ms to 13.2 ms per decision,
  sparrow-nano-general from 9.6 ms to 4.4 ms, and sparrow-pico from 42.9 µs to 9.3 µs."

### Supporting strip (below chart)
Three inline facts with icons:
- `155 / 155` on-chip answers identical to the host runtime.
- C99 runtime, no malloc, model read from flash (ESP-IDF component).
- Link: "How the chip path works ->" `architecture/#esp32`.

---

## 7. Honest limits (`#limits`)

### Purpose
Developers trust projects that say where they are weak. This section is deliberately plain.

### Content
Eyebrow `HONEST LIMITS`. H2: "What it won't do." Three items, verbatim from `facts.honest_limits`:

1. "Open-ended language it never trained on: well behind the 2B (MASSIVE domain routing 0.52-0.67 vs 0.86)."
2. "Yes/no judgement on JevBench is near chance at every tier."
3. "pico answers only the questions it was compiled for."

Plus one guidance line (from `docs/quickstart/pico.md`, no numbers): "A pico model is as good as its
teacher on your spec, and no better. Never use a learned model as the only safety stop."

Closing line: "Keep an LLM or a full decider for open-ended reasoning. Use `confidence` to fall back to it."
(from `docs/quickstart/agents.md`). Link: "Full benchmarks and methodology ->" `benchmarks/`.

### Layout
- 3 cards in a row (desktop), 1 column (tablet/mobile). Cards: transparent fill, 1 px hairline border, a
  muted "minus-circle" icon (not a warning triangle: tone is candid, not alarming). No gradient anywhere in
  this section.
- Guidance line in a full-width callout below with a 3 px amber left border.

### Interaction
Standard scroll reveal only (interaction.md 2.4). No hover lift on these cards (they are not links).

---

## 8. Final CTA band (`#get-started`)

### Purpose
Convert. Same three actions as the hero, nothing new.

### Content
- H2: "Ship a decision today." Sub: "numpy only. C99 with no malloc. From a laptop to a $10 chip."
- `copy-command` large: `pip install sparrow-decider`.
- Buttons: `Download models` (releases), `View on GitHub` (repo), `Read the docs` (docs).
- Small line: "Unofficial community project. Not an AWS or Strands product." is **not** repeated here (it is in
  the footer directly below).

### Layout
- Full-bleed band with the sunrise gradient as a soft background: ink base + a 30%-opacity animated
  conic/radial gradient blob centred behind the text (CSS only). Content centred, max-width 720 px.
- Mobile: buttons stacked full width, install block full width.

### Interaction
- Gradient blob drifts slowly (transform translate/rotate, 24 s loop, `linear`, `will-change: transform`).
  Paused when off-screen (CSS `animation-play-state` toggled by IntersectionObserver) and removed entirely
  under reduced motion.
- Buttons follow standard hover states (interaction.md 3.1).

---

## Facts requests (for the lead; do not build until resolved)

1. **Hero trace probabilities.** Proposed facts.json addition, values from the ESP32-S3 example log in
   `docs/quickstart/esp32.md`:
   ```json
   "hero_trace": [
     {"model": "sparrow-pico", "winner": "dock", "p": "0.81", "source": "docs/quickstart/esp32.md"},
     {"model": "sparrow-nano-robot", "winner": "pick", "p": "0.93", "source": "docs/quickstart/esp32.md"}
   ]
   ```
   Confirm these were logged with the v1.1 pico / v1.0 nano-robot models. Without it, the hero uses the
   no-numerals fallback.
2. **Bundled models.** Docs say the pip package bundles the two nano models (`sparrow-nano-general-v1.0` per
   the docs, while facts.json lists `sparrow-nano-general-v1.1`). Confirm which version ships before the
   site says "bundled".
3. **nano-general laptop latency** is absent from facts.json (README has an older figure). The tier panel
   omits it until added.
