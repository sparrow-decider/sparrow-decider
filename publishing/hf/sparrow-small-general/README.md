---
license: apache-2.0
library_name: sparrow-decider
pipeline_tag: text-classification
language:
  - en
base_model: jhu-clsp/ettin-encoder-68m
base_model_relation: finetune
tags:
  - sparrow-decider
  - decision-making
  - text-classification
  - encoder
  - edge
  - distillation
  - agents
  - robotics
---

# sparrow-small-general (v1.0)

The largest Sparrow Decider model: 47 MB, built on the Ettin 68M bidirectional encoder. It answers
yes/no (`noul`), pick-one (`choice`) and rate-on-a-scale (`score`) questions about a text state,
with calibrated probabilities, in **64 ms per decision on one laptop core** with numpy only.

Part of [Sparrow Decider](https://github.com/sparrow-decider/sparrow-decider), a family of decision
models from 47 MB down to a few KB. Same question and answer shapes as
[Strands Decider](https://github.com/strands-labs/strands-decider).

> Unofficial community project. Not an AWS or Strands product.

| | |
|---|---|
| Model ID | `sparrow-small-general-v1.0` |
| Tier | small (Ettin 68M encoder + pointer head) |
| File | `sparrow-small-general-v1.0.sparrow` (47 MB) |
| Input | text |
| Runs on | laptop, Raspberry Pi, Jetson |
| Runtime | Python, numpy only (no C runtime for encoder tiers) |

## Intended use

- The most general Sparrow tier: text decisions (routing, gating, urgency) where tens of
  milliseconds on a CPU are fine and no GPU or model server is available.
- Best MASSIVE domain routing of the released Sparrow models (0.673).

**Out of scope:** microcontrollers (use a nano), open-ended language far from its training data,
yes/no judgement that needs reasoning, and being the only safety mechanism on a physical system.

## How to use

```bash
pip install sparrow-decider huggingface_hub
```

```python
from huggingface_hub import hf_hub_download
from sparrow_decider import Decider

path = hf_hub_download("sparrow-decider/sparrow-small-general", "sparrow-small-general-v1.0.sparrow", revision="v1.0")
d = Decider.load(path)
d.ask("User: please move my 3pm meeting with Sam to Friday", {
    "tool": {"type": "choice", "instructions": "Which tool should the agent call?",
             "criteria": {"weather": "get a weather forecast", "calendar": "read or change calendar events",
                          "email": "send or read email", "search": "search the web"}},
})  # -> calendar
```

To load it by name (`Decider.load("small-general")`, `sparrow-decider --model small-general ...`),
put the file in `~/.cache/sparrow-decider/` or any folder listed in `$SPARROW_MODELS`:

```bash
hf download sparrow-decider/sparrow-small-general sparrow-small-general-v1.0.sparrow --local-dir ~/.cache/sparrow-decider
```

## Measured results

All numbers are from the project's
[bench/RESULTS.md](https://github.com/sparrow-decider/sparrow-decider/blob/main/bench/RESULTS.md) and
`site/facts.json`. Local runs on one Apple M4 Pro core, not leaderboard scores.

**Speed (numpy, 1 core)**

| Measure | Value |
|---|--:|
| Time per decision (p50) | **64 ms** |
| JevBench p50 / p95 | 64.17 ms / 328.14 ms |
| RobotBench time per question | 54.78 ms |
| Peak RSS, JevBench run | 948.6 MB |

**Quality**

| Benchmark | sparrow-small-general-v1.0 | Strands Decider 2B (public) |
|---|--:|--:|
| MASSIVE 1.1 en-US, 600 held-out utterances: domain / intent | 0.673 / 0.599 | 0.86 / 0.871 |
| JevBench public, 231 tasks (local v1.5 proxy) | 122/231 | |
| RobotBench v0, 55 hand-written robot decisions | 24/55 | 40/55 |

## Limitations

- Weak on robot decisions (RobotBench 24/55); for robots use
  [sparrow-nano-robot](https://huggingface.co/sparrow-decider/sparrow-nano-robot), which is 1.11 MB and
  scores 36/55.
- Open-ended language it never trained on is still well behind the 2B (MASSIVE above).
- Yes/no judgement on JevBench is near chance at every Sparrow tier. A `noul` near 0.5 means
  "don't know".
- Peak memory is about 0.95 GB with the numpy runtime.
- English only.
- It suggests decisions. Never use it as the only safety stop on a physical system.

## Training

- **Init:** [Ettin encoder 68M](https://huggingface.co/jhu-clsp/ettin-encoder-68m).
- **Architecture:** the encoder plus a pointer head: each option's logit is a scaled dot product
  between the mean encoder state over the `<answer>` tokens and the mean over that option's span.
  One forward pass answers the question.
- **Prompt:** states, questions and numbered options rendered exactly as Strands Decider renders
  them.
- **Data:** a general decision mix. Only tasksource rows marked for commercial use were used;
  sources keep their own licences.
- **Teacher:** distilled from a Strands Decider 4B checkpoint (targets 50% teacher, 50% gold);
  per-kind temperature calibration.

Details: [research report](https://github.com/sparrow-decider/sparrow-decider/blob/main/research/REPORT.md).

## Licence and credits

- **Licence:** Apache-2.0 (see `LICENSE` and `NOTICE` in this repo).
- **Base weights:** derived from the [Ettin encoders](https://huggingface.co/jhu-clsp) (Johns
  Hopkins University CLSP), released under the MIT licence. Their copyright notice and full MIT
  text are in `LICENSE-ettin.txt` in this repo and apply to the corresponding weights.
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
