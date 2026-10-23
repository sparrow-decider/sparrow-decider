"""Time a sparrow-pico header on a real ESP32-S3 (c/examples/esp32s3_pico_bench).

  python bench/esp32/pico_run.py [--fastmath] [--o3] [--tag NAME]   -> bench/results/esp32-pico-rover-<variant>.json
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from run import esptool, idf_in, read_serial  # noqa: E402

APP = os.path.join(ROOT, "c", "examples", "esp32s3_pico_bench")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fastmath", action="store_true")
    ap.add_argument("--o3", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--kernel", type=int, default=1, help="0 simple, 1 four accumulators, 2 skip zeros")
    ap.add_argument("--port")
    a = ap.parse_args()
    port = a.port or sorted(glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/ttyACM*"))[0]
    variant = "-".join(x for x in [f"k{a.kernel}", "fastmath" if a.fastmath else "", "o3" if a.o3 else "", a.tag] if x)
    env = dict(os.environ)
    env["PATH"] = "/opt/homebrew/opt/python@3.12/libexec/bin:" + env["PATH"]
    build = os.path.join(APP, f"build-{variant}")
    idf_in(APP, ["-B", build, "-D", f"SDKCONFIG={build}/sdkconfig", "-D", f"PICO_FASTMATH={int(a.fastmath)}",
                 "-D", f"PICO_O3={int(a.o3)}", "-D", f"PICO_KERNEL={a.kernel}", "build"], env)
    esptool(f"--chip esp32s3 -p {port} -b 921600 --after watchdog_reset write_flash @flash_args", env, cwd=build)
    line = next(l for l in read_serial(port, end="PICO_RESULT") if l.startswith("PICO_RESULT"))
    r = dict(kv.split("=") for kv in line.split()[1:])
    rep = {"model": "sparrow-pico-rover-v1.0", "bench": "esp32s3-pico", "variant": variant, "cpu_mhz": 240,
           **{k: (float(v) if "." in v else v if "/" in v else int(v)) for k, v in r.items() if k != "sink"}}
    json.dump(rep, open(os.path.join(ROOT, "bench", "results", f"esp32-pico-rover-{variant}.json"), "w"), indent=1)
    print(json.dumps(rep))


if __name__ == "__main__":
    main()
