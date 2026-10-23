# Interaction, accessibility, performance and SEO spec

Applies to every page in `site/www/`. Values here are the tokens the other UX docs reference.

---

## 1. Design tokens the build must define (CSS custom properties on `:root`)

Brand team owns final colours; these are the starting tokens with verified contrast.

### 1.1 Colour

| Token | Dark (default) | Light | Use |
|---|---|---|---|
| `--bg` | `#0B1020` | `#FFFFFF` | page background (set on `body` explicitly) |
| `--surface` | `#111832` | `#F4F6FB` | bands, cards, footer |
| `--surface-2` | `#18213F` | `#FFFFFF` | raised cards, diagram nodes |
| `--code-bg` | `#070B17` | `#0B1020` | code blocks (code stays dark in both themes) |
| `--text` | `#F5F7FF` | `#0B1020` | body text |
| `--muted` | `#A8B0CC` | `#4A5272` | secondary text, labels |
| `--line` | `#2A335C` | `#DDE2EE` | decorative hairlines only (not for meaningful boundaries) |
| `--line-strong` | `#5B6488` | `#8A92B2` | input/button borders, chart axes (>= 3:1 against bg) |
| `--accent` | `#22D3EE` | `#0E7490` | links, focus ring, live dot, "Copied" state |
| `--accent-warm` | `#FFB547` | `#B45309` | limits callout border, solid stand-in for gradient |
| `--ref` | `#5B6488` | `#8A92B2` | reference-model bars (hatched) |
| `--sunrise` | `linear-gradient(90deg,#FFB547,#FF6B4A,#FF3D8B,#8B5CF6)` | `linear-gradient(90deg,#B45309,#C2410C,#BE185D,#6D28D9)` | gradient text, accents |
| `--sunrise-btn` | `linear-gradient(90deg,#FFB547,#FF6B4A,#FF3D8B)` | same as dark | primary button fill (ink text) |

Measured contrast (WCAG relative luminance, computed for this spec):
- Dark: text `#F5F7FF` on `#0B1020` 17.7:1, on `#111832` 16.35:1. Muted `#A8B0CC` on `#0B1020` 8.79:1, on
  `#111832` 8.12:1. Accent `#22D3EE` on `#0B1020` 10.48:1. `--line-strong` `#5B6488` on `#0B1020` 3.27:1 (non-text OK).
- Gradient stops on ink (gradient text): `#FFB547` 10.78, `#FF6B4A` 6.72, `#FF3D8B` 5.67, `#8B5CF6` **4.47**
  (fails 4.5 for small text). Rule: gradient text only at >= 24 px (large text, needs 3:1), never on body copy.
- Primary button: ink `#0B1020` text on `--sunrise-btn` (lowest stop `#FF3D8B` = 5.67:1). The violet stop is
  excluded from button fills on purpose. Never put white text on the sunrise gradient (`#FFFFFF` on `#FF3D8B`
  is 3.34:1).
- Light: text 18.93:1; muted `#4A5272` on white 7.66:1, on `#F4F6FB` 7.09:1; accent `#0E7490` on white 5.36:1,
  on `#F4F6FB` 4.96:1. The dark-theme cyan `#22D3EE` on white is 1.81:1: **never** use it as text or focus
  colour in light theme. Light sunrise stops on white: `#B45309` 5.02, `#C2410C` 5.18, `#BE185D` 6.04,
  `#6D28D9` 7.1.
- Tier badge on violet: ink on `#8B5CF6` is 4.47:1. Use `#A78BFA` as the violet badge fill in dark theme
  (ink text) or make the badge text >= 14 px bold (large-text rule, 3:1).

### 1.2 Theme mechanism
- Default follows `prefers-color-scheme`. Header toggle sets `data-theme="light|dark"` on `<html>`.
- CSS: dark tokens on `:root`; light tokens under `@media (prefers-color-scheme: light) { :root:not([data-theme="dark"]) {...} }`
  and again under `:root[data-theme="light"]`.
- An inline 6-line script in `<head>` (before CSS paints) reads `localStorage['sd-theme']` in try/catch and sets
  `data-theme`, to avoid a flash. Everything renders correctly if storage throws.
- `<meta name="color-scheme" content="dark light">` and two `<meta name="theme-color">` tags (one per scheme).

