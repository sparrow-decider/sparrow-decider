"""Generate robot decision rows in the decider training format, with rule-derived gold labels.

Families (task names in the rows):
  robot_skill     operator utterance -> skill to run              choice
  robot_action    sensor readings -> next motion action            choice
  robot_check     yes/no predicate over a robot state              noul
  robot_recover   failure report -> recovery                       choice
  robot_urgency   event -> urgency level                           score
  robot_compare   pick the zone/item with the most/least of X      choice

Wording, robots, field names and thresholds are randomised, and none of it is copied from
bench/robot (RobotBench is written separately, to measure transfer).

  python training/gen_robot.py --n 60000 --seed 1 --out corpus/robot.jsonl
"""
from __future__ import annotations

import argparse
import json
import random

R: random.Random

ROBOTS = ["warehouse AMR", "delivery rover", "hospital cart robot", "lawn mower robot", "vacuum robot",
          "service robot", "inspection crawler", "farm rover", "security patrol robot", "tour guide robot",
          "mobile manipulator", "forklift AGV", "kitchen assistant arm", "retail shelf scanner", "drone"]

# ---- skill routing ------------------------------------------------------------------------------
OBJ = ["wrench", "red mug", "parcel", "tray", "water bottle", "tote", "pallet", "book", "apple", "phone",
       "toolbox", "sample tube", "box of screws", "plate", "keys", "medicine pack", "cable", "helmet"]
LOC = ["dock 2", "the lab", "aisle 7", "room 214", "the lobby", "the kitchen", "bay C", "the nurse station",
       "the front gate", "workbench 3", "the storage room", "the cafe", "zone B", "the elevator", "the garden"]
PERSON = ["the visitor", "Dr. Rao", "the supervisor", "me", "the customer", "the new staff member"]
SKILL_DESC = {
    "pick": ["pick up an object", "grasp and lift an item", "take hold of something"],
    "place": ["put down the item being held", "place an object at a spot", "release a held item onto a surface"],
    "navigate": ["drive to a location", "move to a named place", "travel somewhere"],
    "speak": ["reply to the person", "talk or answer a question", "say something out loud"],
    "stop": ["stop moving immediately", "freeze all motors", "emergency halt"],
    "follow": ["follow a person", "walk behind someone", "track and follow a human"],
    "scan": ["scan or inspect the area", "take a camera survey", "look around and map"],
    "charge": ["go charge the battery", "return to the charger", "recharge at the dock"],
    "open_door": ["open a door", "push a door open", "open the gate or door"],
    "wait": ["stay put and wait", "pause and do nothing", "hold position"],
    "handover": ["hand an item to a person", "give the held object to someone", "pass the item over"],
}
UTTER = {
    "pick": ["get the {o}", "can you grab the {o}?", "pick up that {o}", "take the {o} off the shelf",
             "lift the {o}", "please collect the {o} from the floor", "grab {o} for me"],
    "place": ["put the {o} down on the table", "leave the {o} at {l}", "drop the {o} into the bin",
              "set the {o} on the cart", "place it on the shelf", "put that back where it was"],
    "navigate": ["go to {l}", "head to {l}", "move over to {l}", "drive to {l} please", "can you go to {l}?",
                 "make your way to {l}", "return to {l}"],
    "speak": ["what time is it?", "tell {p} the meeting moved", "how far is {l}?", "what's your status?",
              "introduce yourself", "are you busy?", "explain what you're doing", "greet {p}"],
    "stop": ["stop!", "stop right now", "halt", "freeze", "stop moving, you're too close", "emergency stop",
             "whoa whoa stop"],
    "follow": ["follow me", "come with me", "follow {p}", "stay behind me", "walk with me to the exit"],
    "scan": ["check the area for spills", "scan this room", "look around for the {o}", "inspect the shelves",
             "do a survey of {l}"],
    "charge": ["go charge yourself", "you need to recharge", "head to your charger", "plug yourself in"],
    "open_door": ["open the door", "get the door for {p}", "can you open that gate?", "open up the door to {l}"],
    "wait": ["wait here", "hold on a second", "stay there", "don't go anywhere yet", "pause for a minute"],
    "handover": ["give me the {o}", "hand the {o} to {p}", "pass me that {o}", "give {p} the {o}"],
}
SPEAKERS = ["operator", "user", "staff", "nurse", "customer", "voice command", "supervisor"]


