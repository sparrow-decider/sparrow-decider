# Publishing Sparrow Decider models to Hugging Face

Prepared 2026-10-23. Nothing has been created or uploaded. Steps that need an account or a token
are marked **(owner)**.

## 0. Name availability (checked 2026-10-23)

| Check | Result |
|---|---|
| `curl https://huggingface.co/api/organizations/sparrow-decider/overview` | **404** "Sorry, we can't find the page you are looking for.": no organisation with that name |
| `curl https://huggingface.co/api/users/sparrow-decider/overview` | **404** "This user does not exist": no user with that name either (orgs and users share one namespace) |
| `curl "https://huggingface.co/api/models?author=sparrow-decider"` | **200 `[]`**: no models under that namespace |
| `https://huggingface.co/sparrow-decider` | 404 |

So `sparrow-decider` is free. Create the org soon; names are first come, first served.

Base models referenced in the cards exist and are MIT: `minishlab/potion-base-8M`,
`jhu-clsp/ettin-encoder-32m`, `jhu-clsp/ettin-encoder-68m`. The pico teacher
`StrandsAgents/strands-decider-2B-qwen3.5-v1-2610` exists and is Apache-2.0.

## 1. Layout: one repo per model line, versions as tags

| Repo | Current version | Files | Size |
|---|---|---|---|
| `sparrow-decider/sparrow-nano-general` | v1.1 | `sparrow-nano-general-v1.1.sparrow`, `sparrow-nano-general-v1.1.spb` | 2.2 MB + 2.5 MB |
| `sparrow-decider/sparrow-nano-robot` | v1.2 | `sparrow-nano-robot-v1.2.sparrow`, `sparrow-nano-robot-v1.2.spb` | 1.1 MB + 1.3 MB |
| `sparrow-decider/sparrow-micro-general` | v1.1 | `sparrow-micro-general-v1.1.sparrow`, `sparrow-micro-general-v1.1.spb` | 7.6 MB + 8.9 MB |
| `sparrow-decider/sparrow-tiny-general` | v1.0 | `sparrow-tiny-general-v1.0.sparrow` | 17.9 MB |
| `sparrow-decider/sparrow-small-general` | v1.0 | `sparrow-small-general-v1.0.sparrow` | 47 MB |
| `sparrow-decider/sparrow-pico-rover` (example) | v1.1 | `sparrow_pico_rover.h`, `rover.json` | 24 KB |

Every repo also gets `README.md` (the model card in `publishing/hf/<repo>/`), `LICENSE`, `NOTICE`
and a generated `SHA256SUMS`.

**Why no version in the repo name** (`sparrow-nano-robot`, not `sparrow-nano-robot-v1.2`):

- **Stable URL.** Links in the README, website, launch post and code keep working across releases.
  A new version is a new commit, not a new repo, so likes, downloads, discussions and the
  collection entry carry over instead of being split across `-v1.0`, `-v1.1`, `-v1.2`.
- **Versions are still exact.** Each release is tagged (`v1.1`, `v1.2`), and the file name keeps
  the full ID from `NAMING.md` (`sparrow-nano-robot-v1.2.sparrow`). Users pin with
  `revision="v1.2"` and `Decider.load()` sees the same name it sees in the pip package and the
  GitHub release.
- **Matches the Hub's model.** Hub repos are git repos; tags and revisions are the native way to
  version. The repo's commit history is the changelog of that model line.
- **Old versions stay downloadable** by tag even after `main` moves on. If an old version should
  stay prominent, keep its file next to the new one; the card says which is current.

Trade-off: someone who links to `main` gets the newest version silently. The cards show the
`revision=` pin, so anyone who needs reproducibility has the pattern in front of them.

Not mirrored to the Hub: superseded versions (nano-general v1.0, nano-robot v1.0/v1.1, micro v1.0,
pico-rover v1.0). They stay on the GitHub v0.1.0 release. You can upload them first and tag them if
you want full history in each repo; `upload.py` only handles the current set.

Source files (sha256 verified by `upload.py` before upload):

| File | Source |
|---|---|
| nano-general v1.1 `.sparrow` / `.spb`, nano-robot v1.2 `.sparrow` / `.spb`, `sparrow-pico-rover-v1.1.h` | `~/sparrow-decider-lab/release-assets-v0.2.0/` |
| micro-general v1.1 `.sparrow` / `.spb`, tiny-general v1.0, small-general v1.0 | `~/sparrow-decider-lab/release-assets/` (identical to `release/`) |
| `rover.json` | `c/examples/specs/rover.json` |

## 2. One-time setup (owner)

1. **(owner)** Sign up at https://huggingface.co/join with `vivek@sparrowdecider.com` (or add it
   as a verified email on an existing account). The mailbox must work first (see `CHECKLIST.md`).
2. **(owner)** Create the org: https://huggingface.co/organizations/new -> name `sparrow-decider`,
   full name "Sparrow Decider", type "Community" (or "Non-profit"/"Company" as you prefer),
   homepage `https://sparrowdecider.com`, GitHub `sparrow-decider`. Upload the logo from
   `site/brand/previews/logo-mark-512-light.png`.
3. **(owner)** In the org card (Settings -> Organization card) add one paragraph and the line
   "Unofficial community project. Not an AWS or Strands product."
   Add "Contact: vivek@sparrowdecider.com". Every model card already has a Contact section with
   this address.
4. **(owner)** Create a **fine-grained** token at https://huggingface.co/settings/tokens with
   *Write* access to repos under the `sparrow-decider` org only (and "Write access to collections"
   for the org). Do not use a classic write token.
