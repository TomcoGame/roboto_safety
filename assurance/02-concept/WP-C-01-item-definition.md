# WP-C-01 Item Definition

| Field | Value |
|---|---|
| Work product | WP-C-01 Item definition |
| Standard reference | ISO 12100:2010 §5.3 (limits of the machinery); ISO 13849-1:2023 §4 (inputs to safety function design); ISO 10218-1:2025 (robot as machine) |
| Version | 0.2 (zone separation, fall zone and speed limit applied: DQ-013 A, DQ-014 A, DQ-015 A; 2026-10-28). 0.1 (first draft; 2026-10-28) |
| Status | Draft, I0 (AI-authored, not verified). Human review requested |
| Author | Claude (AI assistant) |
| Decisions applied | Intended use: industrial work cell alongside trained workers (DQ-001 B); reference configuration (DQ-008 A); development operating rules (DQ-009 A); zone separation (DQ-013 A); fall into a clear zone accepted (DQ-014 A); speed with a worker in the cell (DQ-015 A) |

## 1. Item identification

The item is one RPO humanoid robot in its reference configuration, with the software that runs on it and the
operator controls that command it.

| Element | Reference configuration (DQ-008 A) |
|---|---|
| Robot | RPO V2.0 mechanics (`modules/rpo_hardware/V2.0`), 23 joints |
| Joint motors | 23 Damiao (DM) motors on 4 CAN buses (6, 7, 5, 5 motors): model 1 (120 N·m peak, 25 rad/s) at hips, knees and torso; model 0 (27 N·m peak, 8 rad/s) at ankles and arms (`robots/rpo/robot.yaml`, `rpo_description/urdf/rpo.urdf`) |
| Compute | RDK X5 8 GB single-board computer, Linux, ROS 2 |
| CAN adapters | 4 × `roboto_usb2can` (STM32G431, Zephyr, `gs_usb` pass-through), one per bus |
| IMU | HiPNUC, serial at 921600 baud |
| Power | 48 V 15 Ah (720 Wh) Li-ion pack; emergency-stop switch on the supply (BOM item 28) |
| Software | A tagged `roboto_safety` release; inference node `modules/roboparty_deploy/src/inference`, default walking policy `policy.onnx` with `configs/default.yaml` |
| Operator input | Gamepad through `joy_node` (`/joy`); `/cmd_vel` as an alternative source |

Mass 33.8 kg (sum of the URDF link masses; to be weighed). Ankle to shoulder 0.98 m in the URDF frames; overall
height with the shell to be measured.

## 2. Purpose and functions

The robot walks on a flat floor inside an industrial work cell, following a velocity command from a trained
operator, while trained workers are present in the cell (DQ-001 B). Manipulation and carrying are not part of the
first claim.

### 2.1 Functions

| ID | Function | Realised by | In the first claim |
|---|---|---|---|
| F-01 | Balance and walk at the commanded velocity (forward −0.4…0.6 m/s, sideways ±0.4 m/s, turn ±0.8 rad/s) | RL policy at 50 Hz; joint PD at 250 Hz in the motors' MIT mode | Yes |
| F-02 | Accept velocity commands from the operator; zero them when input stops | `joy_node`, `/cmd_vel`, input timeout (0.5 s) | Yes |
| F-03 | Operator modes: enable and disable the motors, reset to the default pose, start and pause walking | Gamepad buttons X, A, B; ROS services | Yes |
| F-04 | Hold the pose while enabled and not walking | Hold keep-alive in the control thread | Yes |
| F-05 | Detect faults (fall, joint out of limit, software error, overruns) and stop: damp the joints, then disable the motors | Safe stop in the inference node | Yes |
| F-06 | Stop the motors when commands stop arriving | Motor CAN command timeout (200 ms) | Yes |
| F-07 | Emergency stop: remove power | Red switch on the 48 V supply | Yes |
| F-08 | Soft stop: crouch, then remove power (DQ-006 A) | Not built yet | Planned |
| F-09 | Report state (joint states, IMU, actions) | ROS topics | Yes, QM |
| F-10 | Protective stop when a worker enters the robot's zone; speed limited to 0.3 m/s while a worker is in the cell (DQ-013 A, DQ-015 A) | Safety-rated presence sensor (not chosen) and the soft stop | Planned |

Out of the first claim, joining later by impact analysis: the other policies (parkour, get-up, motion imitation,
interrupt, AMP, attention encoder), XR teleoperation, navigation, depth perception.

## 3. Item boundary

### 3.1 Inside the item

Robot structure and shell; 23 joint motors with their firmware; the 4 CAN adapters with their firmware; IMU; the
RDK X5 with its operating system, ROS 2 and the deployment software; policy model files and configuration; battery
pack and emergency-stop switch; wiring; gamepad and receiver.

### 3.2 Outside the item

