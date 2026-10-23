# Publishing `sparrow-decider` to PyPI

Prepared 2026-10-23 for version 0.2.0. Nothing here has been uploaded. Commands that need an
account or a token are marked **(owner)**.

## 0. Status checked on 2026-10-23

| Check | Result |
|---|---|
| `curl https://pypi.org/pypi/sparrow-decider/json` | **404 `{"message": "Not Found"}`: the name is free** |
| `curl https://pypi.org/pypi/sparrow_decider/json` (normalised spelling) | 404: free |
| `curl https://test.pypi.org/pypi/sparrow-decider/json` | 404: free on TestPyPI too |
| `python -m build` (setuptools, clean venv, from `git archive HEAD` at e07e9ce) | built `sparrow_decider-0.2.0-py3-none-any.whl` and `sparrow_decider-0.2.0.tar.gz` |
| Wheel size | **3,336,183 bytes (3.3 MB)**; 3,369,673 bytes uncompressed, 15 files |
| sdist size | 3,342,889 bytes (3.3 MB) |
| Bundled models in the wheel | `sparrow_decider/models/sparrow-nano-general-v1.1.sparrow` (2,201,031 B) and `sparrow_decider/models/sparrow-nano-robot-v1.2.sparrow` (1,112,028 B): **both present** |
| `LICENSE` and `NOTICE` in the wheel | present (`dist-info/licenses/`) |
| `twine check --strict dist/*` | **PASSED** for both files |
| Install the wheel in a fresh venv, `Decider.load()`, `sparrow-decider --help` | works; `available_models()` lists both nanos |
| Installed size | 3.3 MB (`site-packages/sparrow_decider`) |

The build artifacts and the temporary venv were in the session scratch directory and have been
deleted. Nothing was written to the repo.

**Things to fix before uploading** (PyPI files are immutable: a version can never be re-uploaded):

1. **README says "1.4 MB installed"** (Quickstart, the `pip install` comment). The measured install
   is 3.3 MB, because both nanos are bundled (2.2 MB + 1.11 MB). Change it to "3.3 MB installed".
2. **setuptools deprecation warnings** (not errors; they stop working after 2027-02-18):
   `project.license` as a TOML table and the `License ::` classifier. Recommended `pyproject.toml`
   change (needs `setuptools>=77`):
   ```toml
   [build-system]
   requires = ["setuptools>=77"]
   ...
   license = "Apache-2.0"
   license-files = ["LICENSE", "NOTICE"]
   # and delete the "License :: OSI Approved :: Apache Software License" classifier
   ```
3. **Relative links and images in README.md break on PyPI** (section 6). Fix before the first
   upload, or the PyPI page for 0.2.0 will have a broken hero image and ~20 dead links forever.
4. Optional: add `Homepage = "https://sparrowdecider.com"` and `Source`, `Issues` URLs to
   `[project.urls]` once the site and repo are public (section 6).
5. **Contact email in package metadata.** Add the maintainer email so it shows on PyPI:
   ```toml
   authors = [{ name = "Vivek Raja P S", email = "vivek@sparrowdecider.com" }]
   maintainers = [{ name = "Vivek Raja P S", email = "vivek@sparrowdecider.com" }]
   ```
   Use the same address for the PyPI and TestPyPI accounts (or at least as a verified secondary
   address), so security notices reach the project mailbox. The mailbox must work first (see
   `CHECKLIST.md` step 0).
6. The `Decider.load` docstring in `python/sparrow_decider/__init__.py` says
   `Decider.load("nano-robot")  # bundled sparrow-nano-robot-v1.1`; the bundled one is now v1.2.

## 1. Build and check locally (no account needed)

Always build in a throwaway venv outside the repo so `build/`, `dist/` and `*.egg-info` never land
in the working tree (they are git-ignored, but a stale `build/` can leak old files into a wheel).

