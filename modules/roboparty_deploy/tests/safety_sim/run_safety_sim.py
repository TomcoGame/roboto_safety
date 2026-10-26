#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0
"""Drive the real inference node, built against fake drivers, through the safety scenarios.

Usage (after building, see README.md):
    python3 run_safety_sim.py <path to safety_sim_node>

Each check prints PASS or FAIL; the exit code is the number of failures.
"""

import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import rclpy
import yaml
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Joy

HERE = Path(__file__).resolve().parent
RPO = HERE.parent.parent / "src" / "inference" / "robots" / "rpo"
X, A, B = 2, 0, 1  # button indices used by the node
GAP_LIMIT = 0.1  # s; half the 200 ms motor command timeout
FAILS = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}{'  (' + detail + ')' if detail else ''}", flush=True)
    if not ok:
        FAILS.append(name)


class Gamepad:
    """Publishes /joy at 20 Hz, like joy_node with its default autorepeat."""

    def __init__(self, node):
        qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=1,
                         reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.VOLATILE)
        self.pub = node.create_publisher(Joy, "/joy", qos)
        self.axes = [0.0] * 8
        self.buttons = [0] * 11
        self.enabled = True
        self.lock = threading.Lock()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while True:
            with self.lock:
                if self.enabled:
                    self.pub.publish(Joy(axes=list(self.axes), buttons=list(self.buttons)))
            time.sleep(0.05)

    def press(self, button, hold=0.15):
        with self.lock:
            self.buttons[button] = 1
        time.sleep(hold)
        with self.lock:
            self.buttons[button] = 0
        time.sleep(0.1)

    def send_raw(self, msg):
        self.pub.publish(msg)


class Sim:
    def __init__(self, binary, workdir, extra_params=()):
        self.workdir = Path(workdir)
        self.trig = self.workdir / "trig"
        self.trig.mkdir()
        self.log = self.workdir / "motors.csv"
        self.out = self.workdir / "node.log"
        env = dict(os.environ, FAKE_MOTOR_LOG=str(self.log), FAKE_TRIGGER_DIR=str(self.trig))
        self.proc = subprocess.Popen(
            [binary, "--ros-args", "-r", "__node:=inference_node",
             "--params-file", str(RPO / "configs" / "default.yaml"),
             "-p", f"robot_config:={RPO / 'robot.yaml'}", "-p", f"model_dir:={RPO / 'models'}",
             *[a for p in extra_params for a in ("-p", p)]],
            env=env, stdout=open(self.out, "w"), stderr=subprocess.STDOUT)
        time.sleep(3.0)

    def trigger(self, name, on=True):
        p = self.trig / name
        p.touch() if on else p.unlink(missing_ok=True)

    def output(self):
        return self.out.read_text(errors="replace")

    def events(self, since=0.0, until=1e18):
        rows = []
        for line in self.log.read_text().splitlines():
            t, mid, kind, *vals = line.split(",")
            t = float(t)
            if since <= t <= until:
                rows.append((t, int(mid), kind, [float(v) for v in vals]))
        return rows

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def now():
    return time.monotonic()


def max_gap(rows, motor=1, start=None):
    """Longest time motor went uncommanded; counted from start when given."""
    ts = [t for t, mid, kind, _ in rows if mid == motor and kind == "mit"]
    if start is not None:
        ts = [start] + ts
    if len(ts) < 2:
        return float("inf")
    return max(b - a for a, b in zip(ts, ts[1:]))