5. Install the CLI (any venv): `pip install -U "huggingface_hub>=1.0"`. The new CLI is `hf`
   (`huggingface-cli` is the deprecated name for the same tool).
6. **(owner)** Log in: `hf auth login` (paste the token) and check with `hf auth whoami`. For the
   script you can instead `export HF_TOKEN=hf_...`.

## 3. Upload with the script (recommended)

`publishing/hf/upload.py` does every step below for all six repos: verify checksums, create the
repo (private unless `--public`), upload card + files + LICENSE + NOTICE + SHA256SUMS in one
commit per repo, tag the version, create the "Sparrow Decider" collection and add the repos, and
print the URLs. It is idempotent: re-running updates in place.

```bash
cd ~/sparrow-decider
python -m venv /tmp/hfvenv && /tmp/hfvenv/bin/pip install -U "huggingface_hub>=1.0"
export HF_ORG=sparrow-decider
export HF_TOKEN=hf_...                                   # or rely on `hf auth login`

/tmp/hfvenv/bin/python publishing/hf/upload.py --dry-run # plan only, no network writes
/tmp/hfvenv/bin/python publishing/hf/upload.py           # private repos, review them on the Hub
/tmp/hfvenv/bin/python publishing/hf/upload.py --public  # only flips NEW repos to public; see below
```

`--public` affects repos the script creates. For repos already created private, flip them with
`--make-public` (calls `update_repo_settings(private=False)`) once you have reviewed them:

```bash
/tmp/hfvenv/bin/python publishing/hf/upload.py --make-public
```

Single repo: `--only sparrow-nano-robot`. Different file locations: `--lab-dir PATH`.

## 4. Manual commands (same result, by hand)

```bash
ORG=sparrow-decider
LAB=~/sparrow-decider-lab
REPO=~/sparrow-decider

# per repo; example: nano-robot
hf repos create $ORG/sparrow-nano-robot --private --exist-ok
mkdir -p /tmp/hf-nano-robot && cd /tmp/hf-nano-robot
cp $REPO/publishing/hf/sparrow-nano-robot/README.md $REPO/LICENSE $REPO/NOTICE .
cp $LAB/release-assets-v0.2.0/sparrow-nano-robot-v1.2.sparrow $LAB/release-assets-v0.2.0/sparrow-nano-robot-v1.2.spb .
shasum -a 256 *.sparrow *.spb > SHA256SUMS
hf upload $ORG/sparrow-nano-robot . . --commit-message "sparrow-nano-robot-v1.2"
hf repos tag create $ORG/sparrow-nano-robot v1.2 -m "sparrow-nano-robot-v1.2"
```

Repeat for `sparrow-nano-general` (v1.1), `sparrow-micro-general` (v1.1, files from
`release-assets/`), `sparrow-tiny-general` (v1.0), `sparrow-small-general` (v1.0) and
`sparrow-pico-rover` (v1.1: copy `sparrow-pico-rover-v1.1.h` as `sparrow_pico_rover.h`, and
`c/examples/specs/rover.json`).

Collection:

```bash
hf collections create "Sparrow Decider" --namespace $ORG --private \
  --description "Decision models from 47 MB down to a few KB. Unofficial; not an AWS or Strands product."
# prints the slug, e.g. sparrow-decider/sparrow-decider-<id>
SLUG=sparrow-decider/sparrow-decider-xxxxxxxx
for r in sparrow-nano-general sparrow-nano-robot sparrow-micro-general sparrow-tiny-general sparrow-small-general sparrow-pico-rover; do
  hf collections add-item $SLUG $ORG/$r model --exists-ok
done
```

Make public (after review), per repo: Settings -> "Change repository visibility", or
`hf repos settings $ORG/<repo> --no-private` (huggingface_hub 2.3; check
`hf repos settings --help` on your version), or `upload.py --make-public`.

A collection containing private repos is visible only to org members; make the collection public
after the repos (Collection page -> "..." -> visibility) or let `upload.py --make-public` do it.

## 5. Collection "Sparrow Decider"

Order (the script adds them in this order, with a short note each):

1. `sparrow-nano-general`: 2.2 MB, default model, bundled with pip
2. `sparrow-nano-robot`: 1.11 MB, reads sensor numbers, bundled with pip
3. `sparrow-pico-rover`: example compiled C header, ~2 KB per question
4. `sparrow-micro-general`: 7.6 MB
5. `sparrow-tiny-general`: 17.9 MB
6. `sparrow-small-general`: 47 MB

Description (max 150 chars): "Decision models from 47 MB down to a few KB. Unofficial; not an AWS
or Strands product." (88 chars).

## 6. Releasing a new model version later

1. Put the new file next to the old one or replace it (`--delete "*-v1.2.*"` on `hf upload` if
   replacing), update the card's numbers from `site/facts.json` / `bench/RESULTS.md`, commit.
2. `hf repos tag create sparrow-decider/<repo> v1.3`.
3. Update `MODELS` in `publishing/hf/upload.py` so the script stays the source of truth.

## 7. Things to know

- **Cards contain only numbers from `site/facts.json` and `bench/RESULTS.md`.** If those change,
  regenerate the cards before uploading.
- `library_name: sparrow-decider` is not a library the Hub knows, so there is no "Use this model"
  snippet button. The cards carry the snippets instead. You can request integration later
  (huggingface.js `model-libraries.ts` PR) once there are users.
- There is no Inference widget for these models; the Hub cannot run `.sparrow` files.
- The pico repo is tagged `tabular-classification`, not `text-classification`: it reads sensor
  numbers, not text.
- README badge idea once live: `[![HF](https://img.shields.io/badge/%F0%9F%A4%97-models-yellow)](https://huggingface.co/collections/<slug>)`.