```bash
T=$(mktemp -d) && mkdir "$T/src"
git -C ~/sparrow-decider archive HEAD | tar -x -C "$T/src"
python3.12 -m venv "$T/venv"
"$T/venv/bin/pip" install --upgrade pip build twine
cd "$T/src" && "$T/venv/bin/python" -m build --outdir "$T/dist"
"$T/venv/bin/twine" check --strict "$T/dist/"*

# inspect: both models must be listed, size should be ~3.3 MB
unzip -l "$T/dist/"*.whl
ls -l "$T/dist/"

# smoke test in a clean venv
python3.12 -m venv "$T/smoke" && "$T/smoke/bin/pip" install "$T/dist/"*.whl
(cd /tmp && "$T/smoke/bin/python" -c "import sparrow_decider as s; print(s.available_models()); s.Decider.load()")

rm -rf "$T"   # clean up
```

Building from `git archive HEAD` means you ship exactly what is committed. Commit first.

## 2. Pre-release checklist

- [ ] Version bumped in **both** `pyproject.toml` (`version = "0.2.0"`) and
      `python/sparrow_decider/__init__.py` (`__version__ = "0.2.0"`), plus `site/facts.json`
      (`"version"`) and `CITATION.cff`. `sparrow-decider --version` must print the new version.
- [ ] `CHANGELOG.md` has a dated section for the version (0.2.0 is dated 2026-10-23: done).
- [ ] `pytest -q` green on CI (`.github/workflows/ci.yml`).
- [ ] README fixes from section 0 (install size, absolute URLs) committed.
- [ ] `pyproject.toml` licence fields modernised (optional but recommended).
- [ ] Local build + `twine check --strict` pass (section 1).
- [ ] TestPyPI dry run done and `pip install` from TestPyPI works (section 3).
- [ ] README renders on the TestPyPI project page: hero image shows, badges show, links work
      (mermaid diagrams show as code blocks on PyPI; that is expected, see section 6).
- [ ] Repo is public (Trusted Publishing works with a private repo, but the PyPI page links to it).
- [ ] Git tag `v0.2.0` created by the GitHub release (section 4). The workflow refuses to publish
      if the tag does not match `pyproject.toml`.

## 3. TestPyPI dry run

TestPyPI is a separate site with separate accounts. Uploads there are also permanent per version,
but nobody depends on them.

**(owner)** Create an account at https://test.pypi.org/account/register/ with
`vivek@sparrowdecider.com` and turn on 2FA.

### 3a. Via GitHub Actions (recommended, same path as production)

**(owner)** On https://test.pypi.org/manage/account/publishing/ add a *pending publisher*:

| Field | Value |
|---|---|
| PyPI Project Name | `sparrow-decider` |
| Owner | `sparrow-decider` |
| Repository name | `sparrow-decider` |
| Workflow name | `publish-pypi.yml` |
| Environment name | `testpypi` |

Then in GitHub: **Settings -> Environments -> New environment -> `testpypi`** (no secrets needed).
Run **Actions -> publish-pypi -> Run workflow**, target `testpypi`.

### 3b. Or from your laptop with a token

**(owner)** Create an API token at https://test.pypi.org/manage/account/token/ (scope: entire
account for the first upload; narrow it to the project afterwards).

```bash
"$T/venv/bin/twine" upload --repository testpypi "$T/dist/"*
# username: __token__   password: pypi-... (the TestPyPI token)
```

### Verify

```bash
python3.12 -m venv /tmp/tp && /tmp/tp/bin/pip install \
  --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ \
  sparrow-decider==0.2.0
/tmp/tp/bin/sparrow-decider models
/tmp/tp/bin/sparrow-decider ask "battery: 6%" --noul "Is the battery low?"
```

(`--extra-index-url` is needed because numpy is not on TestPyPI.) Open
https://test.pypi.org/project/sparrow-decider/ and check the README renders.

## 4. Production: Trusted Publishing from GitHub Actions (recommended)

No long-lived token anywhere. GitHub mints a short-lived OIDC token for the `publish-pypi` job,
and PyPI only accepts it from this exact repo + workflow + environment.

**(owner)** One-time setup:

