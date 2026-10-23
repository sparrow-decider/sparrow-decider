# Sparrow Decider site: information architecture

Owner: UX. Build target: static HTML/CSS/vanilla JS in `site/www/`, no build step, deployable to GitHub Pages.
Every number on the site comes from `site/facts.json` (see "Source-of-truth rules" at the end).

---

## 1. Sitemap

```
/                     Home
/models/              Models          (tiers, cards, comparison table, downloads, model card summary)
/architecture/        Architecture    (pipeline, pico compiler flow, ESP32-S3 optimisation stack)
/benchmarks/          Benchmarks      (quality, speed, on-chip, parity, methodology, limits)
/contact/             Contact         (GitHub issues, discussions, contributing pointers)
/404.html             Not found       (GitHub Pages serves this automatically)
/sitemap.xml, /robots.txt, /favicon.svg, /og.png (1200x630)
```

File layout in `site/www/`:

```
index.html
models/index.html
architecture/index.html
benchmarks/index.html
contact/index.html
404.html
assets/css/site.css        one stylesheet, all pages
assets/js/site.js          shared: theme, nav, copy buttons, tabs, reveal, count-up
assets/js/hero.js          home only: decision-trace animation
assets/js/charts.js        home + benchmarks: bar charts (inline SVG, no library)
assets/img/                logo.svg, og.png, favicon.svg
sitemap.xml  robots.txt
```

**Paths:** all internal links and asset URLs are **relative** (`../assets/css/site.css`, `models/`), so the
site works both at a custom domain root and at `https://<org>.github.io/sparrow-decider/`. Never start an
internal href with `/`. Directory URLs end in `/` (GitHub Pages serves `index.html`).

**Page depth:** one level. No sub-pages, no blog, no search at v0.1.0.

---

## 2. External link registry (use these exact URLs)

All derive from `facts.json.repo` = `https://github.com/sparrow-decider/sparrow-decider`.

| Key | URL | Used by |
|---|---|---|
| `repo` | `https://github.com/sparrow-decider/sparrow-decider` | "View on GitHub", header icon, footer |
| `releases` | `{repo}/releases` | "Download models" |
| `docs` | `{repo}/tree/main/docs/quickstart` | "Docs" / "Read the docs" |
| `guide.python` | `{repo}/blob/main/docs/quickstart/python.md` | code tabs, Models page |
| `guide.agents` | `{repo}/blob/main/docs/quickstart/agents.md` | code tabs |
| `guide.c` | `{repo}/blob/main/docs/quickstart/c.md` | code tabs |
| `guide.esp32` | `{repo}/blob/main/docs/quickstart/esp32.md` | code tabs, Architecture |
| `guide.pico` | `{repo}/blob/main/docs/quickstart/pico.md` | code tabs, Architecture |
| `modelcard` | `{repo}/blob/main/docs/models.md` | Models page |
| `results` | `{repo}/blob/main/bench/RESULTS.md` | Benchmarks page |
| `report` | `{repo}/blob/main/research/REPORT.md` | Architecture, Benchmarks |
| `license` | `{repo}/blob/main/LICENSE` | footer |
| `notice` | `{repo}/blob/main/NOTICE` | footer |
| `issues` | `facts.contact.github_issues` | Contact, footer |
| `discussions` | `facts.contact.discussions` | Contact, footer |

Assumption to confirm before launch: the default branch is `main`. If not, find-replace `/tree/main/` and `/blob/main/`
across `site/www/` (links are hard-coded in HTML; there is no build step).

External links open in the **same tab** (no `target="_blank"`); developers control tabs themselves.
Each external link gets a small trailing "arrow-up-right" glyph (inline SVG, `aria-hidden="true"`).

---

## 3. Global header

### 3.1 Contents, left to right (desktop >= 1024 px)

1. **Logo lock-up** (link to Home, `aria-label="Sparrow Decider home"`): geometric sparrow mark (24 px tall
   SVG, sunrise gradient fill) + wordmark "Sparrow Decider" in the display face, 18 px, weight 600.
   Version pill to the right of the wordmark: `v0.1.0` (from `facts.version`), mono 12 px, 1 px border,
   muted text. The pill is not a link.
