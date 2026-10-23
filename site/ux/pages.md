# Inner pages spec: Models, Architecture, Benchmarks, Contact

Shared skeleton, header, footer, in-page nav and source rules: see `IA.md`. Motion, tokens, accessibility:
see `interaction.md`. Chart and diagram rules common to all pages are in section 0.

---

## 0. Shared components for inner pages

### 0.1 Page hero (inner)
- Eyebrow (mono 12 px, cyan), H1 (display face, clamp 40-64 px), lede (18-20 px muted, max 60ch).
- Height: content only; 96 px top padding desktop, 64 px mobile. Background: ink with one soft radial
  gradient (single hue from the sunrise ramp, different per page: Models amber, Architecture violet,
  Benchmarks cyan, Contact pink), 25% opacity, top-right.
- In-page nav chips directly under the lede (see IA.md 6).

### 0.2 Inline SVG diagram rules
- One `<svg>` per diagram, `viewBox` given below, `width="100%"`, `height="auto"`, `preserveAspectRatio="xMidYMid meet"`.
- Colours come from CSS custom properties via `currentColor` and classes (`.node`, `.node--accent`,
  `.edge`, `.edge--accent`, `.label`), so diagrams switch with the theme. No hard-coded hex in SVG.
- Node: rect with `rx="12"`, fill `var(--surface-2)`, stroke `var(--line)` 1.5 px. Accent node: stroke uses the
  sunrise gradient (`<linearGradient id="g-sunrise">` defined once per SVG).
- Edge: 1.5 px `var(--muted)` path with an arrowhead `<marker>`; edge labels 12 px mono on a small
  `var(--bg)` backing rect so lines do not cross text.
- Text: `<text>` elements, `font-family: inherit`, 14 px titles (weight 600), 12 px sub-lines (muted).
  Minimum rendered text size 11 px at 360 px viewport: if a diagram would render text smaller than that on
  mobile, provide the **mobile variant** described (usually a vertical re-layout), switched with
  `<picture>`-like logic: two SVGs, one hidden via CSS at each breakpoint.
- Every diagram is a `<figure>` with a `<figcaption>` (visible, 14 px muted) that states the flow in one or
  two sentences. The SVG has `role="img"` and `aria-labelledby` pointing at a `<title>` + `<desc>` inside it.
- Animation (optional, on scroll into view, once): edges draw via `stroke-dashoffset` in flow order,
  120 ms stagger, 500 ms each, `--ease-out`; nodes fade in 80 ms before their incoming edge completes.
  Reduced motion: static.

### 0.3 Chart rules
- Inline SVG built by `charts.js` from a `<script type="application/json" id="data-...">` island. The same
  island also renders a real `<table>` (visible on Benchmarks; behind "Show as table" on Home).
- Horizontal bar charts only (labels are long model names). Bars 14 px, 4 px radius, 10 px gap.
- Colour roles: **Sparrow models** = sunrise gradient (or solid `--accent-warm` where a gradient is too busy);
  **reference models (Strands Decider 2B / 4B)** = neutral `var(--ref)` with a 45-degree hatch pattern;
  value labels in text colour, never inside bars smaller than 40 px.
- Every chart states its unit and scale (linear or log) in a caption under the axis.
- Values printed are the exact strings from the source; geometry may parse them, labels never reformat.
- Hover/focus on a bar row: row background highlight + tooltip-free (the value is already labelled).
  Rows are not focusable (they are not interactive); the table is the accessible equivalent.

---

## 1. Models (`/models/`)

### 1.1 Page hero
- Eyebrow `MODELS` · H1 "Six models. One question format." · Lede: "From a 47 MB model on a laptop down to a
  ~2 KB compiled model on a microcontroller. Every tier answers yes/no, pick-one and score questions with
  calibrated probabilities."
- In-page nav: Family · Compare · Download · Model card.

### 1.2 Family cards (`#family`)

Six cards, in size order smallest first: pico, nano-robot, nano-general, micro, tiny, small.