1. Create a PyPI account at https://pypi.org/account/register/ with `vivek@sparrowdecider.com`
   (verify it) and enable 2FA (required).
2. Go to https://pypi.org/manage/account/publishing/ -> **Add a new pending publisher** -> GitHub,
   and enter exactly:

   | Field | Value |
   |---|---|
   | PyPI Project Name | `sparrow-decider` |
   | Owner | `sparrow-decider` |
   | Repository name | `sparrow-decider` |
   | Workflow name | `publish-pypi.yml` |
   | Environment name | `pypi` |

   A *pending* publisher reserves nothing until the first upload; publish soon after adding it.
3. In GitHub, **Settings -> Environments -> New environment -> `pypi`**. Recommended protection:
   *Required reviewers* = you, and *Deployment branches and tags* = tags matching `v*`. Then a
   release waits for your click before anything reaches PyPI.
4. Commit `.github/workflows/publish-pypi.yml` (already written, not committed) to `main`.

**(owner)** Each release:

```bash
git tag -a v0.2.0 -m "Sparrow Decider 0.2.0"   # or let the GitHub release create the tag
git push origin v0.2.0
gh release create v0.2.0 --title "Sparrow Decider 0.2.0" --notes-file <(sed -n '/^## 0.2.0/,/^## 0.1.0/p' CHANGELOG.md | sed '$d') \
  ~/sparrow-decider-lab/release-assets-v0.2.0/* ~/sparrow-decider-lab/release-assets/sparrow-micro-general-v1.1.* \
  ~/sparrow-decider-lab/release-assets/sparrow-tiny-general-v1.0.sparrow ~/sparrow-decider-lab/release-assets/sparrow-small-general-v1.0.sparrow
```

Publishing the release triggers `publish-pypi.yml`: tests (Ubuntu + macOS, Python 3.10 and 3.12),
tag-equals-version check, `python -m build`, `twine check --strict`, a check that both models are
in the wheel, a clean-venv smoke test, then upload. Approve the `pypi` environment if you set a
reviewer. Watch it with `gh run watch`.

Afterwards, on https://pypi.org/manage/project/sparrow-decider/settings/ consider adding a
co-maintainer account so the project is not tied to one login.

## 5. Fallback: API token from your laptop

Use only if Trusted Publishing is not possible.

**(owner)**
1. https://pypi.org/manage/account/token/ -> create a token. For the very first upload the scope
   must be "Entire account" (the project does not exist yet). After the first upload, delete it
   and create a new one scoped to `sparrow-decider` only.
2. Upload the files you built and checked in section 1:
   ```bash
   "$T/venv/bin/twine" upload "$T/dist/"*
   # username: __token__   password: pypi-...
   ```
   Or put it in `~/.pypirc` (`chmod 600`):
   ```ini
   [pypi]
   username = __token__
   password = pypi-...
   ```
3. If you want CI to use a token instead of OIDC: store it as the `PYPI_API_TOKEN` secret of the
   `pypi` environment and add `with: password: ${{ secrets.PYPI_API_TOKEN }}` to the publish step.
   Trusted Publishing is better; prefer it.

## 6. README on PyPI: relative links and images

PyPI renders `README.md` (via `readme_renderer`) with no repository context, so every relative path
resolves against `pypi.org/project/sparrow-decider/` and 404s. GitHub-only features also differ:

