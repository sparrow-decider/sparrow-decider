# ESP32-S3 example

This example runs `sparrow-nano` text decisions and a compiled `sparrow-pico` model on an ESP32-S3,
and prints each answer with its time. Build steps, expected output and QEMU instructions are in
[docs/quickstart/esp32.md](../../../docs/quickstart/esp32.md).

```bash
python ../../tools/pack.py ../../../python/sparrow_decider/models/sparrow-nano-robot-v1.0.sparrow -o main/model.spb
idf.py set-target esp32s3 && idf.py build flash monitor
```