### 1.3 Type
- Display: **Sora** (Google Fonts, weights 600 and 700). Body: **Inter** (400, 500, 600). Code:
  **JetBrains Mono** (400, 600). Brand team may swap the display face for another geometric Google font.
- Scale (fluid, `clamp`): H1 `clamp(2.5rem, 1.6rem + 3.6vw, 4.5rem)` line-height 1.05, letter-spacing -0.02em;
  H2 `clamp(1.875rem, 1.4rem + 1.8vw, 2.75rem)` lh 1.15; H3 1.25rem lh 1.3; body 1rem/1.0625rem lh 1.6;
  small 0.875rem; mono labels 0.75rem uppercase +0.08em.
- `font-variant-numeric: tabular-nums` on every number display, counter, table numeric cell.
- Units: always a thin no-break space between number and unit in HTML (`9.3&#8239;µs`), so "9.3 µs" never
  breaks across lines. Use the real micro sign `µ` (U+00B5), as in facts.json.

### 1.4 Spacing, radius, elevation
- 4 px base: `--s1` 4, `--s2` 8, `--s3` 12, `--s4` 16, `--s5` 24, `--s6` 32, `--s7` 48, `--s8` 64, `--s9` 96, `--s10` 128.
- Radius: 8 (buttons, chips), 12 (diagram nodes, inputs), 16 (cards, code blocks), 999 (pills).
- Elevation: no drop shadows on dark; use border + 1 px inner highlight. Light theme: `0 1px 2px rgb(11 16 32 / .06), 0 8px 24px rgb(11 16 32 / .06)` on cards.

---

## 2. Motion system

### 2.1 Durations
| Token | ms | Use |
|---|---|---|
| `--dur-xs` | 120 | colour/opacity on hover, focus ring appear |
| `--dur-s` | 180 | button press, chip select, tab cross-fade |
| `--dur-m` | 240 | panel open, step slide, reveal of small items |
| `--dur-l` | 420 | ruler marker slide, section reveal |
| `--dur-xl` | 700 | chart bars, count-ups (count-ups use 1,200) |

