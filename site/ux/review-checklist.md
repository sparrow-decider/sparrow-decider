# Build review checklist

The build in `site/www/` is reviewed against this list. Each item is pass/fail. "Blocker" items must pass
before launch. References: IA.md, home.md, pages.md, interaction.md.

## A. Facts and honesty (all blockers)

- [ ] Every number on every page appears verbatim in `site/facts.json` (or, on Benchmarks only, in `bench/RESULTS.md` for a released model ID, with RESULTS.md cited). Check by grepping each rendered number against both files.
- [ ] No rounding, unit conversion or derived numbers are displayed (no "4.6x faster", no "~10 µs", no percentages computed from fractions). Geometry may use derived ratios; labels may not.
- [ ] None of the stale figures appear: "6 KB" per question, "0.2 µs", "2.33 MB" attributed to v1.1, "1,500 parameters", "94.3%", "pending hardware". (2.33 MB may appear only on Benchmarks rows labelled `sparrow-nano-general-v1.0`.)
- [ ] Model IDs match the source of their numbers: Models/Home use facts IDs; Benchmarks rows use the IDs as run, with the v1.0 footnote on nano-general.
- [ ] No user counts, download counts, GitHub stars, testimonials, logos of companies, partners, or individual people's names anywhere (including HTML comments, meta tags, JSON-LD, OG image).
- [ ] Credit line names only "the Sparrow Decider contributors".
- [ ] Disclaimer "Unofficial community project. Not an AWS or Strands product." appears verbatim in the footer of all 6 pages, in the Home hero foot-note, on Contact, and in the OG image.
- [ ] Credits and licence text match `facts.credits` and `facts.license` exactly.
- [ ] Hero probability values: shown only if `hero_trace` was added to facts.json; otherwise the no-numerals fallback with "Probabilities illustrative." No per-option values for non-winning options in either case.
- [ ] Hero slow-down labels read "replayed 250,000x slower" (pico) and "replayed 200x slower" (nano-robot), and the resolve phases last 2,325 ms and 2,640 ms.
- [ ] Honest limits section present on Home, Models (callout) and Benchmarks; no softening of the wording.
- [ ] Open facts issues resolved by the lead or handled with the documented fallback: (1) hero_trace, (2) which nano versions are bundled, (3) MASSIVE range 0.52-0.67 vs tiny 0.368, (4) REPORT.md "pending hardware" note, (5) security reporting link, (6) default branch name `main`.

## B. Content and links

- [ ] All 6 pages exist at the paths in IA.md 1; internal links are relative and work both at a domain root and under `/sparrow-decider/`.
- [ ] 404.html works at a deep bad URL (assets load via its `<base>`), is `noindex`, offers Home/Models/Docs.
- [ ] Every external link matches the registry in IA.md 2; no 404s (run a link checker against the deployed preview).
- [ ] `pip install sparrow-decider` copy buttons copy exactly that string (no `$`, no trailing newline) on Home hero, header, footer, CTA band, Models download card.
- [ ] Code tab snippets match the docs verbatim (except the documented removal of the version comment in the Python tab); copy buttons copy raw text, not highlighted HTML.
- [ ] CTAs present on Home: pip copy (primary), Download models -> releases, View on GitHub -> repo, Docs -> docs/quickstart.
- [ ] Contact page has no forms, no email address, no third-party widgets.

## C. Visual and layout

- [ ] Home sections appear in order: hero, numbers, tiers, code, pico-or-nano, on-chip, limits, final CTA.
- [ ] No horizontal page scroll at 320, 360, 390, 768, 1024, 1280, 1440 px (tables and code scroll inside their own containers).
- [ ] Both themes complete: every page checked in dark and light; toggle persists across pages; no flash of the wrong theme on load.
- [ ] Gradient text only at >= 24 px; primary buttons use ink text on the three-stop gradient; no white text on gradient.
- [ ] Diagrams (pipeline, kv pooling, pico flow, ESP32 stack, pico-or-nano flowchart) are inline SVG, theme-aware, with mobile variants where specified; no text renders below 11 px at 360 px.
- [ ] Charts state units and scale; the laptop speed chart says "log scale"; the on-chip chart says "Each row has its own scale"; reference models are hatched and labelled.
- [ ] Tier ruler places dots at the correct log positions (2 KB, 1.37 MB, 2.2 MB, 7.6 MB, 17.9 MB, 47 MB).
- [ ] Empty data: tier panels and cards omit missing fields; tables show an em dash with "not measured" for screen readers.
- [ ] Typography: Sora / Inter / JetBrains Mono loaded; numbers tabular; "9.3 µs" never breaks across lines; micro sign is U+00B5.

