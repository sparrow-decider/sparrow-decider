# Naming standard

Every Sparrow Decider model has one ID:

    sparrow-<tier>-<domain>-v<major>.<minor>

| Part | Values | Meaning |
|---|---|---|
| `tier` | `pico`, `nano`, `micro`, `tiny`, `small` | Size class, smallest first (SI order). Fixed meaning below. |
| `domain` | `general`, `robot`, or a spec name such as `rover` | What it was trained or compiled for: `general` = any text decision, `robot` = also trained on robot/sensor decisions, a spec name = a pico model compiled for that one device. |
| `v<major>.<minor>` | `v1.0`, `v1.1`, ... | Major = new architecture or data recipe; minor = retrain or recalibration. |

## Tiers

| Tier | What it is | Typical size | Runs on | Input |
|---|---|---|---|---|
| `pico` | One small MLP per question, compiled from a spec (`training/pico_compile.py`) | 1-10 KB | any MCU | numbers, flags, enums |
| `nano` | Static embeddings (pruned vocabulary, 128-d) + MLP; `robot` adds key-value number pooling | ~1-2.5 MB | ESP32-S3, STM32H7, RP2350 | text |
| `micro` | Static embeddings (full 29.5k vocabulary, 256-d) + MLP | ~8 MB | Linux SBCs, ESP32-S3 with 16 MB flash | text |
| `tiny` | Ettin 32M encoder + pointer head | ~18 MB | laptops, Raspberry Pi | text |
| `small` | Ettin 68M encoder + pointer head | ~47 MB | laptops, Raspberry Pi, Jetson | text |

All tiers answer the same three question kinds (`noul`, `choice`, `score`) with the Strands Decider
answer shapes.

## Files and packages

| Thing | Name |
|---|---|
| Python package | `sparrow-decider` on PyPI, `import sparrow_decider` |
| CLI | `sparrow-decider ask ...`, `sparrow-decider serve` |
| Model file (Python runtime) | `<id>.sparrow` (zip: `config.json`, `tokenizer.json`, `model.npz`) |
| Model blob (C runtime) | `<id>.spb` (SPB1 flat binary, `c/tools/pack.py`) |
| C library / ESP-IDF component | `sparrow` (`c/sparrow`), API prefix `sparrow_` |
| Compiled pico header | `sparrow_pico_<spec>.h`, API prefix `<spec>_` |
| Benchmarks | `bench/results/<bench>-<id>.json` |

Unofficial community project. Not an AWS or Strands product.
