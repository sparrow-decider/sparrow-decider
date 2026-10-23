#!/usr/bin/env python3
"""Regenerate the static Sparrow Decider site from site/facts.json.

The generated HTML is committed, so deploying needs no build step: GitHub Pages serves
site/www/ as is. Run this only after facts.json (or the copy below) changes:

    python3 site/www/_build/build.py

Every number on Home, Models and Architecture comes from facts.json. Benchmarks also quotes
bench/RESULTS.md rows for released model IDs, each table citing RESULTS.md (see BENCH below).
"""
import html
import json
import math
import re
from pathlib import Path

WWW = Path(__file__).resolve().parent.parent
F = json.loads((WWW.parent / "facts.json").read_text())
(WWW / "assets" / "facts.json").write_text(json.dumps(F, indent=2, ensure_ascii=False) + "\n")

SITE_URL = "https://sparrow-decider.github.io/sparrow-decider/"  # set to the deployed base URL
VER = F["version"]
REPO = F["repo"]
BR = F.get("default_branch", "main")
L = {
    "repo": REPO,
    "releases": REPO + "/releases",
    "docs": REPO + "/tree/" + BR + "/docs/quickstart",
    "python": REPO + "/blob/" + BR + "/docs/quickstart/python.md",
    "agents": REPO + "/blob/" + BR + "/docs/quickstart/agents.md",
    "c": REPO + "/blob/" + BR + "/docs/quickstart/c.md",
    "esp32": REPO + "/blob/" + BR + "/docs/quickstart/esp32.md",
    "pico": REPO + "/blob/" + BR + "/docs/quickstart/pico.md",
    "modelcard": REPO + "/blob/" + BR + "/docs/models.md",
    "results": REPO + "/blob/" + BR + "/bench/RESULTS.md",
    "report": REPO + "/blob/" + BR + "/research/REPORT.md",
    "license": REPO + "/blob/" + BR + "/LICENSE",
    "notice": REPO + "/blob/" + BR + "/NOTICE",
    "contributing": REPO + "/blob/" + BR + "/CONTRIBUTING.md",
    "citation": REPO + "/blob/" + BR + "/CITATION.cff",
    "issues": F["contact"]["github_issues"],
    "discussions": F["contact"]["discussions"],
}
E = html.escape


# ---------------------------------------------------------------- helpers
def tier(id_part):
    for t in F["tiers"]:
        if id_part in t["id"] or t["tier"] == id_part:
            return t
    raise KeyError(id_part)


def size_parts(s):
    m = re.match(r"^(~?[\d.]+\s*(?:KB|MB|GB))\s*(.*)$", s)
    return (m.group(1), m.group(2)) if m else (s, "")


def size_bytes(s):
    m = re.search(r"([\d.]+)\s*(KB|MB|GB)", s)
    return float(m.group(1)) * {"KB": 1e3, "MB": 1e6, "GB": 1e9}[m.group(2)]


def short_time(s):
    m = re.search(r"([\d.]+\s*(?:µs|ms))", s)
    return m.group(1) if m else s


def to_us(s):
    m = re.search(r"([\d.]+)\s*(µs|ms)", s)
    v = float(m.group(1))
    return v * 1000 if m.group(2) == "ms" else v


def short_id(i):
    return i.replace("sparrow-", "")


ICON = {
    "github": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .5a11.5 11.5 0 0 0-3.64 22.41c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.52-1.33-1.28-1.69-1.28-1.69-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.41-2.69 5.38-5.25 5.67.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5z"/></svg>',
    "copy": '<svg class="i-cp" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg><svg class="i-ok" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>',
    "moon": '<svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg><svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line class="b1" x1="4" y1="7" x2="20" y2="7"/><line class="b2" x1="4" y1="12" x2="20" y2="12"/><line class="b3" x1="4" y1="17" x2="20" y2="17"/></svg>',
    "ext": '<svg class="ext" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 2h6v6M10 2 2 10"/></svg>',
    "download": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></svg>',
    "minus": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9.5"/><path d="M8 12h8"/></svg>',
    "pause": '<svg class="i-pause" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><rect x="3" y="2" width="3.5" height="12" rx="1"/><rect x="9.5" y="2" width="3.5" height="12" rx="1"/></svg><svg class="i-play" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M4 2.5v11a.5.5 0 0 0 .77.42l8.5-5.5a.5.5 0 0 0 0-.84l-8.5-5.5A.5.5 0 0 0 4 2.5z"/></svg>',
    "toggle": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="2" y="7" width="20" height="10" rx="5"/><circle cx="16" cy="12" r="3" fill="currentColor"/></svg>',
    "radio": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="5" cy="12" r="3"/><circle cx="12" cy="12" r="3" fill="currentColor"/><circle cx="19" cy="12" r="3"/></svg>',
    "scale": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="3" y="14" width="3.5" height="6" rx="1"/><rect x="8.2" y="10" width="3.5" height="10" rx="1"/><rect x="13.4" y="6" width="3.5" height="14" rx="1" opacity=".45"/><rect x="18.6" y="3" width="3.5" height="17" rx="1" opacity=".25"/></svg>',
    "chat": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1.1-4.5A8 8 0 1 1 21 12z"/></svg>',
    "bug": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/></svg>',
    "code": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m8 7-5 5 5 5M16 7l5 5-5 5"/></svg>',
}
ARR = '<span class="arr" aria-hidden="true">→</span>'


def ext_link(href, text, cls="text-link"):
    return f'<a class="{cls}" href="{href}">{text}{ICON["ext"]}</a>'


def copy_block(cls="copy", label="Copy install command"):
    inst = F["install"]
    return (f'<div class="{cls}"><span class="prompt" aria-hidden="true">$ </span><code>{E(inst)}</code>'
            f'<button class="copy-btn" type="button" data-copy="{E(inst)}" aria-label="Copy {E(inst)}">{ICON["copy"]}<span class="label">Copy</span></button></div>')


# ---------------------------------------------------------------- syntax highlighting (build time, zero runtime cost)
KW = {
    "python": r"from|import|def|return|if|else|for|in|as|print|None|True|False|with|class|lambda",
    "c": r"include|static|const|float|int|void|extern|uint8_t|asm|return|struct|unsigned|char",
    "bash": r"pip|python|sparrow-decider|cd|install",
    "json": None,
}


def hl(code, lang):
    com = {"python": r"#[^\n]*", "bash": r"#[^\n]*", "c": r"/\*[\s\S]*?\*/|//[^\n]*|#include", "json": r"(?!x)x"}[lang]
    kw = KW[lang]
    parts = ["(" + com + ")", r'("(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\')', r"(\b\d+(?:\.\d+)?f?\b)",
             "(" + (r"\b(?:" + kw + r")\b" if kw else r"(?!x)x") + ")", r"(\b[A-Za-z_]\w*(?=\())"]
    rx = re.compile("|".join(parts))
    out, last = [], 0
    for m in rx.finditer(code):
        out.append(E(code[last:m.start()], quote=False))
        g = m.group(0)
        if m.group(1):
            cls = "k" if g == "#include" else "c"
        elif m.group(2):
            cls = "s"
        elif m.group(3):
            cls = "n"
        elif m.group(4):
            cls = "k"
        else:
            cls = "f"
        out.append(f'<span class="{cls}">{E(g, quote=False)}</span>')
        last = m.end()
    out.append(E(code[last:], quote=False))
    return "".join(out)


SNIP = {
    "python": '''from sparrow_decider import Decider

d = Decider.load()   # bundled nano model

answers = d.ask(
    "User: I was charged twice for order 1182 and nobody replied to my email.",
    {
        "intent":  {"type": "choice", "instructions": "What does the user want?",
                    "criteria": {"refund": "money back for a charge", "cancel": "stop an order",
                                 "status": "where is my order"}},
        "upset":   {"type": "noul",   "instructions": "Is the user upset?"},
        "urgency": {"type": "score",  "instructions": "How urgent is this?",
                    "criteria": ["can wait", "today", "right now"]},
    },
)
print(answers["intent"]["choice"], answers["intent"]["confidence"])''',
    "cli": '''pip install sparrow-decider
sparrow-decider models
sparrow-decider ask "battery: 6%\\nfront_obstacle_m: 7.0" --model nano-robot \\
    --choice "What next?" -o "continue=keep going" -o "dock=go charge" -o "stop=halt"
sparrow-decider serve --port 8000        # POST /v1/systemone''',
    "c": '''#include "sparrow.h"
static sparrow_model m;
static sparrow_ctx ctx;   /* working memory; keep it static */

sparrow_load(&m, blob, blob_len);
float p_true = sparrow_noul(&m, &ctx, "motor_temp_c: 96\\nmax_temp_c: 80", "Is the motor overheating?");
float conf;
int k = sparrow_choice(&m, &ctx, state, "Which skill?", opts, n_opts, &conf);
float level = sparrow_score(&m, &ctx, state, "How urgent?", levels, n_levels, &conf);''',
    "esp32": '''#include "sparrow.h"

extern const uint8_t model_start[] asm("_binary_model_spb_start");
extern const uint8_t model_end[]   asm("_binary_model_spb_end");
static sparrow_model model;
static sparrow_ctx ctx;

void app_main(void) {
    sparrow_load(&model, model_start, model_end - model_start);
    sparrow_option opts[] = {{"pick", "pick up an object"}, {"navigate", "move somewhere"},
                             {"speak", "answer the person"}};
    float conf;
    int k = sparrow_choice(&model, &ctx, "operator: bring me the red mug", "Which skill?", opts, 3, &conf);
}''',
    "pico_spec": '''{
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
}''',
    "pico_c": '''#include "sparrow_pico_greenhouse.h"

greenhouse_state s = {.temp_c = 34.0f, .soil_moisture = 40.0f, .raining = 0,
                      .time_of_day = GREENHOUSE_TIME_OF_DAY_AFTERNOON};
float p[GREENHOUSE_ACTION_N];
greenhouse_action(&s, p);                  /* probabilities over the options */''',
    "pico_cmds": '''python training/pico_compile.py sample greenhouse.json --n 3000 --work runs/pico-greenhouse
python training/label_decider.py <checkpoint dir> runs/pico-greenhouse/rows.jsonl runs/pico-greenhouse/teacher.jsonl
python training/pico_compile.py build greenhouse.json --work runs/pico-greenhouse --out firmware/main''',
}


def code_block(cid, lang, fname, guide=None, guide_text="Read the guide"):
    foot = f'<div class="code-foot"><a href="{guide}">{guide_text} {ARR}</a></div>' if guide else ""
    return (f'<div class="bar"><span>{E(fname)}</span><button class="copy-btn" type="button" data-copy-target="{cid}" aria-label="Copy {E(fname)}">{ICON["copy"]}<span class="label">Copy</span></button></div>'
            f'<pre class="code" tabindex="0"><code id="{cid}">{hl(SNIP[lang if lang in SNIP else cid], LANG_OF.get(lang, lang))}</code></pre>{foot}')


LANG_OF = {"python": "python", "cli": "bash", "c": "c", "esp32": "c", "pico_spec": "json", "pico_c": "c", "pico_cmds": "bash"}


