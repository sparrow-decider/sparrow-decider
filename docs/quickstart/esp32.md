# Quickstart: ESP32-S3 (sparrow-nano on a microcontroller)

The C runtime reads a packed model straight from flash. It needs no malloc and about 68 KB of static
working memory. With `sparrow-nano-robot-v1.1` the whole example firmware is 1.84 MB of flash.

## Hardware

- **Recommended board:** ESP32-S3-DevKitC-1-N16R8 (16 MB flash, 8 MB PSRAM).
- **Other ESP32-S3 boards:** any board with 4 MB or more of flash works for nano. PSRAM is optional.
- **4 MB boards:** set the `factory` partition in `partitions.csv` to `3M`. The example ships with
  `12M`, so micro (8.9 MB) also fits on 16 MB boards.

## Build and flash

```bash
# 1. ESP-IDF v5.4 (https://docs.espressif.com/projects/esp-idf/en/v5.4/esp32s3/get-started/)
. $IDF_PATH/export.sh

# 2. pack a model into the example
pip install -e .                      # for the packer
python c/tools/pack.py python/sparrow_decider/models/sparrow-nano-robot-v1.1.sparrow \
    -o c/examples/esp32s3_robot/main/model.spb

# 3. build, flash, watch
cd c/examples/esp32s3_robot
idf.py set-target esp32s3
idf.py build flash monitor
```

You should see each decision with its time:

```
sparrow_load rc=0  blob 1600988 bytes  V=8192 D=128 hidden=256 kv=1  ctx 68096 bytes
[ ... ms] battery: 6%|front_obstacle_m: 7.0|goal_m: 30|path: clear     -> dock (confidence 0.93)
[ ... ms] battery: 73%|front_obstacle_m: 0.2|goal_m: 15|path: blocked  -> stop (confidence 1.00)
[ ... ms] operator: grab that blue bottle                              -> pick (confidence 0.93)
[pico ... us] battery 6%, clear path -> dock (p=0.81), need_charge P(true)=0.66
```

The example also runs a compiled sparrow-pico model (`main/sparrow_pico_rover.h`) for comparison.

## No board yet? Use QEMU

Espressif's QEMU runs the same firmware. Timings there are not real-board timings.

```bash
python $IDF_PATH/tools/idf_tools.py install qemu-xtensa
cd c/examples/esp32s3_robot/build
esptool.py --chip esp32s3 merge_bin --fill-flash-size 16MB -o qemu_flash.bin @flash_args
qemu-system-xtensa -nographic -machine esp32s3 -drive file=qemu_flash.bin,if=mtd,format=raw
```

- **PSRAM:** QEMU has no octal PSRAM. The example sets `CONFIG_SPIRAM_IGNORE_NOTFOUND=y`, so it
  boots without it. The model does not need PSRAM.

## Use it in your own project

Add `c/sparrow` as a component, then:

```c
#include "sparrow.h"

extern const uint8_t model_start[] asm("_binary_model_spb_start");
extern const uint8_t model_end[]   asm("_binary_model_spb_end");
static sparrow_model model;
static sparrow_ctx ctx;

void app_main(void) {
    sparrow_load(&model, model_start, model_end - model_start);
    sparrow_option opts[] = {{"pick", "pick up an object"}, {"navigate", "move somewhere"},
                             {"speak", "answer the person"}};
    float conf;
    int k = sparrow_choice(&model, &ctx, "operator: bring me the red mug", "Which skill?", opts, 3, &conf);
}
```

- **Component:** in `CMakeLists.txt`, set
  `EXTRA_COMPONENT_DIRS` to `path/to/sparrow-decider/c/sparrow`.
- **Embedding the model:** in `main/CMakeLists.txt`, add `EMBED_FILES "model.spb"` and
  `REQUIRES sparrow`.
