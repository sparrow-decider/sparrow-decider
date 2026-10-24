# Sparrow Decider: social copy (launch)

Rules for anyone posting: numbers only from `site/facts.json`; no names of individuals; attach
`site/brand/previews/og-image.png` where an image is allowed; link to
https://github.com/sparrow-decider/sparrow-decider. Do not post until the launch is approved.

---

## X / Twitter thread (6 posts)

**1/6**
Sparrow Decider 0.2.0 is out.

Tiny decision models for agents, robots and microcontrollers.
From 47 MB on a laptop to ~2 KB on a chip.

9.3 µs per decision on a $10 ESP32-S3.

pip install sparrow-decider
(thread)
*[image: og-image.png]*

**2/6**
What it does: yes/no, pick-one and score questions about a state, with calibrated probabilities.

Same shapes as Strands Decider, so your question schemas carry over.

No GPU. No network. No model server.

**3/6**
On the ESP32-S3 (240 MHz, 8 MB PSRAM):

• sparrow-pico: 9.3 µs per decision, ~2 KB per question
• nano-general: 3.8 ms per text decision
• nano-robot v1.1: 7.6 ms, text with sensor readings

int8 builds agree with the host on 150-155 of 155 decisions.

**4/6**
A 1.37 MB nano-robot v1.0 scores 40 / 55 on RobotBench.
The public 2-billion-parameter Strands Decider also scores 40 / 55.

nano-robot v1.1 gets navigation from sensor numbers 10/10. The public 2B: 3/10.

**5/6**
How: a 4B Strands Decider teaches the text tiers on ~430k decisions.

pico is a compiler. Write a spec (sensors, rules, questions), the public 2B labels sampled states, and out comes one tiny MLP per question as a C header.

C99 runtime, no malloc.

**6/6**
Honest limits:
• new open-ended language: behind the 2B (MASSIVE routing 0.52-0.67 vs 0.86)
• JevBench yes/no: near chance at every tier
• pico: only the questions it was compiled for

github.com/sparrow-decider/sparrow-decider
Unofficial community project. Not an AWS or Strands product.

---

## LinkedIn post

**Decisions that fit on a chip.**

The Sparrow Decider contributors have released Sparrow Decider 0.2.0: a family of tiny decision models
for agents, robots and embedded products.

Each model answers yes/no, pick-one and score questions about a state, with calibrated probabilities,
in the same shapes as Strands Decider. The family runs from a 47 MB model on a laptop down to a ~2 KB
compiled model on a microcontroller.

Measured on a $10 ESP32-S3 (240 MHz, 16 MB flash, 8 MB PSRAM):
→ 9.3 µs per decision with sparrow-pico (501 parameters per question)
→ 3.8 ms per text decision with sparrow-nano-general (2.2 MB)
→ ~2 KB per compiled question with sparrow-pico

On robot decisions, a 1.37 MB nano-robot v1.0 scores 40 / 55 on RobotBench, tying the public
2-billion-parameter Strands Decider.

What we like most is how ordinary it is to use: pip install sparrow-decider pulls in numpy only, and
the C99 runtime has no malloc and reads the model from flash as an ESP-IDF component.

We publish the limits too. Open-ended language it never trained on is well behind the 2B, yes/no
judgement on JevBench is near chance at every tier, and pico answers only the questions it was
compiled for.

If you build robots, agents or IoT devices and want a decision step that runs locally, we would like
to hear what you try it on.

https://github.com/sparrow-decider/sparrow-decider

Unofficial community project. Not an AWS or Strands product.

#EdgeAI #TinyML #Robotics #ESP32 #EmbeddedSystems #OpenSource

---

## Hacker News

**Title (Show HN, 80 char limit):**

Show HN: Sparrow Decider – tiny decision models, 9.3 µs per decision on an ESP32-S3

*Alternative:* Show HN: Sparrow Decider – decision models from 47 MB down to ~2 KB of C

**URL:** https://github.com/sparrow-decider/sparrow-decider

**First comment (post as the submitting account):**

