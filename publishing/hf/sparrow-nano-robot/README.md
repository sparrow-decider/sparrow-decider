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
  - robotics
  - tinyml
  - embedded
  - esp32
  - microcontroller
  - static-embeddings
  - distillation
  - agents
---

# sparrow-nano-robot (v1.2)

A 1.11 MB decision model for robots. It answers yes/no (`noul`), pick-one (`choice`) and
rate-on-a-scale (`score`) questions about a text state, and it reads `key: number` pairs such as
`battery: 6%` as values, not just as words. It runs in **3.5 ms per decision on a $10 ESP32-S3**
and in about 0.08 ms on a laptop core with the C runtime.

Part of [Sparrow Decider](https://github.com/sparrow-decider/sparrow-decider), a family of decision
models from 47 MB down to a few KB. Same question and answer shapes as
[Strands Decider](https://github.com/strands-labs/strands-decider).

> Unofficial community project. Not an AWS or Strands product.

| | |
|---|---|
| Model ID | `sparrow-nano-robot-v1.2` |
| Tier | nano (static embeddings + key-value number pooling + MLP) |
| File | `sparrow-nano-robot-v1.2.sparrow` (1.11 MB, Python) · `sparrow-nano-robot-v1.2.spb` (1.29 MB packed SPB1 blob, C) |
| Input | text, typically with sensor readings |
| Runs on | ESP32-S3, Raspberry Pi, laptop |
| Dependencies | numpy (Python) · C99 + libm, no malloc (C) |
| Also bundled in | `pip install sparrow-decider` |

## Intended use

- Routing an operator's command to a robot skill, choosing the next action from sensor readings,
  yes/no checks, recovery choices and urgency scores, on the device itself.
- Fast, local decisions in a known domain where a 2B+ model is too slow or too big.

**Out of scope:** open-ended language it never trained on, yes/no judgement tasks that need
reasoning (see Limitations), and being the only safety mechanism on a physical system.

## How to use

### Python

This model ships inside the pip package, so the quickest path is:

```bash
pip install sparrow-decider
```

```python
from sparrow_decider import Decider

d = Decider.load("sparrow-nano-robot")      # bundled copy
d.ask("operator: grab that blue bottle", {
    "skill": {"type": "choice", "instructions": "Which skill should the robot run?",
              "criteria": {"pick": "pick up an object", "place": "put an object down",
                           "navigate": "move somewhere", "speak": "answer the person",
                           "stop": "halt"}},
})
```

The answer is `pick`, with its probability and a confidence, in the Strands Decider shape:
`{"skill": {"type": "choice", "choice": "pick", "probabilities": {...}, "confidence": ...}}`.

To use the exact file from this repo (pinned to a version):

```python
from huggingface_hub import hf_hub_download
from sparrow_decider import Decider

path = hf_hub_download("sparrow-decider/sparrow-nano-robot", "sparrow-nano-robot-v1.2.sparrow", revision="v1.2")
d = Decider.load(path)
d.ask("battery: 6%\nfront_obstacle_m: 7.0\ngoal_m: 30\npath: clear", {
    "action": {"type": "choice", "instructions": "What should the robot do next?",
               "criteria": {"continue": "keep driving", "slow": "reduce speed", "stop": "halt",
                            "dock": "go back to the charging dock", "replan": "plan a new route"}},
})  # -> dock
```

CLI: `sparrow-decider --model nano-robot ask "operator: grab that blue bottle" --choice "Which skill?" -o "pick=pick up an object" -o "navigate=move somewhere" -o "speak=answer the person"`

### C / ESP32-S3

`sparrow-nano-robot-v1.2.spb` is the packed blob for the C99 runtime in
[`c/sparrow`](https://github.com/sparrow-decider/sparrow-decider/tree/main/c/sparrow) (one `.c`, one
`.h`, an ESP-IDF component). It is read in place from flash; no malloc.

```c
#include "sparrow.h"
static sparrow_model m;
static sparrow_ctx ctx;   /* working memory; keep it static */

sparrow_load(&m, blob, blob_len);            /* blob = contents of the .spb, e.g. in flash */
const char *state = "battery: 6%\nfront_obstacle_m: 7.0\ngoal_m: 30\npath: clear";
sparrow_option opts[] = {{"continue", "keep driving"}, {"slow", "reduce speed"}, {"stop", "halt"},
                         {"dock", "go back to the charging dock"}, {"replan", "plan a new route"}};
float conf;
int k = sparrow_choice(&m, &ctx, state, "What should the robot do next?", opts, 5, &conf);
float p_true = sparrow_noul(&m, &ctx, state, "Is the path clear?");
```

Build with `-DSPARROW_MAX_DIM=128` to halve RAM for nano. On an ESP32-S3, follow the
[ESP32-S3 guide](https://github.com/sparrow-decider/sparrow-decider/blob/main/docs/quickstart/esp32.md):
flash the blob with the `c/examples/esp32s3_robot` example (`model.spb`), or generate a C array with
`python c/tools/pack.py sparrow-nano-robot-v1.2.sparrow -o model.spb --header nano_model.h --symbol nano_model`.

## Measured results

All numbers are from the project's
[bench/RESULTS.md](https://github.com/sparrow-decider/sparrow-decider/blob/main/bench/RESULTS.md) and
`site/facts.json`. Local runs, not leaderboard scores.

**Speed**

| Where | Time per decision (p50) |
|---|--:|
| ESP32-S3, 240 MHz (int8 SIMD) | **3.5 ms** (first on-chip build: 73.5 ms) |
| Laptop, 1 Apple M4 Pro core, C runtime | 0.08 ms (84.5 µs) |
| Laptop, 1 core, numpy | 0.22 ms (RobotBench) |

**Quality**

| Benchmark | sparrow-nano-robot-v1.2 | Strands Decider 2B (public) |
|---|--:|--:|
| RobotBench v0, 55 hand-written robot decisions | 36/55 | 40/55 |
| RobotBench navigation from sensor numbers | **8/10** | 3/10 |
| RobotBench by family: skill / check / recover / urgency | 10/15 · 10/12 · 6/10 · 2/8 | 15/15 · 10/12 · 10/10 · 2/8 |
| MASSIVE 1.1 en-US, 600 utterances: domain / intent | 0.518 / 0.522 | 0.86 / 0.871 |
| JevBench public, 231 tasks (local v1.5 proxy) | 115/231 | |

**C parity:** on the host, the C runtime agrees with numpy on 286/286 argmaxes, max probability
difference 2e-6. On the ESP32-S3, int8 builds agree with the host on 150-155 of 155 decisions; the
few mismatches are rounding near ties.

## Limitations

- Static embeddings pool words without order: negation and multi-step reasoning are weak.
- Open-ended language it never trained on is well behind the 2B (MASSIVE domain routing above).
- Yes/no judgement on JevBench is near chance. A `noul` near 0.5 means "don't know".
- English only. Text normalisation is exact for Latin scripts.
- It suggests decisions. Never use it as the only safety stop on a physical system.

## Training

- **Init:** potion-base-8M static embeddings, PCA-reduced to 128-d, vocabulary pruned to 8k
  pieces (every single character kept, so any word still tokenizes).
- **Architecture:** mean-pooled state / question / option vectors, an MLP (64 hidden) that scores
  every option, plus key-value number pooling: each `key: number` pair becomes the key's vector
  times a learned function of the number.
- **Data:** a general decision mix plus generated robot decisions (skill routing, sensor-driven
  action, yes/no checks, recovery, urgency, compare), with gold labels from rules.
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
