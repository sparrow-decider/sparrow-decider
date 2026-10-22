# usage: bash remote/sweep_kd.sh NAME ENCODER LR EPOCHS [extra args]
cd /work
export SPARROW_JEVBENCH=/work/jev/all.jsonl SPARROW_JEV_PROXY=/work/jev HF_HUB_DISABLE_PROGRESS_BARS=1
name=$1; enc=$2; lr=$3; ep=$4; shift 4
EV="data/train_v5.holdout.jsonl corpus/families_eval.jsonl corpus/tasksource_eval.jsonl corpus/synth_pairs_eval.jsonl"
python training/train.py --out runs/$name --encoder $enc --lr $lr --epochs $ep --keep corpus/keep16k.json \
  --data corpus/teacher_src.jsonl corpus/transfer.jsonl corpus/tasksource.jsonl \
  --teacher corpus/teacher_src.jsonl=corpus/teacher_v22.jsonl corpus/transfer.jsonl=corpus/teacher_transfer.jsonl corpus/tasksource.jsonl=corpus/teacher_tasksource.jsonl \
  --tok-budget 10000 "$@" > logs/$name.train.log 2>&1
python training/evaluate.py runs/$name --holdout $EV --n 6000 > logs/$name.eval.json 2>logs/$name.eval.err
