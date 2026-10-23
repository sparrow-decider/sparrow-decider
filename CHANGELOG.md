# Changelog

## 0.2.0 (2026-10-23)

- **New models:**
  - `sparrow-nano-general-v1.1` (128 hidden): 3.8 ms per decision on an ESP32-S3.
  - `sparrow-nano-robot-v1.1` (7.6 ms) and `sparrow-nano-robot-v1.2` (64 hidden, 3.5 ms).
  - `sparrow-pico-rover-v1.1` (16 hidden): 9.3 µs on an ESP32-S3.
- **The pip package** bundles `sparrow-nano-general-v1.1` and `sparrow-nano-robot-v1.2`.
- **C runtime:**
  - options are scored in batches
  - ESP32-S3 int8 SIMD port (ESP-NN dot kernel)
  - `sparrow_mlp_bytes` / `sparrow_move_mlp`
  - block-balanced packing (`pack.py --balance`)
  - optional per-stage profiling (`SPARROW_PROFILE`)
- **pico headers** add `<q>_logits` and `<q>_argmax`, and a faster dense kernel.
- **On-device benchmarks:** `bench/esp32/run.py`, `bench/esp32/pico_run.py` and results from a real
  ESP32-S3.

## 0.1.0

First public release.

- **Models:** `sparrow-nano-general-v1.0`, `sparrow-nano-robot-v1.0`, `sparrow-micro-general-v1.1`,
  `sparrow-tiny-general-v1.0`, `sparrow-small-general-v1.0` and the example `sparrow-pico-rover-v1.0`.
- **Python runtime:** numpy only, with load by name, a CLI and a `/v1/systemone` HTTP server.
- **C99 runtime:** an ESP-IDF component, with an ESP32-S3 example that also runs in QEMU.
- **sparrow-pico compiler:** turns a device spec plus a Strands Decider teacher into a C header.
- **Benchmarks:** RobotBench v0, MASSIVE routing, JevBench public, C parity.
