# Model card

## Released models

| ID | Tier | Size | Base weights | Training data | Intended use |
|---|---|---|---|---|---|
| `sparrow-nano-general-v1.1` | nano | 2.2 MB | potion-base-8M (PCA to 128-d, 16k vocab) | general decision mix + robot | short text decisions on any device (3.8 ms on ESP32-S3) |
| `sparrow-nano-robot-v1.2` | nano | 1.11 MB | potion-base-8M (PCA to 128-d, 8k vocab) | general decision mix + robot, key-value number pooling | decisions over sensor readings and operator commands (3.5 ms on ESP32-S3) |
| `sparrow-micro-general-v1.1` | micro | 7.6 MB | potion-base-8M (full vocab, 256-d) | general decision mix + robot | broader text decisions, sub-millisecond |
| `sparrow-tiny-general-v1.0` | tiny | 17.9 MB | Ettin encoder 32M | general decision mix | text decisions when 20-50 ms is fine |
| `sparrow-small-general-v1.0` | small | 47 MB | Ettin encoder 68M | general decision mix | the most general tier |
| `sparrow-pico-rover-v1.1` | pico | ~2 KB per question (501 parameters) | none | 3,000 states labelled by the public Strands Decider 2B | example compiled model for `c/examples/specs/rover.json` (9.3 µs on ESP32-S3) |

- **Teacher:** all text models are distilled from a Strands Decider 4B checkpoint.
- **Answers:** all text models answer `noul`, `choice` and `score` questions with calibrated
  per-kind temperatures.

Superseded versions (nano-robot v1.0 and v1.1, nano-general v1.0, pico-rover v1.0) are listed in
[CHANGELOG.md](../CHANGELOG.md) and the research report.

## Measured quality

See [bench/RESULTS.md](../bench/RESULTS.md) and [research/REPORT.md](../research/REPORT.md).

**Headline numbers:**
- **RobotBench:** `sparrow-nano-robot-v1.2` scores 36/55 and gets 8/10 navigation calls from sensor numbers right. The public Strands Decider 2B scores 40/55 overall, but gets 3/10 on navigation.
- **MASSIVE routing:** the Sparrow models score 0.35-0.67 on domain routing, against 0.86 for the 2B.
- **JevBench:** every tier is near chance on yes/no judgement tasks.

## Limitations

- **Static tiers (pico aside):** micro and nano pool words without order, so negation and long
  multi-step reasoning are weak.
- **Language:** English only. Normalisation is exact for Latin scripts.
- **Yes/no answers:** near 0.5 means "don't know". Treat them that way.
- **Safety:** these models suggest decisions. Don't use them as the only safety mechanism on a
  physical system.

## Licences

| Part | Licence |
|---|---|
| Code | Apache-2.0 |
| micro and nano weights | derived from potion-base-8M (MIT, MinishLab) |
| tiny and small weights | derived from the Ettin encoders (MIT, Johns Hopkins CLSP) |
| Training data | sources keep their own licences; only tasksource rows marked for commercial use were used |
