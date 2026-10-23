# Quickstart: compile a decision with sparrow-pico

Use pico when your device's inputs are sensor values and its questions are known at build time.
For each question you get a small C function with no dependencies, about 2 KB in size (501 parameters for the rover example). It is
distilled from a full Strands Decider, so it inherits that model's judgement for your device.

## 1. Write a spec

```json
{
  "name": "greenhouse",
  "context": "open vents when it is above 30 C; water when soil moisture is below 25%; never water and vent at the same time in frost.",
  "features": [
    {"name": "temp_c",        "type": "number", "min": -10, "max": 50},
    {"name": "soil_moisture", "type": "number", "min": 0,   "max": 100, "unit": "%"},
    {"name": "raining",       "type": "bool"},
    {"name": "time_of_day",   "type": "enum", "values": ["night", "morning", "afternoon", "evening"]}
  ],
  "questions": {
    "action":   {"type": "choice", "instructions": "What should the controller do now?",
                 "criteria": {"nothing": "no change", "water": "start watering",
                              "vent": "open the vents", "heat": "turn on the heater"}},
    "alert":    {"type": "noul", "instructions": "Should the grower be alerted?"},
    "stress":   {"type": "score", "instructions": "How stressed are the plants?",
                 "criteria": ["fine", "mild", "severe"]}
  }
}
```

- **`features`:** what your firmware measures. A `number` has a `min` and `max`; there are also
  `bool` and `enum`.
- **`context`:** optional. The rules in plain language. The teacher reads them on every sample.
- **`questions`:** the decisions you need, in the same question format as the Python API.

## 2. Sample, label, build

```bash
python training/pico_compile.py sample greenhouse.json --n 3000 --work runs/pico-greenhouse

# label with a full Strands Decider, in an env with strands-decider installed
# (the public 2B: StrandsAgents/strands-decider-2B-qwen3.5-v1-2610)
python training/label_decider.py <checkpoint dir> runs/pico-greenhouse/rows.jsonl runs/pico-greenhouse/teacher.jsonl

python training/pico_compile.py build greenhouse.json --work runs/pico-greenhouse --out firmware/main
```

- **`build`:** trains one MLP per question, prints its agreement with the teacher on held-out
  states, and writes `sparrow_pico_greenhouse.h`.
- **Labelling time:** about 9,000 labels take about 40 minutes on an Apple M-series GPU, and much
  less on a CUDA GPU.

## 3. Use it

```c
#include "sparrow_pico_greenhouse.h"

greenhouse_state s = {.temp_c = 34.0f, .soil_moisture = 40.0f, .raining = 0,
                      .time_of_day = GREENHOUSE_TIME_OF_DAY_AFTERNOON};
float p[GREENHOUSE_ACTION_N];
greenhouse_action(&s, p);                  /* probabilities over the options */
/* greenhouse_action_options[i] holds the option names */
```

## How good is it?

`c/examples/specs/rover.json` was compiled from the public 2B. On 600 held-out states:

| Question | pico vs teacher | Teacher vs the rules | pico vs the rules |
|---|---|---|---|
| action (5 options) | 98.2% | 94.2% | 94.3% |
| needs charging | 99.2% | 99.0% | 99.8% |

A pico model is as good as its teacher on your spec, and no better. Check the teacher's answers on
the cases that matter before shipping. Never use a learned model as the only safety stop.
