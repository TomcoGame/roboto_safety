# Safety behaviour simulation test

Runs the real inference node sources (`src/inference/src/*.cpp`) against fake motor and IMU drivers
(`fake_drivers.cpp`), drives it with `/joy` messages, and checks how it commands the motors:

| Scenario | What is checked |
|---|---|
| Enable (X) | Command timeout set on all 23 motors; enabled-but-idle motors keep being commanded; no stale targets replayed |
| Joint reset (A) | Motors never go uncommanded longer than half the timeout, including the 1 s status refresh |
| Gamepad silent | Velocity command drops to zero after `cmd_timeout` |
| Disable (X) | One press does nothing; two presses within 1 s disable all motors and clear the timeout |
| Fall (IMU tilt) | Safe stop: joints damped (kp 0, kd from `robot.yaml`) for `safe_stop_damp_time`, then disabled; start refused meanwhile; X re-enables |
| Slow inference | Consecutive overruns trigger the safe stop |
| Malformed `/joy` | Ignored, node stays up |
| Narrow joint limits | Joint targets clamped inside `joint_limits`; no limit trip |

It needs no CAN hardware. It does **not** show how the real motors behave (timeout units, what a
motor does when it times out, damping feel); that needs the gantry tests.

## Run

Ubuntu 24.04 with ROS 2 Jazzy (`ros-jazzy-rclcpp`, `ros-jazzy-rclpy`, `sensor-msgs`, `geometry-msgs`,
`std-srvs`), plus `libeigen3-dev libspdlog-dev libfmt-dev zlib1g-dev`, on x86_64:

```sh
source /opt/ros/jazzy/setup.bash
cmake -S modules/roboparty_deploy/tests/safety_sim -B /tmp/safety_sim
cmake --build /tmp/safety_sim -j
python3.12 modules/roboparty_deploy/tests/safety_sim/run_safety_sim.py /tmp/safety_sim/safety_sim_node
```

Each check prints PASS or FAIL; the exit code is the number of failures. A full run takes about
two and a half minutes. Against the code before these safety changes (`c71fd92`), 20 of the 26
checks fail.
