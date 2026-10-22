# Benchmarks

| Bench | What | Files |
|---|---|---|
| RobotBench v0 | 55 hand-written robot decisions: skill routing, navigation from sensors, yes/no checks, recovery, urgency | `robot/` |
| MASSIVE routing | Amazon MASSIVE 1.1 en-US test (CC BY 4.0), 600 utterances: domain (18-way) and intent within domain. Held out of all training | `massive/` |
| JevBench public | 231 public JevBench tasks, scored with the local v1.5 proxy | `bench_jev.py` |
| C parity | the C runtime vs the numpy runtime: probability difference, argmax agreement, time | `../c/tests/parity.py` |
| pico | a compiled pico model vs its teacher and vs the spec's rules | `pico/` |

```bash
bench/evaluate_model.sh path/to/model.sparrow        # RobotBench + JevBench + C parity -> results/
python bench/robot/run_robot.py MODEL --bench bench/massive/massive_domain.jsonl --out results/massive-domain-NAME.json
python bench/aggregate.py                             # results/*.json -> RESULTS.md
```

- **JevBench inputs:** set `SPARROW_JEVBENCH` to the JevBench `all.jsonl` and `SPARROW_JEV_PROXY`
  to the folder holding `v15_proxy.py` (both from the Strands Decider repo, `evaluation/jevbench`).
- **Reference scores:** to score a full Strands Decider on the same benches, run
  `robot/run_reference.py` in an env with strands-decider installed.

All numbers in `results/` come from these scripts on one Apple M4 Pro core unless stated.
