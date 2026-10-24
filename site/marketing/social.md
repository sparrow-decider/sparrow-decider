# Sparrow Decider: social copy (launch, 0.2.0)

**Rules:**
- Numbers come only from `site/facts.json`, using the current models only.
- Keep the disclaimer on every post.

**Links:**
- Site: https://sparrowdecider.com
- Install: `pip install sparrow-decider` (https://pypi.org/project/sparrow-decider/)
- Models: https://huggingface.co/sparrow-decider
- Code: https://github.com/sparrow-decider/sparrow-decider

**Assets:**

| Where | Asset |
|---|---|
| LinkedIn | `video/out/sparrow-decider-linkedin-1x1.mp4` |
| Instagram feed | `video/out/sparrow-decider-instagram-4x5.mp4` |
| Instagram Stories / Reels | `video/out/sparrow-decider-story-9x16.mp4` |
| X, HN thumbnails, link previews | `site/brand/previews/og-image.png` |

---

## X / Twitter thread (6 posts)

**1/6**
I just released Sparrow Decider 0.2.0.

Decision models that fit on a chip: from 47 MB on a laptop to ~2 KB on a microcontroller.

9.3 µs per decision on a $10 ESP32-S3.

pip install sparrow-decider
🧵
*[video: linkedin-1x1.mp4, or image: og-image.png]*

**2/6**
What it does: answers yes/no, pick-one and score questions about a state, with calibrated probabilities.

"Is the user upset?" "Which tool fits?" "Battery 6%, path clear: continue, slow, stop, dock or replan?"

No GPU. No network. No model server.

**3/6**
Measured on an ESP32-S3 (240 MHz):

• sparrow-pico: 9.3 µs per decision, ~2 KB per question
• sparrow-nano-robot: 3.5 ms, reads "battery: 6%" as a value
• sparrow-nano-general: 3.8 ms per text decision

The first on-chip builds took 42.9 µs, 73.5 ms and 9.6 ms.

**4/6**
Size isn't everything: on navigation from sensor numbers, the 1.11 MB nano-robot gets 8/10 right.

The public 2-billion-parameter Strands Decider gets 3/10.

**5/6**
pico is a compiler. Write a spec (sensors, rules, questions), a full Strands Decider labels sampled states, and out comes one tiny MLP per question as a C header.

The C99 runtime has no malloc and is an ESP-IDF component.

**6/6**
Honest limits:
• open-ended language it never trained on: behind the 2B (MASSIVE routing 0.37-0.67 vs 0.86)
• yes/no judgement on JevBench: near chance at every tier
• pico answers only the questions it was compiled for

sparrowdecider.com
Unofficial community project. Not an AWS or Strands product.

---

## LinkedIn post

*Attach `sparrow-decider-linkedin-1x1.mp4`.*

**Decisions that fit on a chip.** 🐦

Today I'm releasing Sparrow Decider 0.2.0, an open-source family of tiny decision models for agents,
robots and embedded devices.

Each model answers yes/no, pick-one and score questions about a state, with calibrated probabilities.
They use the same shapes as Strands Decider. The family runs from a 47 MB model on a laptop down to a
~2 KB compiled model on a microcontroller.

Measured on a $10 ESP32-S3:
→ 9.3 µs per decision with sparrow-pico (~2 KB per question)
→ 3.5 ms per robot decision with sparrow-nano-robot (1.11 MB)
→ 3.8 ms per text decision with sparrow-nano-general (2.2 MB)

One result I like: on navigation from sensor readings, the 1.11 MB nano-robot gets 8 of 10 right. The
public 2-billion-parameter Strands Decider gets 3 of 10.

It's simple to use:
- `pip install sparrow-decider` pulls in numpy only.
- The C99 runtime has no malloc and runs as an ESP-IDF component.
- Every model is on Hugging Face.

I publish the limits too:
- Open-ended language it never trained on is well behind the 2B.
- Yes/no judgement is near chance on JevBench.
- pico answers only the questions it was compiled for.

If you build robots, agents or IoT devices and want a decision step that runs locally, I'd love to
hear what you try it on.

🌐 https://sparrowdecider.com
📦 https://pypi.org/project/sparrow-decider/
🤗 https://huggingface.co/sparrow-decider
💻 https://github.com/sparrow-decider/sparrow-decider

Unofficial community project. Not an AWS or Strands product.

#EdgeAI #TinyML #Robotics #ESP32 #EmbeddedSystems #OpenSource #AIAgents

---

## Instagram (feed post and Reel)

*Attach `sparrow-decider-instagram-4x5.mp4` (feed) or `sparrow-decider-story-9x16.mp4` (Reel).*

Decisions that fit on a chip. 🐦

Sparrow Decider is a family of tiny AI decision models, from 47 MB on a laptop down to ~2 KB on a
microcontroller.

⚡ 9.3 µs per decision on a $10 ESP32-S3
🤖 3.5 ms robot decisions, 3.8 ms text decisions on the same chip
📦 pip install sparrow-decider

Open source. Link in bio → sparrowdecider.com

Unofficial community project. Not an AWS or Strands product.

#TinyML #EdgeAI #ESP32 #Robotics #EmbeddedSystems #MachineLearning #OpenSource #Maker #IoT

**Story frames** (use with the 9:16 video; add a link sticker to https://sparrowdecider.com):
1. "Decisions that fit on a chip."
2. "9.3 µs per decision on a $10 ESP32-S3"
3. "pip install sparrow-decider", with the link sticker

---

## Hacker News

**Title (Show HN, 80 characters max):**

Show HN: Sparrow Decider – tiny decision models, 9.3 µs per decision on an ESP32-S3

*Alternative:* Show HN: Sparrow Decider – decision models from 47 MB down to ~2 KB of C

**URL:** https://sparrowdecider.com

**First comment (post from the submitting account):**

Hi HN. Sparrow Decider is a family of small models for one narrow job: answering yes/no, pick-one
and score questions about a state, with calibrated probabilities. "Is the user upset?" "Which tool
fits?" "Battery 6%, path clear: continue, slow, stop, dock or replan?"

It uses the same question shapes as Strands Decider. The text tiers are distilled from a 4B Strands
Decider on ~430k decisions.

The part I find most interesting is the bottom of the range:

- **nano (text).** It uses static embeddings with a pruned 8-16k vocabulary at 128 dimensions. It also
  pools key-value numbers, so "battery: 6%" is read as a value.
  - Speed on an ESP32-S3 at 240 MHz, using int8 SIMD through ESP-NN: 3.5 ms per decision for
    nano-robot (1.11 MB) and 3.8 ms for nano-general (2.2 MB).
  - On navigation from sensor numbers, nano-robot gets 8/10; the public 2B Strands Decider gets 3/10.
- **pico.** It's a compiler. You write a spec of sensors, rules and questions; a full Strands Decider
  labels sampled states; the compiler emits one tiny MLP per question as a C header.
  - The rover example has 501 parameters (~2 KB per question).
  - It runs at 9.3 µs per decision on the ESP32-S3, or 0.18 µs on a laptop.
  - It matches the spec's rules 94.0% of the time; its 2B teacher gets 94.2%.
- **C99 runtime.** It has no malloc and reads the model from flash.
  - On the host, it matches the Python runtime to within 1e-5.
  - On the ESP32-S3, int8 builds agree with the host on 150-155 of 155 decisions.

Where it falls short, measured:
- On open-ended language it never trained on, it is well behind the 2B (MASSIVE domain routing
  0.37-0.67 vs 0.86).
- Yes/no judgement on JevBench is near chance at every tier.
- pico only answers the questions it was compiled for.

Getting it:
- `pip install sparrow-decider` (numpy is the only dependency)
- Models: https://huggingface.co/sparrow-decider
- Code (Apache-2.0): https://github.com/sparrow-decider/sparrow-decider

This is an unofficial community project, not an AWS or Strands product. Happy to answer questions
about the distillation, the number pooling or the ESP32-S3 port. Results on other boards would be very
welcome.

---

## Reddit: r/embedded

**Title:** I built decision models for MCUs: 9.3 µs per decision on an ESP32-S3, C99, no malloc (open source)

**Body:**

I've been working on Sparrow Decider, an open-source (Apache-2.0) family of small decision models.
The embedded side is the part I'd most like feedback on.

**What it is:** models that answer yes/no, pick-one and score questions about a device state, with
calibrated probabilities. Think "given these sensor readings, should the rover continue, slow, stop,
dock or replan?"

**Board I measured on:** ESP32-S3 (QFN56 rev0.2), 240 MHz, 16 MB flash, 8 MB PSRAM.

**Two ways to run on a chip:**

1. **sparrow-pico** (numbers in, no text). You write a spec: sensors, flags, enums, rules and
   questions. The compiler outputs a C header with one tiny MLP per question.
   - `sparrow-pico-rover-v1.1`: 501 parameters, ~2 KB per question
   - 9.3 µs per decision on the ESP32-S3 (the first build took 42.9 µs)
   - 94.0% agreement with the spec's rules (the 2B model that labelled its training states: 94.2%)
   - Answers only the questions it was compiled for
2. **sparrow-nano** (text in). Static embeddings, int8 SIMD on the S3 vector unit via ESP-NN, and
   weights in PSRAM and internal RAM.
   - `sparrow-nano-robot-v1.2`, 1.11 MB, reads text with sensor readings: 3.5 ms per decision (the
     first build took 73.5 ms)
   - `sparrow-nano-general-v1.1`, 2.2 MB: 3.8 ms per decision (the first build took 9.6 ms)

**Runtime:**
- C99, no malloc, the model read from flash, shipped as an ESP-IDF component.
- On the host, the C runtime matches the Python runtime to within 1e-5.
- On the ESP32-S3, int8 builds agree with the host on 150-155 of 155 decisions.
- There's a QEMU path in the docs if you have no board.

**Limits I know about:** the text tiers are weak on open-ended language they never trained on, and
yes/no judgement on JevBench is near chance at every tier. This is for fixed-answer decisions about
a known state, not general NLP.

Site: https://sparrowdecider.com · Code: https://github.com/sparrow-decider/sparrow-decider ·
Models: https://huggingface.co/sparrow-decider · `pip install sparrow-decider`

I'd love numbers from other MCUs (anything with a C99 compiler should run pico), and criticism of the
memory layout. Unofficial community project, not an AWS or Strands product.
