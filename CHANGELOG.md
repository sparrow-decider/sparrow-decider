# Changelog

## 0.1.0

First public release.

- **Models:** `sparrow-nano-general-v1.0`, `sparrow-nano-robot-v1.0`, `sparrow-micro-general-v1.1`,
  `sparrow-tiny-general-v1.0`, `sparrow-small-general-v1.0` and the example `sparrow-pico-rover-v1.0`.
- **Python runtime:** numpy only, with load by name, a CLI and a `/v1/systemone` HTTP server.
- **C99 runtime:** an ESP-IDF component, with an ESP32-S3 example that also runs in QEMU.
- **sparrow-pico compiler:** turns a device spec plus a Strands Decider teacher into a C header.
- **Benchmarks:** RobotBench v0, MASSIVE routing, JevBench public, C parity.