Card anatomy (all fields from `facts.tiers`; omit any field the tier does not have):
```
+------------------------------------------+
| [tier badge: PICO]          [input icon] |
| sparrow-pico-rover-v1.1          (mono)  |
|                                          |
| ~2 KB per question        <- size, display 28 px, gradient
| (501 parameters)          <- muted 13 px (split from size string at "(")
|                                          |
| Input     sensor numbers, flags, enums   |
| Runs on   any microcontroller            |
| ESP32-S3  9.3 µs per decision            |
| Laptop    0.18 µs                        |
| Quality   94.0% vs the spec's rules      |
|           (its 2B teacher: 94.2%)        |
|                                          |
| [Compile your own ->]                    |
+------------------------------------------+
```
- Tier badge colours step along the sunrise ramp from small to big: pico `#FFB547`, nano `#FF6B4A`, micro
  `#FF3D8B`, tiny and small `#8B5CF6` (badge text is ink, so contrast holds for amber/coral/pink; for violet
  use off-white text at 14 px bold, or ink text on `#A78BFA`; see interaction.md 1.1).
- Input icon: `pico` = gauge (numbers), text tiers = "Aa", `nano-robot` = "Aa" + small gauge.
- Card action: pico -> `guide.pico` "Compile your own"; nano-robot and nano-general -> `guide.python`
  "Use from Python"; micro, tiny, small -> `releases` "Download".
- **Grid:** desktop 3 columns (2 rows), tablet 2 columns, mobile 1 column. Cards equal height per row.
- **Hover (pointer devices):** card lifts 2 px, border becomes gradient, 180 ms. Whole card is **not** a link
  (only the action link is), so text stays selectable.

### 1.3 Comparison table (`#compare`)

H2 "Compare". A real `<table>` with `<caption>` "Sparrow Decider models, from facts.json".

| Tier | Model | Size | Input | Runs on | ESP32-S3 | Laptop | Quality |
|---|---|---|---|---|---|---|---|
| pico | sparrow-pico-rover-v1.1 | ~2 KB per question (501 parameters) | sensor numbers, flags, enums | any microcontroller | 9.3 µs per decision | 0.18 µs | 94.0% vs the spec's rules (its 2B teacher: 94.2%) |
| nano | sparrow-nano-robot-v1.0 | 1.37 MB | text with sensor readings | ESP32-S3, Pi, laptop | 13.2 ms per decision | 0.12 ms (C) | RobotBench 40/55, same as the public Strands Decider 2B (40/55) |
| nano | sparrow-nano-general-v1.1 | 2.2 MB | text | ESP32-S3, Raspberry Pi, laptop | 4.4 ms per decision | — | general text decisions |
| micro | sparrow-micro-general-v1.1 | 7.6 MB | text | Pi, laptop | — | 0.22 ms (C) | — |
| tiny | sparrow-tiny-general-v1.0 | 17.9 MB | text | laptop, Pi | — | 23 ms (numpy) | — |
| small | sparrow-small-general-v1.0 | 47 MB | text | laptop, Pi, Jetson | — | 64 ms (numpy) | — |

- In a table, empty cells are an em dash with `<span class="visually-hidden">not measured</span>`. (Cards omit
  the row instead.)
- Numeric columns right-aligned, `tabular-nums`. Model IDs in mono.
- **Mobile:** the table scrolls horizontally inside a wrapper with a right-edge fade shadow and the first
  column (`Model`) `position: sticky; left: 0`. The wrapper is focusable (`tabindex="0"`,
  `role="region"`, `aria-label="Model comparison table, scrolls horizontally"`).
- Under the table, 13 px muted note: "Laptop times are per question on one CPU core, with the runtime shown
  in brackets. See Benchmarks for methodology." -> `../benchmarks/#method`.

### 1.4 Download (`#download`)

H2 "Get the models". Three cards in a row (stack on mobile):

1. **pip** (nano models): `copy-command` `pip install sparrow-decider`. Text: "numpy only. The nano models
   load with `Decider.load()`." (Do **not** state which nano versions are bundled until the lead confirms;
   see home.md "Facts requests" 2.) Link `guide.python`.
