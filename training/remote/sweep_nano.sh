#!/bin/sh
# nano ablations on one GPU box, all in parallel. Run from the bundle root.
D="--data corpus/teacher_src.jsonl corpus/transfer.jsonl corpus/tasksource.jsonl corpus/robot.jsonl"
T="--teacher corpus/teacher_src.jsonl=corpus/teacher_v22.jsonl corpus/transfer.jsonl=corpus/teacher_transfer.jsonl corpus/tasksource.jsonl=corpus/teacher_tasksource.jsonl"
mkdir -p runs logs
run() { name=$1; shift; nohup python training/static3.py $D $T "$@" --out runs/$name --name sparrow-$name > logs/$name.log 2>&1 & }
run nano-nokv   --vocab 8192  --dim 128 --hidden 256
run nano-s      --vocab 4096  --dim 64  --hidden 128 --kv
run nano-v16k   --vocab 16384 --dim 128 --hidden 256 --kv
run nano-h384   --vocab 8192  --dim 128 --hidden 384 --kv
run micro-kv    --dim 256 --hidden 384 --kv
run micro-nokv  --dim 256 --hidden 384
wait
