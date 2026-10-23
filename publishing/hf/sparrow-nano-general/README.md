---
license: apache-2.0
library_name: sparrow-decider
pipeline_tag: text-classification
language:
  - en
base_model: minishlab/potion-base-8M
base_model_relation: finetune
tags:
  - sparrow-decider
  - decision-making
  - text-classification
  - tinyml
  - embedded
  - esp32
  - microcontroller
  - static-embeddings
  - distillation
  - agents
  - robotics
---

# sparrow-nano-general (v1.1)

A 2.2 MB general-purpose decision model. It answers yes/no (`noul`), pick-one (`choice`) and
rate-on-a-scale (`score`) questions about a text state, with calibrated probabilities. It runs in
**3.8 ms per decision on a $10 ESP32-S3** and in about 0.06 ms on a laptop core with the C runtime.
It is the default model of the `sparrow-decider` pip package.

Part of [Sparrow Decider](https://github.com/sparrow-decider/sparrow-decider), a family of decision
models from 47 MB down to a few KB. Same question and answer shapes as
[Strands Decider](https://github.com/strands-labs/strands-decider).

> Unofficial community project. Not an AWS or Strands product.

| | |
|---|---|
| Model ID | `sparrow-nano-general-v1.1` |
| Tier | nano (static embeddings + MLP) |
| File | `sparrow-nano-general-v1.1.sparrow` (2.2 MB, Python) · `sparrow-nano-general-v1.1.spb` (2.53 MB packed SPB1 blob, C) |
| Input | text |
| Runs on | ESP32-S3, Raspberry Pi, laptop |
| Dependencies | numpy (Python) · C99 + libm, no malloc (C) |
| Also bundled in | `pip install sparrow-decider` (default model) |

## Intended use

- Tool and intent routing inside an agent, gating ("should I call the big model?"), urgency
  scores, short text decisions on edge devices.
- Any place where a decision must be made in milliseconds without a GPU, network or model server.

**Out of scope:** open-ended language far from its training data, yes/no judgement that needs
reasoning (see Limitations), and being the only safety mechanism on a physical system. For
decisions over sensor numbers, prefer
[sparrow-nano-robot](https://huggingface.co/sparrow-decider/sparrow-nano-robot).

## How to use

### Python

```bash
pip install sparrow-decider
```

```python
from sparrow_decider import Decider

d = Decider.load()                       # the bundled sparrow-nano-general-v1.1
d.ask("User: please move my 3pm meeting with Sam to Friday", {
    "tool": {"type": "choice", "instructions": "Which tool should the agent call?",
             "criteria": {"weather": "get a weather forecast", "calendar": "read or change calendar events",
                          "email": "send or read email", "search": "search the web"}},
    "urgency": {"type": "score", "instructions": "How urgent is this?", "criteria": ["can wait", "today", "now"]},
})
# {"tool": {"type": "choice", "choice": "calendar", "probabilities": {...}, "confidence": ...},
#  "urgency": {"type": "score", "score": ..., ...}}
```

The exact file from this repo, pinned to a version:

```python
from huggingface_hub import hf_hub_download
from sparrow_decider import Decider

path = hf_hub_download("sparrow-decider/sparrow-nano-general", "sparrow-nano-general-v1.1.sparrow", revision="v1.1")
d = Decider.load(path)
```

CLI and HTTP server: `sparrow-decider ask "..." --choice "..." -o name=description`,
`sparrow-decider serve --port 8000` (`POST /v1/systemone`).

### C / ESP32-S3

`sparrow-nano-general-v1.1.spb` is the packed blob for the C99 runtime in
[`c/sparrow`](https://github.com/sparrow-decider/sparrow-decider/tree/main/c/sparrow) (one `.c`, one
`.h`, an ESP-IDF component). It is read in place from flash; no malloc.

```c
#include "sparrow.h"
static sparrow_model m;
static sparrow_ctx ctx;   /* working memory; keep it static */

sparrow_load(&m, blob, blob_len);            /* blob = contents of the .spb, e.g. in flash */
sparrow_option opts[] = {{"weather", "get a weather forecast"}, {"calendar", "read or change calendar events"},
                         {"email", "send or read email"}, {"search", "search the web"}};
const char *state = "User: please move my 3pm meeting with Sam to Friday";
float conf;
int k = sparrow_choice(&m, &ctx, state, "Which tool should the agent call?", opts, 4, &conf);
float p_true = sparrow_noul(&m, &ctx, state, "Is the user upset?");
```

Build with `-DSPARROW_MAX_DIM=128` to halve RAM for nano. On an ESP32-S3, follow the
[ESP32-S3 guide](https://github.com/sparrow-decider/sparrow-decider/blob/main/docs/quickstart/esp32.md);
to compile the model in as a C array use
`python c/tools/pack.py sparrow-nano-general-v1.1.sparrow -o model.spb --header nano_model.h --symbol nano_model`.

## Measured results

All numbers are from the project's
[bench/RESULTS.md](https://github.com/sparrow-decider/sparrow-decider/blob/main/bench/RESULTS.md) and
`site/facts.json`. Local runs, not leaderboard scores.

**Speed**

| Where | Time per decision (p50) |
|---|--:|
| ESP32-S3, 240 MHz (int8 SIMD) | **3.8 ms** (first on-chip build: 9.6 ms) |
| Laptop, 1 Apple M4 Pro core, C runtime | 0.06 ms (63.5 µs) |
| Laptop, 1 core, numpy | 0.21 ms (RobotBench) · 0.37 ms p50 / 4.64 ms p95 (JevBench) |
| Peak RSS, numpy, JevBench run | 52.2 MB |

**Quality**

| Benchmark | sparrow-nano-general-v1.1 | Strands Decider 2B (public) |
|---|--:|--:|
| JevBench public, 231 tasks (local v1.5 proxy) | **122/231** | |
| MASSIVE 1.1 en-US, 600 held-out utterances: domain / intent | 0.50 / 0.588 | 0.86 / 0.871 |
| RobotBench v0, 55 hand-written robot decisions | 32/55 | 40/55 |

**C parity:** on the host, the C runtime agrees with numpy on 286/286 argmaxes, max probability
difference 1e-6. On the ESP32-S3, int8 builds agree with the host on 150-155 of 155 decisions; the
few mismatches are rounding near ties.

## Limitations

- Static embeddings pool words without order: negation and multi-step reasoning are weak.
- Open-ended language it never trained on is well behind the 2B (MASSIVE routing above).
- Yes/no judgement on JevBench is near chance at every Sparrow tier. A `noul` near 0.5 means
  "don't know"; treat it that way, or use a full decider or an LLM for those questions.
- Close calls between similar options can have low confidence; read `confidence`, not just
  `choice`.
- English only. Text normalisation is exact for Latin scripts.
- It suggests decisions. Never use it as the only safety stop on a physical system.

## Training

- **Init:** potion-base-8M static embeddings, PCA-reduced to 128-d, vocabulary pruned to 16k
  pieces (every single character kept, so any word still tokenizes).
- **Architecture:** mean-pooled state / question / option vectors and an MLP (128 hidden) that
  scores every option against the state and the question.
- **Data:** a general decision mix plus generated robot decisions. Only tasksource rows marked for
  commercial use were used; sources keep their own licences.
- **Teacher:** distilled from a Strands Decider 4B checkpoint (targets 50% teacher, 50% gold) on
  about 430k decisions; per-kind temperature calibration.
- **Compression:** int8 matrices with a per-row scale.

Details: [research report](https://github.com/sparrow-decider/sparrow-decider/blob/main/research/REPORT.md).

## Licence and credits

- **Licence:** Apache-2.0 (see `LICENSE` and `NOTICE` in this repo).
- **Base weights:** derived from [potion-base-8M](https://huggingface.co/minishlab/potion-base-8M)
  ([Model2Vec](https://github.com/MinishLab/model2vec), MinishLab), released under the MIT licence.
  Its copyright notice and full MIT text are in `LICENSE-potion-base-8M.txt` in this repo and apply
  to the corresponding weights.
- **Teacher and prompt format:** [Strands Decider](https://github.com/strands-labs/strands-decider)
  (Apache-2.0).
- **Evaluation only:** Amazon MASSIVE 1.1 (CC BY 4.0), JevBench (MIT).

Unofficial community project. Not an AWS or Strands product.

## Contact

- Email: vivek@sparrowdecider.com
- Issues: https://github.com/sparrow-decider/sparrow-decider/issues
- Discussions: https://github.com/sparrow-decider/sparrow-decider/discussions

## Citation

```bibtex
@software{sparrow_decider,
  author  = {Raja P S, Vivek},
  title   = {Sparrow Decider: decision models from 47 MB down to a few KB},
  year    = {2026},
  version = {0.2.0},
  url     = {https://github.com/sparrow-decider/sparrow-decider}
}
```
