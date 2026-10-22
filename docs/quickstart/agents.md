# Quickstart: decisions inside an agent

An LLM call takes about a second. A Sparrow decision takes about a millisecond, inside the process, and costs
nothing. Use Sparrow for the small, frequent calls an agent makes:

- **Routing:** which tool to use, which sub-agent, or whether a message needs a human.
- **Gating:** is this message on topic, should we escalate, is the task done?
- **Labelling:** intent, category, urgency.

Keep the LLM for open-ended reasoning.

## As a plain function

```python
from sparrow_decider import Decider

decider = Decider.load()

TOOLS = {"search_flights": "find and book flights", "weather": "forecasts for a city",
         "calendar": "create or move meetings", "none": "no tool fits; answer directly"}

def route(user_message: str) -> str:
    a = decider.ask(user_message, {"tool": {"type": "choice", "instructions": "Which tool fits this request?",
                                            "criteria": TOOLS}})["tool"]
    return a["choice"] if a["confidence"] > 0.3 else "none"   # low confidence: let the LLM decide
```

## As a tool for a Strands agent

```python
from strands import Agent, tool
from sparrow_decider import Decider

decider = Decider.load()

@tool
def classify(text: str, options: dict[str, str], question: str) -> dict:
    """Pick one option for `text`. options maps option name -> short description."""
    return decider.ask(text, {"q": {"type": "choice", "instructions": question, "criteria": options}})["q"]

agent = Agent(tools=[classify])
```

## Tips

- Short option descriptions help more than long ones. Name options as the user would say them.
- Use `confidence` to fall back to a bigger model. Low confidence is a signal, not an error.
- Put the facts the decision depends on in the state, one per line (`battery: 6%`). `nano-robot`
  reads `key: number` pairs as values.