def fill(t):
    return t.format(o=R.choice(OBJ), l=R.choice(LOC), p=R.choice(PERSON))


def skill_row():
    gold = R.choice(list(UTTER))
    others = R.sample([s for s in SKILL_DESC if s != gold], R.randint(2, 6))
    names = others + [gold]
    R.shuffle(names)
    opts = [[n, R.choice(SKILL_DESC[n])] for n in names]
    state = f"{R.choice(SPEAKERS)}: {fill(R.choice(UTTER[gold]))}"
    if R.random() < 0.4:
        state = f"robot: {R.choice(ROBOTS)}\n" + state
    ins = ["Which skill should run?", "What skill does this request need?", "Pick the robot skill for this command.",
           "Route the command to one skill."]
    return row("choice", state, ins, opts, names.index(gold), "robot_skill")


# ---- sensor-driven action ------------------------------------------------------------------------
ACT_DESC = {
    "continue": ["keep going to the goal", "proceed as planned", "carry on with the route"],
    "slow": ["reduce speed and continue", "slow down but keep moving", "proceed carefully at low speed"],
    "stop": ["halt now", "stop immediately", "come to a full stop"],
    "dock": ["go back and charge", "return to the charging station", "head to the dock to recharge"],
    "replan": ["compute another route", "find an alternative path", "re-route around the blockage"],
}


def num(v, unit=""):
    return f"{v}{unit}"


def battery_field(pct):
    style = R.random()
    if style < 0.5:
        return R.choice(["battery", "battery_pct", "batt", "charge"]), f"{pct}%"
    if style < 0.8:
        return R.choice(["soc", "state_of_charge", "battery_level"]), f"{pct}"
    return "battery_frac", f"{pct / 100:.2f}"


def dist_field(m):
    k = R.choice(["front_obstacle_m", "nearest_obstacle_m", "lidar_min_m", "obstacle_dist_m", "clearance_m"])
    if R.random() < 0.2:
        return k.replace("_m", "_cm"), f"{int(m * 100)}"
    return k, f"{m:.2f}" if m < 1 else f"{m:.1f}"


def action_row():
    low = R.choice([10, 12, 15, 20])
    stop_d = R.choice([0.3, 0.4, 0.5])
    gold = R.choices(["continue", "slow", "stop", "dock", "replan"], [3, 2, 3, 2, 2])[0]
    batt = R.randint(low + 3, 100)
    dist = round(R.uniform(2.0, 15.0), 1)
    path = R.choice(["clear", "free", "open", "nothing ahead"])
    if gold == "stop":
        dist = round(R.uniform(0.05, stop_d - 0.05), 2)
        if R.random() < 0.4:
            path = R.choice(["person directly ahead", "child in path", "obstacle at bumper", "blocked"])
    elif gold == "dock":
        batt = R.randint(1, low - 1)
    elif gold == "replan":
        path = R.choice(["route blocked by boxes, alternative corridor open", "door on route is closed",
                         "bridge closed for maintenance", "lane blocked by a parked cart, side lane free"])
        dist = round(R.uniform(1.0, 4.0), 1)
    elif gold == "slow":
        path = R.choice(["crowd of people nearby", "wet floor", "gravel and slope ahead", "narrow passage",
                         "children playing nearby", "low visibility, fog"])
        dist = round(R.uniform(0.8, 3.0), 1)
    fields = [battery_field(batt), dist_field(dist), (R.choice(["path", "route_status", "scene"]), path)]
    if R.random() < 0.6:
        fields.append((R.choice(["goal_m", "goal_distance_m", "remaining_m"]), str(R.randint(1, 80))))
    if R.random() < 0.4:
        fields.append(("speed_mps", f"{R.uniform(0.1, 1.5):.1f}"))
    if R.random() < 0.3:
        fields.append(("mode", R.choice(["autonomous", "mission", "delivering"])))
    if R.random() < 0.5:
        fields.append(("low_battery_threshold", f"{low}%"))
    R.shuffle(fields)
    state = "\n".join(f"{k}: {v}" for k, v in fields)
    names = R.sample(list(ACT_DESC), R.randint(3, 5))
    if gold not in names:
        names[R.randrange(len(names))] = gold
    opts = [[n, R.choice(ACT_DESC[n])] for n in names]
    ins = ["What should the robot do next?", "Choose the next motion action.", "Given the sensors, what now?",
           "Decide the robot's next move."]
    return row("choice", state, ins, opts, names.index(gold), "robot_action")