def main(binary):
    robot = yaml.safe_load((RPO / "robot.yaml").read_text())
    params = yaml.safe_load((RPO / "configs" / "default.yaml").read_text())["inference_node"]["ros__parameters"]
    kd = robot["robot"]["kd"]
    sign = robot["robot"]["motor_sign"]
    limits = params["joint_limits"]
    ankles = {i + 1 for i in robot["robot"]["close_chain_motor_idx"]}  # motor ids
    timeout_ms = robot["motors"]["can_timeout_ms"]

    rclpy.init()
    node = rclpy.create_node("safety_sim_driver")
    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()
    pad = Gamepad(node)

    with tempfile.TemporaryDirectory() as tmp:
        sim = Sim(binary, tmp)
        try:
            check("node starts and stays up", sim.proc.poll() is None, sim.output()[-300:] if sim.proc.poll() else "")

            # 1. Enabling the motors applies the timeout and keeps them commanded with cleared targets.
            t0 = now()
            pad.press(X)
            time.sleep(1.0)
            ev = sim.events(t0)
            inits = {mid for _, mid, k, _ in ev if k == "init"}
            touts = [v[0] for _, _, k, v in ev if k == "timeout"]
            check("X enables all 23 motors", len(inits) == 23)
            check(f"command timeout {timeout_ms} ms set on every motor", len(touts) == 23 and set(touts) == {timeout_ms})
            hold = sim.events(now() - 0.8)
            check("enabled but idle: commands keep flowing (gap < half the timeout)", max_gap(hold) < GAP_LIMIT, f"gap {max_gap(hold):.3f} s")
            mits = [v for _, _, k, v in hold if k == "mit"]
            check("enabled but idle: no stale targets replayed (kp = 0)", bool(mits) and all(v[2] == 0.0 for v in mits))

            # 2. A joint reset, including its 1 s status refresh, never leaves the motors uncommanded.
            t0 = now()
            pad.press(A)
            time.sleep(6.5)
            ev = sim.events(t0)
            gap = max_gap(ev, start=t0)
            check("reset: commands keep flowing throughout (gap < half the timeout)", gap < GAP_LIMIT, f"gap {gap:.3f} s")
            last = [v for _, mid, k, v in ev if mid == 1 and k == "mit"][-1]
            check("reset: robot holds the default pose with full gains afterwards", last[2] > 0.0, f"kp {last[2]}")

            # 3. Inference runs; when the gamepad goes silent the velocity command drops to zero.
            pad.axes[4] = 1.0
            t_run = now()
            pad.press(B)
            time.sleep(2.0)
            check("B starts inference", "Inference started" in sim.output())
            pad.enabled = False
            time.sleep(1.2)
            check("gamepad silent 1.2 s: velocity command set to zero", "No velocity command" in sim.output())
            pad.axes[4] = 0.0
            pad.enabled = True
            time.sleep(0.5)

            run = sim.events(t_run, now())
            out_of_limit = [(mid, v[0]) for _, mid, k, v in run
                            if k == "mit" and v[2] > 0 and mid not in ankles
                            and not (limits[2 * (mid - 1)] - 1e-4 <= v[0] * sign[mid - 1] <= limits[2 * (mid - 1) + 1] + 1e-4)]
            check("running: every joint target inside joint_limits", not out_of_limit, str(out_of_limit[:3]))

            # 4. One X press does not disable the motors; a second within 1 s does.
            t0 = now()
            pad.press(X)
            time.sleep(1.5)
            ev = sim.events(t0)
            check("single X press: motors stay enabled", not any(k == "deinit" for _, _, k, _ in ev))
            check("single X press: operator told to press again", "Press 'X' again" in sim.output())
            t0 = now()
            pad.press(X)
            pad.press(X)
            time.sleep(0.5)
            ev = sim.events(t0)
            check("double X press: all motors disabled", len({mid for _, mid, k, _ in ev if k == "deinit"}) == 23)
            check("double X press: command timeout cleared (0)",
                  sorted(v[0] for _, _, k, v in ev if k == "timeout") == [0.0] * 23)

            # 5. A fall during inference: damped for the configured time, then disabled.
            t0 = now()
            pad.press(X)
            time.sleep(0.5)
            mits = [v for _, _, k, v in sim.events(t0) if k == "mit"]
            check("re-enabled after a disable: walking pose not replayed (kp = 0)",
                  bool(mits) and all(v[2] == 0.0 for v in mits))
            pad.press(A)
            time.sleep(6.5)
            pad.press(B)
            time.sleep(1.0)
            t_fault = now()
            sim.trigger("tilt")
            time.sleep(0.5)
            sim.trigger("tilt", on=False)
            check("tilt: safe stop entered", "Safe stop: inference error: robot fell" in sim.output())
            check("tilt: node keeps running (no shutdown)", sim.proc.poll() is None)
            damped = sim.events(t_fault + 0.2, t_fault + 2.5)
            m1 = [v for _, mid, k, v in damped if mid == 1 and k == "mit"]
            check("tilt: joints damped (kp = 0, kd from robot.yaml)",
                  bool(m1) and all(v[2] == 0.0 and abs(v[3] - kd[0]) < 1e-3 for v in m1))
            check("tilt: damping keeps being commanded (gap < half the timeout)", max_gap(damped) < GAP_LIMIT)
            pad.press(B)
            check("tilt: start refused during safe stop", "Safe stop is active, cannot start inference" in sim.output())
            time.sleep(3.5)
            ev = sim.events(t_fault)
            deinits = [t for t, _, k, _ in ev if k == "deinit"]
            check("tilt: motors disabled after the damping time",
                  len(deinits) == 23 and 2.5 < min(deinits) - t_fault < 4.0,
                  f"after {min(deinits) - t_fault:.2f} s" if deinits else "no deinit")
            t0 = now()
            pad.press(X)
            time.sleep(0.5)
            check("after safe stop: X re-enables the motors", len({mid for _, mid, k, _ in sim.events(t0) if k == "init"}) == 23)

            # 6. Inference overruns trip the safe stop.
            pad.press(A)
            time.sleep(6.5)
            pad.press(B)
            time.sleep(1.0)
            sim.trigger("slow")
            time.sleep(1.0)
            sim.trigger("slow", on=False)
            check("overruns: safe stop after consecutive overruns", "consecutive inference overruns" in sim.output())
            time.sleep(4.0)

            # 7. A malformed /joy message is ignored instead of read out of bounds.
            pad.enabled = False
            time.sleep(0.2)
            pad.send_raw(Joy(axes=[0.0, 0.0], buttons=[0]))
            time.sleep(0.5)
            pad.enabled = True
            check("short /joy message ignored, node still up",
                  "Ignoring /joy message" in sim.output() and sim.proc.poll() is None)
        finally:
            sim.stop()
            if FAILS:
                print("---- node output (tail) ----")
                print(sim.output()[-3000:])

    # 8. Joint targets are clamped to joint_limits. Limits narrowed to +-0.05 rad around the default
    # pose so the policy's targets cross them; unclamped, the joints follow and trip the limit check.
    default = params["joint_default_angle"]
    narrow = [x for a in default for x in (a - 0.05, a + 0.05)]
    with tempfile.TemporaryDirectory() as tmp:
        sim = Sim(binary, tmp, extra_params=["joint_limits:=[" + ",".join(f"{x:.4f}" for x in narrow) + "]"])
        try:
            pad.press(X)
            pad.press(A)
            time.sleep(6.5)
            t_run = now()
            pad.press(B)
            time.sleep(3.0)
            run = sim.events(t_run, now())
            outside = [(mid, round(v[0], 3)) for _, mid, k, v in run
                       if k == "mit" and v[2] > 0 and mid not in ankles
                       and not (narrow[2 * (mid - 1)] - 1e-4 <= v[0] * sign[mid - 1] <= narrow[2 * (mid - 1) + 1] + 1e-4)]
            check("narrow limits: every joint target clamped inside them", bool(run) and not outside, str(outside[:3]))
            check("narrow limits: no joint-limit trip while running", "out of limit" not in sim.output())
        finally:
            sim.stop()
            if FAILS:
                print("---- node output (tail) ----")
                print(sim.output()[-2000:])
    node.destroy_node()
    rclpy.shutdown()
    print(f"\n{len(FAILS)} failed" if FAILS else "\nall checks passed")
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
