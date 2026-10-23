"""Python runtime: loading, answer shapes, a few decisions that must hold, and the CLI."""
import json
import subprocess
import sys

import pytest

from sparrow_decider import Decider, available_models

ACTIONS = {"continue": "keep driving toward the goal", "dock": "go back to the charging dock",
           "stop": "halt immediately"}


@pytest.fixture(scope="module")
def general():
    return Decider.load()


@pytest.fixture(scope="module")
def robot():
    return Decider.load("nano-robot")


def test_bundled_models():
    assert {"sparrow-nano-general-v1.1", "sparrow-nano-robot-v1.1"} <= set(available_models())


def test_unknown_model_is_a_clear_error():
    with pytest.raises(FileNotFoundError, match="available"):
        Decider.load("does-not-exist")


def test_answer_shapes(general):
    a = general.ask("User: I was charged twice for order 1182", {
        "refund": {"type": "noul", "instructions": "Is the user asking for money back?"},
        "intent": {"type": "choice", "instructions": "Primary intent?",
                   "criteria": {"billing": "charges, invoices", "bug": "broken feature"}},
        "urgency": {"type": "score", "instructions": "How urgent?", "criteria": ["not urgent", "soon", "now"]},
    })
    assert a["refund"]["type"] == "noul" and 0 <= a["refund"]["noul"] <= 1
    assert a["intent"]["choice"] in ("billing", "bug")
    assert abs(sum(a["intent"]["probabilities"].values()) - 1) < 1e-3
    assert 0 <= a["urgency"]["score"] <= 2 and set(a["urgency"]["legend"]) == {"0", "1", "2"}


@pytest.mark.parametrize("state,want", [
    ("battery: 5%\nfront_obstacle_m: 6.0\npath: clear", "dock"),
    ("battery: 80%\nfront_obstacle_m: 0.1\npath: blocked", "stop"),
    ("battery: 85%\nfront_obstacle_m: 7.5\npath: clear", "continue"),
])
def test_robot_sensor_decisions(robot, state, want):
    a = robot.ask(state, {"q": {"type": "choice", "instructions": "What should the robot do next?",
                                "criteria": ACTIONS}})
    assert a["q"]["choice"] == want


def test_bad_questions_raise(general):
    with pytest.raises(ValueError):
        general.ask("x", {"q": {"type": "choice", "instructions": "?", "criteria": {"only": "one"}}})
    with pytest.raises(ValueError):
        general.ask("x", {"q": {"type": "maybe", "instructions": "?"}})


def test_cli_ask():
    out = subprocess.run([sys.executable, "-m", "sparrow_decider.cli", "--model", "nano-robot", "ask",
                          "operator: grab that blue bottle", "--choice", "Which skill?",
                          "-o", "pick=pick up an object", "-o", "navigate=move somewhere"],
                         capture_output=True, text=True, check=True).stdout
    assert json.loads(out)["choice"] == "pick"