## D. Interaction and motion

- [ ] Hero loop: timings per home.md 1; counter ends on the exact facts string; pauses off-screen and on hidden tab; pause button works by mouse and keyboard and exposes `aria-pressed`.
- [ ] Count-ups trigger once at 35% visibility and end on the exact facts strings.
- [ ] Tier selector and code tabs follow the ARIA tabs keyboard model (arrows, Home, End).
- [ ] pico-or-nano widget: both paths reach the right result, focus moves to the result, result announced, "Start over" works; flowchart highlights the path on >= 1024 px.
- [ ] Speedup chart animates once per spec, labels end on exact strings, "Show as table" disclosure works.
- [ ] Scroll reveal never hides above-the-fold content, never re-triggers, and nothing is hidden without JS.
- [ ] Mobile menu: opens/closes, Escape closes, focus trapped and returned, body scroll locked, closes on resize to desktop.
- [ ] Reduced motion (OS setting on): no count-ups, no loops, no slides, no ambient gradient motion; hero shows the resolved frame with a scene switcher.
- [ ] No-JS (JS disabled): all content readable; hero shows scene A resolved; tiers render as stacked cards; flowchart shown instead of the widget; tables visible.

## E. Accessibility (WCAG 2.2 AA)

- [ ] axe DevTools: 0 violations on every page, both themes.
- [ ] Skip link first in tab order and visible on focus.
- [ ] Visible focus ring on every interactive element; not obscured by the sticky header.
- [ ] Keyboard-only walk-through of every page completes every task (copy, switch tier, switch code tab, answer widget, open table disclosures, use menu, toggle theme).
- [ ] VoiceOver + Safari and NVDA + Firefox: headings outline is logical (one H1), landmarks named, copy announcements heard, tabs announced with position, charts/diagrams have text alternatives.
- [ ] Contrast checked with the token pairs in interaction.md 1.1; any new colour pair measured and recorded.
- [ ] 200% zoom and 320 px reflow pass; text-spacing bookmarklet causes no clipping.
- [ ] Targets >= 44x44 for buttons and icon buttons.

## F. Performance

- [ ] No frameworks or libraries; total JS < 150 KB uncompressed (report actual size per file).
- [ ] Only third-party hosts: fonts.googleapis.com, fonts.gstatic.com. No analytics, trackers, embeds, or external scripts.
- [ ] Fonts: preconnect + one CSS request + preloaded critical woff2 files; `display=swap`; fallback metrics prevent CLS.
- [ ] Lighthouse mobile on every page: Performance >= 95, Accessibility 100, Best Practices >= 95, SEO 100 (attach reports).
- [ ] LCP < 1.8 s, CLS < 0.02, TBT < 100 ms (lab).
- [ ] No raster images on pages; og.png < 150 KB.

## G. SEO and meta

- [ ] Unique `<title>` and description per page as in interaction.md 6.2 (titles <= 60 chars, descriptions <= 155).
- [ ] Absolute canonical and OG URLs using the deployed `{SITE_URL}`; OG image renders in a card validator.
- [ ] JSON-LD on Home validates and contains no ratings or person authors.
- [ ] `sitemap.xml` lists the five indexable pages; `robots.txt` points at it; 404 is `noindex`.
- [ ] Valid HTML (W3C validator) on every page; `lang="en"`.

## H. Constraints from the brief

- [ ] Static HTML/CSS/vanilla JS, no build step, deployable to GitHub Pages from `site/www/`.
- [ ] Nothing committed, pushed, published or deployed by the build agent; no accounts created.
- [ ] Brand tokens (palette, fonts) isolated in `:root` so the brand team can swap them in one place.