2. **Primary nav** (centred group): `Models` · `Architecture` · `Benchmarks` · `Contact`.
   Home is reached via the logo. Current page: `aria-current="page"`, off-white text plus a 2 px sunrise
   gradient underline 6 px below the baseline. Others: muted text, underline animates in on hover
   (see interaction.md 3.2).
3. **Utility group** (right):
   - `Docs` text link (external, `docs`).
   - Theme toggle: icon button, 40x40 px hit area, `aria-label="Switch to light theme"` /
     `"Switch to dark theme"` (label reflects the action). Cycles dark <-> light; initial state follows
     `prefers-color-scheme`. Choice stored in `localStorage` key `sd-theme` inside try/catch.
   - GitHub icon button (Octicon-style mark, inline SVG, 40x40 hit area, `aria-label="Sparrow Decider on GitHub"`).
     No star count (we never show stars).
   - **Primary CTA button**: label `pip install`; clicking copies `pip install sparrow-decider` to the
     clipboard (same component as the hero copy button, compact variant) and shows "Copied" for 1.6 s.
     Tooltip/visually-hidden text: "Copy pip install sparrow-decider".

### 3.2 Behaviour

- Height 64 px. `position: sticky; top: 0`. Background: ink at 72% opacity + `backdrop-filter: blur(12px)`
  (fallback: solid surface colour when `backdrop-filter` unsupported). 1 px bottom hairline, shown only
  after the page has scrolled > 8 px (toggle a class from a passive scroll listener or an
  IntersectionObserver on a sentinel at the top of `<main>`).
- Header never hides on scroll (predictable; it is short).
- Skip link is the first focusable element in `<body>`: "Skip to content" -> `#main`
  (see interaction.md 4, Operable).

### 3.3 Tablet (768-1023 px)

- Logo + version pill, nav collapses into the menu button, utility group keeps GitHub icon and the compact
  `pip install` CTA. Theme toggle and Docs move into the menu panel.

### 3.4 Mobile (< 768 px) navigation

- Header shows: logo (mark + wordmark; version pill hidden < 400 px), GitHub icon, menu button.
  The `pip install` CTA is hidden in the header on mobile (the hero has the full one).
- **Menu button:** 44x44 px, hamburger icon morphing to a close "X" (two bars rotate, 200 ms, `--ease-out`).
  `aria-expanded="false|true"`, `aria-controls="site-menu"`, label "Menu" / "Close menu".
- **Panel:** full-width sheet that drops below the header (not an off-canvas drawer), height = content,
  max-height `calc(100dvh - 64px)` with internal scroll. Background solid surface. Contents in order:
  1. Nav links, 20 px, 56 px row height, full-width tap targets, current page marked.
  2. Divider.
  3. `Docs`, `Download models`, `View on GitHub` (external).
  4. Copy row: `pip install sparrow-decider` with copy button (full width).
  5. Theme toggle as a labelled row: "Theme: Dark / Light".
- **Open:** panel fades + translates from -8 px to 0 over 200 ms. Body scroll locked
  (`overflow: hidden` on `<html>`). Focus moves to the first nav link.
- **Close:** on Escape, on menu button, on any link activation, on resize to >= 1024 px, or on a tap on the
  dimmed backdrop below the panel. Focus returns to the menu button.
- Focus is trapped inside header + panel while open (Tab from the last item wraps to the menu button).
- Without JS: the panel is a `<details>`-free fallback: the nav renders as a horizontally scrollable row
  under the logo (`<noscript>` is not needed; the default CSS state is "nav visible as a scroll row", and
  JS adds `.js` on `<html>` to switch to the collapsible menu).

---

## 4. Global footer

Background: surface (`#111832` dark / `#F4F6FB` light). Top border hairline. Padding 64 px top / 40 px bottom
desktop, 48/32 mobile.

### 4.1 Layout

Desktop: 4 columns (brand column 2fr, then three 1fr link columns). Tablet: brand full width on top, three
link columns below. Mobile: everything stacked, link columns as two-column grid of short lists.

**Brand column**
- Logo lock-up (no version pill).
- One line: "Tiny decision models. From 47 MB on a laptop to ~2 KB on a microcontroller."
  (Sizes from `facts.tiers`.)
