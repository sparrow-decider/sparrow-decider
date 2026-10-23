# Launch checklist: Sparrow Decider 0.2.0

Do these in order. Details: `publishing/PYPI.md`, `publishing/HUGGINGFACE.md`.
Status checked 2026-10-23: `sparrow-decider` is free on PyPI, TestPyPI and Hugging Face.

## 0. Before anything goes public (repo edits, then commit)

- [ ] **Set up the mailbox `vivek@sparrowdecider.com` first.** It is the contact/maintainer
      address in the PyPI metadata guidance, the PyPI/TestPyPI/HF accounts and every HF model card.
      Owner reports the domain has no working mail yet. A `dig MX sparrowdecider.com` on 2026-10-23
      returned only GoDaddy's defaults (`10 mailstore1.secureserver.net`, `0 smtp.secureserver.net`),
      which do not deliver unless a GoDaddy mailbox or forwarding is bought. Either buy one, or point
      MX at your provider (Google Workspace, Fastmail, Zoho, or Cloudflare Email Routing to forward
      to a personal inbox). Add SPF/DMARC too. Send a test email from outside before using the
      address to sign up anywhere.
- [ ] `pyproject.toml`: add `email = "vivek@sparrowdecider.com"` to `authors` and a matching
      `maintainers` entry (`PYPI.md` section 0, item 5).
- [ ] README: "1.4 MB installed" -> "3.3 MB installed" (measured wheel 3.3 MB, both nanos inside).
- [ ] README: make the 20 relative links/images absolute (table in `PYPI.md` section 6). Hero
      image: use the PNG (`site/brand/previews/og-image.png`), not the SVG.
- [ ] README pico table says "pico vs the spec's rules 94.3%"; `site/facts.json` (the source of
      truth) says 94.0% for `sparrow-pico-rover-v1.1` (teacher 94.2%). Reconcile one of them.
- [ ] `python/sparrow_decider/__init__.py` docstring: `nano-robot` is v1.2 now, not v1.1.
- [ ] `NOTICE` says "potion-base-8M / Model2Vec, Copyright (c) MinishLab"; the upstream Model2Vec
      LICENSE says "Copyright (c) 2024 Thomas van Dongen". Consider quoting it exactly (the full
      text is in `publishing/hf/third_party/LICENSE-potion-base-8M.txt`).
- [ ] `pyproject.toml`: SPDX `license = "Apache-2.0"` + `license-files`, drop the licence classifier,
      `setuptools>=77`; add `Homepage`/`Source`/`Issues` URLs (`PYPI.md` sections 0 and 6).
- [ ] Commit `.github/workflows/publish-pypi.yml` and `publishing/`.

## 1. GitHub public

- [ ] Final review of history for secrets/private paths (`git log -p | grep -i -E "token|secret|/Users/"`).
- [ ] Settings -> General -> Change visibility -> Public (`sparrow-decider/sparrow-decider`).
- [ ] Enable Discussions (facts.json links to them) and Issues. Set the org's public email to
      `vivek@sparrowdecider.com`; consider adding it to `SECURITY.md`/`CITATION.cff` (`email:`).
- [ ] Settings -> Environments: create `pypi` (required reviewer: you; tags `v*`) and `testpypi`.
- [ ] Create release `v0.2.0` **as a draft** with assets: everything in
      `~/sparrow-decider-lab/release-assets-v0.2.0/` plus micro (`.sparrow` + `.spb`), tiny and small
      from `~/sparrow-decider-lab/release-assets/`. Do not publish it yet: publishing triggers PyPI.

Links that become valid now: every `github.com/sparrow-decider/sparrow-decider/...` URL in
README, `pyproject.toml`, `CITATION.cff`, `site/facts.json`, the website and the HF cards.

## 2. PyPI (TestPyPI first)

- [ ] TestPyPI account + pending publisher (environment `testpypi`), run the workflow manually with
      target `testpypi`, `pip install` from TestPyPI, check the page renders.
- [ ] PyPI account (`vivek@sparrowdecider.com`, 2FA) + pending publisher: owner `sparrow-decider`, repo `sparrow-decider`,
      workflow `publish-pypi.yml`, environment `pypi`.
- [ ] Publish the `v0.2.0` release -> approve the `pypi` environment -> check
      https://pypi.org/project/sparrow-decider/ and `pip install sparrow-decider` in a clean venv.

Links that become valid now: `pip install sparrow-decider` everywhere (README, site, launch post),
https://pypi.org/project/sparrow-decider/. Optional: add a PyPI version badge to README
(`https://img.shields.io/pypi/v/sparrow-decider`).

## 3. Hugging Face

- [ ] Account (email `vivek@sparrowdecider.com`), org `sparrow-decider` with the same contact
      email in its card, fine-grained write token for the org.
- [ ] `python publishing/hf/upload.py --dry-run`, then without `--dry-run` (private), review all six
      repos and the cards on the Hub, then `--make-public`.
- [ ] Note the collection URL it prints (`https://huggingface.co/collections/sparrow-decider/...`).

Links to switch now:
- README line 88-89 ("the others are on the releases page"): add the HF collection link next to
  the releases link; the Credits section can also link to the org.
- `docs/quickstart/python.md` line 50-51 ("Larger models ... attached to the GitHub releases"): add
  `hf download sparrow-decider/sparrow-micro-general ... --local-dir ~/.cache/sparrow-decider`.
- `python/sparrow_decider/__init__.py` `_resolve` error message ("Download more from the GitHub
  releases") can mention Hugging Face too (next package release).
- `pyproject.toml` `[project.urls]`: `Models = "https://huggingface.co/sparrow-decider"` (next
  package release; the 0.2.0 metadata on PyPI is frozen).

## 4. Website (https://sparrowdecider.com)

- [ ] Add `"pypi"` and `"huggingface"` (collection URL) to `site/facts.json`, and links for them in
      `site/www/_build/build.py` (`L = {...}` near line 28; "Download models" buttons at lines 304,
      328, 516, 691, 755 and per-model actions at 391 and 734-740). Rebuild with
      `site/www/_build/build.py`.
- [ ] Per-model "Download" links: point micro/tiny/small to their HF repos
      (`https://huggingface.co/sparrow-decider/sparrow-<tier>-general`), keep GitHub releases as
      the secondary link.
- [ ] Once the site is live: README hero image can use `https://sparrowdecider.com/assets/img/og.png`;
      set the HF org homepage and the GitHub repo "Website" field to https://sparrowdecider.com;
      add `Homepage` in `pyproject.toml` (next release).

## 5. Announce

- [ ] Launch post (`site/marketing/launch-post.md`) and press kit: check every number against
      `site/facts.json`; replace any relative or private links with GitHub / PyPI / HF / site URLs.
- [ ] Post with the disclaimer: "Unofficial community project. Not an AWS or Strands product."
- [ ] Pin the HF collection on the org page; add the HF and PyPI links to the GitHub repo "About".

## Links: what must be absolute/public, and when

| Link | Where | Switch when |
|---|---|---|
| 20 relative README links + hero image | README.md | before the first PyPI upload (step 0) |
| `../../releases` | README.md line 89 | step 0 (absolute GitHub releases URL) |
| GitHub repo URLs | README, pyproject, CITATION.cff, facts.json, site, HF cards | valid at step 1 |
| `pip install sparrow-decider` | README, site, docs, HF cards | valid at step 2 |
| HF repo / collection URLs | README, docs/quickstart/python.md, site, launch post | step 3 |
| https://sparrowdecider.com | pyproject `Homepage`, HF org, GitHub About, README image | step 4 |
