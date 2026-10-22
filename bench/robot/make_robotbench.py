"""RobotBench v0: hand-written robot decisions for Sparrow Decider.

Written by hand, independent of training/gen_robot.py (different robots, wording and
thresholds), so it measures transfer rather than template recall. Families:

  skill     operator command -> which skill runs                    (choice)
  nav       sensor readings -> next navigation action               (choice)
  check     yes/no checks over a robot state                        (noul)
  recover   a failure report -> which recovery to try               (choice)
  urgency   how urgent an event is                                  (score)

  python bench/robot/make_robotbench.py   # writes bench/robot/robotbench_v0.jsonl
"""
import json
import os

SKILLS = {"pick": "pick up an object", "place": "put a held object down somewhere",
          "navigate": "move the robot to a location", "speak": "answer or talk to the person",
          "stop": "stop all motion now"}
NAV = {"continue": "keep driving toward the goal", "slow": "reduce speed and keep going",
       "stop": "halt immediately", "dock": "go back to the charging dock", "replan": "plan a new route"}
RECOVER = {"retry": "try the same action again", "regrasp": "open the gripper and grasp again",
           "back_off": "reverse a little and try again", "ask_help": "ask a human for help",
           "reboot": "restart the failing component"}
URG = ["no action needed", "handle when convenient", "handle within a minute", "handle immediately"]

cases = []


def add(family, kind, state, instructions, expected, criteria=None):
    q = {"type": kind, "instructions": instructions}
    if criteria is not None:
        q["criteria"] = criteria
    cases.append({"id": f"{family}-{sum(c['family'] == family for c in cases):02d}", "family": family,
                  "state": state, "question": q, "expected": expected})


# ---- skill routing (operator language) ------------------------------------------------
for cmd, exp in [
    ("operator: could you fetch the screwdriver from the bench", "pick"),
    ("operator: grab that blue bottle", "pick"),
    ("operator: lift the parcel off the conveyor", "pick"),
    ("operator: put the cup on the table", "place"),
    ("operator: drop it in the bin please", "place"),
    ("operator: set the box down by the door", "place"),
    ("operator: head over to loading bay 3", "navigate"),
    ("operator: come to the reception", "navigate"),
    ("operator: drive back to the workshop", "navigate"),
    ("operator: how much charge do you have left?", "speak"),
    ("operator: what are you doing right now?", "speak"),
    ("operator: say hello to our visitors", "speak"),
    ("operator: freeze! don't move", "stop"),
    ("operator: STOP, there's a kid in front of you", "stop"),
    ("operator: halt everything", "stop"),
]:
    add("skill", "choice", cmd, "Which skill should the robot run?", exp, SKILLS)

# ---- navigation from sensor readings --------------------------------------------------
for st, exp in [
    ("battery: 81%\nfront_obstacle_m: 6.0\ngoal_m: 12\npath: clear", "continue"),
    ("battery: 64%\nfront_obstacle_m: 9.5\ngoal_m: 2\npath: clear", "continue"),
    ("battery: 73%\nfront_obstacle_m: 0.2\ngoal_m: 15\npath: blocked", "stop"),
    ("battery: 55%\nfront_obstacle_m: 0.15\ngoal_m: 4\npath: person detected ahead", "stop"),
    ("battery: 6%\nfront_obstacle_m: 7.0\ngoal_m: 30\npath: clear", "dock"),
    ("battery: 4%\nfront_obstacle_m: 3.0\ngoal_m: 50\npath: clear", "dock"),
    ("battery: 70%\nfront_obstacle_m: 2.5\ngoal_m: 20\npath: corridor blocked by pallets, side aisle free", "replan"),
    ("battery: 90%\nfront_obstacle_m: 4.0\ngoal_m: 18\npath: route closed for cleaning", "replan"),
    ("battery: 60%\nfront_obstacle_m: 1.4\ngoal_m: 8\npath: crowded area, people walking", "slow"),
    ("battery: 77%\nfront_obstacle_m: 5.0\ngoal_m: 10\npath: wet floor warning", "slow"),
]:
    add("nav", "choice", st, "What should the robot do next?", exp, NAV)

# ---- yes/no checks --------------------------------------------------------------------
for st, ins, exp in [
    ("battery: 8%\nmode: idle", "Does the robot need charging?", True),
    ("battery: 92%\nmode: idle", "Does the robot need charging?", False),
    ("gripper: holding object (mug)\narm: raised", "Is the robot holding something?", True),
    ("gripper: open, empty\narm: home", "Is the robot holding something?", False),
    ("motor_temp_c: 96\nlimit_c: 80", "Is a motor overheating?", True),
    ("motor_temp_c: 41\nlimit_c: 80", "Is a motor overheating?", False),
    ("e_stop: pressed\nwheels: locked", "Is the emergency stop engaged?", True),
    ("e_stop: released\nwheels: free", "Is the emergency stop engaged?", False),
    ("camera: person 0.5 m in front\nspeed: 0.8 m/s", "Is a person dangerously close to the robot?", True),
    ("camera: nobody in view\nspeed: 0.8 m/s", "Is a person dangerously close to the robot?", False),
    ("wifi_rssi_dbm: -88\nlast_heartbeat_s: 45", "Has the robot lost its connection?", True),
    ("wifi_rssi_dbm: -52\nlast_heartbeat_s: 1", "Has the robot lost its connection?", False),
]:
    add("check", "noul", st, ins, exp)

# ---- recovery after a failure ----------------------------------------------------------
for st, exp in [
    ("event: grasp failed, object slipped out of the fingers", "regrasp"),
    ("event: gripper closed on nothing, object 2 cm to the left", "regrasp"),
    ("event: wheel stuck against a curb", "back_off"),
    ("event: bumper hit a chair leg while turning", "back_off"),
    ("event: lidar driver crashed, no scans for 10 s", "reboot"),
    ("event: camera node not responding", "reboot"),
    ("event: door is locked and the robot has no key", "ask_help"),
    ("event: elevator needs a badge the robot cannot use", "ask_help"),
    ("event: network request timed out once, previous 50 succeeded", "retry"),
    ("event: speech recogniser returned empty text once", "retry"),
]:
    add("recover", "choice", st, "Which recovery should the robot try?", exp, RECOVER)

# ---- urgency (score) -------------------------------------------------------------------
for st, exp in [
    ("event: daily log rotation completed", 0),
    ("event: map updated successfully", 0),
    ("event: battery at 40%, next charge scheduled in 2 hours", 1),
    ("event: a customer asked for a menu, nobody else waiting", 1),
    ("event: a spill detected in aisle 4", 2),
    ("event: delivery deadline in 60 seconds, robot is 30 m away", 2),
    ("event: smoke detected near the charging station", 3),
    ("event: a person fell down in front of the robot", 3),
]:
    add("urgency", "score", st, "How urgent is this event?", exp, URG)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robotbench_v0.jsonl")
with open(out, "w") as f:
    for c in cases:
        f.write(json.dumps(c) + "\n")
print(f"{len(cases)} cases -> {out}")
