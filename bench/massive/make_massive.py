"""MASSIVE routing benchmark (Amazon MASSIVE 1.1, en-US test split, CC BY 4.0), held out of all
Sparrow training. Two tasks per sampled utterance:

  domain   which of the 18 assistant domains handles the utterance          (choice, 18 options)
  intent   which intent inside the gold domain (2-9 options, names only; single-intent domains skipped)

  python bench/massive/make_massive.py --n 600   # -> bench/massive/massive_{domain,intent}.jsonl
"""
import argparse
import os
import random
import re

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

HERE = os.path.dirname(os.path.abspath(__file__))
DOMAINS = {
    "social": "social media posts and complaints to companies", "transport": "trains, taxis, tickets and traffic",
    "calendar": "events, reminders and the calendar", "play": "music, radio, podcasts, audiobooks and games",
    "news": "news headlines and updates", "datetime": "the current time, date and time zones",
    "recommendation": "recommend places, events or movies", "email": "read, send or manage email",
    "iot": "smart home devices: lights, plugs, vacuum, coffee machine", "general": "jokes, repeats, greetings, small talk",
    "audio": "volume and muting", "lists": "to-do and shopping lists", "qa": "facts, definitions, maths, stocks, currency",
    "cooking": "recipes and cooking", "takeaway": "order or ask about takeaway food", "music": "music likes, settings and info",
    "alarm": "set, remove or list alarms", "weather": "weather forecasts",
}


def load():
    p = hf_hub_download("AmazonScience/massive", "en-US/test/0000.parquet", repo_type="dataset",
                        revision="refs/convert/parquet", local_dir=os.path.join(HERE, "..", "..", "ext", "massive"))
    src = open(hf_hub_download("AmazonScience/massive", "massive.py", repo_type="dataset")).read()
    scen = eval(re.search(r"_SCENARIOS = (\[.*?\])", src, re.S).group(1))
    ints = eval(re.search(r"_INTENTS = (\[.*?\])", src, re.S).group(1))
    return pq.read_table(p).to_pylist(), scen, ints


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=600)
    a = ap.parse_args()
    rows, scen, ints = load()
    random.Random(0).shuffle(rows)
    rows = rows[:a.n]
    by_scen = {}
    for i in ints:
        by_scen.setdefault(i.split("_")[0], []).append(i)
    dom = open(os.path.join(HERE, "massive_domain.jsonl"), "w")
    itn = open(os.path.join(HERE, "massive_intent.jsonl"), "w")
    import json
    for k, r in enumerate(rows):
        s, it = scen[r["scenario"]], ints[r["intent"]]
        state = f"user: {r['utt']}"
        dom.write(json.dumps({"id": f"domain-{k:03d}", "family": "domain", "state": state,
                              "question": {"type": "choice", "instructions": "Which assistant domain should handle this request?",
                                           "criteria": DOMAINS}, "expected": s}) + "\n")
        opts = {i: i.split("_", 1)[1].replace("_", " ") for i in by_scen[s]}
        if len(opts) < 2:  # weather has a single intent
            continue
        itn.write(json.dumps({"id": f"intent-{k:03d}", "family": "intent", "state": state,
                              "question": {"type": "choice", "instructions": f"Which {s} action does the user want?",
                                           "criteria": opts}, "expected": it}) + "\n")
    print(f"{len(rows)} utterances -> massive_domain.jsonl, massive_intent.jsonl")


if __name__ == "__main__":
    main()