- **Mermaid** (` ```mermaid ` blocks, 2 of them) shows as plain code on PyPI. Acceptable; or replace
  with an image.
- **In-page anchors** (`#quickstart`, `#the-family`, `#benchmarks`) rely on GitHub's generated
  heading ids, which PyPI does not add. They will not jump.
- **SVG hero image**: use the PNG (`site/brand/previews/og-image.png` exists) for the PyPI copy, or
  host it on sparrowdecider.com. SVGs served from `raw.githubusercontent.com` are sent as
  `text/plain` and often do not render through PyPI's image proxy.

Relative links and images in `README.md` (line numbers as of e07e9ce):

| Line | Relative target | Replace with |
|--:|---|---|
| 2 | `<img src="site/brand/og-image.svg">` (**image**) | `https://raw.githubusercontent.com/sparrow-decider/sparrow-decider/main/site/brand/previews/og-image.png` (or `https://sparrowdecider.com/assets/img/og.png` once the site is live) |
| 6 | `href="LICENSE"` | `https://github.com/sparrow-decider/sparrow-decider/blob/main/LICENSE` |
| 14 | `href="#quickstart"` | `https://github.com/sparrow-decider/sparrow-decider#quickstart` |
| 15 | `href="#the-family"` | `https://github.com/sparrow-decider/sparrow-decider#the-family` |
| 16 | `href="#benchmarks"` | `https://github.com/sparrow-decider/sparrow-decider#benchmarks` |
| 17 | `href="docs/quickstart"` | `https://github.com/sparrow-decider/sparrow-decider/tree/main/docs/quickstart` |
| 18 | `href="research/REPORT.md"` | `https://github.com/sparrow-decider/sparrow-decider/blob/main/research/REPORT.md` |
| 70 | `(docs/quickstart/python.md)` | `.../blob/main/docs/quickstart/python.md` |
| 71 | `(docs/quickstart/agents.md)` | `.../blob/main/docs/quickstart/agents.md` |
| 72 | `(docs/quickstart/esp32.md)` | `.../blob/main/docs/quickstart/esp32.md` |
| 73 | `(docs/quickstart/pico.md)` | `.../blob/main/docs/quickstart/pico.md` |
| 74 | `(docs/quickstart/c.md)` | `.../blob/main/docs/quickstart/c.md` |
| 89 | `href="../../releases"` | `https://github.com/sparrow-decider/sparrow-decider/releases` (this one is also fragile on GitHub itself) |
| 89 | `href="NAMING.md"` | `.../blob/main/NAMING.md` |
| 125 | `href="bench/RESULTS.md"` | `.../blob/main/bench/RESULTS.md` |
| 128 | `(c/examples/specs/rover.json)` | `.../blob/main/c/examples/specs/rover.json` |
| 187 | `(research/REPORT.md)` | `.../blob/main/research/REPORT.md` |
| 213 | `(NOTICE)` | `.../blob/main/NOTICE` |
| 213 | `(docs/models.md)` | `.../blob/main/docs/models.md` |
| 213 | `(CITATION.cff)` | `.../blob/main/CITATION.cff` |

(`...` = `https://github.com/sparrow-decider/sparrow-decider`.) All shields.io badges and the
Strands Decider / Hugging Face links are already absolute.

Pinning to `main` means the PyPI page of an old version shows today's docs. If you prefer exact
docs per release, use `/blob/v0.2.0/...` instead and update the tag each release. Absolute links
work on GitHub too, so there is no need for two READMEs.

Once the Hugging Face repos are live, the "others are on the releases page" sentence (line 88-89)
can also point to the Hugging Face collection (see `publishing/CHECKLIST.md`).

Suggested `[project.urls]` once public:

```toml
[project.urls]
Homepage = "https://sparrowdecider.com"
Source = "https://github.com/sparrow-decider/sparrow-decider"
Documentation = "https://github.com/sparrow-decider/sparrow-decider/tree/main/docs"
Changelog = "https://github.com/sparrow-decider/sparrow-decider/blob/main/CHANGELOG.md"
Issues = "https://github.com/sparrow-decider/sparrow-decider/issues"
Models = "https://huggingface.co/sparrow-decider"
```

## 7. If something goes wrong

- **Wrong file uploaded:** you cannot overwrite. *Yank* the version on PyPI (Manage -> Releases ->
  Options -> Yank) and release `0.2.1`. Deleting is possible but the version number stays burned.
- **`invalid-publisher` error from the action:** one of owner / repo / workflow file name /
  environment differs from what was entered on pypi.org. They are case-sensitive.
- **Upload over 100 MB:** not an issue (wheel is 3.3 MB). Do not bundle micro/tiny/small; they
  belong on GitHub releases and Hugging Face.
