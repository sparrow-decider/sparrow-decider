# Quickstart: Python

Install the package. numpy is the only dependency, and the install is 1.4 MB with two models bundled.

```bash
pip install sparrow-decider            # or, from a clone: pip install -e .
```

## Ask a question

```python
from sparrow_decider import Decider

d = Decider.load()   # sparrow-nano-general-v1.1, bundled

answers = d.ask(
    "User: I was charged twice for order 1182, I want my money back",
    {
        "tool":    {"type": "choice", "instructions": "Which tool fits this request?",
                    "criteria": {"flights": "search and book flights", "refunds": "refund a payment",
                                 "weather": "forecasts for a city", "calendar": "create or move meetings"}},
        "upset":   {"type": "noul",   "instructions": "Is the user upset?"},
        "urgency": {"type": "score",  "instructions": "How urgent is this?",
                    "criteria": ["can wait", "today", "right now"]},
    },
)
print(answers["tool"]["choice"], answers["tool"]["confidence"])   # refunds, high confidence
```

There are three question types. The answers have the same shapes as
[Strands Decider](https://github.com/strands-labs/strands-decider):

| type | criteria | answer |
|---|---|---|
| `noul` | optional `{"false": ..., "true": ...}` | `{"noul": P(true)}` |
| `choice` | `{name: description}`, 2 or more | `{"choice", "probabilities", "confidence"}` |
| `score` | list of 2-10 levels, lowest first | `{"score": expected level, "legend", "probabilities", "confidence"}` |

## Pick a model

```python
from sparrow_decider import Decider, available_models

print(available_models())            # ['sparrow-nano-general-v1.1', 'sparrow-nano-robot-v1.2', ...]
robot = Decider.load("nano-robot")    # names can be short
micro = Decider.load("path/to/sparrow-micro-general-v1.1.sparrow")
```

- **Bundled models:** the two nano models.
- **Larger models:** micro, tiny and small are attached to the GitHub releases. Put the `.sparrow`
  files in `~/.cache/sparrow-decider/` (or any folder listed in `$SPARROW_MODELS`) to load them by
  name.

| Need | Model |
|---|---|
| Any short text decision, smallest and fastest | `nano-general` |
| Decisions that depend on sensor readings such as `battery: 6%` | `nano-robot` |
| Broader text, still sub-millisecond | `micro-general` |
| The most general, if 20-60 ms is fine | `tiny-general`, `small-general` |

## Command line and HTTP

```bash
sparrow-decider models
sparrow-decider ask "battery: 6%\nfront_obstacle_m: 7.0" --model nano-robot \
    --choice "What next?" -o "continue=keep going" -o "dock=go charge" -o "stop=halt"
sparrow-decider serve --port 8000
```

`serve` exposes `POST /v1/systemone`, which takes `{"state": ..., "questions": {...}}` and returns
`{"model", "answers", "usage"}`. The request and answer shapes follow the Strands Decider
`/v1/systemone` contract.

## Probabilities

- Each model ships per-kind temperatures fitted on held-out data, so probabilities are calibrated
  rather than overconfident.
- A yes/no answer near 0.5 means the model is unsure: treat it as "don't know".
