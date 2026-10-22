#!/bin/sh
# Seed repeats for the nano configs that matter. Run from the bundle root.
D="--data corpus/teacher_src.jsonl corpus/transfer.jsonl corpus/tasksource.jsonl corpus/robot.jsonl"
T="--teacher corpus/teacher_src.jsonl=corpus/teacher_v22.jsonl corpus/transfer.jsonl=corpus/teacher_transfer.jsonl corpus/tasksource.jsonl=corpus/teacher_tasksource.jsonl"
run() { name=$1; shift; nohup python training/static3.py $D $T "$@" --out runs/$name --name sparrow-$name > logs/$name.log 2>&1 & }
run nano-v16k-s1 --vocab 16384 --dim 128 --hidden 256 --kv --seed 1
run nano-v16k-s2 --vocab 16384 --dim 128 --hidden 256 --kv --seed 2
run nano-a-s1    --vocab 8192  --dim 128 --hidden 256 --kv --seed 1
run nano-vfull   --dim 128 --hidden 256 --kv
run nano-v16k-nokv --vocab 16384 --dim 128 --hidden 256
wait