2. **GitHub releases** (micro, tiny, small): button `Download models` -> `releases`. Text: "Put the
   `.sparrow` files in `~/.cache/sparrow-decider/` (or any folder in `$SPARROW_MODELS`) to load them by
   name." (from python.md). Do not link individual asset files (asset names not confirmed).
3. **Compile** (pico): "pico models are compiled for your device from a spec." Link `guide.pico`.
   Secondary: "C runtime and ESP-IDF component" -> `guide.c`.

### 1.5 Model card summary (`#model-card`)

H2 "Model card". Two-column layout desktop (left: definition list; right: limitations callout), single column
mobile. Link at the end: "Full model card ->" `modelcard`.

Content (claims from facts.json and docs/models.md; no numbers beyond facts.json):
- **What it does:** answers `noul` (yes/no), `choice` (pick one) and `score` (rate on a scale) questions about
  a state, with calibrated probabilities, in the same shapes as Strands Decider.
- **Teachers:** a full Strands Decider (4B) teaches the text tiers through distillation on ~430k decisions.
  pico models are labelled by the public Strands Decider 2B on sampled device states.
- **Base weights:** micro and nano from potion-base-8M (MinishLab, MIT); tiny and small from Ettin encoders
  (JHU CLSP, MIT).
- **Runtimes:** Python (numpy only); C99, no malloc, model read from flash (ESP-IDF component); sparrow-pico
  compiler: device spec -> C header.
- **Calibration:** each model ships per-kind temperatures fitted on held-out data (python.md). A yes/no answer
  near 0.5 means "don't know".
- **Licence:** Apache-2.0 (code); model weights derived from MIT-licensed potion-base-8M and Ettin encoders.

Limitations callout (amber left border, same style as Home limits):
- The three `facts.honest_limits` lines, verbatim.
- micro and nano pool words without order, so negation and long multi-step reasoning are weak.
- English only.
- These models suggest decisions. Don't use them as the only safety mechanism on a physical system.

---

## 2. Architecture (`/architecture/`)

### 2.1 Page hero
- Eyebrow `ARCHITECTURE` · H1 "How a 4B decider becomes a 2 KB function." · Lede: "Distil a full Strands
  Decider into small students, keep its question format, and run them on numpy, C99 or bare metal."
  (Note: "2 KB" in the H1 is shorthand for facts' "~2 KB per question"; keep the tilde if the brand team
  prefers strictness: "a ~2 KB function".) Recommend the tilde version.
- In-page nav: Pipeline · Inside nano · pico compiler · On the ESP32-S3 · Contract.

### 2.2 Pipeline diagram (`#pipeline`)

**Desktop SVG, viewBox `0 0 1120 440`.** Four columns left to right: Teachers, Distillation, Tiers, Runtimes.
Column headers as 12 px mono uppercase labels at y=24: `TEACHERS` x=40, `DISTILLATION` x=300, `TIERS` x=580,
`RUNTIMES` x=860.

Nodes (x, y, w, h):
| id | Box | Title | Sub-line |
|---|---|---|---|
| T4 | 40, 80, 200, 72 | Strands Decider 4B | teacher |
| T2 | 40, 300, 200, 72 | Strands Decider 2B | public |
| D1 | 300, 80, 220, 72 | Distillation | ~430k decisions |
| D2 | 300, 300, 220, 72 | Label sampled states | from your device spec |
| S1 | 580, 48, 220, 56 | nano | 1.37-2.2 MB · static |
| S2 | 580, 116, 220, 56 | micro | 7.6 MB · static |
| E1 | 580, 184, 220, 56 | tiny · small | 17.9-47 MB · encoder |
| P1 | 580, 300, 220, 72 | sparrow-pico compiler | one MLP per question |
| R1 | 860, 48, 220, 56 | Python | numpy only |
| R2 | 860, 136, 220, 72 | C99 runtime | no malloc · model in flash |
| R3 | 860, 300, 220, 72 | C header | ~2 KB per question |

Note on sub-lines: size ranges like "1.37-2.2 MB" and "17.9-47 MB" join two facts values with a hyphen; they
introduce no new number. If the reviewer prefers, replace with the separate values ("1.37 MB / 2.2 MB").