def snippet(key, fname, cid=None, guide=None, guide_text="Read the guide"):
    cid = cid or "code-" + key
    foot = f'<div class="code-foot"><a href="{guide}">{guide_text} {ARR}</a></div>' if guide else ""
    return (f'<div class="bar"><span>{E(fname)}</span><button class="copy-btn" type="button" data-copy-target="{cid}" aria-label="Copy {E(fname)}">{ICON["copy"]}<span class="label">Copy</span></button></div>'
            f'<pre class="code" tabindex="0"><code id="{cid}">{hl(SNIP[key], LANG_OF[key])}</code></pre>{foot}')


# ---------------------------------------------------------------- page chrome
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">')
BOOT = ('<script>(function(){var d=document.documentElement;d.classList.add("js");try{var q=/[?&]theme=(light|dark)/.exec(location.search),t=q?q[1]:localStorage.getItem("sd-theme");'
        'if(t==="light"||t==="dark")d.setAttribute("data-theme",t)}catch(e){}})();</script>')


def head(root, path, title, desc, extra="", noindex=False, base_script=""):
    canon = SITE_URL + path
    meta = [f'<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">', base_script,
            f"<title>{E(title)}</title>"]
    if desc:
        meta.append(f'<meta name="description" content="{E(desc)}">')
    if noindex:
        meta.append('<meta name="robots" content="noindex">')
    else:
        meta += [f'<link rel="canonical" href="{canon}">', '<meta property="og:type" content="website">',
                 '<meta property="og:site_name" content="Sparrow Decider">', f'<meta property="og:title" content="{E(title)}">',
                 f'<meta property="og:description" content="{E(desc)}">', f'<meta property="og:url" content="{canon}">',
                 f'<meta property="og:image" content="{SITE_URL}assets/img/og.png">',
                 '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
                 '<meta property="og:image:alt" content="Sparrow Decider: 9.3 µs per decision on a $10 ESP32-S3">',
                 '<meta name="twitter:card" content="summary_large_image">']
    meta += ['<meta name="color-scheme" content="dark light">', '<meta name="theme-color" content="#0B1020">',
             f'<link rel="icon" href="{root}assets/img/favicon.svg" type="image/svg+xml">',
             f'<link rel="icon" href="{root}assets/img/favicon-32.png" sizes="32x32" type="image/png">', BOOT, FONTS,
             f'<link rel="stylesheet" href="{root}assets/tokens.css?v={VER}">', f'<link rel="stylesheet" href="{root}assets/styles.css?v={VER}">', extra]
    return "\n".join(x for x in meta if x)


NAV = [("models/", "Models"), ("architecture/", "Architecture"), ("benchmarks/", "Benchmarks"), ("contact/", "Contact")]


SHARED_DEFS = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'
               '<linearGradient id="g-sunrise" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFB547"/><stop offset=".35" stop-color="#FF6B4A"/>'
               '<stop offset=".68" stop-color="#FF3D8B"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient>'
               '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah" d="M0 0 10 5 0 10z"/></marker>'
               '<marker id="ara" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah-accent" d="M0 0 10 5 0 10z"/></marker>'
               '</defs></svg>')


def header(root, current):
    home = root or "./"
    nav = "".join(f'<a href="{root}{h}"' + (' aria-current="page"' if h == current else "") + f">{t}</a>" for h, t in NAV)
    sheet_links = "".join(f'<a href="{root}{h}"' + (' aria-current="page"' if h == current else "") + f">{t}</a>" for h, t in NAV)
    inst = F["install"]
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<div id="sr-status" class="sr-only" aria-live="polite"></div>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{home}" aria-label="Sparrow Decider home"><img src="{root}assets/img/mark.svg" alt="" width="28" height="28"><span class="wm">Sparrow <span>Decider</span></span></a>
    <span class="ver-pill">v{VER}</span>
    <nav class="nav" aria-label="Primary">{nav}</nav>
    <div class="header-actions">
      <a class="hdr-docs" href="{L["docs"]}">Docs{ICON["ext"]}</a>
      <button class="icon-btn theme-toggle hdr-theme" type="button" aria-label="Switch to light theme">{ICON["moon"]}</button>
      <a class="icon-btn" href="{L["repo"]}" aria-label="Sparrow Decider on GitHub">{ICON["github"]}</a>
      <button class="copy-btn hdr-copy" type="button" data-copy="{E(inst)}" data-label="pip install" aria-label="Copy {E(inst)}">{ICON["copy"]}<span class="label">pip install</span></button>
      <button class="icon-btn menu-btn" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="site-menu">{ICON["menu"]}</button>
    </div>
  </div>
</header>
<div class="menu-sheet" id="site-menu" hidden>
  <div class="backdrop"></div>
  <nav class="panel" aria-label="Menu">
    <div class="main-links">{sheet_links}</div>
    <div class="sub">
      <a href="{L["docs"]}">Read the docs{ICON["ext"]}</a>
      <a href="{L["releases"]}">Download models{ICON["ext"]}</a>
      <a href="{L["repo"]}">View on GitHub{ICON["ext"]}</a>
    </div>
    {copy_block()}
    <div class="theme-row"><span>Theme: <span class="theme-name">Dark</span></span><button class="theme-toggle" type="button" aria-label="Switch to light theme">Switch</button></div>
  </nav>
</div>'''


def footer(root):
    cr = F["credits"]
    built = [c for c in cr if "evaluation only" not in c]
    evals = [c.replace(", evaluation only", "") for c in cr if "evaluation only" in c]
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="f-grid">
      <div class="f-brand">
        <a class="brand" href="{root or './'}" aria-label="Sparrow Decider home"><img src="{root}assets/img/mark.svg" alt="" width="28" height="28"><span class="wm">Sparrow <span>Decider</span></span></a>
        <p>Decisions that fit on a chip.</p>
        <p class="ver">v{VER} · Apache-2.0</p>
        {copy_block()}
      </div>
      <div class="f-col"><h2>Product</h2><ul>
        <li><a href="{root}models/">Models</a></li><li><a href="{root}architecture/">Architecture</a></li>
        <li><a href="{root}benchmarks/">Benchmarks</a></li><li><a href="{L["releases"]}">Download models{ICON["ext"]}</a></li></ul></div>
      <div class="f-col"><h2>Developers</h2><ul>
        <li><a href="{L["docs"]}">Read the docs{ICON["ext"]}</a></li><li><a href="{L["python"]}">Python{ICON["ext"]}</a></li>
        <li><a href="{L["esp32"]}">ESP32-S3{ICON["ext"]}</a></li><li><a href="{L["pico"]}">sparrow-pico{ICON["ext"]}</a></li>
        <li><a href="{L["c"]}">C library{ICON["ext"]}</a></li></ul></div>
      <div class="f-col"><h2>Community</h2><ul>
        <li><a href="{L["repo"]}">GitHub{ICON["ext"]}</a></li><li><a href="{L["discussions"]}">Discussions{ICON["ext"]}</a></li>
        <li><a href="{L["issues"]}">Report an issue{ICON["ext"]}</a></li><li><a href="{root}contact/">Contact</a></li></ul></div>
    </div>
    <div class="legal">
      <p class="disc">{E(F["disclaimer"])}</p>
      <p>Built by the Sparrow Decider contributors. Code under <a href="{L["license"]}">Apache-2.0</a>; model weights derived from MIT-licensed potion-base-8M and Ettin encoders. Strands Decider is referenced for compatibility and comparison only. <a href="{L["notice"]}">NOTICE</a></p>
      <p>Built on: {" · ".join(E(c) for c in built)}. Evaluation only: {" · ".join(E(c) for c in evals)}.</p>
      <p>No cookies, no tracking. © the Sparrow Decider contributors.</p>
    </div>
  </div>
</footer>'''


def page(path, root, current, title, desc, body, extra_head="", noindex=False, base_script="", scripts=True):
    js = f'<script src="{root}assets/main.js?v={VER}" defer></script>' if scripts else ""
    return f'''<!doctype html>
<html lang="en" data-theme="dark">
<head>
{head(root, path, title, desc, extra_head, noindex, base_script)}
</head>
<body>
{header(root, current)}
<main id="main" tabindex="-1">
{SHARED_DEFS}
{body}
</main>
{footer(root)}
{js}
</body>
</html>
'''


# ---------------------------------------------------------------- shared components
def model_card(t, root, body=None, actions=None):
    big, sub = size_parts(t["size"])
    rows = [("Input", t["input"], ""), ("Runs on", t["where"], "")]
    if t.get("esp32s3"):
        rows.append(("ESP32-S3", t["esp32s3"], "t"))
    if t.get("laptop"):
        rows.append(("Laptop", t["laptop"], "t"))
    if t.get("quality"):
        rows.append(("Quality", t["quality"], ""))
    glyph = "# · flags" if t["tier"] == "pico" else ("Aa + #" if "robot" in t["id"] else "Aa")
    if actions is None:
        actions = default_actions(t)
    dl = "".join(f"<dt>{E(a)}</dt><dd{' class=' + chr(34) + c + chr(34) if c else ''}>{E(b)}</dd>" for a, b, c in rows)
    return (f'<article class="card model-card"><div class="mc-top"><span class="badge t-{t["tier"]}">{t["tier"]}</span><span class="mc-ic" aria-hidden="true">{glyph}</span></div>'
            f'<h3>{E(t["id"])}</h3><div class="size"><span class="grad-text">{E(big)}</span></div>' + (f'<div class="size-sub">{E(sub)}</div>' if sub else "") +
            (f'<p class="body">{body}</p>' if body else "") + f'<dl class="spec">{dl}</dl><div class="act">{actions}</div></article>')


def default_actions(t):
    if t["tier"] == "pico":
        return ext_link(L["pico"], "Read the pico guide")
    if t["tier"] == "nano":
        return ext_link(L["python"], "Use from Python")
    return ext_link(L["releases"], "Download")


def speed_rows(cls_extra=""):
    labels = {"nano-general": "text", "nano-robot": "text with sensor readings", "pico": "compiled C"}
    out, rows_tbl = [], []
    for key, val in F["speedups_on_esp32s3"].items():
        t = tier(key)
        steps = []
        for part in val.split("->"):
            m = re.match(r"\s*([\d.]+\s*(?:µs|ms))\s*(?:\(([^)]*)\))?", part)
            steps.append((m.group(1), m.group(2) or ""))
        mx = max(to_us(s[0]) for s in steps)
        unit_max = steps[0][0] if to_us(steps[0][0]) == mx else max(steps, key=lambda s: to_us(s[0]))[0]
        bars = []
        for i, (v, lab) in enumerate(steps):
            last = i == len(steps) - 1
            lab = lab or ("earlier build" if not last else "current release")
            w = to_us(v) / mx * 80
            bars.append(f'<div class="sbar{" last" if last else ""}"><span class="lbl">{E(lab)}</span><span class="trk"><span class="f" style="width:{w:.2f}%"></span>'
                        f'<span class="v" style="left:{w:.2f}%">{E(v)}</span></span></div>')
        title = "sparrow-" + key if any(lab.startswith("v") for _, lab in steps) else t["id"]
        out.append(f'<article class="card srow"><div class="srow-head"><h3>{E(title)}<small>{labels.get(key, "")}</small></h3><span class="scale">scale: 0 to {E(unit_max)}</span></div>{"".join(bars)}</article>')
        rows_tbl.append(f'<tr><td class="id">{E(title)}</td><td>{E(val.replace("->", "→"))}</td></tr>')
    table = ('<details class="tbl"><summary>Show as table</summary><div class="table-wrap" role="region" aria-label="On-chip speedups" tabindex="0"><table class="data mid">'
             '<thead><tr><th>Model</th><th>Time per decision on ESP32-S3, earlier to current</th></tr></thead><tbody>' + "".join(rows_tbl) + "</tbody></table></div></details>")
    legend = '<ul class="legend" aria-hidden="true"><li><i class="lg-ref"></i>earlier builds</li><li><i class="lg-ours"></i>current release</li></ul>'
    summary = "; ".join(f'sparrow-{k} {v.replace("->", "to")}' for k, v in F["speedups_on_esp32s3"].items())
    return (f'<figure class="chart-fig" style="margin:0">{legend}<div class="speed-rows anim {cls_extra}" aria-hidden="true">' + "".join(out) + '</div>'
            f'<figcaption class="sr-only">Time per decision on the ESP32-S3: {E(summary)}.</figcaption>'
            f'<p class="scale-note">Each row has its own scale. Board: {E(F["board"])}.</p>{table}</figure>')


