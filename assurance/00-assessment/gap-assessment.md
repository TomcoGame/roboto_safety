# Baseline Gap Assessment: ROBOTO_ORIGIN (RPO) as found

| Field | Value |
|---|---|
| Work product | Baseline gap assessment |
| Baseline | `roboto_safety` at `c71fd92` (snapshot of Roboparty `roboto_origin`, sub-repositories under `modules/`) |
| Version | 0.2 (F-14 resolution recorded, DQ-002 A; 2026-10-26). 0.1 (first review; 2026-10-26) |
| Status | Draft, I0 (AI-authored, not verified). Human review requested |
| Author | Claude (AI assistant) |

## 1. What was reviewed

`roboto_safety` is a fork of Roboparty's `roboto_origin` aggregation repository: daily snapshots of eight
sub-repositories for the ROBOTO_ORIGIN / RPO open-source biped humanoid. This review looked at the paths that decide
whether the robot moves and how it stops:

| Area | Path | What it is |
|---|---|---|
| Deployment | `modules/roboparty_deploy/src/inference` | ROS 2 node: reads IMU and joints, runs the RL policy (ONNX), turns actions into joint position targets |
| Motor drivers | `modules/roboparty_deploy/src/motors` | CAN / CAN FD drivers for DM, EVO, LRO and XYN joint motors (MIT mode: position, velocity, kp, kd, feed-forward torque) |
| Robot config | `modules/roboparty_deploy/src/inference/robots/rpo` | 23 joints on 4 CAN buses, all DM motors; gains, signs, zero offsets; one config per policy |
| CAN adapters | `modules/roboparty_firmware/roboto_usb2can` | Zephyr firmware for an STM32G431 USB-to-CAN adapter (`gs_usb` / candleLight protocol), one per bus |
| Training | `modules/roboparty_train` | IsaacLab RL training, sim-to-sim transfer to MuJoCo |
| Teleoperation | `modules/roboparty_xr_teleop` | XR headset arm teleoperation through IK |
| Hardware | `modules/rpo_hardware`, `assets/BOM_EN.md` | Mechanics, PCB, bill of materials: RDK X5 compute board, 48 V 15 Ah Li-ion pack, emergency-stop switch |

Not reviewed in depth yet: the board support build (`orangepi-build`, `x5-rdk-gen`), navigation, the motor
vendors' own firmware (closed), the training reward design, and the mechanical design.

## 2. Architecture as found

```
 Gamepad (/joy) ─┐                                                         48 V battery
 /cmd_vel topic ─┼─▶ RDK X5 SBC (Linux, ROS 2)                                   │
 XR teleop ──────┘   inference_node: IMU + joints ─▶ RL policy (ONNX) ─▶          E-stop (BOM 28)
                     action clip ─▶ PD targets ─▶ MIT command per joint           cuts power
                              │ USB                                               │
                              ▼                                                   ▼
                     4 × roboto_usb2can (STM32G431, gs_usb pass-through) ─▶ CAN ─▶ 23 joint motors (DM)
```

Every command the policy produces reaches the motors unchanged except for one clip. There is no element between the
policy and the actuators whose job is safety. The nearest LionDriver analogue would be the panda safety MCU; here
the USB-to-CAN adapters sit in the same place in the chain but only pass frames through.

## 3. Findings

Each finding names the gap and the code behind it. "Hazard" is the plain-language consequence, not yet a rated
hazard; ratings come from the hazard analysis (WP-C-03, not yet written).