# ---- yes/no checks -------------------------------------------------------------------------------
def check_row():
    t = R.choice(["batt", "hold", "temp", "estop", "near", "link", "arrived", "stall", "door", "payload"])
    y = R.random() < 0.5
    if t == "batt":
        low = R.choice([10, 15, 20, 25])
        v = R.randint(1, low - 1) if y else R.randint(low + 5, 100)
        k, s = battery_field(v)
        st = f"{k}: {s}" + (f"\nlow_threshold: {low}%" if R.random() < 0.5 else "")
        q = R.choice(["Is the battery low?", "Should the robot recharge now?", "Is charge below the safe level?"])
    elif t == "hold":
        o = R.choice(OBJ)
        st = (f"gripper: closed on {o}\nforce_n: {R.randint(5, 40)}" if y else
              f"gripper: {R.choice(['open', 'closed, empty', 'idle'])}\nforce_n: 0")
        q = R.choice(["Is the gripper holding an item?", "Does the robot have an object in hand?"])
    elif t == "temp":
        lim = R.choice([70, 75, 80, 90])
        v = R.randint(lim + 3, lim + 40) if y else R.randint(25, lim - 8)
        st = f"{R.choice(['motor_temp_c', 'joint3_temp_c', 'driver_temp_c'])}: {v}\nmax_temp_c: {lim}"
        q = R.choice(["Is anything overheating?", "Is the temperature above its limit?", "Is the motor too hot?"])
    elif t == "estop":
        st = f"estop: {'active' if y else 'inactive'}\nbrakes: {'engaged' if y else 'released'}"
        q = R.choice(["Is the e-stop triggered?", "Is the emergency stop on?"])
    elif t == "near":
        d = round(R.uniform(0.1, 0.9), 1) if y else round(R.uniform(2.5, 10), 1)
        st = f"person_distance_m: {d}\nrobot_speed_mps: {R.uniform(0.2, 1.5):.1f}"
        q = R.choice(["Is a human too close to the robot?", "Is someone within the safety zone?"])
    elif t == "link":
        hb = R.randint(20, 300) if y else R.randint(0, 3)
        st = f"last_heartbeat_s: {hb}\nrssi_dbm: {R.randint(-95, -80) if y else R.randint(-65, -40)}"
        q = R.choice(["Is the robot disconnected?", "Has the link to base dropped?"])
    elif t == "arrived":
        d = round(R.uniform(0.0, 0.2), 2) if y else round(R.uniform(1.5, 40), 1)
        st = f"goal: {R.choice(LOC)}\ndistance_to_goal_m: {d}"
        q = R.choice(["Has the robot reached its goal?", "Is the robot at the destination?"])
    elif t == "stall":
        cmd = round(R.uniform(0.3, 1.0), 1)
        st = f"commanded_speed_mps: {cmd}\nmeasured_speed_mps: {0.0 if y else round(cmd * R.uniform(0.9, 1.0), 2)}"
        st += f"\nwheel_current_a: {R.randint(9, 15) if y else R.randint(1, 4)}"
        q = R.choice(["Are the wheels stalled?", "Is the robot stuck?"])
    elif t == "door":
        st = f"door_sensor: {'open' if y else 'closed'}\nlocation: {R.choice(LOC)}"
        q = R.choice(["Is the door open?", "Can the robot pass through the door?"])
    else:
        cap = R.choice([5, 10, 20])
        w = round(R.uniform(cap + 1, cap * 2), 1) if y else round(R.uniform(0.5, cap - 1), 1)
        st = f"payload_kg: {w}\nmax_payload_kg: {cap}"
        q = R.choice(["Is the robot overloaded?", "Is the payload above capacity?"])
    if R.random() < 0.3:
        st = f"robot: {R.choice(ROBOTS)}\n" + st
    return row("noul", st, [q], [["false", "the statement does not hold for this state"],
                                 ["true", "the statement holds for this state"]], int(y), "robot_check")