def limits_cards():
    return "".join(f'<div class="card limit">{ICON["minus"]}<p>{E(x)}</p></div>' for x in F["honest_limits"])


def hbar_chart(rows, mx, log=False, marker=None, lo=None):
    """rows: list of (name, note, value_number, label, is_ref)."""
    out = []
    for name, note, v, lab, ref in rows:
        if log:
            w = (math.log10(v) - lo) / (math.log10(mx) - lo) * 70
        else:
            w = v / mx * 82
        w = max(w, 0.6)
        mk = f'<span class="mk" style="left:{marker / mx * 82:.2f}%"></span>' if marker is not None else ""
        out.append(f'<div class="hc-row{" ref" if ref else ""}"><span class="nm">{E(name)}' + (f"<small>{E(note)}</small>" if note else "") +
                   f'</span><span class="trk">{mk}<span class="f" style="width:{w:.2f}%"></span><span class="v" style="left:{w:.2f}%">{E(lab)}</span></span></div>')
    return '<div class="hc anim" aria-hidden="true">' + "".join(out) + "</div>"


def table(head_cells, rows, caption, cls="mid", label="Table"):
    th = "".join(f'<th scope="col"{" class=" + chr(34) + c + chr(34) if c else ""}>{E(h)}</th>' for h, c in head_cells)
    return (f'<div class="table-wrap" role="region" aria-label="{E(label)}, scrolls horizontally" tabindex="0"><table class="data {cls}">'
            f'<caption>{caption}</caption><thead><tr>{th}</tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


DASH = '<span class="dash" aria-hidden="true">—</span><span class="sr-only">not measured</span>'


# ---------------------------------------------------------------- HOME
def nice_factor(t_ms):
    cands = sorted(m * 10 ** e for e in range(0, 8) for m in (1, 2, 2.5, 5))
    best = min(cands, key=lambda f: abs(t_ms * f - 2300))
    return best


def trace_scenes():
    scenes = []
    for key in ("pico", "nano"):
        h = F["hero_trace"][key]
        state = [s.split(": ", 1) for s in re.split(r"\s{2,}", h["state"].strip())]
        tm = re.match(r"([\d.]+)\s*(µs|ms)", h["time"])
        value, unit = float(tm.group(1)), tm.group(2)
        t_ms = value / 1000 if unit == "µs" else value
        fac = nice_factor(t_ms)
        fac_s = f"{fac:,.0f}" if fac == int(fac) else f"{fac:,}"
        where = h["time"].split(" on ", 1)[1] if " on " in h["time"] else ""
        scenes.append({
            "key": key, "model": h["model"], "state": state, "question": h["question"],
            "options": [[k, v] for k, v in h["probabilities"].items()], "answer": h["answer"],
            "time": f"{tm.group(1)} {unit}", "value": value, "unit": unit, "decimals": len(tm.group(1).split(".")[1]) if "." in tm.group(1) else 0,
            "resolveMs": round(t_ms * fac), "caption": f"per decision on {where} · replayed {fac_s}x slower",
        })
    return scenes


def trace_card(scene, board, static_id="trace", controls=True):
    st = "".join(f'<span><span class="k">{E(k)}: </span><span class="v">{E(v)}</span></span>' for k, v in scene["state"])
    bars = "".join(f'<div class="t-bar{" win" if o == scene["answer"] else ""}"><span class="o">{E(o)}</span><span class="trk"><span class="fill" style="width:{p * 100:.0f}%"></span></span><span class="p">{p:.2f}</span></div>'
                   for o, p in scene["options"])
    pause = f'<button class="pause" type="button" aria-pressed="false" aria-label="Pause animation">{ICON["pause"]}</button>' if controls else ""
    return f'''<figure class="trace resolved" id="{static_id}">
      <div class="trace-head"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="board">{E(board)}</span><span class="model">{E(scene["model"])}</span>{pause}</div>
      <div class="trace-body" aria-hidden="true">
        <div><div class="t-label">state</div><div class="t-state">{st}</div></div>
        <div><div class="t-label">question</div><div class="t-q">{E(scene["question"])}</div></div>
        <div class="t-bars-wrap"><div class="t-bars">{bars}</div><span class="t-scan" style="opacity:0"></span></div>
        <div class="t-foot"><div class="t-answer"><div class="t-label">answer</div><b>{E(scene["answer"])}</b></div>
          <div class="t-lat"><span class="n">{E(scene["time"])}</span><small>{E(scene["caption"])}</small></div></div>
      </div>'''


def home():
    root = ""
    pico, ng, nr = tier("pico"), tier("nano-general"), tier("nano-robot")
    nr2 = [t for t in F["tiers"] if "nano-robot" in t["id"] and t["id"] != nr["id"]]
    nr_fast = min([nr] + nr2, key=lambda t: to_us(t["esp32s3"]))
    scenes = trace_scenes()
    board = "esp32-s3 · " + re.search(r"(\d+ MHz)", F["board"]).group(1)
    cap_sr = " ".join(f'{s["model"]}: {", ".join(k + " " + v for k, v in s["state"])}. {s["question"]} Answer {s["answer"]}, {s["time"]} on the ESP32-S3.' for s in scenes)
    trace = trace_card(scenes[0], board) + f'<figcaption class="sr-only">Example decisions computed with the released models. {E(cap_sr)}</figcaption></figure>'
    trace_json = json.dumps({"scenes": scenes}, ensure_ascii=False)
    switch = "".join(f'<button type="button" aria-pressed="{"true" if i == 0 else "false"}">{E(short_id(s["model"]))}</button>' for i, s in enumerate(scenes))

    hero = f'''<section class="hero" id="top" aria-labelledby="hero-title">
  <div class="hero-bg" aria-hidden="true"><div class="blob b1"></div><div class="blob b2"></div><div class="grid"></div></div>
  <div class="wrap hero-grid">
    <div>
      <span class="eyebrow-chip"><b>v{VER}</b>open source</span>
      <h1 id="hero-title">Decisions that fit <span class="grad-text nw">on a chip.</span></h1>
      <p class="lede">Tiny decision models for agents, robots and microcontrollers. From 47 MB on a laptop to ~2 KB on a chip, with calibrated answers in the same shapes as Strands Decider.</p>
      {copy_block("copy copy-lg")}
      <div class="btn-row">
        <a class="btn btn-primary" href="{L["releases"]}">{ICON["download"]}Download models</a>
        <a class="btn btn-ghost" href="{L["repo"]}">{ICON["github"]}View on GitHub</a>
        <a class="text-link" href="{L["docs"]}">Read the docs {ARR}</a>
      </div>
      <p class="proof">{E(short_time(pico["esp32s3"]))} per decision on a $10 ESP32-S3. No GPU, no network, no model server.</p>
      <p class="footnote">{E(F["disclaimer"])}</p>
    </div>
    <div class="trace-wrap">
      {trace}
      <div class="trace-under"><div class="scene-switch" role="group" aria-label="Choose example">{switch}</div>
      <p class="trace-note">Probabilities computed with the released models; the C runtime on the ESP32-S3 gives the same answers. Times are measured on the board. <a href="benchmarks/">See Benchmarks</a>.</p></div>
      <script type="application/json" id="trace-data">{trace_json}</script>
    </div>
  </div>
</section>'''

    stats = "".join(f'<div class="stat"><dt>{E(h["label"])}</dt><dd>{E(h["value"]).replace(" ", "&nbsp;") if h["value"][:1].isdigit() else E(h["value"])}</dd></div>' for h in F["headline_numbers"])
    numbers = f'''<section class="numbers" id="numbers" aria-labelledby="numbers-title">
  <div class="wrap">
    <div class="numbers-head"><h2 id="numbers-title">Numbers first.</h2><p>Measured on an ESP32-S3 at 240 MHz and on a laptop. Every figure is on the Benchmarks page with its conditions.</p></div>
    <dl class="stats" aria-label="Headline measurements">{stats}</dl>
    <p class="more"><a class="text-link" href="benchmarks/">See every benchmark {ARR}</a></p>
  </div>
</section>'''

    # tiers
    groups = []
    for t in F["tiers"]:
        if not groups or groups[-1][0] != t["tier"]:
            groups.append([t["tier"], []])
        groups[-1][1].append(t)
    tabs, panels = [], []
    for i, (name, models) in enumerate(groups):
        ss = [size_parts(m["size"])[0] for m in sorted(models, key=lambda m: size_bytes(m["size"]))]
        sizes = ss[0] if len(ss) == 1 else ss[0] + " to " + ss[-1]
        tabs.append(f'<button class="tier-tab" role="tab" id="tt-{name}" data-tier="{name}" aria-controls="tp-{name}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{name}<small>{E(sizes)}</small></button>')
        panels.append(f'<div class="tier-panel{" n" + str(len(models)) if len(models) > 1 else ""}" role="tabpanel" id="tp-{name}" aria-labelledby="tt-{name}" tabindex="0"{"" if i == 0 else " hidden"}>' +
                      "".join(model_card(m, root) for m in models) + "</div>")
    # ruler
    def rx(b):
        return 24 + (math.log10(b) - 3) / 5 * 952
    ticks = "".join(f'<line class="tick" x1="{rx(10 ** e):.1f}" y1="44" x2="{rx(10 ** e):.1f}" y2="52"/><text class="tlabel{"" if e in (3, 6, 8) else " minor"}" x="{rx(10 ** e):.1f}" y="84" text-anchor="middle">{lab}</text>'
                    for e, lab in zip(range(3, 9), ["1 KB", "10 KB", "100 KB", "1 MB", "10 MB", "100 MB"]))
    dots, labels = [], []
    for name, models in groups:
        ms = sorted(models, key=lambda m: size_bytes(m["size"]))
        for j, m in enumerate(ms):
            x = rx(size_bytes(m["size"]))
            dots.append(f'<circle class="dot" data-tier="{name}" cx="{x:.1f}" cy="48" r="5"><title>{E(m["id"])}: {E(size_parts(m["size"])[0])}</title></circle>')
            if 0 < j < len(ms) - 1:
                continue
            anchor = "middle" if len(ms) == 1 else ("end" if j == 0 else "start")
            dx = 0 if len(ms) == 1 else (-4 if j == 0 else 4)
            labels.append(f'<text class="dlabel" data-tier="{name}" x="{x + dx:.1f}" y="20" text-anchor="{anchor}">{E(size_parts(m["size"])[0])}</text>')
    ruler = (f'<div class="ruler" id="ruler" aria-hidden="true"><svg viewBox="0 -14 1000 104" preserveAspectRatio="xMidYMid meet"><defs><linearGradient id="rg" x1="0" x2="1">'
             '<stop offset="0" stop-color="#FFB547"/><stop offset=".5" stop-color="#FF3D8B"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient></defs>'
             f'<line class="axis" x1="24" y1="48" x2="976" y2="48"/>{ticks}{"".join(dots)}{"".join(labels)}</svg></div>')
    tiers_sec = f'''<section class="section" id="tiers" aria-labelledby="tiers-title">
  <div class="wrap">
    <div class="sec-head reveal"><span class="eyebrow">The family</span><h2 id="tiers-title">From laptop to microcontroller.</h2><p>Pick the smallest model that fits your input and your hardware.</p></div>
    <div class="tier-tabs" role="tablist" aria-label="Model tiers" id="tier-tabs">{"".join(tabs)}</div>
    {ruler}
    {"".join(panels)}
    <p style="margin:24px 0 0"><a class="text-link" href="models/">Compare all models {ARR}</a></p>
  </div>
</section>'''

    # code
    ctabs = [("py", "Python", snippet("python", "triage.py", guide=L["python"], guide_text="Python guide")),
             ("cli", "CLI", snippet("cli", "terminal", guide=L["python"], guide_text="CLI and HTTP server")),
             ("c", "C", snippet("c", "main.c", guide=L["c"], guide_text="C library guide")),
             ("esp", "ESP32-S3", snippet("esp32", "main/app_main.c", guide=L["esp32"], guide_text="ESP32-S3 guide")),
             ("pico", "pico spec", snippet("pico_spec", "greenhouse.json") + '<div class="arrowlabel">pico_compile.py build</div>' +
              snippet("pico_c", "firmware/main.c", guide=L["pico"], guide_text="sparrow-pico guide"))]
    tab_btns = "".join(f'<button class="code-tab" role="tab" id="ct-{k}" aria-controls="cp-{k}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{n}</button>' for i, (k, n, _) in enumerate(ctabs))
    tab_panels = "".join(f'<div class="code-panel" role="tabpanel" id="cp-{k}" aria-labelledby="ct-{k}"{"" if i == 0 else " hidden"}>{c}</div>' for i, (k, n, c) in enumerate(ctabs))
    code_sec = f'''<section class="section" id="code" aria-labelledby="code-title">
  <div class="wrap code-layout">
    <div>
      <div class="sec-head reveal" style="margin-bottom:0"><span class="eyebrow">Use it</span><h2 id="code-title">Small questions. Calibrated answers.</h2>
      <p>Most decisions in an agent or a robot have a short list of answers. Sparrow answers them about a state you give it, with calibrated probabilities, in the same shapes as Strands Decider.</p></div>
      <ul class="qtypes">
        <li class="qtype"><span class="g">{ICON["toggle"]}</span><div><h3>Yes / no <code>noul</code></h3><p>"Is the user upset?" A probability you can threshold.</p></div></li>
        <li class="qtype"><span class="g">{ICON["radio"]}</span><div><h3>Pick one <code>choice</code></h3><p>"Which skill should run?" A choice from your list, with a probability for each option.</p></div></li>
        <li class="qtype"><span class="g">{ICON["scale"]}</span><div><h3>Score <code>score</code></h3><p>"How urgent is this?" A rating on the scale you define.</p></div></li>
      </ul>
    </div>
    <div class="codebox">
      <div class="code-tabs" role="tablist" aria-label="Code examples">{tab_btns}</div>
      {tab_panels}
    </div>
  </div>
</section>'''

    # pico or nano
    pn = {
        "questions": [
            {"html": "Are your inputs sensor values, and are the questions known at build time?", "short": "Sensor values, fixed questions?",
             "yes": {"r": 0, "edges": ["e-q1y"], "node": "n-pico"}, "no": {"q": 1, "edges": ["e-q1n"]}},
            {"html": "Do decisions hinge on numbers like <code>battery: 6%</code>?", "short": "Hinges on numbers?",
             "yes": {"r": 1, "edges": ["e-q1n", "e-q2y"], "node": "n-nr"}, "no": {"r": 2, "edges": ["e-q1n", "e-q2n"], "node": "n-ng"}},
        ],
        "results": [
            {"name": "sparrow-pico", "html": f'Compile a spec into C. {E(size_parts(pico["size"])[0])} per question. {E(short_time(pico["esp32s3"]))} per decision on an ESP32-S3. Runs on {E(pico["where"])}.',
             "links": f'<a href="{L["pico"]}">Read the pico guide {ARR}</a>'},
            {"name": "sparrow-nano-robot", "html": f'Reads <code>key: number</code> pairs as values. <code>{E(nr["id"])}</code> ships with pip: {E(nr["size"])}, {E(short_time(nr["esp32s3"]))} per decision on an ESP32-S3.' + (f' <code>{E(nr_fast["id"])}</code> is {E(nr_fast["size"])} and takes {E(short_time(nr_fast["esp32s3"]))}.' if nr_fast is not nr else ""),
             "links": f'<a href="{L["python"]}">Use from Python {ARR}</a>'},
            {"name": "sparrow-nano-general", "html": f'{E(ng["size"])}. General text decisions. {E(short_time(ng["esp32s3"]))} per decision on an ESP32-S3.',
             "links": f'<a href="{L["python"]}">Use from Python {ARR}</a><a href="#tiers" data-select-tier="micro">More breadth and the RAM? Try micro, tiny or small</a>'},
        ],
    }
    flow = f'''<figure class="flow" id="pn-flow"><svg class="dg" viewBox="0 0 640 372" role="img" aria-labelledby="pnf-t pnf-d">
<title id="pnf-t">pico or nano flowchart</title><desc id="pnf-d">If inputs are sensor values and questions are known at build time, use sparrow-pico. Otherwise, if decisions hinge on numbers like battery: 6%, use sparrow-nano-robot; if not, use sparrow-nano-general.</desc>
<path class="edge" id="e-q1y" d="M240 112 C285 112 285 76 324 76" marker-end="url(#ar)"/>
<path class="edge" id="e-q1n" d="M130 168 V222" marker-end="url(#ar)"/>
<path class="edge" id="e-q2y" d="M240 282 C285 282 285 232 324 232" marker-end="url(#ar)"/>
<path class="edge" id="e-q2n" d="M240 282 C285 282 285 324 324 324" marker-end="url(#ar)"/>
<polygon class="node" points="20,112 130,56 240,112 130,168"/>
<text class="title" x="130" y="100" text-anchor="middle">Sensor values,</text><text class="title" x="130" y="118" text-anchor="middle">questions fixed</text><text class="title" x="130" y="136" text-anchor="middle">at build time?</text>
<polygon class="node" id="n-q2" points="20,282 130,226 240,282 130,338"/>
<text class="title" x="130" y="272" text-anchor="middle">Decisions hinge</text><text class="title" x="130" y="290" text-anchor="middle">on numbers like</text><text class="lbl" x="130" y="308" text-anchor="middle">battery: 6%?</text>
<rect class="node node--accent" id="n-pico" x="328" y="40" width="292" height="72" rx="12"/>
<text class="title" x="348" y="70">sparrow-pico</text><text class="sub" x="348" y="92">{E(size_parts(pico["size"])[0])} per question · {E(short_time(pico["esp32s3"]))} · any MCU</text>
<rect class="node" id="n-nr" x="328" y="200" width="292" height="64" rx="12"/>
<text class="title" x="348" y="226">sparrow-nano-robot</text><text class="sub" x="348" y="247">{E(nr["size"])} · {E(short_time(nr["esp32s3"]))}{(" (v1.1) · " + E(short_time(nr_fast["esp32s3"])) + " (" + nr_fast["id"].rsplit("-", 1)[1] + ")") if nr_fast is not nr else " on ESP32-S3"}</text>
<rect class="node" id="n-ng" x="328" y="292" width="292" height="64" rx="12"/>
<text class="title" x="348" y="318">sparrow-nano-general</text><text class="sub" x="348" y="339">{E(ng["size"])} · {E(short_time(ng["esp32s3"]))} on ESP32-S3</text>
<rect class="lblbg" x="268" y="80" width="30" height="18" rx="4"/><text class="lbl" x="283" y="93" text-anchor="middle">yes</text>
<rect class="lblbg" x="140" y="186" width="26" height="18" rx="4"/><text class="lbl" x="153" y="199" text-anchor="middle">no</text>
<rect class="lblbg" x="268" y="238" width="30" height="18" rx="4"/><text class="lbl" x="283" y="251" text-anchor="middle">yes</text>
<rect class="lblbg" x="270" y="304" width="26" height="18" rx="4"/><text class="lbl" x="283" y="317" text-anchor="middle">no</text>
</svg></figure>'''
    pn_sec = f'''<section class="section" id="pico-or-nano" aria-labelledby="pn-title">
  <div class="wrap">
    <div class="sec-head reveal"><span class="eyebrow">Choosing</span><h2 id="pn-title">pico or nano?</h2><p>nano reads text and answers any question you pose at runtime. pico has no text and no vocabulary: you describe your device's sensors and questions, and get C.</p></div>
    <div class="pn-layout">
      <div><div class="widget" id="pn-widget" aria-live="polite"></div><p class="pn-both">Many devices use both: pico in the control loop, nano for anything said or written.</p></div>
      {flow}
    </div>
    <script type="application/json" id="pn-data">{json.dumps(pn, ensure_ascii=False)}</script>
  </div>
</section>'''

    # on chip
    pc = F["headline_numbers"][4]
    chip_sec = f'''<section class="section" id="on-chip" aria-labelledby="chip-title">
  <div class="wrap">
    <div class="sec-head reveal"><span class="eyebrow">On the chip</span><h2 id="chip-title">Every release got faster.</h2><p>{E(F["how_it_works"][3])}</p></div>
    {speed_rows()}
    <div class="strip">
      <div class="card"><div class="big">{E(pc["value"])}</div><p>{E(pc["label"])}</p></div>
      <div class="card"><h3>Python</h3><p><code>{E(F["install"])}</code>. numpy only.</p></div>
      <div class="card"><h3>C99</h3><p>No malloc, model read from flash. Ships as an ESP-IDF component.</p></div>
      <div class="card"><h3>sparrow-pico compiler</h3><p>Write a device spec, get a C header.</p></div>
    </div>
    <p style="margin:20px 0 0"><a class="text-link" href="architecture/#esp32">How the chip path works {ARR}</a></p>
  </div>
</section>'''

    limits_sec = f'''<section class="section" id="limits" aria-labelledby="limits-title">
  <div class="wrap">
    <div class="sec-head reveal"><span class="eyebrow">Honest limits</span><h2 id="limits-title">What it is not.</h2><p>Sparrow is for fixed-answer decisions about a known kind of state. We publish the misses next to the wins.</p></div>
    <div class="grid-3">{limits_cards()}</div>
    <div class="callout"><p><b>A pico model is as good as its teacher on your spec, and no better.</b> Never use a learned model as the only safety stop.</p>
    <p>Keep an LLM or a full decider for open-ended reasoning. Use <code>confidence</code> to fall back to it.</p></div>
    <p style="margin:20px 0 0"><a class="text-link" href="benchmarks/#limits">Read the limits {ARR}</a></p>
  </div>
</section>'''

    cta = f'''<section class="cta" id="get-started" aria-labelledby="cta-title">
  <div class="glow" aria-hidden="true"></div>
  <div class="wrap"><div class="inner">
    <h2 id="cta-title">Give your device <span class="grad-text">a decider.</span></h2>
    <p class="sub">Install in one line, or flash a model to a $10 board.</p>
    {copy_block("copy copy-lg")}
    <div class="btn-row">
      <a class="btn btn-primary" href="{L["releases"]}">{ICON["download"]}Download models</a>
      <a class="btn btn-ghost" href="{L["repo"]}">{ICON["github"]}View on GitHub</a>
      <a class="btn btn-ghost" href="{L["docs"]}">Read the docs</a>
    </div>
  </div></div>
</section>'''

    ld = {"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": F["name"], "codeRepository": REPO,
          "programmingLanguage": ["Python", "C"], "license": "https://www.apache.org/licenses/LICENSE-2.0", "version": VER, "description": F["what"],
          "author": {"@type": "Organization", "name": "the Sparrow Decider contributors"}}
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    body = "\n".join([hero, numbers, tiers_sec, '<hr class="hr">', code_sec, '<hr class="hr">', pn_sec, '<hr class="hr">', chip_sec, '<hr class="hr">', limits_sec, cta])
    return page("", root, "", "Sparrow Decider: decisions that fit on a chip",
                "Tiny decision models for agents, robots and microcontrollers. From 47 MB on a laptop to ~2 KB on a chip. 9.3 µs per decision on a $10 ESP32-S3.",
                body, extra_head=extra)


# ---------------------------------------------------------------- inner page helpers
def page_hero(eyebrow, h1, lede, cls=""):
    return f'''<section class="page-hero {cls}"><div class="wrap"><span class="eyebrow">{eyebrow}</span><h1>{h1}</h1><p class="lede">{lede}</p></div></section>'''


def inpage(items):
    return '<nav class="inpage" aria-label="On this page"><div class="wrap"><ul class="chips">' + "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in items) + "</ul></div></nav>"


def sec(id_, title, inner, lead=None):
    lp = f'<p class="lead-para">{lead}</p>' if lead else ""
    return f'<section class="page-sec" id="{id_}" aria-labelledby="{id_}-t"><div class="wrap"><h2 id="{id_}-t">{title}</h2>{lp}{inner}</div></section>'


# ---------------------------------------------------------------- MODELS
def models():
    root = "../"
    order = sorted(F["tiers"], key=lambda t: size_bytes(t["size"]))
    pico, ng, nr = tier("pico"), tier("nano-general"), tier("nano-robot")
    bodies = {
        pico["id"]: f'Numbers in, decision out. You write a spec of sensors, flags, enums, rules and questions, and the compiler writes one tiny MLP per question as a C header. It answers only the questions it was compiled for.',
        ng["id"]: f'Reads text and answers in {E(short_time(ng["esp32s3"]))} on an ESP32-S3. Good for routing and gating inside an agent when you want no network call.',
        nr["id"]: f'Reads states like <code>battery: 6%</code> as values, not words. Ships with pip. The earlier v1.0 (1.37 MB) scores 40/55 on RobotBench, the same as the public 2B.',
    }
    for t in F["tiers"]:
        if "nano-robot" in t["id"] and t["id"] != nr["id"]:
            bodies[t["id"]] = f'The fastest robot nano: {E(short_time(t["esp32s3"]))} per decision on an ESP32-S3. Reads <code>battery: 6%</code> as a value. Download it from the releases page.' if "fastest" in t.get("quality", "") else "Reads states like <code>battery: 6%</code> as values, not words."
    acts = {
        pico["id"]: ext_link(L["pico"], "Read the pico guide"),
        ng["id"]: ext_link(L["esp32"], "Read the ESP32-S3 guide") + ext_link(L["releases"], "Download"),
        nr["id"]: ext_link(L["esp32"], "Read the robot guide") + ext_link(L["releases"], "Download"),
    }
    for t in F["tiers"]:
        acts.setdefault(t["id"], ext_link(L["esp32"], "Read the ESP32-S3 guide") + ext_link(L["releases"], "Download") if t["tier"] == "nano" else None)
    cards = "".join(model_card(t, root, bodies.get(t["id"], "More room, more reach: a text model for a Raspberry Pi, a laptop or a Jetson."),
                               acts.get(t["id"]) or (ext_link(L["python"], "Read the Python guide") + ext_link(L["releases"], "Download"))) for t in order)
    rows = []
    for t in F["tiers"]:
        rows.append(f'<tr class="ours"><td>{t["tier"]}</td><td class="sticky"><span class="id">{E(t["id"])}</span></td><td>{E(t["size"])}</td><td>{E(t["input"])}</td><td>{E(t["where"])}</td>'
                    f'<td class="r">{E(short_time(t["esp32s3"])) if t.get("esp32s3") else DASH}</td><td class="r">{E(t["laptop"]) if t.get("laptop") else DASH}</td><td>{E(t["quality"]) if t.get("quality") else DASH}</td></tr>')
    tbl = table([("Tier", ""), ("Model ID", "sticky"), ("Size", ""), ("Input", ""), ("Runs on", ""), ("ESP32-S3", "r"), ("Laptop", "r"), ("Quality", "")], rows,
                "The Sparrow Decider family. Timings are measured; blank cells were not measured.", "wide", "Model comparison table")
    which = '''<ul class="prose" style="padding-left:20px">
<li>Your input is sensor numbers and the questions never change → <strong>pico</strong></li>
<li>Your input is text and the device is an ESP32-S3 → <strong>nano-general</strong></li>
<li>Your input mixes text and sensor readings → <strong>nano-robot</strong></li>
<li>You have a Pi, a laptop or a Jetson and want more headroom → <strong>micro</strong>, <strong>tiny</strong> or <strong>small</strong></li></ul>'''
    bundled = " and ".join(f"<code>{E(b)}</code>" for b in F.get("bundled_in_pip", []))
    dl = f'''<div class="grid-3">
<div class="card"><span class="eyebrow">pip</span><h3 style="font-size:20px">nano, bundled</h3><p class="muted" style="margin:10px 0 16px">numpy only. The package bundles {bundled}; load them with <code>Decider.load()</code>.</p>{copy_block()}<p style="margin:10px 0 0">{ext_link(L["python"], "Python guide")}</p></div>
<div class="card"><span class="eyebrow">GitHub releases</span><h3 style="font-size:20px">micro, tiny, small</h3><p class="muted" style="margin:10px 0 16px">Put the <code>.sparrow</code> files in <code>~/.cache/sparrow-decider/</code> (or any folder in <code>$SPARROW_MODELS</code>) to load them by name.</p><a class="btn btn-primary" href="{L["releases"]}">{ICON["download"]}Download models</a></div>
<div class="card"><span class="eyebrow">Compile</span><h3 style="font-size:20px">pico</h3><p class="muted" style="margin:10px 0 16px">pico models are compiled for your device from a spec.</p><p style="margin:0">{ext_link(L["pico"], "sparrow-pico guide")}</p><p style="margin:0">{ext_link(L["c"], "C runtime and ESP-IDF component")}</p></div>
</div>'''
    mc = f'''<div class="grid-2" style="align-items:start">
<dl class="spec" style="margin:0;grid-template-columns:minmax(0,130px) minmax(0,1fr);font-size:15.5px">
<dt>What it does</dt><dd>Answers <code>noul</code> (yes/no), <code>choice</code> (pick one) and <code>score</code> (rate on a scale) questions about a state, with calibrated probabilities, in the same shapes as Strands Decider.</dd>
<dt>Teachers</dt><dd>{E(F["how_it_works"][0])} pico models are labelled by the public Strands Decider 2B on sampled device states.</dd>
<dt>Base weights</dt><dd>micro and nano from potion-base-8M (MinishLab, MIT); tiny and small from Ettin encoders (JHU CLSP, MIT).</dd>
<dt>Runtimes</dt><dd>{E("; ".join(F["runtimes"])).replace("-&gt;", "→")}.</dd>
<dt>Calibration</dt><dd>Each model ships per-kind temperatures fitted on held-out data. A yes/no answer near 0.5 means "don't know".</dd>
<dt>Licence</dt><dd>{E(F["license"])}.</dd></dl>
<div class="callout" style="margin:0"><p><b>Limitations</b></p><ul>{"".join("<li>" + E(x) + "</li>" for x in F["honest_limits"])}<li>These models suggest decisions. Don't use them as the only safety mechanism on a physical system.</li></ul></div>
</div><p style="margin:20px 0 0">{ext_link(L["modelcard"], "Full model card")}</p>'''
    body = (page_hero("Models", "Pick the smallest bird that does the job.", "Every model answers yes/no, pick-one and score questions with calibrated probabilities. They differ in input, size and where they run.") +
            inpage([("family", "Family"), ("compare", "Compare"), ("which", "Which one?"), ("download", "Download"), ("model-card", "Model card")]) +
            sec("family", "The family", f'<div class="grid-3">{cards}</div>', "Smallest first. Every field comes from a measurement; fields we have not measured are left out.") +
            sec("compare", "Compare", tbl + f'<p class="tnote">Laptop times are per question on one CPU core, with the runtime in brackets. See <a href="../benchmarks/#method">Benchmarks</a> for methodology.</p>') +
            sec("which", "Which one?", which) +
            sec("download", "Get the models", dl) +
            sec("model-card", "Model card", mc))
    return page("models/", root, "models/", "Models · Sparrow Decider", "Decision models from 47 MB to ~2 KB per question. Pick by input, hardware and time budget.", body)


# ---------------------------------------------------------------- ARCHITECTURE
def pipeline_svgs():
    ng, nr, mi, ti, sm, pico = tier("nano-general"), tier("nano-robot"), tier("micro"), tier("tiny"), tier("small"), tier("pico")
    nz = sorted((t["size"] for t in F["tiers"] if t["tier"] == "nano"), key=size_bytes)
    nano_sz = nz[0] if len(nz) == 1 else f"{nz[0]} to {nz[-1]}"
    enc_sz = f'{ti["size"]} / {sm["size"]}'
    defs = ''

    def node(x, y, w, h, t, s, accent=False):
        return (f'<rect class="node{" node--accent" if accent else ""}" x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/>'
                f'<text class="title" x="{x + 16}" y="{y + h / 2 - 3}">{E(t)}</text><text class="sub" x="{x + 16}" y="{y + h / 2 + 15}">{E(s)}</text>')

    desk = f'''<svg viewBox="0 0 1120 420" role="img" aria-labelledby="pl-t pl-d">{defs}
<title id="pl-t">Distillation pipeline</title><desc id="pl-d">Strands Decider 4B teaches nano, micro, tiny and small through distillation on ~430k decisions; they run on Python numpy or the C99 runtime. Strands Decider 2B labels sampled device states for the sparrow-pico compiler, which writes a C header.</desc>
<text class="cap" x="40" y="24">TEACHERS</text><text class="cap" x="300" y="24">DISTILLATION</text><text class="cap" x="580" y="24">TIERS</text><text class="cap" x="860" y="24">RUNTIMES</text>
<path class="edge" d="M240 116 H296" marker-end="url(#ar)"/>
<path class="edge" d="M520 116 C550 116 550 76 576 76" marker-end="url(#ar)"/><path class="edge" d="M520 116 C550 116 550 144 576 144" marker-end="url(#ar)"/><path class="edge" d="M520 116 C550 116 550 212 576 212" marker-end="url(#ar)"/>
<path class="edge" d="M800 76 C830 76 830 76 856 76" marker-end="url(#ar)"/><path class="edge" d="M800 76 C830 76 830 172 856 172" marker-end="url(#ar)"/>
<path class="edge" d="M800 144 C830 144 830 84 856 84" marker-end="url(#ar)"/><path class="edge" d="M800 144 C830 144 830 164 856 164" marker-end="url(#ar)"/>
<path class="edge" d="M800 212 C836 212 836 92 856 92" marker-end="url(#ar)"/>
<path class="edge edge--accent flowing" d="M240 336 H296" marker-end="url(#ara)"/><path class="edge edge--accent flowing" d="M520 336 H576" marker-end="url(#ara)"/><path class="edge edge--accent flowing" d="M800 336 H856" marker-end="url(#ara)"/>
<rect class="lblbg" x="248" y="94" width="44" height="16" rx="3"/><text class="lbl" x="270" y="106" text-anchor="middle">soft</text>
<rect class="lblbg" x="248" y="314" width="44" height="16" rx="3"/><text class="lbl" x="270" y="326" text-anchor="middle">labels</text>
{node(40, 80, 200, 72, "Strands Decider 4B", "teacher")}
{node(40, 300, 200, 72, "Strands Decider 2B", "public", True)}
{node(300, 80, 220, 72, "Distillation", "~430k decisions")}
{node(300, 300, 220, 72, "Label sampled states", "from your device spec", True)}
{node(580, 48, 220, 56, "nano", nano_sz + " · static")}
{node(580, 116, 220, 56, "micro", mi["size"] + " · static")}
{node(580, 184, 220, 56, "tiny · small", enc_sz + " · encoder")}
{node(580, 300, 220, 72, "sparrow-pico compiler", "one MLP per question", True)}
{node(860, 48, 220, 56, "Python", "numpy only")}
{node(860, 136, 220, 72, "C99 runtime", "no malloc · model in flash")}
{node(860, 300, 220, 72, "C header", size_parts(pico["size"])[0] + " per question", True)}
</svg>'''

    def vnode(y, t, s, accent=False, x=30, w=300, h=60):
        return node(x, y, w, h, t, s, accent)

    mob = f'''<svg viewBox="0 0 360 860" role="img" aria-labelledby="plm-t"><title id="plm-t">Distillation pipeline, stacked</title>{defs}
<text class="cap" x="30" y="20">TEXT TIERS</text>
{vnode(32, "Strands Decider 4B", "teacher")}
<path class="edge" d="M180 92 V114" marker-end="url(#ar)"/>
{vnode(116, "Distillation", "~430k decisions")}
<path class="edge" d="M180 176 V198" marker-end="url(#ar)"/>
{node(30, 200, 300, 52, "nano", nano_sz)}{node(30, 258, 300, 52, "micro", mi["size"])}{node(30, 316, 300, 52, "tiny · small", enc_sz)}
<path class="edge" d="M180 368 V390" marker-end="url(#ar)"/>
{node(30, 392, 145, 60, "Python", "numpy only")}{node(185, 392, 145, 60, "C99", "no malloc")}
<text class="cap" x="30" y="500">PICO</text>
{vnode(512, "Strands Decider 2B", "public", True)}
<path class="edge edge--accent" d="M180 572 V594" marker-end="url(#ara)"/>
{vnode(596, "Label sampled states", "from your device spec", True)}
<path class="edge edge--accent" d="M180 656 V678" marker-end="url(#ara)"/>
{vnode(680, "sparrow-pico compiler", "one MLP per question", True)}
<path class="edge edge--accent" d="M180 740 V762" marker-end="url(#ara)"/>
{vnode(764, "C header", size_parts(pico["size"])[0] + " per question", True)}
</svg>'''
    return desk, mob


def kv_svgs():
    defs = ''

    def node(x, y, w, h, t, s="", accent=False):
        if s:
            txt = f'<text class="title" x="{x + w / 2}" y="{y + h / 2 - 3}" text-anchor="middle">{E(t)}</text><text class="sub" x="{x + w / 2}" y="{y + h / 2 + 15}" text-anchor="middle">{E(s)}</text>'
        else:
            txt = f'<text class="title" x="{x + w / 2}" y="{y + h / 2 + 5}" text-anchor="middle">{E(t)}</text>'
        return f'<rect class="node{" node--accent" if accent else ""}" x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/>{txt}'

    vec = lambda x, y, cls: "".join(f'<rect class="{cls}" x="{x + i * 13}" y="{y}" width="10" height="10" rx="2" opacity="{0.25 + (i * 37 % 7) / 9:.2f}"/>' for i in range(8))
    state = ('<rect class="card-bg" x="20" y="70" width="230" height="130" rx="12"/><text class="lbl" x="36" y="96">state</text>'
             '<text class="mono" x="36" y="124"><tspan class="monok">battery: </tspan>6%</text><text class="mono" x="36" y="150"><tspan class="monok">front_obstacle_m: </tspan>7.0</text>'
             '<text class="mono" x="36" y="176"><tspan class="monok">path: </tspan>clear</text>')
    desk = f'''<svg viewBox="0 0 1000 290" role="img" aria-labelledby="kv-t kv-d">{defs}<title id="kv-t">Inside nano</title>
<desc id="kv-d">Text in becomes tokens and static embeddings of 128 dimensions. Number pooling builds one vector per key: number pair, so battery: 6% is read as a value. A decision head turns both into probabilities.</desc>
{state}
<path class="edge" d="M250 110 C280 110 280 70 306 70" marker-end="url(#ar)"/><path class="edge edge--accent flowing" d="M250 160 C280 160 280 210 306 210" marker-end="url(#ar)"/>
{node(310, 40, 150, 60, "tokens", "static embeddings")}
{node(310, 180, 150, 60, "number pooling", "key: number pairs", True)}
<path class="edge" d="M460 70 H496" marker-end="url(#ar)"/>
{node(500, 40, 150, 60, "mean pool", "128-d")}
<path class="edge edge--accent" d="M460 210 H496" marker-end="url(#ar)"/>
<rect class="node node--accent" x="500" y="180" width="150" height="60" rx="12"/><text class="title" x="575" y="206" text-anchor="middle">battery × f(6%)</text><g transform="translate(523 216)">{vec(0, 0, "sq")}</g>
<path class="edge" d="M650 70 C690 70 690 130 726 130" marker-end="url(#ar)"/><path class="edge edge--accent" d="M650 210 C690 210 690 150 726 150" marker-end="url(#ar)"/>
{node(730, 100, 160, 80, "decision head", "+ question, options")}
<path class="edge" d="M890 140 H916" marker-end="url(#ar)"/>
<g transform="translate(922 104)"><rect class="sq" x="0" y="0" width="56" height="10" rx="3"/><rect class="sq2" x="0" y="18" width="14" height="10" rx="3"/><rect class="sq2" x="0" y="36" width="8" height="10" rx="3"/><rect class="sq2" x="0" y="54" width="20" height="10" rx="3"/></g>
<text class="lbl" x="950" y="190" text-anchor="middle">probabilities</text>
</svg>'''
    mob = f'''<svg viewBox="0 0 360 620" role="img" aria-labelledby="kvm-t"><title id="kvm-t">Inside nano, stacked</title>{defs}
<g transform="translate(45 -50)">{state}</g>
<path class="edge" d="M110 152 V184" marker-end="url(#ar)"/><path class="edge edge--accent" d="M250 152 V184" marker-end="url(#ar)"/>
{node(30, 186, 145, 60, "tokens", "static embeddings")}{node(185, 186, 145, 60, "number pooling", "key: number", True)}
<path class="edge" d="M102 246 V276" marker-end="url(#ar)"/><path class="edge edge--accent" d="M257 246 V276" marker-end="url(#ar)"/>
{node(30, 278, 145, 60, "mean pool", "128-d")}{node(185, 278, 145, 60, "battery × f(6%)", "a value, not a token", True)}
<path class="edge" d="M102 338 C102 370 170 360 176 384" marker-end="url(#ar)"/><path class="edge edge--accent" d="M257 338 C257 370 190 360 184 384" marker-end="url(#ar)"/>
{node(80, 386, 200, 70, "decision head", "+ question, options")}
<path class="edge" d="M180 456 V484" marker-end="url(#ar)"/>
<g transform="translate(120 492)"><rect class="sq" x="0" y="0" width="120" height="12" rx="3"/><rect class="sq2" x="0" y="20" width="30" height="12" rx="3"/><rect class="sq2" x="0" y="40" width="16" height="12" rx="3"/><rect class="sq2" x="0" y="60" width="44" height="12" rx="3"/></g>
<text class="lbl" x="180" y="600" text-anchor="middle">probabilities</text>
</svg>'''
    return desk, mob


def architecture():
    root = "../"
    pico = tier("pico")
    pd, pm = pipeline_svgs()
    kd, km = kv_svgs()
    distil = (f'<figure class="diagram dg"><div class="dg-desktop">{pd}</div><div class="dg-mobile">{pm}</div>'
              f'<figcaption>{E(F["how_it_works"][0])} For pico, the public Strands Decider 2B labels sampled states from your device spec, and the compiler writes C.</figcaption></figure>')
    nano = (f'<figure class="diagram dg"><div class="dg-desktop">{kd}</div><div class="dg-mobile">{km}</div>'
            '<figcaption>Mean-pooled words lose which number belongs to which key. nano also builds one vector per <code>key: number</code> pair, so <code>battery: 6%</code> is read as a value, not just a token.</figcaption></figure>')
    sz = size_parts(pico["size"])
    steps = [("{ }", "Write a spec", "sensors, rules, questions", False), ("· ·", "Sample states", "from your sensor ranges", False),
             ("2B", "Label", "public Strands Decider 2B", False), ("MLP", "Train", "one tiny MLP per question", False),
             (".h", "Emit C", f'{sz[0]} {sz[1]}', True)]
    st = "".join(f'<li class="step{" accent" if a else ""}"><span class="no">{i + 1}</span><span class="gl" aria-hidden="true">{E(g)}</span><h3>{E(t)}</h3><p>{E(s)}</p></li>' for i, (g, t, s, a) in enumerate(steps))
    pico_html = (f'<ol class="steps">{st}</ol><div class="ribbon"><span>{E(pico["esp32s3"])} on ESP32-S3</span><span>{E(pico["laptop"])} on a laptop</span></div>'
                 f'<div class="grid-2" style="margin-top:28px;align-items:start"><div class="codebox"><div class="code-panel">{snippet("pico_spec", "greenhouse.json", cid="a-spec")}</div></div>'
                 f'<div class="stack"><div class="codebox"><div class="code-panel">{snippet("pico_c", "firmware/main.c", cid="a-c")}</div></div>'
                 f'<div class="codebox"><div class="code-panel">{snippet("pico_cmds", "terminal", cid="a-cmd", guide=L["pico"], guide_text="sparrow-pico guide")}</div></div></div></div>'
                 f'<p class="lead-para" style="margin-top:24px"><strong>{E(pico["quality"])}.</strong> A pico model is as good as its teacher on your spec, and no better.</p>')
    hw = F["board"]
    mhz = re.search(r"(\d+ MHz)", hw).group(1)
    flash = re.search(r"(\d+ MB flash)", hw).group(1)
    psram = re.search(r"(\d+ MB PSRAM)", hw).group(1)
    layers = f'''<ol class="layers" aria-label="ESP32-S3 software stack, top to bottom">
<li class="layer"><h3>Your firmware</h3><span class="d">app_main() · sparrow_choice(...)</span></li>
<li class="layer"><h3>sparrow C99 runtime</h3><span class="d">no malloc · model read from flash</span></li>
<li class="layer accent"><h3>int8 SIMD kernels</h3><span class="d">ESP-NN on the vector unit</span></li>
<li class="layer accent"><h3>Memory placement</h3><span class="d">weights in PSRAM / internal RAM</span></li>
<li class="layer hw"><h3>ESP32-S3</h3><span class="d">{E(mhz)} · {E(flash)} · {E(psram)}</span></li></ol>'''
    esp = (f'<div class="esp-layout"><div>{layers}<p class="mono-line" style="margin-top:14px">{E(F["board"])}</p>'
           f'<p class="lead-para" style="margin:14px 0 0">On-chip answers matched the host runtime <strong class="nw">{E(F["headline_numbers"][4]["value"])}</strong>.</p>'
           f'<p style="margin:8px 0 0">{ext_link(L["esp32"], "Flash it yourself")}</p></div><div>{speed_rows()}</div></div>')
    rt = table([("Runtime", ""), ("What you get", "")],
               ['<tr><td><strong>Python</strong></td><td>numpy only</td></tr>', '<tr><td><strong>C99</strong></td><td>no malloc, model read from flash, ESP-IDF component</td></tr>',
                '<tr><td><strong>sparrow-pico compiler</strong></td><td>device spec in, C header out</td></tr>'], "Runtimes.", "mid", "Runtimes")
    contract = table([("type", ""), ("criteria", ""), ("answer", "")],
                     ['<tr><td><code>noul</code></td><td>optional <code>{"false": ..., "true": ...}</code></td><td><code>{"noul": P(true)}</code></td></tr>',
                      '<tr><td><code>choice</code></td><td><code>{name: description}</code>, 2 or more</td><td><code>{"choice", "probabilities", "confidence"}</code></td></tr>',
                      '<tr><td><code>score</code></td><td>list of 2-10 levels, lowest first</td><td><code>{"score": expected level, "legend", "probabilities", "confidence"}</code></td></tr>'],
                     f'Question types and answer shapes, from the <a href="{L["python"]}">Python guide</a>.', "wide", "Question contract")
    body = (page_hero("Architecture", "Big teacher. Small student. Plain C.", "How a 4B decider's judgement ends up in a few KB of firmware.", "ph-arch") +
            inpage([("distillation", "Distillation"), ("nano", "nano"), ("pico", "pico"), ("esp32", "On the chip"), ("runtimes", "Runtimes")]) +
            sec("distillation", "Taught by a full Strands Decider", distil, f'{E(F["how_it_works"][0])} The students keep the same question shapes, so a schema written for Strands Decider works here.') +
            sec("nano", "Static embeddings that can read a number", nano, 'nano uses static embeddings over a pruned 8-16k vocabulary at 128 dimensions. Key-value number pooling reads <code>battery: 6%</code> as a value, so sensor readings in text are not just tokens.') +
            sec("pico", "A compiler, not a model download", pico_html, "You write a spec: sensors, rules and questions. The public Strands Decider 2B labels sampled states. The compiler writes one tiny MLP per question as C. Your firmware includes the header and calls a function.") +
            sec("esp32", "Built for the ESP32-S3", esp, "int8 SIMD on the vector unit through the ESP-NN kernel, with weights in PSRAM or internal RAM. The C99 runtime has no malloc and reads the model from flash.") +
            sec("runtimes", "Three runtimes, one contract", '<div class="stack">' + rt + contract + f'<p class="lead-para" style="margin:0"><code>sparrow-decider serve</code> exposes <code>POST /v1/systemone</code>, following the Strands Decider <code>/v1/systemone</code> contract.</p><p style="margin:0">{ext_link(L["report"], "Research report")}</p></div>'))
    return page("architecture/", root, "architecture/", "Architecture · Sparrow Decider",
                "Distillation from a 4B Strands Decider, static embeddings with number pooling, and a compiler that turns a device spec into C.", body)


# ---------------------------------------------------------------- BENCHMARKS (RESULTS.md rows for released IDs)
REF4, REF2 = "Strands Decider 4B (teacher)", "Strands Decider 2B (public)"
BENCH = {
    # RobotBench v0: name, right/55, skill/15, nav/10, check/12, recover/10, urgency/8, ref
    "robot": [(REF4, 46, "14/15", "6/10", "10/12", "10/10", "6/8", True), (REF2, 40, "15/15", "3/10", "10/12", "10/10", "2/8", True),
              ("sparrow-nano-robot-v1.0", 40, "11/15", "10/10", "10/12", "6/10", "3/8", False), ("sparrow-nano-robot-v1.1", 38, "9/15", "10/10", "10/12", "6/10", "3/8", False),
              ("sparrow-nano-robot-v1.2", 36, "10/15", "8/10", "10/12", "6/10", "2/8", False),
              ("sparrow-nano-general-v1.1", 32, "10/15", "4/10", "9/12", "7/10", "2/8", False), ("sparrow-micro-general-v1.1", 30, "10/15", "5/10", "7/12", "6/10", "2/8", False),
              ("sparrow-small-general-v1.0", 24, "7/15", "2/10", "7/12", "5/10", "3/8", False), ("sparrow-tiny-general-v1.0", 20, "7/15", "2/10", "6/12", "3/10", "2/8", False)],
    # MASSIVE: name, domain, intent, ref
    "massive": [(REF2, "0.86", "0.871", True), ("sparrow-small-general-v1.0", "0.673", "0.599", False), ("sparrow-micro-general-v1.1", "0.635", "0.542", False),
                ("sparrow-nano-robot-v1.0", "0.52", "0.494", False), ("sparrow-nano-robot-v1.1", "0.515", "0.485", False), ("sparrow-nano-robot-v1.2", "0.518", "0.522", False), ("sparrow-nano-general-v1.1", "0.5", "0.588", False),
                ("sparrow-tiny-general-v1.0", "0.368", "0.592", False)],
    # JevBench public: name, right/231
    "jev": [("sparrow-tiny-general-v1.0", "123/231"), ("sparrow-nano-general-v1.1", "122/231"), ("sparrow-small-general-v1.0", "122/231"),
            ("sparrow-micro-general-v1.1", "117/231"), ("sparrow-nano-robot-v1.2", "115/231"), ("sparrow-nano-robot-v1.0", "113/231"), ("sparrow-nano-robot-v1.1", "105/231")],
    # C runtime parity on the host: name, cases, argmax agree, max prob diff
    "parity": [("sparrow-nano-robot-v1.1", "286", "286/286", "2e-06"), ("sparrow-nano-robot-v1.2", "286", "286/286", "2e-06"), ("sparrow-nano-general-v1.1", "286", "286/286", "1e-06"), ("sparrow-micro-general-v1.1", "586", "586/586", "3e-06")],
}


def benchmarks():
    root = "../"
    cite = f'Source: <a href="{L["results"]}">bench/RESULTS.md</a>. Local runs.'
    chip_t = [t for t in F["tiers"] if t.get("esp32s3")]
    lap_t = [t for t in F["tiers"] if t.get("laptop")]
    chip_tbl = table([("Model", "sticky"), ("Size", ""), ("Time per decision", "r")],
                     [f'<tr class="ours"><td class="sticky"><span class="id">{E(t["id"])}</span></td><td>{E(size_parts(t["size"])[0])}</td><td class="r">{E(short_time(t["esp32s3"]))}</td></tr>' for t in chip_t],
                     f'Measured on the board: {E(F["board"])}.', "mid", "ESP32-S3 timings")
    lo = math.log10(min(to_us(t["esp32s3"]) for t in chip_t)) - 0.6
    chip_chart = hbar_chart([(t["id"], size_parts(t["size"])[0], to_us(t["esp32s3"]), short_time(t["esp32s3"]), False) for t in chip_t],
                            max(to_us(t["esp32s3"]) for t in chip_t), log=True, lo=lo)
    chip = (f'<div class="grid-2" style="align-items:start">{chip_tbl}<figure class="chart"><h3>Time per decision on an ESP32-S3</h3>{chip_chart}'
            f'<p class="axis-cap">Log scale: pico is in µs, nano in ms. Every bar carries its unit.</p><figcaption class="sr-only">Same data as the table.</figcaption></figure></div>')
    lap_tbl = table([("Model", "sticky"), ("Time per question", "r")],
                    [f'<tr class="ours"><td class="sticky"><span class="id">{E(t["id"])}</span></td><td class="r">{E(t["laptop"])}</td></tr>' for t in lap_t],
                    "One CPU core on a laptop, per question. The runtime (C or numpy) is in brackets.", "mid", "Laptop timings")
    lo2 = math.log10(min(to_us(t["laptop"]) for t in lap_t)) - 0.6
    lap_chart = hbar_chart([(t["id"], "", to_us(t["laptop"]), t["laptop"], False) for t in lap_t], max(to_us(t["laptop"]) for t in lap_t), log=True, lo=lo2)
    laptop = f'<div class="grid-2" style="align-items:start">{lap_tbl}<figure class="chart"><h3>Time per question on a laptop</h3>{lap_chart}<p class="axis-cap">Log scale. Values span 0.18 µs to 64 ms.</p></figure></div>'
    nr, ng, pico = tier("nano-robot"), tier("nano-general"), tier("pico")
    hn = F["headline_numbers"][2]
    quality = f'''<div class="tiles">
<div class="card tile"><h3>Robot decisions (RobotBench)</h3><div class="vs"><div><div class="big">40/55</div><p>sparrow-nano-robot-v1.0 (1.37 MB)</p></div><div><div class="big">40/55</div><p>public 2B Strands Decider</p></div></div><p>{E(hn["value"])} {E(hn["label"])}. nano-robot v1.1 ({E(nr["size"])}) scores 38/55.</p></div>
<div class="card tile"><h3>Navigation from sensor numbers</h3><div class="vs"><div><div class="big">10/10</div><p>sparrow-nano-robot-v1.1</p></div><div><div class="big">3/10</div><p>public 2B Strands Decider</p></div></div><p>{E(nr["quality"])}.</p>{"".join("<p>" + E(t["id"]) + ": " + E(t["quality"]) + ".</p>" for t in F["tiers"] if "nano-robot" in t["id"] and t["id"] != nr["id"] and t.get("quality"))}</div>
<div class="card tile"><h3>pico vs its spec's rules</h3><div class="vs"><div><div class="big">94.0%</div><p>{E(pico["id"])}</p></div><div><div class="big">94.2%</div><p>its 2B teacher</p></div></div><p>{E(pico["quality"])}.</p></div>
<div class="card tile"><h3>General text</h3><p style="margin:0">{E(ng["id"])}: {E(ng["quality"].split("; ", 1)[-1])}.</p><p>Yes/no judgement on JevBench is near chance at every tier.</p></div>
</div>'''
    # RobotBench
    rb_rows = [f'<tr class="{"ref" if r[7] else "ours"}"><td class="sticky"><span class="id">{E(r[0])}</span></td><td class="r"><strong>{r[1]}/55</strong></td>' +
               "".join(f'<td class="r">{x}</td>' for x in r[2:7]) + "</tr>" for r in BENCH["robot"]]
    rb_tbl = table([("Model", "sticky"), ("Right", "r"), ("skill", "r"), ("nav", "r"), ("check", "r"), ("recover", "r"), ("urgency", "r")], rb_rows,
                   "RobotBench v0: 55 robot decisions written by hand, separately from the robot training generator. " + cite, "wide", "RobotBench results")
    rb_chart = hbar_chart([(r[0], "", r[1], f"{r[1]}/55", r[7]) for r in BENCH["robot"]], 55, marker=40)
    robot = (f'<figure class="chart" style="margin-bottom:20px"><h3>Right answers out of 55</h3><div class="hc-legend" aria-hidden="true"><span><i style="background:var(--grad)"></i>Sparrow models</span><span><i style="background:var(--ref-hatch)"></i>Strands Decider reference</span><span><span class="dl"></span>public 2B (40)</span></div>{rb_chart}'
             f'<p class="axis-cap">Linear scale, 0 to 55.</p></figure>{rb_tbl}<p class="tnote">55 items: each item moves the score by one. Small differences between models are within run-to-run noise.</p>')
    ms_rows = [f'<tr class="{"ref" if r[3] else "ours"}"><td class="sticky"><span class="id">{E(r[0])}</span></td><td class="r">{r[1]}</td><td class="r">{r[2]}</td></tr>' for r in BENCH["massive"]]
    ms_tbl = table([("Model", "sticky"), ("Domain (18 options)", "r"), ("Intent within domain", "r")], ms_rows,
                   "Amazon MASSIVE 1.1 en-US test, 600 utterances, held out of training. Evaluation only (CC BY 4.0). " + cite, "mid", "MASSIVE results")
    ms_chart = hbar_chart([(r[0], "", float(r[1]), r[1], r[3]) for r in BENCH["massive"]], 1.0)
    massive = f'<div class="stack"><figure class="chart"><h3>Domain routing accuracy</h3><div class="hc-legend" aria-hidden="true"><span><i style="background:var(--grad)"></i>Sparrow models</span><span><i style="background:var(--ref-hatch)"></i>Strands Decider reference</span></div>{ms_chart}<p class="axis-cap">Linear scale, 0 to 1.</p></figure>{ms_tbl}</div>'
    jv = table([("Model", "sticky"), ("Right (of 231)", "r")],
               [f'<tr class="ours"><td class="sticky"><span class="id">{E(r[0])}</span></td><td class="r">{r[1]}</td></tr>' for r in BENCH["jev"]],
               "JevBench public tasks, local v1.5 proxy: not leaderboard scores. Evaluation only (MIT). " + cite, "mid", "JevBench results")
    jev = f'<div class="grid-2" style="align-items:start">{jv}<div class="callout" style="margin:0"><p><b>Read with care.</b> These are local proxy scores on the public tasks. Yes/no judgement on JevBench is near chance at every tier, so use a full decider or an LLM for yes/no judgement calls.</p></div></div>'
    par = table([("Model", "sticky"), ("Cases", "r"), ("Argmax agree", "r"), ("Max prob diff", "r")],
                [f'<tr class="ours"><td class="sticky"><span class="id">{E(r[0])}</span></td><td class="r">{r[1]}</td><td class="r">{r[2]}</td><td class="r">{r[3]}</td></tr>' for r in BENCH["parity"]],
                "C runtime vs numpy on the host, one core. " + cite, "mid", "C runtime parity")
    hp = F["headline_numbers"][4]
    parity = (f'<div class="grid-2" style="align-items:start"><div class="stack"><div class="card tile"><h3>On the chip</h3><div class="big">{E(hp["value"])}</div><p>{E(hp["label"])}.</p></div>'
              f'<div class="codebox"><div class="code-panel"><div class="bar"><span>check parity on your machine</span><button class="copy-btn" type="button" data-copy-target="par-cmd" aria-label="Copy parity command">{ICON["copy"]}<span class="label">Copy</span></button></div>'
              f'<pre class="code" tabindex="0"><code id="par-cmd">python c/tests/parity.py MODEL</code></pre></div></div></div>{par}</div>')
    method = f'''<ul class="prose" style="padding-left:20px">
<li><strong>RobotBench v0:</strong> 55 robot decisions written by hand, separately from the robot training generator.</li>
<li><strong>MASSIVE:</strong> Amazon MASSIVE 1.1 en-US test, 600 utterances, never trained on. Evaluation only (CC BY 4.0).</li>
<li><strong>JevBench:</strong> public tasks, local v1.5 proxy, not leaderboard scores. Evaluation only (MIT).</li>
<li><strong>Laptop timings:</strong> local runs, one CPU core, per question; the runtime (C or numpy) is named next to each value.</li>
<li><strong>ESP32-S3 timings:</strong> measured on the board: {E(F["board"])}.</li>
<li><strong>Tables</strong> are generated by <code>bench/aggregate.py</code> from <code>bench/results/</code>. Model IDs are shown exactly as run.</li></ul>
<p class="btn-row" style="margin-top:20px">{ext_link(L["results"], "bench/RESULTS.md")}{ext_link(L["report"], "Research report")}</p>'''
    lim = (f'<div class="grid-3">{limits_cards()}</div>'
           '<div class="callout"><p>RobotBench was written by hand, separately from the robot training generator. MASSIVE was never trained on, and it is where the gap to the 2B shows.</p></div>'
           f'<div class="card" style="margin-top:28px;display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between;box-shadow:none"><p style="margin:0;font-size:18px;font-weight:600">Run it on your hardware and tell us what you measure.</p>'
           f'<a class="btn btn-primary" href="{L["discussions"]}">Share your results</a></div>'
           '<p class="tnote">Evaluation data: Amazon MASSIVE (CC BY 4.0, evaluation only) · JevBench (MIT, evaluation only).</p>')
    body = (page_hero("Benchmarks", "Measured, with the conditions attached.", f'On-chip timings are from an {E(F["board"])}. Laptop timings name the runtime.', "ph-bench") +
            inpage([("chip", "On the chip"), ("faster", "How we got there"), ("laptop", "Laptop"), ("quality", "Quality"), ("robotbench", "RobotBench"),
                    ("massive", "MASSIVE"), ("jevbench", "JevBench"), ("parity", "Parity"), ("method", "Method"), ("limits", "Limits")]) +
            sec("chip", "Time per decision on an ESP32-S3", chip) +
            sec("faster", "Every release got faster", speed_rows(), E(F["how_it_works"][3])) +
            sec("laptop", "Speed on a laptop", laptop) +
            sec("quality", "Against the public 2B", quality) +
            sec("robotbench", "RobotBench", robot, "Robot decisions over sensor readings and commands. Released model IDs only, plus the two Strands Decider references.") +
            sec("massive", "MASSIVE routing", massive, "This is where Sparrow is weakest: open-ended language it never trained on.") +
            sec("jevbench", "JevBench", jev) +
            sec("parity", "Same answers on the chip as on the host", parity) +
            sec("method", "Methodology", method) +
            sec("limits", "Where it falls short", lim))
    return page("benchmarks/", root, "benchmarks/", "Benchmarks · Sparrow Decider",
                "Measured timings on an ESP32-S3 and a laptop, quality against the public 2B Strands Decider, and the limits we know about.", body)


# ---------------------------------------------------------------- CONTACT
def contact():
    root = "../"
    body = page_hero("Contact", "Talk to the flock.", "Sparrow Decider is built in the open by the Sparrow Decider contributors. GitHub is the best place to reach us.", "ph-contact") + f'''
<section class="page-sec" style="padding-top:8px"><div class="wrap stack">
<div class="contact-grid">
<a class="lcard" href="{L["discussions"]}"><span class="ic">{ICON["chat"]}</span><h2>Questions and ideas</h2><p>Ask how to fit a decision to your device, share what you built, or post benchmark results from your hardware.</p><span class="go">Open Discussions {ARR}</span></a>
<a class="lcard" href="{L["issues"]}"><span class="ic">{ICON["bug"]}</span><h2>Bugs and requests</h2><p>Something wrong or missing? File an issue with your model ID, runtime (Python, C, ESP-IDF), your board, and the smallest input that shows the problem.</p><span class="go">Open an issue {ARR}</span></a>
<a class="lcard wide" href="{L["contributing"]}"><span class="ic">{ICON["code"]}</span><h2>Contribute</h2><p>Code is Apache-2.0. Read the contributing guide and the quickstarts on GitHub before opening a pull request.</p><span class="go">Read the contributing guide {ARR}</span></a>
</div>
<p class="muted" style="max-width:880px">Cite this work with <a class="text-link" style="min-height:0" href="{L["citation"]}">CITATION.cff{ICON["ext"]}</a> in the repository. We do not offer paid support, and we do not collect email addresses on this site.</p>
<div class="disc-block"><p>{E(F["disclaimer"])}</p><p>For questions about Strands Decider itself, please use that project's own channels.</p></div>
</div></section>'''
    return page("contact/", root, "contact/", "Contact · Sparrow Decider", "Questions, bugs and results from your hardware: GitHub Discussions and Issues.", body)


# ---------------------------------------------------------------- 404
def notfound():
    # GitHub Pages serves 404.html at any depth, so resolve the site base before any relative URL loads.
    base = ('<script>(function(){var p=location.pathname.split("/"),b="/";'
            'if(/\\.github\\.io$/.test(location.hostname)&&p.length>2&&p[1])b="/"+p[1]+"/";'
            'var e=document.createElement("base");e.href=b;document.head.appendChild(e)})();</script>')
    sc = {"model": "sparrow-pico", "state": [["page", "not found"]], "question": "Where next?", "options": [], "answer": "home", "time": "", "caption": ""}
    card = f'''<figure class="trace" aria-label="A small decision trace: page not found, where next? home, models or docs">
<div class="trace-head"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="model">sparrow-pico</span></div>
<div class="trace-body" aria-hidden="true"><div><div class="t-label">state</div><div class="t-state"><span><span class="k">page: </span><span class="v">not found</span></span></div></div>
<div><div class="t-label">question</div><div class="t-q">Where next?   home | models | docs</div></div></div></figure>'''
    body = f'''<section class="nf"><div class="wrap"><div class="inner">{card}
<h1>This branch was never compiled.</h1>
<p class="body">sparrow-pico only answers the questions it was built for, and this page was not one of them.</p>
<div class="btn-row"><a class="btn btn-primary" href="./">Back to home</a><a class="btn btn-ghost" href="models/">Browse models</a><a class="btn btn-ghost" href="{L["docs"]}">Docs</a></div>
<p class="small">Think a link is broken? <a href="{L["issues"]}">Open an issue</a>.</p></div></div></section>'''
    return page("404.html", "", "", "Not found · Sparrow Decider", "", body, noindex=True, base_script=base)


# ---------------------------------------------------------------- write
def main():
    out = {
        "index.html": home(), "models/index.html": models(), "architecture/index.html": architecture(),
        "benchmarks/index.html": benchmarks(), "contact/index.html": contact(), "404.html": notfound(),
    }
    for p, s in out.items():
        f = WWW / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(s)
    (WWW / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    urls = "".join(f"  <url><loc>{SITE_URL}{u}</loc></url>\n" for u in ["", "models/", "architecture/", "benchmarks/", "contact/"])
    (WWW / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    print("wrote", ", ".join(out))


if __name__ == "__main__":
    main()
