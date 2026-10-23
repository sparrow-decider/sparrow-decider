"""C runtime: the packed nano models give the numpy runtime's answers, and the generated
sparrow-pico header compiles and decides."""
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "python", "sparrow_decider", "models")
pytestmark = pytest.mark.skipif(shutil.which("cc") is None, reason="needs a C compiler")


@pytest.mark.parametrize("model", ["sparrow-nano-general-v1.1", "sparrow-nano-robot-v1.2"])
def test_c_matches_numpy(model, tmp_path):
    out = tmp_path / "parity.json"
    subprocess.run([sys.executable, os.path.join(ROOT, "c/tests/parity.py"), os.path.join(MODELS, model + ".sparrow"),
                    "--n", "200", "--out", str(out)], check=True, capture_output=True)
    import json
    r = json.loads(out.read_text())
    agree, n = map(int, r["argmax_agree"].split("/"))
    assert agree == n and r["max_abs_diff"] < 1e-4


def test_pico_header_compiles_and_decides():
    src = """
#include <stdio.h>
#include "sparrow_pico_rover.h"
static int top(const float *p, int n) { int b = 0; for (int i = 1; i < n; i++) if (p[i] > p[b]) b = i; return b; }
int main(void) {
    float p[ROVER_ACTION_N];
    rover_state s = {.battery = 6, .front_obstacle_m = 7.0f, .goal_m = 30, .path = ROVER_PATH_CLEAR};
    rover_action(&s, p); printf("%s ", rover_action_options[top(p, ROVER_ACTION_N)]);
    s.battery = 80; s.front_obstacle_m = 0.2f;
    rover_action(&s, p); printf("%s ", rover_action_options[top(p, ROVER_ACTION_N)]);
    s.front_obstacle_m = 6.0f; s.path = ROVER_PATH_BLOCKED;
    rover_action(&s, p); printf("%s\\n", rover_action_options[top(p, ROVER_ACTION_N)]);
    return 0;
}
"""
    d = tempfile.mkdtemp()
    open(os.path.join(d, "t.c"), "w").write(src)
    subprocess.run(["cc", "-std=c99", "-Wall", "-Werror", "-I", os.path.join(ROOT, "c/examples/esp32s3_robot/main"),
                    os.path.join(d, "t.c"), "-lm", "-o", os.path.join(d, "t")], check=True)
    assert subprocess.run([os.path.join(d, "t")], capture_output=True, text=True).stdout.split() == ["dock", "stop", "replan"]