### 2.2 Easings
| Token | Value | Use |
|---|---|---|
| `--ease-out` | `cubic-bezier(0.22, 1, 0.36, 1)` | default for things entering |
| `--ease-in` | `cubic-bezier(0.55, 0, 1, 0.45)` | things leaving |
| `--ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` | things moving between two places (marker, strip) |
| `--ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | count-ups, chart "after" bars |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | single highlight moments (winner chip); max once per view |
| linear | `linear` | clocks (hero counter), ambient drift |

### 2.3 Stagger
- Lists/grids reveal with 60 ms stagger, capped at 6 items (item 7+ appear with item 6).
- Number band 90 ms; chart rows 180 ms; diagram edges 120 ms.

### 2.4 Scroll-reveal rules
- One IntersectionObserver in `site.js` for elements with `[data-reveal]`; threshold 0.15, rootMargin
  `0px 0px -10% 0px`; unobserve after first reveal (never re-animate on scroll back).
- Reveal = opacity 0 -> 1 + translateY 16 px -> 0, `--dur-l`, `--ease-out`.
- Only section headers, cards and charts reveal. **Never** reveal body paragraphs, tables, code blocks, nav,
  CTAs or anything in the first viewport (above-the-fold content is visible on first paint; LCP must not wait
  for JS).
- Initial hidden state is applied only when `html.js` is present and reduced motion is not requested, so
  content is never invisible without JS.
- Animate only `transform` and `opacity` (plus `stroke-dashoffset`, `clip-path` for the specific effects
  named in the page specs). No layout-affecting animations except the code card height (see home.md 4).

### 2.5 Reduced motion
- `@media (prefers-reduced-motion: reduce)`: all `[data-reveal]` visible immediately; transitions longer than
  `--dur-xs` become 0 ms except colour/opacity changes on hover/focus (kept at 120 ms); no count-ups (final
  values shown); hero renders a static resolved frame with a scene switcher; ambient gradients do not move;
  chart bars render at final size.
- JS checks `matchMedia('(prefers-reduced-motion: reduce)')` and listens for changes.

### 2.6 Ambient motion budget
At most one ambient (looping) animation visible at a time: the hero trace, or the final CTA gradient drift.
Both pause off-screen and when the tab is hidden. The hero has a visible pause control.

---

## 3. Component states

### 3.1 Buttons
| Variant | Idle | Hover (pointer) | Active | Focus-visible | Disabled |
|---|---|---|---|---|---|
| Primary | `--sunrise-btn` fill, ink text, 600 weight, 44 px min height | background-position shifts 30% over 240 ms (gradient slides), translateY -1 px | translateY 0, brightness 0.95 | 2 px `--accent` ring, 2 px offset | not used |
| Secondary | transparent, 1 px gradient border (border-image or padding-box/border-box trick), `--text` | fill `--surface`, border brightens | brightness 0.95 | ring as above | not used |
| Ghost | transparent, `--text`, icon left | underline-free; fill `--surface` | | ring | |
| Text link | `--accent`, underline 1 px offset 3 px | underline thickness 2 px | | ring | |

Hover effects apply only under `@media (hover: hover) and (pointer: fine)`. Minimum target size 44x44 px for
all buttons and icon buttons (exceeds WCAG 2.2 2.5.8's 24x24).

### 3.2 Nav links
Idle muted; hover text colour -> `--text` and a 2 px gradient underline scales from 0 to 1 on the x-axis from
the left, `--dur-s`, `--ease-out`. Current page: underline always visible.

### 3.3 Copy-command component (hero, header, footer, CTA band, code tabs)
- Markup: `<div class="copy"> <code>pip install sparrow-decider</code> <button type="button" aria-label="Copy pip install sparrow-decider">...</button> </div>`
  plus one shared visually hidden `<div aria-live="polite" id="sr-status">` per page.
- Click: `navigator.clipboard.writeText(text)`; on success icon swaps to check, label "Copied", accent colour,
  for 1,600 ms; status region text set to "Copied to clipboard". On failure (insecure context / permission),
  select the `<code>` contents with a Range and set label "Press Ctrl+C" (or "⌘C" on Mac).
- The button keeps its width when the label changes (reserve width with `min-width`).

### 3.4 Tabs (tier selector, code tabs)
WAI-ARIA Tabs, automatic activation: `role="tablist"` with `aria-label`, each tab `role="tab"`,
`aria-selected`, `aria-controls`, roving `tabindex` (0 on selected, -1 others); panels `role="tabpanel"`,
`aria-labelledby`, `tabindex="0"`. Keys: Left/Right (wrap), Home, End. Selected-tab indicator slides between
tabs with `--dur-m` `--ease-in-out` (transform on a single indicator element).

### 3.5 Cards
Interactive cards (Contact links): hover lift -2 px + gradient border, `--dur-s`. Informational cards: no hover
effect (do not suggest clickability).

---

## 4. Accessibility checklist (WCAG 2.2 AA)

Perceivable
- [ ] Text contrast >= 4.5:1 (body, labels, table text, chart value labels); large text (>= 24 px, or >= 18.66 px bold) >= 3:1. Use the token pairs in 1.1; do not introduce new pairs without measuring.
- [ ] Non-text contrast >= 3:1 for focus rings, button borders, chart bars against the background, axis lines, tab indicators (1.4.11).
- [ ] Gradient text only on display sizes; never the only carrier of meaning.
- [ ] Information never by colour alone: reference rows in charts are hatched and labelled "(reference)"; the winner chip in the hero has a check glyph as well as the gradient.
- [ ] Every chart and diagram has a text alternative: `<figcaption>` + table (charts) or `<title>`/`<desc>` (diagrams).
- [ ] Text resizes to 200% without loss; layout reflows at 320 CSS px without horizontal page scroll (tables scroll inside their own focusable region) (1.4.10).
- [ ] Text spacing override (1.4.12) does not clip: no fixed heights on text containers.
- [ ] Icons are `aria-hidden="true"`; icon-only buttons have `aria-label`.
- [ ] `lang="en"` on `<html>`.

Operable
- [ ] Skip link "Skip to content" is the first focusable element, visible on focus (top-left, 12 px offset, surface fill, accent ring), targets `<main id="main" tabindex="-1">`.
- [ ] All functionality via keyboard: nav, menu, theme toggle, copy buttons, tabs, the pico-or-nano widget, pause button, "Show as table" disclosures.
- [ ] Visible focus on every focusable element: `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }` (3 px offset on pills). Never `outline: none` without a replacement.
- [ ] Focus not obscured by the sticky header (2.4.11): `scroll-padding-top: 80px` on `html`.
- [ ] Mobile menu: focus moves in on open, trapped while open, Escape closes, focus returns to the toggle.
- [ ] Moving content > 5 s (hero loop) has pause control (2.2.2); nothing flashes more than 3 times per second (2.3.1). The counter's cyan flash happens once per scene.
- [ ] Target size >= 24x24 (2.5.8); this spec uses 44x44.
- [ ] No hover-only content.
- [ ] Headings in order (one H1, H2 per section, H3 in cards); landmarks `header`, `nav` (with `aria-label="Primary"`; footer nav `aria-label="Footer"`), `main`, `footer`.
- [ ] Page `<title>` unique per page (see 6).

Understandable
- [ ] Link text meaningful out of context ("Download models", not "here"). External links indicated with an icon and a visually hidden "(GitHub)" where the destination is not obvious.
- [ ] The pico-or-nano widget announces results via `aria-live="polite"` and moves focus to the result heading.
- [ ] Consistent navigation and identification across pages (3.2.3/3.2.4): same header/footer markup everywhere.

Robust
- [ ] Valid HTML (W3C validator clean), unique ids, native elements first (`<button>`, `<a>`, `<details>`, `<table>`).
- [ ] ARIA only where needed: tabs, `aria-expanded` on menu, `aria-pressed` on pause, `aria-current` on nav, live region for copy and widget.
- [ ] Tested with keyboard only, VoiceOver (Safari) and NVDA (Firefox) on Home and Benchmarks; axe DevTools shows 0 violations on all pages in both themes.

Motion
- [ ] `prefers-reduced-motion` respected as in 2.5, verified by toggling the OS setting.

---

## 5. Performance budget

| Item | Budget |
|---|---|
| Frameworks / libraries | none (no React, no chart lib, no animation lib, no syntax highlighter) |
| JavaScript total, all files, uncompressed | **< 150 KB** hard cap; target < 40 KB (site.js ~12 KB, hero.js ~6 KB, charts.js ~10 KB) |
| JS per page, gzip | target < 15 KB |
| CSS | one file, < 50 KB uncompressed; critical above-the-fold CSS may be inlined (< 14 KB) on Home |
| HTML per page | < 60 KB uncompressed (Benchmarks may be larger due to tables, < 100 KB) |
| Fonts | Google Fonts, max 7 font files total (Sora 600/700, Inter 400/500/600, JetBrains Mono 400/600) requested in one CSS2 API URL with `display=swap`; Latin subset only |
| Images | SVG only for logo/diagrams/icons; one `og.png` (1200x630, < 150 KB) used only by social crawlers; no raster images on pages |
| Third-party requests | only `fonts.googleapis.com` and `fonts.gstatic.com`; no analytics, no tracking, no embeds |
| Lighthouse (mobile, simulated throttling) | Performance >= 95, Accessibility 100, Best Practices >= 95, SEO 100, on every page |
| Core Web Vitals (lab) | LCP < 1.8 s, CLS < 0.02, TBT < 100 ms |

Rules:
- `<link rel="preconnect" href="https://fonts.googleapis.com">` and `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>`;
  one stylesheet request for all three families. Preload the two most critical woff2 files (Sora 700 for the
  H1, Inter 400 for body) with `<link rel="preload" as="font" type="font/woff2" crossorigin>` pointing at the
  exact gstatic URLs the CSS2 response returns (resolve once at build time and hard-code; verify they match).
- Fallback font metrics: define `@font-face` fallbacks with `size-adjust`/`ascent-override` for Arial
  (Inter) so the swap causes no CLS (CLS budget above).
- All scripts `defer`; no inline handlers. No `document.write`. Animations use `requestAnimationFrame` and pause off-screen.
- Reserve space for everything that animates in (counters `min-width`, charts fixed aspect ratio) to keep CLS ~0.
- The hero LCP element is the H1 text (not an image), rendered from HTML + CSS with no JS dependency.
- Cache: GitHub Pages defaults; filenames are stable, so add `?v=0.1.0` to CSS/JS URLs and bump on release.

---

## 6. SEO and meta

### 6.1 Per-page `<head>`
```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{PAGE TITLE}</title>
<meta name="description" content="{DESCRIPTION}">
<link rel="canonical" href="{SITE_URL}{PATH}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sparrow Decider">
<meta property="og:title" content="{PAGE TITLE}">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:url" content="{SITE_URL}{PATH}">
<meta property="og:image" content="{SITE_URL}assets/img/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Sparrow Decider: 9.3 µs per decision on an ESP32-S3">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{relative}/assets/img/favicon.svg" type="image/svg+xml">
<meta name="color-scheme" content="dark light">
```
`{SITE_URL}` is the deployed absolute base (e.g. `https://sparrow-decider.github.io/sparrow-decider/`), to be
filled once at deploy; canonical and OG URLs must be absolute. No Twitter/X handle (none in facts).

