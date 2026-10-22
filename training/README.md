# Training

This folder holds the code that produced every released model. The training corpora are not in the
repo, because of their size and because their sources carry their own licences. This page lists
what each one is and how it was made.

## Corpora

| File | Rows | What |
|---|---|---|
| `corpus/teacher_src.jsonl` | 196k | The Strands Decider public training mix plus generated policy, guardrail, rubric and state-tracking families. |
| `corpus/transfer.jsonl` | 150k | New state and question pairings for distillation (`transfer.py`). Teacher labels only. |
| `corpus/tasksource.jsonl` | 87k | 227 tasksource tasks marked for commercial use (`tasksource_convert.py`). |
| `corpus/robot.jsonl` | 60k | Robot decisions with rule-derived gold labels (`gen_robot.py --n 60000 --seed 1`). |
| `corpus/teacher_*.jsonl` | | The teacher's calibrated option distribution per row (`remote/teacher_label.py`). |

- **Row format:** `{kind, state, instructions, options: [[name, description]], label, task, weight, instruction_variants}`.
- **Teacher:** every row was labelled by a Strands Decider 4B checkpoint (v22).
- **Training targets:** 50% teacher distribution and 50% gold. Transfer rows use the teacher alone.
- **Not yet scripted:** corpus assembly for `teacher_src.jsonl` is not fully scripted here.

## Recipes

### sparrow-nano-robot-v1.0
```bash
python training/static3.py --data corpus/teacher_src.jsonl corpus/transfer.jsonl corpus/tasksource.jsonl corpus/robot.jsonl \
  --teacher corpus/teacher_src.jsonl=corpus/teacher_v22.jsonl corpus/transfer.jsonl=corpus/teacher_transfer.jsonl \
            corpus/tasksource.jsonl=corpus/teacher_tasksource.jsonl \
  --vocab 8192 --dim 128 --hidden 256 --kv --seed 1 --out runs/nano-robot
python training/calibrate.py runs/nano-robot/nano-robot.sparrow --out sparrow-nano-robot-v1.0.sparrow --name sparrow-nano-robot-v1.0
```

### sparrow-nano-general-v1.0
Same as nano-robot with `--vocab 16384` and no `--kv` (seed 0).

### sparrow-micro-general-v1.1
```bash
python training/static2.py --data <same four files> --teacher <same three pairs> --out runs/micro
python training/export_pico.py runs/micro --out runs/micro/micro.sparrow
python training/calibrate.py runs/micro/micro.sparrow --out sparrow-micro-general-v1.1.sparrow --name sparrow-micro-general-v1.1
```

### sparrow-tiny-general-v1.0 / sparrow-small-general-v1.0
```bash
python training/train.py --encoder jhu-clsp/ettin-encoder-32m --data corpus/teacher_src.jsonl corpus/transfer.jsonl corpus/tasksource.jsonl \
  --teacher <same three pairs> --keep training/vocab/ettin-keep16k.json --epochs 3 --lr 2e-4 --tok-budget 10000 --out runs/tiny
python training/export.py runs/tiny --vocab 16384 --out sparrow-tiny-general-v1.0.sparrow --temps '{"noul":1.4,"choice":1.4,"score":0.75}'
```
For small, use `ettin-encoder-68m`, `--lr 1e-4` and temperatures `{"noul":2.3,"choice":1.4,"score":0.65}`.

### sparrow-pico models
See [docs/quickstart/pico.md](../docs/quickstart/pico.md).

## Hardware used

- **Static models (micro, nano):** one RTX 4090 (about 20-30 min per run, several runs in parallel)
  or an Apple M4 Pro.
- **Encoder tiers and teacher labelling:** RTX 4090s rented on vast.ai.
- **Sweeps:** `remote/sweep_*.sh` are the sweeps behind the ablations in the report.
