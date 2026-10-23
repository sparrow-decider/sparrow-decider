#!/bin/sh
# v0.2 sweep: smaller-hidden nanos for the ESP32-S3, and the generic device-rule experiment.
D="corpus/teacher_src.jsonl corpus/transfer.jsonl corpus/tasksource.jsonl corpus/robot.jsonl"
T="--teacher corpus/teacher_src.jsonl=corpus/teacher_v22.jsonl corpus/transfer.jsonl=corpus/teacher_transfer.jsonl corpus/tasksource.jsonl=corpus/teacher_tasksource.jsonl"
run() { name=$1; shift; nohup python training/static3.py $T "$@" --out runs/$name --name sparrow-$name > logs/$name.log 2>&1 & }
mkdir -p runs logs
run nano-robot-h128   --data $D --vocab 8192  --dim 128 --hidden 128 --kv --seed 1
run nano-general-h128 --data $D --vocab 16384 --dim 128 --hidden 128 --seed 0
run nano-specs-h128   --data $D corpus/specs.jsonl --vocab 8192 --dim 128 --hidden 128 --kv --seed 1
run nano-specs-h256   --data $D corpus/specs.jsonl --vocab 8192 --dim 128 --hidden 256 --kv --seed 1
wait
