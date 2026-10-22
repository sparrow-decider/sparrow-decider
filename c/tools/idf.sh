#!/bin/sh
# Run idf.py with ESP-IDF sourced:  c/tools/idf.sh -C c/examples/esp32s3_robot build
# Uses $IDF_PATH (default ~/esp/esp-idf). If export.sh fails on an old system Python, put a newer
# python3 first in PATH.
. "${IDF_PATH:-$HOME/esp/esp-idf}/export.sh" >/dev/null 2>&1 || { echo "ESP-IDF export failed (is IDF_PATH set?)" >&2; exit 1; }
exec idf.py "$@"
