---
title: "Sparrow Decider: decisions that fit on a chip"
description: "A family of tiny decision models, from 47 MB on a laptop to ~2 KB on a microcontroller. 9.3 µs per decision on a $10 ESP32-S3."
author: "The Sparrow Decider contributors"
version: "0.2.0"
image: "../brand/previews/og-image.png"
---

# Sparrow Decider: decisions that fit on a chip

*By the Sparrow Decider contributors. Unofficial community project. Not an AWS or Strands product.*

Most of the decisions an agent or a robot makes are small. Is the user upset? Which skill should run?
Battery at 6% and the path is clear: continue, slow, stop, dock or replan? These questions have a short
list of answers, and they need an answer now, often on hardware with no GPU and no network.

Today we are releasing **Sparrow Decider 0.2.0**, a family of decision models built for exactly that.
They answer yes/no, pick-one and score questions about a state, with calibrated probabilities, in the
same shapes as Strands Decider. The family runs from a 47 MB model on a laptop down to a ~2 KB compiled
model on a microcontroller.

```bash
pip install sparrow-decider
```

## The numbers

All measured on an ESP32-S3 (QFN56 rev0.2, 240 MHz, 16 MB flash, 8 MB PSRAM), the kind of $10 board
you can buy for a weekend project.

- **9.3 µs per decision** with `sparrow-pico-rover-v1.1`. That is ~2 KB per question, 501 parameters.
  On a laptop it takes 0.18 µs. It agrees with its spec's rules 94.0% of the time; its 2B teacher scores 94.2%.
- **3.8 ms per text decision** with `sparrow-nano-general-v1.1` (2.2 MB), on the same chip.
- **7.6 ms per decision** with `sparrow-nano-robot-v1.1` (1.19 MB), which reads text with sensor readings.
  It gets navigation from sensor numbers right 10/10 times. The public 2B Strands Decider gets 3/10.
- **40 / 55 on RobotBench** for the 1.37 MB `sparrow-nano-robot-v1.0`, the same score as the public
  2-billion-parameter Strands Decider (40/55).
- **~2 KB per compiled question** for sparrow-pico (501 parameters).
- **Parity:** The C runtime matches the Python runtime to within 1e-5 on the host; on the ESP32-S3, int8 builds agree with the host on 150-155 of 155 decisions.

We got there step by step. nano-general went from 9.6 ms to 3.8 ms on the chip. nano-robot went
from 73.5 ms on its first run, to 13.2 ms (v1.0), to 7.6 ms (v1.1). pico went from 42.9 µs to 9.3 µs.

## The family

| Tier | Model | Size | Input | Where | Time |
|---|---|---|---|---|---|
| pico | `sparrow-pico-rover-v1.1` | ~2 KB per question | sensor numbers, flags, enums | any microcontroller | 9.3 µs (ESP32-S3) |
| nano | `sparrow-nano-general-v1.1` | 2.2 MB | text | ESP32-S3, Raspberry Pi, laptop | 3.8 ms (ESP32-S3), 0.06 ms (laptop, C) |
| nano | `sparrow-nano-robot-v1.1` | 1.19 MB | text with sensor readings | ESP32-S3, Pi, laptop | 7.6 ms (ESP32-S3), 0.09 ms (laptop, C) |
| micro | `sparrow-micro-general-v1.1` | 7.6 MB | text | Pi, laptop | 0.22 ms (laptop, C) |
| tiny | `sparrow-tiny-general-v1.0` | 17.9 MB | text | laptop, Pi | 23 ms (laptop, numpy) |
| small | `sparrow-small-general-v1.0` | 47 MB | text | laptop, Pi, Jetson | 64 ms (laptop, numpy) |

## How it works

**Distillation.** A full Strands Decider (4B) teaches the text tiers on ~430k decisions.

**nano** uses static embeddings with a pruned 8-16k vocabulary at 128 dimensions, plus key-value
number pooling. That last part matters for robots: it reads `battery: 6%` as a value, not as two tokens.

**pico** is a compiler, not a fixed model. You write a spec: your sensors, your rules, your questions.
The public Strands Decider 2B labels sampled states, and the compiler writes one tiny MLP per question
as a C header. Your firmware includes it like any other header.

**On the ESP32-S3** the runtime uses int8 SIMD on the vector unit through the ESP-NN kernel, with weights
in PSRAM or internal RAM.

There are three runtimes:

- Python, numpy only.
- C99 with no malloc, model read from flash, packaged as an ESP-IDF component.
- The sparrow-pico compiler: device spec in, C header out.

## Honest limits

Small models make trade-offs. Here are ours, measured the same way as the wins.

- **Open-ended language it never trained on** is well behind the 2B. On MASSIVE domain routing we score
  0.52-0.67; the 2B scores 0.86.
- **Yes/no judgement on JevBench is near chance at every tier.** nano-general scores 122/231. Do not
  use Sparrow for open judgement calls.
- **pico answers only the questions it was compiled for.** Change the question, recompile.
- **nano-robot v1.1 trades RobotBench points for navigation.** It scores 38/55 against v1.0's 40/55,
  in exchange for 10/10 on navigation from sensor numbers and 7.6 ms on the chip. Pick the version that fits your robot.

If your decision is a fixed set of answers about a known kind of state, Sparrow is a good fit. If it
needs world knowledge or open-ended reading, use a bigger model, and maybe let Sparrow decide when to call it.

## Try it

```bash
pip install sparrow-decider
sparrow-decider ask "operator: grab that blue bottle" --choice "Which skill?" \
    -o "pick=pick up an object" -o "navigate=move somewhere" -o "speak=answer the person"
```

The guides cover Python, agents, ESP32-S3 (with QEMU if you have no board), sparrow-pico and the C library.
Models are on the GitHub releases page: https://github.com/sparrow-decider/sparrow-decider

Questions, results on your hardware, and bug reports are welcome in
[Discussions](https://github.com/sparrow-decider/sparrow-decider/discussions) and
[Issues](https://github.com/sparrow-decider/sparrow-decider/issues).

## Credits

Sparrow Decider stands on open work: potion-base-8M (MinishLab, MIT), Ettin encoders (JHU CLSP, MIT),
Strands Decider (Apache-2.0), ESP-NN (Espressif, Apache-2.0), Amazon MASSIVE (CC BY 4.0, evaluation only)
and JevBench (MIT, evaluation only).

Code is Apache-2.0. Model weights are derived from MIT-licensed potion-base-8M and Ettin encoders.

---

*Unofficial community project. Not an AWS or Strands product. Sparrow Decider is built by the Sparrow
Decider contributors and is not affiliated with, sponsored or endorsed by Amazon Web Services or the
Strands Agents project. Strands Decider is referenced for compatibility and comparison only. All figures
are our own measurements on the hardware stated; your results will depend on your hardware and workload.*