Edges (all with arrowheads):
- T4 -> D1 (straight). D1 -> S1, D1 -> S2, D1 -> E1 (fan-out, cubic curves from D1's right edge midpoint).
- T2 -> D2 (straight). D2 -> P1 (straight).
- S1 -> R1, S1 -> R2, S2 -> R1, S2 -> R2, E1 -> R1 (curves). P1 -> R3 (straight).
- Edge labels: on T4->D1 `soft labels`; on T2->D2 `labels`.
- Accent: the whole bottom lane (T2 -> D2 -> P1 -> R3) uses `.edge--accent` and `.node--accent`, because
  that is the microcontroller story.

**Mobile variant, viewBox `0 0 360 760`:** same nodes stacked vertically in two lanes: the text lane
(T4 -> D1 -> [S1,S2,E1 as a 3-row group] -> [R1,R2 side by side]) then a 24 px gap and the pico lane
(T2 -> D2 -> P1 -> R3), nodes 300 px wide centred, vertical edges.

Caption: "A Strands Decider 4B teaches the text tiers through distillation on ~430k decisions. For pico, the
public Strands Decider 2B labels sampled states from your device spec, and the compiler writes C."

### 2.3 Inside nano (`#nano`)

Short prose (from `facts.how_it_works[1]`): "nano: static embeddings, pruned 8-16k vocabulary, 128-d, plus
key-value number pooling that reads 'battery: 6%' as a value."

**Diagram: key-value number pooling, viewBox `0 0 1000 300`:**
- Left: a state card (mono) with three lines: `battery: 6%`, `front_obstacle_m: 7.0`, `path: clear`.
- Middle-top lane (text path): the words flow into a box "static embeddings (128-d)" -> "mean pool" -> vector
  glyph (row of 8 small squares with varying opacity).
- Middle-bottom lane (number path): `battery` -> box "key vector"; `6%` -> box "value features" -> both
  join into a "x" circle node -> vector glyph labelled "battery's value".
- Right: both vectors + question + options -> box "MLP scores each option" -> output bars (no values;
  decorative bar heights, labelled "options").
- Caption: "Mean-pooled words lose which number belongs to which key. nano also builds one vector per
  `key: number` pair, so 'battery: 6%' is read as a value, not just a token."
- Mobile: stack lanes vertically (viewBox `0 0 360 620`).
- Interaction (optional): hovering/focusing the `battery: 6%` line highlights its path through the diagram
  (CSS `:has()` or a class toggle). Purely decorative; not required for comprehension.

### 2.4 pico compiler flow (`#pico`)

Prose (from `facts.how_it_works[2]`): "pico: you write a spec (sensors, rules, questions); the public Strands
Decider 2B labels sampled states; the compiler writes one tiny MLP per question as C."

**Diagram: five steps, horizontal on desktop, viewBox `0 0 1120 220`**, five equal nodes 184 x 96 at
x = 20, 244, 468, 692, 916, y = 60; arrows between them; above each node a step number in a 24 px circle.

| Step | Title | Sub-line | Glyph |
|---|---|---|---|
| 1 | Write a spec | sensors, rules, questions | `{ }` |
| 2 | Sample states | from your sensor ranges | scatter dots |
| 3 | Label | public Strands Decider 2B | speech-bubble |
| 4 | Train | one tiny MLP per question | 3-layer node glyph |
| 5 | Emit C | ~2 KB per question · 501 parameters | `.h` file |

- Under step 5, a small "result" ribbon spanning steps 4-5: `9.3 µs per decision on ESP32-S3 · 0.18 µs on a laptop`.
- Under the diagram, the spec-to-C pair from Home section 4 (pico spec tab) is reused as a static two-column
  code block, with copy buttons.
- Commands (code block, from pico.md):
  ```bash
  python training/pico_compile.py sample greenhouse.json --n 3000 --work runs/pico-greenhouse
  python training/label_decider.py <checkpoint dir> runs/pico-greenhouse/rows.jsonl runs/pico-greenhouse/teacher.jsonl
  python training/pico_compile.py build greenhouse.json --work runs/pico-greenhouse --out firmware/main
  ```
- Quality line: "94.0% vs the spec's rules (its 2B teacher: 94.2%). A pico model is as good as its teacher on
  your spec, and no better."
- Mobile variant: vertical, viewBox `0 0 360 640`, nodes 300 x 88.

### 2.5 On the ESP32-S3: optimisation stack (`#esp32`)

Prose: `facts.how_it_works[3]` verbatim, then the board line from `facts.board`.

**Diagram: layered stack, viewBox `0 0 800 420`.** Five full-width horizontal layers (x=40, w=720,
h=64, 12 px gaps), top to bottom:

| Layer | Title | Right-aligned detail (mono 12 px) |
|---|---|---|
| L1 | Your firmware | `app_main()` · `sparrow_choice(...)` |
| L2 | sparrow C99 runtime | no malloc · model read from flash |
| L3 | int8 SIMD kernels | ESP-NN on the vector unit |
| L4 | Memory placement | weights in PSRAM / internal RAM |
| L5 | ESP32-S3 | 240 MHz · 16 MB flash · 8 MB PSRAM |

- L3 and L4 are accent layers (gradient stroke): they are the optimisation.
- To the right of the stack (desktop >= 1200 px) or below it (smaller), reuse the **speedup small-multiples
  chart** from Home section 6 (same component, same data). Caption: "Before: baseline build. After: int8 SIMD
  and memory placement."
- Parity line: "`155 / 155` on-chip answers identical to the host runtime."
- Animation: layers slide up into place bottom-to-top (L5 first), 60 ms stagger, 320 ms `--ease-out`, then the
  chart animates. Reduced motion: static.
- Link: "Flash it yourself ->" `guide.esp32`.

### 2.6 Same contract (`#contract`)

Table from `docs/quickstart/python.md` (shapes, no numbers other than the level count already in the docs):

| type | criteria | answer |
|---|---|---|
| `noul` | optional `{"false": ..., "true": ...}` | `{"noul": P(true)}` |
| `choice` | `{name: description}`, 2 or more | `{"choice", "probabilities", "confidence"}` |
| `score` | list of 2-10 levels, lowest first | `{"score": expected level, "legend", "probabilities", "confidence"}` |

Plus: "`sparrow-decider serve` exposes `POST /v1/systemone`, following the Strands Decider `/v1/systemone`
contract." Link "Research report ->" `report`.

---

## 3. Benchmarks (`/benchmarks/`)

### 3.0 Data rules for this page
- Headline and on-chip figures: `facts.json` only.
- Benchmark tables: `bench/RESULTS.md`, **released model IDs only** (no ablation rows such as
  `sparrow-nano-v16k`, `-nokv`, `-s1`), plus the two Strands Decider reference rows. Each table's caption cites
  RESULTS.md and links `results`.
- Show each model ID **exactly as it was run**. RESULTS.md has `sparrow-nano-general-v1.0` (2.33 MB) but not
  the `v1.1` (2.2 MB) in facts.json: label that row `sparrow-nano-general-v1.0` and add a footnote
  "v1.1 benchmark results not yet published." Do not present v1.0 numbers as v1.1.
- **Blocker to resolve before launch:** `facts.honest_limits[0]` says MASSIVE domain routing is "0.52-0.67"
  for Sparrow models, but RESULTS.md shows `sparrow-tiny-general-v1.0` at 0.368 (and docs/models.md says
  "0.35-0.67"). The lead must correct facts.json or explain the range. Until then this page shows the full
  MASSIVE table (all released rows, including tiny) and does **not** repeat the "0.52-0.67" range in its own
  copy.

### 3.1 Page hero
- Eyebrow `BENCHMARKS` · H1 "Measured, not promised." · Lede: "Every number here comes from a benchmark run in
  the repo. Where Sparrow is weak, the tables say so."
- In-page nav: On the chip · Speed · RobotBench · MASSIVE · JevBench · pico · Parity · Method · Limits.

### 3.2 On the chip (`#chip`)
- Board line (`facts.board`).
- Small table + the speedup small-multiples chart (component from Home 6).

| Model | ESP32-S3, before | ESP32-S3, after |
|---|---|---|
| sparrow-pico | 42.9 µs | 9.3 µs |
| sparrow-nano-general | 9.6 ms | 4.4 ms |
| sparrow-nano-robot | 73.5 ms | 13.2 ms |

- Under it: "`155 / 155` on-chip answers identical to the host runtime."

### 3.3 Speed on a laptop (`#speed`)
Data (`facts.tiers[].laptop`): pico 0.18 µs; nano-robot 0.12 ms (C); micro 0.22 ms (C); tiny 23 ms (numpy);
small 64 ms (numpy). nano-general has no laptop figure in facts: omit it from the chart, list it in the table
with "—".

- **Chart:** horizontal bars on a **log scale** (axis ticks 0.1 µs, 1 µs, 10 µs, 100 µs, 1 ms, 10 ms, 100 ms),
  because the values span six orders of magnitude. Caption must say "log scale". Runtime shown as a pill after
  each label (`C`, `numpy`, `compiled C`).
- Mobile: same chart, tick labels reduced to 1 µs, 1 ms, 100 ms.

### 3.4 RobotBench (`#robotbench`)
Source: RESULTS.md "RobotBench v0 (55 hand-written robot decisions)".

| Model | Size | Right (of 55) |
|---|---|---|
| Strands Decider 4B (teacher) | 4B params | 46 |
| Strands Decider 2B (public) | 2B params | 40 |
| **sparrow-nano-robot-v1.0** | 1.37 MB | **40** |
| sparrow-nano-general-v1.0 * | 2.33 MB | 33 |
| sparrow-micro-general-v1.1 | 7.6 MB | 30 |
| sparrow-small-general-v1.0 | 47 MB | 24 |
| sparrow-tiny-general-v1.0 | 17.9 MB | 20 |

\* v1.0, not the v1.1 in the Models table.

- Chart: horizontal bars, linear 0-55 axis, sorted by score, reference rows hatched neutral. A vertical dashed
  marker at 40 labelled "public 2B" so the tie with nano-robot is visible.
- Optional expandable "By category" table (`<details>`): skill /15, nav /10, check /12, recover /10, urgency /8
  for the same rows, from RESULTS.md. Callout from README (claim with numbers from RESULTS): "nano-robot gets
  10/10 navigation calls where the public 2B gets 3/10."
- Note: "55 items: one item is 1.8 points; seed-to-seed spread is up to 4 items." (REPORT 6.3)

### 3.5 MASSIVE routing (`#massive`)
Source: RESULTS.md "MASSIVE routing (Amazon MASSIVE 1.1 en-US test, 600 utterances, held out of training)".

| Model | Domain (18 options) | Intent within domain |
|---|---|---|
| Strands Decider 2B (public) | 0.86 | 0.871 |
| sparrow-small-general-v1.0 | 0.673 | 0.599 |
| sparrow-micro-general-v1.1 | 0.635 | 0.542 |
| sparrow-nano-general-v1.0 * | 0.557 | 0.572 |
| sparrow-nano-robot-v1.0 | 0.52 | 0.494 |
| sparrow-tiny-general-v1.0 | 0.368 | 0.592 |

- Chart: grouped horizontal bars (domain, intent) per model, linear 0-1 axis. 2B reference hatched. Copy above:
  "This is where Sparrow is weakest: open-ended language it never trained on." (See blocker 3.0.)

### 3.6 JevBench (`#jevbench`)
Source: RESULTS.md "JevBench public (231 tasks, local v1.5 proxy)". Show only the "Right" column.

| Model | Right (of 231) |
|---|---|
| Strands Decider 4B (teacher) | 188 † |
| Strands Decider 2B (public) | 180 † |
| sparrow-nano-general-v1.0 * | 123 |
| sparrow-tiny-general-v1.0 | 123 |
| sparrow-small-general-v1.0 | 122 |
| sparrow-micro-general-v1.1 | 117 |
| sparrow-nano-robot-v1.0 | 113 |

† earlier local runs (README). Note: "Local proxy scores on the public tasks, not leaderboard results. Yes/no
judgement on JevBench is near chance at every tier." (second sentence verbatim from facts). No chart for
JevBench (a table is enough, and a chart would over-emphasise a proxy score).

### 3.7 pico vs its teacher (`#pico`)
From facts only: "sparrow-pico-rover-v1.1: 94.0% vs the spec's rules (its 2B teacher: 94.2%)."
Render as a two-bar comparison (0-100% axis, both bars nearly equal length is the point). Older v1.0 per-question
figures in README/pico.md are **not** used.

### 3.8 Parity (`#parity`)
- On chip: `155 / 155` on-chip answers identical to the host runtime (facts).
- Host C vs numpy (RESULTS.md "C runtime" table, released rows only):

| Model | Cases | Argmax agree | Max prob diff |
|---|---|---|---|
| sparrow-nano-robot-v1.0 | 586 | 586/586 | 3e-06 |
| sparrow-nano-general-v1.0 * | 586 | 586/586 | 2e-06 |
| sparrow-micro-general-v1.1 | 586 | 586/586 | 3e-06 |

Check command (mono block, copyable): `python c/tests/parity.py MODEL`.

### 3.9 Methodology (`#method`)
Bulleted, 15 px, max 72ch:
- RobotBench v0: 55 robot decisions written by hand, separately from the robot training generator.
- MASSIVE: Amazon MASSIVE 1.1 en-US test, 600 utterances, never trained on. Used for evaluation only (CC BY 4.0).
- JevBench: 231 public tasks, local v1.5 proxy, not leaderboard scores. Evaluation only (MIT).
- Laptop timings: local runs, one CPU core, per question; the runtime (C or numpy) is shown next to each value.
- ESP32-S3 timings: measured on the board in `facts.board`.
- Tables are generated by `bench/aggregate.py` from `bench/results/`. Links: `results`, `report`.

**Flag for the lead:** research/REPORT.md 6.3 still says "Microcontroller timings so far come from Espressif's
QEMU... Real ESP32-S3 numbers are pending hardware." The site links that report from this section; update the
report (or this note) so readers don't see a contradiction.

### 3.10 Limits (`#limits`)
Same three `facts.honest_limits` lines as Home 7 (see blocker 3.0 for item 1), plus from REPORT 6.3:
"RobotBench and the robot generator were written by the same author, from different templates. MASSIVE is
the independent check, and it shows the gap." (Rephrase "the same author" to "the same contributor" if the
brand team wants; no names either way.)