| # | Finding | Evidence | Hazard |
|---|---|---|---|
| F-01 | **No independent safety layer.** Policy output goes to joint targets with one clip, and that clip is set to ±100 (normalised action units), which bounds nothing in practice. No joint position, velocity or torque limit is enforced anywhere in software | `robots/rpo/configs/default.yaml:20`; `src/inference_node.cpp:393`; `src/robot_interface.cpp:168-240` | A policy fault or bad output drives a joint at full motor capability |
| F-02 | **Ankle feed-forward torque is unbounded.** For the closed-chain ankles the code computes a PD torque, maps it through the decoupling, and sends it as feed-forward torque with kp = kd = 0 | `src/robot_interface.cpp:196-232` | A large position error commands the full torque the motor will produce |
| F-03 | **No command watchdog in the motors.** The DM driver knows the motor's CAN timeout register (`DM_TIMEOUT`), but the deployment never sets it. What a motor does when commands stop (hold last target, go limp, fault) is not configured or known | `src/motors/src/drivers/dm/dm_motor_driver.hpp:43`; `dm_motor_driver.cpp:123-131` | If the SBC hangs, joints keep following the last command, or drop, depending on the motor's default |
| F-04 | **A crash leaves motors as they were.** An exception in the control loop calls `rclcpp::shutdown()`; motors are not commanded to any safe state | `src/inference_node.cpp:404-408` | Same as F-03, triggered by any software exception |
| F-05 | **Deadline overruns only warn.** A control loop overrun is logged and the loop carries on | `src/inference_node.cpp:412-421` | Stale or late commands during dynamic motion, with no reaction |
| F-06 | **No gamepad timeout.** The last velocity command stays in force if the gamepad stops sending. `/joy` axes are also read by index without a size check (out-of-bounds read on a short message) | `src/ros_interface.cpp:297-308` | Robot keeps walking after the operator loses the link |
| F-07 | **One button disables every motor.** Button X toggles motor init/deinit; deinit unlocks (disables) all motors at once, with no confirmation and no check that the robot is supported | `src/ros_interface.cpp:310-325`; `dm_motor_driver.cpp:168-171` | A stray press while walking makes the robot collapse |
| F-08 | **The only stop is a power cut.** The BOM has one emergency-stop switch on the 48 V supply. Cutting power to a dynamically balanced robot makes it fall (IEC 60204-1 stop category 0). There is no controlled stop (category 1) and no protective stop that keeps balance | `assets/BOM_EN.md` item 28 | The stop function itself creates a fall and a struck-by hazard |
| F-09 | **No fall detection or fall response.** Nothing detects loss of balance, damps the joints for impact, or stops a policy fighting a fall | inference node: no such state | Uncontrolled flailing during a fall; damage; pinch and strike |
| F-10 | **Any ROS node can command motion.** `/cmd_vel` is accepted from any publisher; DDS security (SROS 2) is not used; XR teleop drives arms over the network | `src/ros_interface.cpp:416`; no SROS 2 config | Unintended or malicious motion commands |
| F-11 | **ML policies are unbounded and unmonitored.** Several RL policies (walk, parkour, get-up, motion imitation, interrupt) are selectable at run time. Nothing monitors whether the robot is inside the conditions a policy was trained for | `robots/rpo/configs/*.yaml`; `src/ros_interface.cpp:356-407` | Sim-to-real gap and out-of-distribution behaviour reach the actuators directly |
| F-12 | **Single-channel compute and adapters.** One Linux SBC; four single-channel adapters each seeing only its own bus. The STM32G431 is not a safety MCU (no lockstep core, no safety manual from the supplier) | `roboto_usb2can/readme.md`; `boards/roboto_usb2can/*.dts` | Limits the safety integrity any claim can reach without added hardware |
| F-13 | **No requirements, hazard analysis, tests or reviews.** The deployment package has no tests; no safety documentation exists | `modules/roboparty_deploy` (no test directory) | No evidence for any safety claim |
| F-14 | **Upstream controls the code.** Modules are snapshots of Roboparty repositories, synced daily. Changes made here are overwritten by the next sync unless the fork stops syncing or carries patches | `README.md` "About This Repository"; `RENAME_PLAN.md` | The assured configuration can change without our review. *Resolved by decision 2026-10-26 (DQ-002 A): own pinned fork, upstream merged only by reviewed PR* |

### What is already good

- Motor-offline detection (`throw_if_motors_offline`, `src/robot_interface.cpp:396`) refuses to run with a silent motor.
- ONNX input-size checks at load (`src/inference_node.cpp:99-107`), observation clipping, and a smooth 4-second joint reset.
- The control thread is pinned to a core, runs `SCHED_FIFO` and locks its memory: a sound base for timing analysis.
- The adapters are on every bus between the SBC and the motors, and their firmware is small (586 lines, Zephyr) and open. That is the natural place for a safety envelope, the way the panda is for LionDriver.

## 4. Proposed first engineering actions (tasks, not decisions)

These are low-regret and do not wait on the lead. They become requirements once the safety concept exists.

1. Configure and verify each motor's CAN command timeout and the motor's behaviour on timeout (F-03).
2. Add a `/joy` and `/cmd_vel` staleness timeout that brings commanded velocity to zero; check message sizes (F-06).
3. On control-loop exception or repeated overrun, go to a defined damped state instead of shutting down (F-04, F-05).
4. Put per-joint position, velocity and torque limits in the deployment, taken from the URDF and motor data (F-01, F-02).
5. Make motor disable a two-step action (hold, or a button combination) (F-07).
6. Characterise what the robot does on power cut, motor timeout and SBC freeze, on a gantry, and record it (F-03, F-08).

## 5. What carries over from LionDriver, and what does not

| Carries over | Does not carry over |
|---|---|
| Envelope pattern: a small, verified element between the ML stack and the actuators (§2; WP-M-01 §4) | ISO 26262 ASIL ratings: machinery uses ISO 13849-1 PL or IEC 62061 / IEC 61508 SIL |
| Integrated hazard analysis across malfunction, ML insufficiency, misuse and attack (LionDriver HATARA) | Driver controllability: here there is no supervising driver; bystanders and operators must be protected by distance, speed and force limits |
| Decision register and inbox; Living Safety Case records and validator; requirements trace tooling; terms registry | Vehicle assumptions of use (EPS, PCS): replaced by motor, battery and structure assumptions |
| Upstream management (comma.ai ↔ Roboparty), impact analysis, AI-authored work as I0 | — |
