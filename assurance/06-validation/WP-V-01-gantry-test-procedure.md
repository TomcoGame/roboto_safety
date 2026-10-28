# WP-V-01 Gantry Test Procedure: First Powered Runs

| Field | Value |
|---|---|
| Work product | WP-V-01 Gantry test procedure |
| Version | 0.1 (first draft; 2026-10-28) |
| Status | Draft, I0 (AI-authored, not verified). Not yet run |
| Author | Claude (AI assistant) |
| Verifies | Gap assessment §3.1 open items (F-03…F-09); assumptions AOU-01, AOU-04, AOU-07 ([WP-C-01](../02-concept/WP-C-01-item-definition.md)); safety functions SF-02, SF-04, SF-06, SF-07 ([WP-C-03](../02-concept/WP-C-03-integrated-hazard-analysis.md)) |
| Software under test | The `roboto_safety` commit recorded on the record sheet; inference node with the safety fixes of [TomcoGame/roboto_safety#1](https://github.com/TomcoGame/roboto_safety/pull/1) |
| Needs | A gantry or overhead harness (DQ-017); development rules (DQ-009 A) |

## 1. Purpose

The safety fixes pass a simulation with fake motors ([`tests/safety_sim`](../../modules/roboparty_deploy/tests/safety_sim/README.md)).
That says nothing about what the real motors, battery and switch do. These tests answer that, in the order that is
safest to learn it: the robot hanging first, feet on the floor only once the stops are shown to work.

## 2. Rules for every run

1. The robot is in the harness for every test here. Two people: the **operator** holds the gamepad, the **safety
   person** has a hand on the red switch and does nothing else.
2. Nobody inside 2 m of the robot while it is enabled, except to handle it in a step that says so, with the motors
   disabled first.
3. **Stop the run** (red switch, then investigate) on any motion the step does not expect, any smoke, smell or
   noise from a motor or the battery, or any reading outside its pass band.
4. A failed step is recorded as failed. The test is not repeated until the cause is found and recorded.
5. One change at a time: if code or configuration changes between runs, the record sheet gets a new commit and the
   tests that depend on it are re-run.

## 3. Equipment and set-up

| Item | Use |
|---|---|
| Gantry or overhead harness, rated for the robot's mass with margin | Catches the robot; two heights: **hanging** (feet 5 cm clear of the floor) and **slack** (feet on the floor, about 5 cm of slack) |
| Laptop on the robot's network with `can-utils` | `candump -ta any` on all four buses, saved to a file per test |
| Camera, 120 frames/s or faster, with a visible clock or the laptop screen in frame | Timing of motion and limpness |
| Stopwatch | Back-up timing |
| `ros2 topic echo /joint_states`, `ros2 topic hz /joy` | Joint motion, gamepad rate |
| Second terminal on the RDK X5 | Fault injection (`kill -STOP`, `kill -9`, `stress-ng`) |

Record before the first test: robot mass (IOI-01), motor and adapter firmware versions (IOI-04), battery voltage,
`roboto_safety` commit, the `robot.yaml` and policy config in use.

How to see that a motor has left enable mode: in `candump`, each DM feedback frame carries the motor state in the
high nibble of byte 0 (0 disabled, 1 enabled, 0xD communication lost; `dm_motor_driver.hpp` `DMError`). A motor
that has left enable mode stops answering commands with enabled state; on the robot, the joint goes limp and can be moved by hand (only once the step allows
touching). Record which one you used.

## 4. Tests

Run in this order. Each test lists what it shows, the steps, and the pass criterion.

### GT-01 Enable produces no motion

Shows: SF-06 (no motion on enable), cleared targets. Height: hanging.

1. Start the node. Press X once.
2. Watch every joint for 10 s on camera and in `/joint_states`.

**Pass:** no joint moves more than 0.02 rad; the log says "Motors initialized"; `candump` shows commands to every
motor at about 250 Hz with kp = 0.

### GT-02 Motor command timeout: unit and behaviour

Shows: AOU-01, F-03. Height: hanging.

1. Enable (X), reset (A), wait for "Motors reset". The robot holds its default pose.
2. Read back the timeout register of motor 1 on `can0`:
   `cansend can0 7FF#01003309FFFFFFFF` (the read frame `DmMotorDriver::get_motor_param` sends: motor id, `0x33` read, register 9) and find the reply in `candump`. Expected value 4000 (bytes `A0 0F 00 00`),
   which is 200 ms at 50 µs per count. Repeat for one motor on each bus.
3. On the RDK X5: `kill -9 <pid of the inference node>`. Start the camera before this.
4. From the camera and `candump`, measure the time from the last command frame to the joints going limp.

**Pass:** register reads 4000 on every motor read; every joint goes limp between 150 and 300 ms after the last
command. If the register reads otherwise, or nothing goes limp within 1 s, the unit or register in
`DmMotorDriver::set_can_timeout_ms` is wrong: **stop and fix before any other test**.

### GT-03 Recovery after a timeout

Shows: AOU-01 second half. Height: hanging.

1. After GT-02, restart the node and press X.
2. Note whether all 23 motors enable, and whether the `clear_errors` service is needed first.

**Pass:** recorded either way. If `clear_errors` is needed, record it as an open item for the enable sequence.

### GT-04 Frozen computer

Shows: SF-02 against a hang rather than a crash. Height: hanging.

1. Enable, reset, hold.
2. `kill -STOP <pid>` (the process stays alive but stops).
3. Measure as GT-02, then `kill -CONT <pid>`.

**Pass:** limp between 150 and 300 ms after the last command. After `kill -CONT`, the node does not move the robot
until X, A and B are pressed again.

### GT-05 Hold keep-alive

Shows: F-04; that the timeout does not trip in normal idle. Height: hanging.

1. Enable, reset, then leave it idle for 120 s. Then press A again and wait for the reset to finish.

**Pass:** pose held throughout with no joint going limp; in `candump`, no gap longer than 100 ms between commands
to any motor, including during the 1 s status refresh at the start of the second reset.

### GT-06 Two-press disable

Shows: F-07. Height: hanging.

1. Enabled and holding. Press X once; wait 2 s.
2. Press X twice within 1 s.

**Pass:** after one press, nothing changes and the log says "Press 'X' again"; after two, every joint goes limp.

### GT-07 Safe stop on a fall

Shows: F-05, SF-07 (detection and damping). Height: hanging.

1. Set `gravity_z_upper` lower for this test only, so a tilt of about 15° trips it (record the value used).
2. Enable, reset, start walking in place (B, sticks centred).
3. The safety person tilts the robot in the harness past the threshold.
4. Observe for 5 s.

**Pass:** the log says "Safe stop: … robot fell"; the joints resist motion but do not hold the pose (damped) for
3.0 ± 0.3 s, then go limp; B is refused during the damping. Restore `gravity_z_upper` afterwards.

### GT-08 Safe stop on overruns, and no false trips

Shows: F-05 overrun threshold on the real computer. Height: hanging.

1. Walk in place for 10 minutes with normal load. Count overrun warnings and safe stops.
2. Then run `stress-ng --cpu 0 --timeout 20s` while walking in place.

**Pass:** step 1 has no safe stop (record the number of overrun warnings); step 2 ends in a safe stop naming the
overruns, or records that the computer kept up under load.

### GT-09 Gamepad loss

Shows: F-06 and the `joy_node` autorepeat assumption. Height: slack, feet on the floor.

1. With the sticks held still: `ros2 topic hz /joy` for 10 s.
2. Enable, reset, start, walk slowly forward (half stick).
3. Switch the gamepad off.

**Pass:** step 1 reads at least 15 Hz; after step 3 the log says "No velocity command" within 0.7 s and the robot
stops walking forward within 2 s (stepping in place is acceptable).

### GT-10 Joint limits under the clamp

Shows: F-01. Height: hanging.

1. Narrow `joint_limits` for one knee by 0.1 rad on each side of its default angle (record the values).
2. Walk in place for 60 s.

**Pass:** that knee stays inside the narrowed band in `/joint_states` (allow 0.02 rad overshoot) and no
joint-limit safe stop occurs; if one does, record the overshoot.

### GT-11 Emergency stop and harness catch

Shows: SF-04, AOU-04, AOU-07; fall kinematics for HOI-03. Height: hanging, then slack.

1. Hanging, enabled and holding: press the red switch. Check every joint is limp and the computer state (on or off;
   IOI-02).
2. Slack, walking in place: press the red switch. Film from the side.

**Pass:** all motors unpowered at once; in step 2 the harness stops the robot before any part other than the feet
touches the floor. Record the drop distance and the highest speed of the head or shoulder from the film.

### GT-12 Damping feel (input to the soft stop)

Shows: how the damped safe stop behaves with weight on the legs; input to DQ-006 A's crouch. Height: slack.

1. Standing (reset), trigger a safe stop by the GT-07 method.
2. Film how the robot sinks during the 3 s of damping.

**Pass:** recorded (sink speed, whether it buckles at one joint). No pass band yet; this sets one for the soft stop.

## 5. Record sheet

One row per step, kept with the `candump` files and video in the evidence store.

| Test | Date | Commit | Operator | Safety person | Result (pass / fail / recorded) | Measured values | Notes, deviations |
|---|---|---|---|---|---|---|---|
| GT-01 | | | | | | | |

A failed or stopped test is a finding: it goes to the gap assessment with the record attached, and the fix comes
back through a reviewed pull request.
