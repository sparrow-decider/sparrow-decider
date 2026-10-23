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
  - edge
  - static-embeddings
  - distillation
  - agents
  - robotics
---

# sparrow-micro-general (v1.1)

A 7.6 MB decision model with the full potion-base-8M vocabulary. It answers yes/no (`noul`),
pick-one (`choice`) and rate-on-a-scale (`score`) questions about a text state, with calibrated
probabilities, in **0.22 ms per decision on one laptop core** with the C runtime.

Part of [Sparrow Decider](https://github.com/sparrow-decider/sparrow-decider), a family of decision
models from 47 MB down to a few KB. Same question and answer shapes as
[Strands Decider](https://github.com/strands-labs/strands-decider).

> Unofficial community project. Not an AWS or Strands product.

| | |
|---|---|
| Model ID | `sparrow-micro-general-v1.1` |
| Tier | micro (static embeddings + MLP) |
| File | `sparrow-micro-general-v1.1.sparrow` (7.6 MB, Python) · `sparrow-micro-general-v1.1.spb` (8.88 MB packed SPB1 blob, C) |
| Input | text |
| Runs on | Raspberry Pi, laptop |
| Dependencies | numpy (Python) · C99 + libm, no malloc (C) |

## Intended use

- Short text decisions (routing, gating, urgency) when you have a few MB to spare and want the
  full vocabulary instead of nano's pruned one; sub-millisecond on a CPU.
- Its MASSIVE domain routing (0.635) is higher than the nanos' (0.50-0.518).

**Out of scope:** open-ended language far from its training data, yes/no judgement that needs
reasoning, and being the only safety mechanism on a physical system.

## How to use

### Python

```bash
pip install sparrow-decider huggingface_hub
```

```python
from huggingface_hub import hf_hub_download
from sparrow_decider import Decider

path = hf_hub_download("sparrow-decider/sparrow-micro-general", "sparrow-micro-general-v1.1.sparrow", revision="v1.1")
d = Decider.load(path)
d.ask("User: please move my 3pm meeting with Sam to Friday", {
    "tool": {"type": "choice", "instructions": "Which tool should the agent call?",
             "criteria": {"weather": "get a weather forecast", "calendar": "read or change calendar events",
                          "email": "send or read email", "search": "search the web"}},
})  # -> calendar
```

To load it by name (`Decider.load("micro-general")`, `sparrow-decider --model micro-general ...`),
put the file in `~/.cache/sparrow-decider/` or any folder listed in `$SPARROW_MODELS`:

```bash
hf download sparrow-decider/sparrow-micro-general sparrow-micro-general-v1.1.sparrow --local-dir ~/.cache/sparrow-decider
```

### C

`sparrow-micro-general-v1.1.spb` is the packed blob for the C99 runtime in
[`c/sparrow`](https://github.com/sparrow-decider/sparrow-decider/tree/main/c/sparrow). See the
[C library guide](https://github.com/sparrow-decider/sparrow-decider/blob/main/docs/quickstart/c.md).

```c
#include "sparrow.h"
static sparrow_model m;
static sparrow_ctx ctx;

sparrow_load(&m, blob, blob_len);
float p_true = sparrow_noul(&m, &ctx, "motor_temp_c: 96\nmax_temp_c: 80", "Is the motor overheating?");
```

The default `SPARROW_MAX_DIM` (256) fits micro.

## Measured results

All numbers are from the project's
[bench/RESULTS.md](https://github.com/sparrow-decider/sparrow-decider/blob/main/bench/RESULTS.md) and
`site/facts.json`. Local runs on one Apple M4 Pro core, not leaderboard scores. micro has not been
benchmarked on a microcontroller.

**Speed**

| Where | Time per decision (p50) |
|---|--:|
| Laptop, 1 core, C runtime | **0.22 ms** (217 µs) |
| Laptop, 1 core, numpy | 0.38 ms (RobotBench) · 0.6 ms p50 / 4.93 ms p95 (JevBench) |
| Peak RSS, numpy, JevBench run | 99.4 MB |

**Quality**

| Benchmark | sparrow-micro-general-v1.1 | Strands Decider 2B (public) |
|---|--:|--:|
| MASSIVE 1.1 en-US, 600 held-out utterances: domain / intent | 0.635 / 0.542 | 0.86 / 0.871 |
| JevBench public, 231 tasks (local v1.5 proxy) | 117/231 | |
| RobotBench v0, 55 hand-written robot decisions | 30/55 | 40/55 |

**C parity:** on the host, the C runtime agrees with numpy on 586/586 argmaxes, max probability
difference 3e-6.

## Limitations

- Static embeddings pool words without order: negation and multi-step reasoning are weak.
- Open-ended language it never trained on is well behind the 2B (MASSIVE routing above).
- Yes/no judgement on JevBench is near chance at every Sparrow tier. A `noul` near 0.5 means
  "don't know".
- No key-value number pooling: for decisions that hinge on sensor numbers, use
  [sparrow-nano-robot](https://huggingface.co/sparrow-decider/sparrow-nano-robot).
- English only. Text normalisation is exact for Latin scripts.
- It suggests decisions. Never use it as the only safety stop on a physical system.

## Training

- **Init:** potion-base-8M static embeddings, full vocabulary, 256-d.
- **Architecture:** mean-pooled state / question / option vectors and an MLP that scores every
  option against the state and the question.
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
