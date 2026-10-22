"""`sparrow-decider ask STATE --noul "question"`, `sparrow-decider serve` (a /v1/systemone endpoint) and
`sparrow-decider models`."""
from __future__ import annotations

import argparse
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import Decider, __version__, available_models


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sparrow-decider")
    ap.add_argument("--version", action="version", version=f"sparrow-decider {__version__}")
    ap.add_argument("--model", help="model name (e.g. nano-robot) or .sparrow file; default sparrow-nano-general-v1.0")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("ask", help="answer one question")
    a1.add_argument("state")
    g = a1.add_mutually_exclusive_group(required=True)
    g.add_argument("--noul", metavar="QUESTION")
    g.add_argument("--choice", metavar="QUESTION")
    g.add_argument("--score", metavar="QUESTION")
    a1.add_argument("--option", "-o", action="append", default=[], help="name=description (choice) or level text (score)")
    s = sub.add_parser("serve", help="serve POST /v1/systemone")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    sub.add_parser("models", help="list the models available by name")
    a = ap.parse_args(argv)
    if a.cmd == "models":
        print("\n".join(available_models()))
        return
    d = Decider.load(a.model)
    if a.cmd == "ask":
        if a.noul:
            q = {"type": "noul", "instructions": a.noul}
        elif a.choice:
            q = {"type": "choice", "instructions": a.choice,
                 "criteria": dict(o.split("=", 1) if "=" in o else (o, "") for o in a.option)}
        else:
            q = {"type": "score", "instructions": a.score, "criteria": a.option}
        t = time.perf_counter()
        out = d.ask(a.state, {"q": q})["q"]
        out["latency_ms"] = round((time.perf_counter() - t) * 1000, 2)
        print(json.dumps(out, indent=1))
        return

    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            b = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            self._send(200, {"status": "ok", "model": d.name, "version": __version__})

        def do_POST(self):
            if self.path.rstrip("/") != "/v1/systemone":
                return self._send(404, {"error": "not found"})
            try:
                req = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
                t = time.perf_counter()
                ans = d.ask(req.get("state"), req["questions"])
                self._send(200, {"model": d.name, "answers": ans, "usage": {"input_tokens": 0, "output_tokens": 0},
                                 "latency_ms": round((time.perf_counter() - t) * 1000, 2)})
            except (KeyError, ValueError, TypeError) as e:
                self._send(422, {"error": str(e)})

        def log_message(self, *args):
            pass

    print(f"sparrow-decider {__version__} ({d.name}) on http://{a.host}:{a.port}/v1/systemone", file=sys.stderr)
    ThreadingHTTPServer((a.host, a.port), H).serve_forever()


if __name__ == "__main__":
    main()