- Copy row: `pip install sparrow-decider` + copy button.

**Column "Product"**: Models · Architecture · Benchmarks · Download models (releases).

**Column "Docs"**: Python quickstart · Agents quickstart · C library · ESP32-S3 · sparrow-pico · Model card ·
Research report.

**Column "Community"**: GitHub repository · Issues · Discussions · Contact.

### 4.2 Legal strip (below columns, separated by a hairline, 13 px muted text)

Three lines, in this order, each its own `<p>`:

1. **Disclaimer (verbatim, must not be altered or hidden):**
   "Unofficial community project. Not an AWS or Strands product."
   Rendered in normal muted text weight 500, never smaller than 13 px, never collapsed on mobile.
2. **Licence:** "Code: Apache-2.0. Model weights derived from MIT-licensed potion-base-8M and Ettin encoders."
   Link "Apache-2.0" -> `license`; "NOTICE" link at end -> `notice`.
3. **Credits:** "Built on: potion-base-8M (MinishLab, MIT) · Ettin encoders (JHU CLSP, MIT) · Strands Decider
   (Apache-2.0) · ESP-NN (Espressif, Apache-2.0). Evaluation only: Amazon MASSIVE (CC BY 4.0) ·
   JevBench (MIT)." (verbatim from `facts.credits`; no logos.)
4. "© the Sparrow Decider contributors." (No year assertions beyond the current one; no individual names.)

No newsletter field, no social icons other than GitHub, no analytics badge.

---

## 5. 404 page (`404.html`)

- Same header and footer. Because GitHub Pages serves `404.html` at arbitrary depths, **this page must use
  absolute asset URLs relative to the deployed base**. Approach: put a `<base href="...">` placeholder
  `{{BASE_URL}}` (e.g. `/sparrow-decider/` or `/`) in `404.html` only, set at deploy time; all other pages stay
  relative.
- Content, centred, max-width 560 px:
  - Small decision trace (static, no animation):
    ```
    state     page: not found
    question  Where next?   home | models | docs
    ```
  - H1: "This page didn't make the cut."
  - Body: "The link may be old, or the page moved. Pick an option:"
  - Three buttons in a row (stack on mobile): `Home` (primary), `Models` (secondary), `Docs` (secondary, external).
- `<meta name="robots" content="noindex">`. Not in sitemap.

---

## 6. Page templates (shared skeleton)

```
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">...</header>
<main id="main" tabindex="-1">
  <section class="page-hero"> H1 + one-line lede + optional in-page nav </section>
  <section> ... </section>
</main>
<footer class="site-footer">...</footer>
```

- Exactly one `<h1>` per page. Section titles `<h2>`; card titles `<h3>`.
- Inner pages (Models, Architecture, Benchmarks) get a sticky **in-page nav** ("On this page") on desktop
  >= 1200 px as a right rail (200 px wide), and as a horizontal scroll row of chips under the page hero on
  smaller screens. Active section highlighted via IntersectionObserver (rootMargin `-40% 0px -55% 0px`).
- Content max-width 1200 px; prose max-width 68ch.

---

## 7. Source-of-truth rules (apply to every page)

1. `site/facts.json` is the only source of numbers and claims. Copy them as written: do not round, convert
   units or recompute (e.g. "9.3 µs", never "9 µs" or "~10 µs").
2. Exception, Benchmarks page only: per-benchmark tables may quote `bench/RESULTS.md` for released model IDs
   (see pages.md 3), each table citing RESULTS.md. If a value conflicts with facts.json, facts.json wins and
   the conflicting row is omitted.
3. Never show: user counts, download counts, GitHub stars, testimonials, company logos, partner names,
   individual people's names.
4. Older figures in README.md, docs/models.md and research/REPORT.md (e.g. "6 KB per question", "0.2 µs",
   "2.33 MB" for nano-general, "Real ESP32-S3 numbers are pending hardware") predate facts.json. **Do not
   use them on the site.** facts.json gives pico as "~2 KB per question (501 parameters)", 0.18 µs on a
   laptop, and nano-general v1.1 as 2.2 MB.
5. The disclaimer "Unofficial community project. Not an AWS or Strands product." appears in the footer of
   every page **and** once on Home (hero foot-note, see home.md 1).