| Element | Why it matters |
|---|---|
| Operator | Trained; commands motion, holds the stop, follows the operating rules |
| Workers in the cell | Trained; the people the claim protects alongside the operator |
| Work cell | Floor and boundaries. The robot walks in its own zone; a safety-rated presence sensor around that zone (part of the item once chosen) detects a worker entering (DQ-013 A). Around the robot, a fall zone of at least its height plus a margin is kept clear while it moves (DQ-014 A) |
| Gantry or harness | Development phase: catches the robot on a power cut (DQ-009 A, DQ-017) |
| Other ROS hosts on the network | Can publish to `/cmd_vel` and call services; no authentication today (gap assessment F-10) |
| Charger | Charges the battery outside operation |

### 3.3 Interfaces

| ID | Interface | Between | What crosses it |
|---|---|---|---|
| IF-01 | USB | RDK X5 ↔ CAN adapters | CAN frames (MIT commands, register writes, feedback) |
| IF-02 | CAN (×4) | Adapters ↔ motors | Same frames on the bus |
| IF-03 | Serial | IMU → RDK X5 | Orientation, angular rate |
| IF-04 | ROS 2 DDS (`/joy`, `/cmd_vel`, services) | Operator input and other hosts → inference node | Velocity commands, mode changes |
| IF-05 | 48 V supply via emergency-stop switch | Battery → motors and electronics | Power |
| IF-06 | Physical | Robot ↔ people, floor, objects | Contact, falls |

## 4. Operating modes

| Mode | Motors | Entered by | Left by |
|---|---|---|---|
| M-0 Off | Unpowered | Power switch, emergency stop | Power on |
| M-1 Powered, disabled | Powered, not enabled (limp) | Power on; disable (X twice); end of safe stop | Enable (X) |
| M-2 Enabled, idle | Enabled; zero gains until reset, then hold pose | Enable | Reset, start, disable, safe stop |
| M-3 Reset | Moving to the default pose over 4 s | A | Reset done (M-2) |
| M-4 Walking | Policy commands every joint | B from M-2 | B (pause, M-2), safe stop, disable |
| M-5 Safe stop | Damped (kp 0) for 3 s | Any detected fault | Disable after 3 s (M-1), or X twice |
| M-6 Command lost | Each motor leaves enable mode | No command for 200 ms (process stopped or hung) | Restart and enable |

## 5. Legal requirements and standards

See [WP-M-02](../01-management/WP-M-02-standards-map.md). For this use: EU Machinery Regulation (EU) 2023/1230,
AI Act, Cyber Resilience Act; ISO 12100, ISO 10218-1/-2:2025, ISO 25785-1 (draft), ISO 13849-1, IEC 62061,
IEC 61508, IEC 61800-5-2, IEC 60204-1; US: ANSI/A3 R15.06-2025.

## 6. Known hazards from similar machines

Balancing robots fall when power or control is lost, and the fall is the dominant hazard: a 34 kg robot falling
from about 1 m. Legged robots carry high-torque joints with pinch points at the knee, hip and ankle linkage.
Learned policies behave unpredictably outside their training conditions. Li-ion packs of this size can go into
thermal runaway when damaged or overcharged.

## 7. Assumptions of use (AoU)

Each needs verification; none has any yet.

| ID | Assumption | Verified by |
|---|---|---|
| AOU-01 | A DM motor leaves enable mode (produces no torque) within its configured timeout after the last command, and re-enables on the next enable sequence | Gantry test GT-02, GT-03 ([WP-V-01](../06-validation/WP-V-01-gantry-test-procedure.md)) |
| AOU-02 | The motor firmware limits torque to its rated peak and reports over-current, over-temperature and communication loss | Supplier data; bench test |
| AOU-03 | The battery pack has a battery management system that cuts out on over-current, over-temperature, over- and under-voltage | Supplier data; to obtain |
| AOU-04 | The emergency-stop switch removes power from every motor | Wiring inspection; GT-11 |
| AOU-05 | The cell floor is flat, level and dry | Site rules |
| AOU-06 | Operators and workers are trained and follow the operating rules | Training records |
| AOU-07 | The gantry or harness catches the robot before it reaches the floor | GT-11 |

## 8. Performance

| Quantity | Value | Source |
|---|---|---|
| Mass | 33.8 kg | URDF (to weigh) |
| Walking speed | ≤ 0.6 m/s forward, 0.4 m/s back and sideways, 0.8 rad/s turn | `configs/default.yaml` `clip_cmd` |
| Joint torque, peak | 120 N·m (hips, knees, torso); 27 N·m (ankles, arms) | URDF limits |
| Joint speed, peak | 25 rad/s; 8 rad/s | URDF limits |
| Control rates | Joint commands 250 Hz; policy 50 Hz | `dt` 0.004 s, `decimation` 5 |
| Motor command timeout | 200 ms | `robot.yaml` |
| Battery | 48 V, 15 Ah, 720 Wh | BOM |

## 9. Open items

| ID | Item |
|---|---|
| IOI-01 | Weigh the robot; measure overall height and centre-of-mass height standing |
| IOI-02 | Confirm the emergency-stop wiring: does it cut the motors only, or the computer too? |
| IOI-03 | Obtain the battery pack's protection data (AOU-03) |
| IOI-04 | Record the motor and adapter firmware versions of the reference robot |
