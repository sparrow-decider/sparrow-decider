---
license: apache-2.0
library_name: sparrow-decider
pipeline_tag: tabular-classification
tags:
  - sparrow-decider
  - sparrow-pico
  - decision-making
  - tinyml
  - embedded
  - esp32
  - microcontroller
  - robotics
  - distillation
  - c
---

# sparrow-pico-rover (v1.1): example compiled decision model

An **example** of what the sparrow-pico compiler produces: a single dependency-free C header that
answers three fixed questions for a small rover from its sensor readings. About **2 KB per question
(501 parameters)**, **9.3 µs per decision on a $10 ESP32-S3**, 0.18 µs on a laptop.

pico models are not general: each one is compiled for one device spec and answers only the
questions it was compiled for. This repo is here so you can see, compile and time a real one before
compiling your own. To make one for your device, follow the
[sparrow-pico guide](https://github.com/sparrow-decider/sparrow-decider/blob/main/docs/quickstart/pico.md).

Part of [Sparrow Decider](https://github.com/sparrow-decider/sparrow-decider). Same question shapes
as [Strands Decider](https://github.com/strands-labs/strands-decider).

> Unofficial community project. Not an AWS or Strands product.

| | |
|---|---|
| Model ID | `sparrow-pico-rover-v1.1` |
| Tier | pico (one small MLP per question, compiled to C) |
| Files | `sparrow_pico_rover.h` (the model, 24 KB of C source) · `rover.json` (the spec it was compiled from) |
| Input | sensor numbers, flags, enums (no text) |
| Runs on | any microcontroller with a C compiler and `<math.h>` |
| Dependencies | none |

## The spec

`rover.json` describes the rover:

- **Features:** `battery` (0-100 %), `front_obstacle_m` (0-8), `goal_m` (0-60), `path`
  (clear / blocked / crowded / wet floor), `carrying_load` (bool).
- **Rules given to the teacher:** stop if anything is closer than 0.4 m; go back to the dock when
  battery is below 15%; slow down in crowded areas or on a wet floor; re-plan when the path is
  blocked; otherwise keep going.
- **Questions:**
  - `action` (choice): continue, slow, stop, dock, replan
  - `need_charge` (yes/no): does the robot need to recharge now?
  - `risk` (score): safe, minor risk, high risk, danger

## How to use

```c
#include <stdio.h>
#include "sparrow_pico_rover.h"

int main(void) {
    rover_state s = {.battery = 6.0f, .front_obstacle_m = 7.0f, .goal_m = 30.0f,
                     .path = ROVER_PATH_CLEAR, .carrying_load = 0};
    float p[ROVER_ACTION_N];
    rover_action(&s, p);                      /* probabilities over the options */
    int k = rover_action_argmax(&s);          /* or just the answer */
    printf("%s (p=%.2f)\n", rover_action_options[k], p[k]);   /* dock (p=0.81) */
    return 0;
}
```

```bash
hf download sparrow-decider/sparrow-pico-rover --local-dir rover --revision v1.1
cc -std=c99 -O2 -o rover_demo main.c -Irover -lm && ./rover_demo
```

Each question `q` has `rover_<q>(&s, probs)`, `rover_<q>_argmax(&s)`, `rover_<q>_logits(&s, out)`,
`ROVER_<Q>_N` and `rover_<q>_options[]`. `SPARROW_PICO_KERNEL` (0, 1 or 2) picks the dense kernel.

For the state above, the released header gives `continue 0.06, slow 0.07, stop 0.04, dock 0.81,
replan 0.03`: battery at 6% means dock. On ESP32-S3, the
[`esp32s3_robot` example](https://github.com/sparrow-decider/sparrow-decider/tree/main/c/examples/esp32s3_robot)
runs this header next to a nano text model.

## Measured results

From the project's `site/facts.json`.

| Measure | Value |
|---|--:|
| Size | ~2 KB per question (501 parameters) |
| ESP32-S3, 240 MHz, per decision | **9.3 µs** (first on-chip build: 42.9 µs) |
| Laptop, per decision | 0.18 µs |
| Agreement with the spec's rules (held-out states) | 94.0% (its 2B teacher: 94.2%) |

A pico model is as good as its teacher on your spec, and no better.

## Limitations

- Answers only `action`, `need_charge` and `risk` for this exact feature set. A different robot
  needs its own spec and its own compile.
- Inherits the teacher's mistakes. Check the teacher's answers on the cases that matter before
  shipping.
- Never use a learned model as the only safety stop. Keep hard limits (for example the 0.4 m stop)
  in plain code.

## Training

- **Teacher:** the public Strands Decider 2B
  ([StrandsAgents/strands-decider-2B-qwen3.5-v1-2610](https://huggingface.co/StrandsAgents/strands-decider-2B-qwen3.5-v1-2610),
  Apache-2.0) labelled 3,000 sampled rover states, rendered as text, with the rules above.
- **Student:** one small ReLU MLP per question (16 hidden) on the raw feature vector, distilled from
  the teacher's answers, then written out as C by `training/pico_compile.py`.
- **No base weights:** the student starts from scratch, so no third-party weights are included.

## Licence and credits

- **Licence:** Apache-2.0 (see `LICENSE` and `NOTICE` in this repo).
- **Teacher and prompt format:** [Strands Decider](https://github.com/strands-labs/strands-decider)
  (Apache-2.0).

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