# ---- recovery ------------------------------------------------------------------------------------
REC = {
    "retry": (["try again", "repeat the last action", "attempt once more"],
              ["one request timed out, earlier ones fine", "a single frame was dropped", "transient read error once",
               "the voice command was not understood once", "first upload attempt failed"]),
    "regrasp": (["re-open the gripper and grasp again", "release and try the grasp again", "adjust grip and re-grasp"],
                ["item slipped from the gripper", "grasp missed the handle by a few cm", "fingers closed on air",
                 "object rotated in hand and fell"]),
    "back_off": (["reverse a bit and retry", "back up and approach again", "move back then try again"],
                 ["front wheel wedged against a step", "bumper pressed against a wall", "collided gently with a bin",
                  "caught on a rug edge"]),
    "reboot": (["restart the failed module", "power-cycle the faulty component", "relaunch the crashed node"],
               ["the camera driver crashed", "lidar stopped publishing", "IMU node is frozen",
                "motor controller not responding"]),
    "ask_help": (["call a person for help", "request human assistance", "notify an operator"],
                 ["glass door needs a keycard", "object is too heavy to lift", "stairs block the only route",
                  "item is out of reach on a high shelf"]),
}


def recover_row():
    gold = R.choice(list(REC))
    names = R.sample([k for k in REC if k != gold], R.randint(2, 4)) + [gold]
    R.shuffle(names)
    opts = [[n, R.choice(REC[n][0])] for n in names]
    st = f"{R.choice(['fault', 'event', 'error', 'report'])}: {R.choice(REC[gold][1])}"
    ins = ["Which recovery should run?", "How should the robot recover?", "Pick the recovery action."]
    return row("choice", st, ins, opts, names.index(gold), "robot_recover")


# ---- urgency -------------------------------------------------------------------------------------
URG_EVENTS = [
    ["nightly backup finished", "firmware is up to date", "cleaning cycle completed on schedule",
     "routine status ping"],
    ["toner is at 30%", "a guest asked about opening hours", "battery 45%, next charge in 3 hours",
     "a shelf label is slightly crooked"],
    ["spilled liquid in a walkway", "an order is due in 2 minutes", "a pallet is blocking an exit lane",
     "a freezer door has been open 5 minutes"],
    ["fire alarm triggered", "a person has collapsed", "a child is climbing the robot arm",
     "gas leak detected near the charger"],
]
LEVELS = [["ignore", "monitor", "soon", "now"],
          ["no action", "low priority", "high priority", "emergency"],
          ["not urgent", "can wait", "urgent", "critical"]]


def urgency_row():
    lv = R.randrange(4)
    st = f"event: {R.choice(URG_EVENTS[lv])}"
    lab = R.choice(LEVELS)
    ins = ["How urgent is this?", "Rate the urgency of the event.", "How quickly must the robot react?"]
    return row("score", st, ins, [[str(i), d] for i, d in enumerate(lab)], lv, "robot_urgency")


# ---- compare --------------------------------------------------------------------------------------
def compare_row():
    prop, unit, want = R.choice([("dirt_level", "", "most"), ("battery", "%", "most"), ("distance_m", "", "least"),
                                 ("queue_length", "", "most"), ("temperature_c", "", "most"),
                                 ("waiting_min", "", "most"), ("free_slots", "", "most")])
    n = R.randint(3, 5)
    names = R.sample(["zone_a", "zone_b", "zone_c", "zone_d", "zone_e", "dock_1", "dock_2", "room_3", "bay_4"], n)
    vals = R.sample(range(1, 99), n)
    st = "\n".join(f"{nm}: {prop}={v}{unit}" for nm, v in zip(names, vals))
    i = vals.index(max(vals) if want == "most" else min(vals))
    q = f"Which one has the {'highest' if want == 'most' else 'lowest'} {prop.replace('_', ' ')}?"
    opts = [[nm, f"{nm.replace('_', ' ')}"] for nm in names]
    return row("choice", st, [q], opts, i, "robot_compare")


def row(kind, state, ins, opts, label, task):
    return {"kind": kind, "state": state, "instructions": ins[0], "options": opts, "label": label, "task": task,
            "weight": 1.0, "instruction_variants": ins[1:], "src": "robot"}


FAMS = [(skill_row, 3), (action_row, 3), (check_row, 3), (recover_row, 2), (urgency_row, 1), (compare_row, 1)]


def main():
    global R
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R = random.Random(a.seed)
    fs, ws = zip(*FAMS)
    with open(a.out, "w") as f:
        for _ in range(a.n):
            r = R.choices(fs, ws)[0]()
            # Shuffle the instruction so the canonical phrasing varies
            ins = [r["instructions"]] + r["instruction_variants"]
            R.shuffle(ins)
            r["instructions"], r["instruction_variants"] = ins[0], ins[1:]
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