---

## 4. Contact (`/contact/`)

### 4.1 Rules
- No forms. Nothing on this page sends data anywhere. No email address (none in facts.json). No chat widget.
- Every action is a link to GitHub.

### 4.2 Content
- Eyebrow `CONTACT` · H1 "Talk to us on GitHub." · Lede: "Sparrow Decider is built in the open by the Sparrow
  Decider contributors. Issues and discussions are the fastest way to reach them."
- Two large link cards (desktop side by side, mobile stacked), each the full card clickable (an `<a>` wrapping
  the card content; card has a visible focus ring):
  1. **Report a bug or request a feature** -> `facts.contact.github_issues`.
     Sub: "Include the model ID, the runtime (Python, C, ESP-IDF), your board, and the smallest input that
     shows the problem."
  2. **Ask a question or share what you built** -> `facts.contact.discussions`.
     Sub: "Questions about tiers, pico specs, porting to a new board, or results."
- Third, smaller row: "Contributing" -> `{repo}/blob/main/CONTRIBUTING.md` ("Read the contributing guide and the
  quickstarts first").
- Security note: only if the repo has GitHub private vulnerability reporting enabled (lead to confirm), add
  "Security issue? Report it privately" -> `{repo}/security/advisories/new`. Otherwise omit the line (do not
  tell people to file security bugs publicly).
- "Cite this work" (small): "Use CITATION.cff in the repository." -> `{repo}/blob/main/CITATION.cff`.
- Disclaimer block (callout, muted): "Unofficial community project. Not an AWS or Strands product."

### 4.3 Layout & interaction
- Content max-width 880 px, centred. Cards 1 px border, 24 px padding, GitHub mark + arrow icon.
- Hover: border gradient + arrow nudges 3 px right, 160 ms. No other motion on this page.