Hi HN. Sparrow Decider is a family of small models for one narrow job: answering yes/no, pick-one
and score questions about a state, with calibrated probabilities. "Is the user upset?" "Which skill
should run?" "Battery 6%, path clear: continue, slow, stop, dock or replan?"

It uses the same question shapes as Strands Decider, and the text tiers are distilled from a 4B
Strands Decider on ~430k decisions.

The part we find most interesting is the bottom of the range:

- nano (text) uses static embeddings with a pruned 8-16k vocabulary at 128-d, plus key-value number
  pooling so "battery: 6%" is read as a value. nano-general (2.2 MB) takes 3.8 ms per decision on an
  ESP32-S3 at 240 MHz, using int8 SIMD through ESP-NN.
- pico is a compiler. You write a spec of sensors, rules and questions; the public Strands Decider 2B
  labels sampled states; the compiler emits one tiny MLP per question as a C header. The rover example
  is 501 parameters, ~2 KB per question, 9.3 µs per decision on the ESP32-S3 and 0.18 µs on a laptop.
  It matches the spec's rules 94.0% of the time; its 2B teacher gets 94.2%.
- The C99 runtime has no malloc and reads the model from flash. The C runtime matches the Python
  runtime to within 1e-5 on the host; on the ESP32-S3, int8 builds agree with the host on 150-155 of
  155 decisions.

Where it falls short, measured: on open-ended language it never trained on it is well behind the 2B
(MASSIVE domain routing 0.52-0.67 vs 0.86), and yes/no judgement on JevBench is near chance at every
tier. pico only answers the questions it was compiled for.

Python needs numpy only: `pip install sparrow-decider`. Code is Apache-2.0. This is an unofficial
community project, not an AWS or Strands product.

Happy to answer questions about the distillation, the number pooling or the ESP32-S3 port. Results
on other boards would be very welcome.

---

## Reddit: r/embedded

**Title:** Decision models for MCUs: 9.3 µs per decision on an ESP32-S3, C99, no malloc (open source)

**Body:**

We have been working on Sparrow Decider, an open-source (Apache-2.0) family of small decision models,
and the embedded side is the part we would most like feedback on.

**What it is:** models that answer yes/no, pick-one and score questions about a device state with
calibrated probabilities. Think "given these sensor readings, should the rover continue, slow, stop,
dock or replan?"

**Board we measured on:** ESP32-S3 (QFN56 rev0.2), 240 MHz, 16 MB flash, 8 MB PSRAM.

**Two ways to run on a chip:**

1. **sparrow-pico** (numbers in, no text). You write a spec: sensors, flags, enums, rules and
   questions. The compiler outputs a C header with one tiny MLP per question.
   - Example `sparrow-pico-rover-v1.1`: 501 parameters, ~2 KB per question
   - 9.3 µs per decision on the ESP32-S3 (it started at 42.9 µs)
   - 94.0% agreement with the spec's rules (the 2B model that labelled the training states: 94.2%)
   - Answers only the questions it was compiled for
2. **sparrow-nano** (text in). Static embeddings, int8 SIMD on the S3 vector unit via ESP-NN,
   weights in PSRAM / internal RAM.
   - `sparrow-nano-general-v1.1`, 2.2 MB: 3.8 ms per decision (started at 9.6 ms)
   - `sparrow-nano-robot-v1.1`, 1.19 MB, text with sensor readings: 7.6 ms per decision
     (73.5 ms on the first run, 13.2 ms for v1.0)

**Runtime:** C99, no malloc, model read from flash, shipped as an ESP-IDF component. The C runtime matches
the Python runtime to within 1e-5 on the host; on the ESP32-S3, int8 builds agree with the host on
150-155 of 155 decisions. There is a QEMU path in the docs if you have no board.

**Limits we know about:** text tiers are weak on open-ended language they never trained on, and
yes/no judgement on JevBench is near chance at every tier. This is for fixed-answer decisions about
a known state, not general NLP.

Site: https://sparrowdecider.com · Code: https://github.com/sparrow-decider/sparrow-decider · Models: https://huggingface.co/sparrow-decider · pip install sparrow-decider

We would love numbers from other MCUs (anything with a C99 compiler should run pico), and criticism
of the memory layout. Unofficial community project, not an AWS or Strands product.
