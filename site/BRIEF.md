# Sparrow Decider launch: shared brief (all agents)

**Facts:** every number and claim comes from `site/facts.json`. Never invent metrics, users, logos,
testimonials, partners, stars or downloads. If something would need a number not in facts.json, leave it out.

**Must appear:** "Unofficial community project. Not an AWS or Strands product." (footer and launch copy).
No individual people's names. Credit the work to "the Sparrow Decider contributors".

**Audience:** developers building agents, robots and embedded/IoT products. Tone: confident, precise,
playful-but-engineered. Short sentences. Numbers do the bragging.

**Brand direction (starting point; brand team owns the final):**
- Name: Sparrow Decider. Short form: Sparrow. Mark: geometric sparrow (see docs/assets/banner.svg, may be revamped).
- Palette: vibrant, smooth gradients on deep ink. Suggested: ink #0B1020, surface #111832, sunrise gradient
  #FFB547 -> #FF6B4A -> #FF3D8B -> #8B5CF6, electric cyan accent #22D3EE, off-white text #F5F7FF. Light mode must work too.
- Type: a geometric display face + Inter for body (Google Fonts only), JetBrains Mono for code.
- Motion: smooth, purposeful, respects prefers-reduced-motion.

**Tagline shortlist (brand team picks/improves):**
- "Decisions at the speed of a heartbeat." / "Tiny models. Instant decisions." / "From 47 MB to 2 KB. Same decision." /
  "Decide in microseconds." / "The decider that fits on a chip."

**Site:** static (HTML/CSS/vanilla JS, no build step) in `site/www/`, deployable to GitHub Pages.
Pages: Home (hero, live-feeling demo, numbers, tiers, install/download CTAs), Models, Architecture, Benchmarks, Contact.
CTAs: `pip install sparrow-decider` (copy button), Download models (GitHub releases), View on GitHub, Read the docs.

**Rules for agents:** write only inside your assigned folder. Do not commit, push, publish, deploy or
create accounts. No external scripts except Google Fonts. No tracking/analytics.
