#!/usr/bin/env python3
"""Create the Sparrow Decider model repos on Hugging Face and upload files + model cards.

Nothing happens on import. Run it explicitly:

    export HF_ORG=sparrow-decider
    export HF_TOKEN=hf_...            # or `hf auth login` beforehand
    python publishing/hf/upload.py --dry-run         # print the plan, verify checksums, no network
    python publishing/hf/upload.py                   # create PRIVATE repos, upload, tag, collection
    python publishing/hf/upload.py --make-public     # after review: flip repos + collection to public

Per repo, one commit uploads: README.md (card from publishing/hf/<repo>/), the model files,
LICENSE, NOTICE, the third-party MIT notice for its base weights, and a generated SHA256SUMS.
Every model file is checked against the sha256 below before anything is sent.

Requires: pip install "huggingface_hub>=1.0"
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent            # publishing/hf
REPO_ROOT = HERE.parent.parent                    # sparrow-decider
DEFAULT_LAB = Path.home() / "sparrow-decider-lab"

COLLECTION_TITLE = "Sparrow Decider"
COLLECTION_DESC = "Decision models from 47 MB down to a few KB. Unofficial; not an AWS or Strands product."

# repo name -> version tag, files (source relative to --lab-dir unless it starts with "repo:"),
# expected sha256, third-party licence file, collection note.
MODELS: dict[str, dict] = {
    "sparrow-nano-general": {
        "tag": "v1.1",
        "files": {
            "sparrow-nano-general-v1.1.sparrow": ("release-assets-v0.2.0/sparrow-nano-general-v1.1.sparrow",
                                                  "d1d3ee04cdfa58f325bb7f06b701df92bc29a3debea59743bf14a7a6215ef2e3"),
            "sparrow-nano-general-v1.1.spb": ("release-assets-v0.2.0/sparrow-nano-general-v1.1.spb",
                                              "08f26db48c0e39e02f400f2a06b1bfdbae42226eae47db82062d02a8a8229d52"),
        },
        "third_party": "LICENSE-potion-base-8M.txt",
        "note": "2.2 MB, the default model; bundled with pip. 3.8 ms per decision on an ESP32-S3.",
    },
    "sparrow-nano-robot": {
        "tag": "v1.2",
        "files": {
            "sparrow-nano-robot-v1.2.sparrow": ("release-assets-v0.2.0/sparrow-nano-robot-v1.2.sparrow",
                                                "0fe7a7fee5b369c02c760e2c33c115b72e16a6a0a98e911ee5fea53a25248608"),
            "sparrow-nano-robot-v1.2.spb": ("release-assets-v0.2.0/sparrow-nano-robot-v1.2.spb",
                                            "16df13c6425b955856f4a0c3a45be42e4a4898232d423fcf734c679c2144c589"),
        },
        "third_party": "LICENSE-potion-base-8M.txt",
        "note": "1.11 MB, reads sensor numbers; bundled with pip. 3.5 ms per decision on an ESP32-S3.",
    },
    "sparrow-pico-rover": {
        "tag": "v1.1",
        "files": {
            "sparrow_pico_rover.h": ("release-assets-v0.2.0/sparrow-pico-rover-v1.1.h",
                                     "d418587ce1154242abea85ce1f400c7f458ba2fbe39e78c337fa5f93f9fe75ec"),
            "rover.json": ("repo:c/examples/specs/rover.json",
                           "60829aa0c0ffdd7b801b56f9a3f42853af01f687aaf94028436a8664cc56ec04"),
        },
        "third_party": None,
        "note": "Example compiled C header: ~2 KB per question, 9.3 µs per decision on an ESP32-S3.",
    },
    "sparrow-micro-general": {
        "tag": "v1.1",
        "files": {
            "sparrow-micro-general-v1.1.sparrow": ("release-assets/sparrow-micro-general-v1.1.sparrow",
                                                   "6cf1ed2068dff5d7eb2286f3013dba47801682e4efa1cfea1013706944c23e47"),
            "sparrow-micro-general-v1.1.spb": ("release-assets/sparrow-micro-general-v1.1.spb",
                                               "c799378614820e6823cdb8d52ea9dad966ccd29d70bf519004d72fa618c8c14e"),
        },
        "third_party": "LICENSE-potion-base-8M.txt",
        "note": "7.6 MB, full vocabulary. 0.22 ms per decision on a laptop core (C).",
    },
    "sparrow-tiny-general": {
        "tag": "v1.0",
        "files": {
            "sparrow-tiny-general-v1.0.sparrow": ("release-assets/sparrow-tiny-general-v1.0.sparrow",
                                                  "64b3a9dd2ed5e963685a16ae43ae24acff6eb042fa529c4baf36b9bce82ad7df"),
        },
        "third_party": "LICENSE-ettin.txt",
        "note": "17.9 MB, Ettin 32M encoder. 23 ms per decision on a laptop core (numpy).",
    },
    "sparrow-small-general": {
        "tag": "v1.0",
        "files": {
            "sparrow-small-general-v1.0.sparrow": ("release-assets/sparrow-small-general-v1.0.sparrow",
                                                   "2dc6e280b4d2a963b5c072b882060c62d0fe59aa5edc084415d88a984bf98921"),
        },
        "third_party": "LICENSE-ettin.txt",
        "note": "47 MB, Ettin 68M encoder, the most general tier. 64 ms per decision on a laptop core (numpy).",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_path(src: str, lab: Path) -> Path:
    return REPO_ROOT / src[5:] if src.startswith("repo:") else lab / src


def stage(name: str, spec: dict, lab: Path, out: Path) -> list[str]:
    """Copy everything for one repo into `out`, verifying checksums. Returns the file list."""
    card = HERE / name / "README.md"
    if not card.is_file():
        raise SystemExit(f"missing model card {card}")
    shutil.copyfile(card, out / "README.md")
    for extra in ("LICENSE", "NOTICE"):
        shutil.copyfile(REPO_ROOT / extra, out / extra)
    if spec["third_party"]:
        shutil.copyfile(HERE / "third_party" / spec["third_party"], out / spec["third_party"])
    sums = []
    for dst, (src, want) in spec["files"].items():
        p = source_path(src, lab)
        if not p.is_file():
            raise SystemExit(f"{name}: missing {p}")
        got = sha256(p)
        if got != want:
            raise SystemExit(f"{name}: checksum mismatch for {p}\n  expected {want}\n  got      {got}")
        shutil.copyfile(p, out / dst)
        sums.append(f"{got}  {dst}")
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    return sorted(f.name for f in out.iterdir())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Create Sparrow Decider repos on Hugging Face and upload models + cards. "
                    "Reads HF_ORG (default: sparrow-decider) and HF_TOKEN (or the `hf auth login` token).")
    ap.add_argument("--public", action="store_true",
                    help="create NEW repos and the collection as public (default: private). "
                         "Does not change repos that already exist; use --make-public for that.")
    ap.add_argument("--make-public", action="store_true",
                    help="only flip existing repos and the collection to public, then exit")
    ap.add_argument("--dry-run", action="store_true",
                    help="verify checksums and print the plan; no network calls, no token needed")
    ap.add_argument("--only", action="append", choices=sorted(MODELS), metavar="REPO",
                    help=f"limit to one repo (repeatable): {', '.join(MODELS)}")
    ap.add_argument("--lab-dir", type=Path, default=Path(os.environ.get("SPARROW_LAB", DEFAULT_LAB)),
                    help=f"folder with release-assets/ and release-assets-v0.2.0/ (default: {DEFAULT_LAB})")
    ap.add_argument("--no-collection", action="store_true", help="skip creating/updating the collection")
    ap.add_argument("--no-tag", action="store_true", help="skip creating the version tags")
    args = ap.parse_args(argv)

    org = os.environ.get("HF_ORG", "sparrow-decider")
    names = args.only or list(MODELS)
    private = not args.public

    if args.dry_run:
        print(f"org: {org}   visibility of new repos: {'private' if private else 'public'}   lab: {args.lab_dir}")
        for name in names:
            spec = MODELS[name]
            with tempfile.TemporaryDirectory() as tmp:
                files = stage(name, spec, args.lab_dir, Path(tmp))
                size = sum((Path(tmp) / f).stat().st_size for f in files)
            print(f"\n{org}/{name}  tag {spec['tag']}  ({size / 1e6:.2f} MB)")
            for f in files:
                print(f"  {f}")
        if not args.no_collection:
            print(f"\ncollection: {COLLECTION_TITLE!r} in {org}, items in this order: {', '.join(names)}")
        print("\ndry run: checksums OK, nothing uploaded")
        return 0

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print('huggingface_hub is not installed: pip install -U "huggingface_hub>=1.0"', file=sys.stderr)
        return 2

    api = HfApi(token=os.environ.get("HF_TOKEN"))  # None -> token saved by `hf auth login`
    who = api.whoami()
    print(f"authenticated as {who.get('name')}; org {org}")

    if args.make_public:
        for name in names:
            api.update_repo_settings(f"{org}/{name}", private=False)
            print(f"public: https://huggingface.co/{org}/{name}")
        for c in api.list_collections(owner=org):
            if c.title == COLLECTION_TITLE:
                api.update_collection_metadata(c.slug, private=False)
                print(f"public: https://huggingface.co/collections/{c.slug}")
        return 0

    urls = []
    for name in names:
        spec = MODELS[name]
        repo_id = f"{org}/{name}"
        api.create_repo(repo_id, private=private, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            files = stage(name, spec, args.lab_dir, Path(tmp))
            info = api.upload_folder(repo_id=repo_id, folder_path=tmp,
                                     commit_message=f"{name} {spec['tag']}",
                                     commit_description="Files: " + ", ".join(files))
        print(f"uploaded {repo_id}: {getattr(info, 'commit_url', '')}")
        if not args.no_tag:
            api.create_tag(repo_id, tag=spec["tag"], tag_message=f"{name}-{spec['tag']}", exist_ok=True)
            print(f"  tag {spec['tag']}")
        urls.append(f"https://huggingface.co/{repo_id}")

    if not args.no_collection:
        col = api.create_collection(COLLECTION_TITLE, namespace=org, description=COLLECTION_DESC,
                                    private=private, exists_ok=True)
        for name in names:
            api.add_collection_item(col.slug, f"{org}/{name}", "model", note=MODELS[name]["note"], exists_ok=True)
        urls.append(f"https://huggingface.co/collections/{col.slug}")

    print("\nDone. URLs:")
    for u in urls:
        print(f"  {u}")
    if private:
        print("\nRepos are private. Review them, then run with --make-public.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
