# Contributing

Issues and pull requests are welcome.

```bash
git clone https://github.com/sparrow-decider/sparrow-decider && cd sparrow-decider
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```

- **Runtime changes** (`python/`, `c/`): run `pytest`. It checks C-vs-Python parity and the pico
  header.
- **New models:** add the benchmark JSONs from `bench/evaluate_model.sh` to `bench/results/` and run
  `python bench/aggregate.py`. Name models as in [NAMING.md](NAMING.md).
- **Numbers in docs:** every number needs a results file or a log behind it.

Unofficial community project. Not an AWS or Strands product.
