# Quickstart: the C library anywhere

`c/sparrow` is one C99 source file and one header. It needs only libm, and it works on desktops,
Linux boards and microcontrollers.

```bash
python c/tools/pack.py python/sparrow_decider/models/sparrow-nano-general-v1.1.sparrow -o nano.spb
# or as a C array to compile in:
python c/tools/pack.py ... -o nano.spb --header nano_model.h --symbol nano_model
```

```c
#include "sparrow.h"
static sparrow_model m;
static sparrow_ctx ctx;   /* working memory; keep it static */

sparrow_load(&m, blob, blob_len);
float p_true = sparrow_noul(&m, &ctx, "motor_temp_c: 96\nmax_temp_c: 80", "Is the motor overheating?");
float conf;
int k = sparrow_choice(&m, &ctx, state, "Which skill?", opts, n_opts, &conf);
float level = sparrow_score(&m, &ctx, state, "How urgent?", levels, n_levels, &conf);
```

## Build options

| Macro | Default | Effect |
|---|---|---|
| `SPARROW_MAX_DIM` | 256 | embedding width the context is sized for. Use 128 for nano to halve RAM |
| `SPARROW_MAX_HIDDEN` | 384 | MLP width the context is sized for |
| `SPARROW_MAX_OPTIONS` | 16 | most options per question |
| `SPARROW_INT8_ACT` | 0 | int8 activations: faster on integer SIMD, 99.3% the same argmax in our tests. On the ESP32-S3 the component uses the PIE vector unit (ESP-NN kernel) |
| `SPARROW_BATCH` | 8 | options scored per pass over the MLP weights |

## Speed on a microcontroller

- `sparrow_move_mlp(&m, buf, sparrow_mlp_bytes(&m))` copies the MLP weights (the part read on every
  question) into fast RAM, such as internal SRAM on an ESP32-S3.
- `python c/tools/pack.py MODEL --balance` folds per-block gains into the weights, so the int8 path
  needs one dot product per row.
- The settings behind the ESP32-S3 numbers in the README are in `c/examples/esp32s3_bench`:
  int8 + SIMD, a 64 KB data cache, the blob copied to PSRAM, and the MLP in internal RAM.

- **Compiler flags:** build with `-O3 -ffast-math` (the CMake file does).
- **Parity:** answers match the Python runtime to within 1e-5. `python c/tests/parity.py MODEL`
  checks this on your machine.

## Text handling

- The tokenizer is BERT-uncased WordPiece.
- Normalisation is exact for ASCII and Latin-1/Latin Extended-A.
- Other scripts pass through without case folding.