### 6.2 Titles and descriptions (<= 60 / <= 155 chars)
| Page | `<title>` | Description |
|---|---|---|
| Home | Sparrow Decider: tiny decision models, 9.3 µs on an ESP32-S3 | Decision models from 47 MB on a laptop to ~2 KB on a microcontroller. Yes/no, pick-one and score answers with calibrated probabilities. |
| Models | Models · Sparrow Decider | pico, nano, micro, tiny and small: sizes, inputs, where each runs, and how to download or compile them. |
| Architecture | Architecture · Sparrow Decider | How a Strands Decider teaches tiny students, how sparrow-pico compiles a spec into C, and how the ESP32-S3 path is optimised. |
| Benchmarks | Benchmarks · Sparrow Decider | RobotBench, MASSIVE, JevBench, on-chip timings and runtime parity, with methodology and honest limits. |
| Contact | Contact · Sparrow Decider | Report bugs, request features and ask questions on GitHub. |
| 404 | Page not found · Sparrow Decider | (no description; `noindex`) |

### 6.3 Structured data (Home only)
JSON-LD `SoftwareSourceCode`: `name` "Sparrow Decider", `codeRepository` = `facts.repo`, `programmingLanguage`
["Python", "C"], `license` "https://www.apache.org/licenses/LICENSE-2.0", `version` "0.1.0", `description` =
`facts.what`. No `aggregateRating`, no author persons (contributors only, as an `Organization` named "the
Sparrow Decider contributors" if needed).

### 6.4 sitemap.xml and robots.txt
- `sitemap.xml`: the five indexable pages with absolute `{SITE_URL}` URLs and `<lastmod>` of the deploy date. No 404.
- `robots.txt`:
  ```
  User-agent: *
  Allow: /
  Sitemap: {SITE_URL}sitemap.xml
  ```

### 6.5 OG image (`og.png`, 1200x630)
Ink background, sunrise gradient glow, logo mark, wordmark, and one line: "9.3 µs per decision on a $10
ESP32-S3". Footer strip text in the image: "Unofficial community project. Not an AWS or Strands product."

---

## 7. Responsive breakpoints

| Name | Min width | Columns | Gutter | Notes |
|---|---|---|---|---|
| `xs` | 0 | 4 | 16 px side, 16 gap | smallest supported 320 px; design at 360 and 390 |
| `sm` | 480 | 4 | 20 | two-up grids for numbers band, button pairs |
| `md` | 768 | 8 | 24 | tablet: hero stacks, menu button replaces nav |
| `lg` | 1024 | 12 | 24 | full header nav; hero two columns; pico-or-nano flowchart appears |
| `xl` | 1200 | 12 | 32 | in-page nav right rail on inner pages; container max 1200 |
| `2xl` | 1440 | 12 | 32 | container stays 1200; backgrounds stretch |

- Mobile-first CSS (`min-width` queries only).
- Use `100dvh` (with `vh` fallback) for heights tied to the viewport.
- Test widths: 320, 360, 390, 768, 1024, 1280, 1440, 1920. Also 200% zoom at 1280.
- Touch: no hover-dependent features; `:hover` styles gated by `(hover: hover)`.
- Print stylesheet (small): hide header nav, hero animation, CTA band; show URLs after external links; light theme.
