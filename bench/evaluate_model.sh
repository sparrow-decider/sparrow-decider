#!/bin/sh
# Full benchmark of one .sparrow model -> bench/results/{robot,jev,c}-<name>.json
#   bench/evaluate_model.sh path/to/model.sparrow [--no-c]
set -e
M="$1"; N=$(basename "$M" .sparrow); R="$(dirname "$0")/results"; PY="${PY:-.venv/bin/python}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
$PY bench/robot/run_robot.py "$M" --out "$R/robot-$N.json"
$PY bench/bench_jev.py "$M" --out "$R/jev-$N.json" > /dev/null
[ "$2" = "--no-c" ] || $PY c/tests/parity.py "$M" --n 600 --out "$R/c-$N.json"
