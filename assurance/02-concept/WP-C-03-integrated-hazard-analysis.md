# WP-C-03 Integrated Hazard Analysis

| Field | Value |
|---|---|
| Work product | WP-C-03 Integrated hazard, misuse and threat analysis (H1 of the claim structure) |
| Standard reference | ISO 12100:2010 §5.4–5.6 (hazard identification, risk estimation); ISO 13849-1:2023 Annex A (required performance level); ISO 10218-2:2025 (contact); ISO 25785-1 draft (stability); ISO/SAE 21434 attack feasibility, used as a method; HATARA interaction types (Kriaa et al.), as on LionDriver |
| Version | 0.2 (ratings settled for zone separation (DQ-013 A) and a fall into a clear zone (DQ-014 A); SF-05 defined (DQ-015 A); second channel (DQ-012 A); 2026-10-28). 0.1 (first draft; 2026-10-28) |
| Status | Draft, I0 (AI-authored, not verified). **Every rating is a proposal** for review |
| Author | Claude (AI assistant) |
| Inputs | [WP-C-01 item definition](WP-C-01-item-definition.md); [gap assessment](../00-assessment/gap-assessment.md); decisions DQ-001 B (industrial cell), DQ-004 A (one integrated analysis), DQ-006 A (two-tier stop), DQ-009 A (development rules) |
| Decisions applied | Zone separation (DQ-013 A); fall into a clear zone accepted (DQ-014 A); speed limit (DQ-015 A); second channel before the industrial claim (DQ-012 A) |

## 1. Method

One analysis covers every cause of harm. Each hazardous event lists its causes under four headings, so a hazard is
rated once whatever brings it about:

| Code | Cause | Examples on RPO |
|---|---|---|
| **M** | Malfunction of an electrical or electronic element | Motor fault, CAN loss, computer hang, IMU error, adapter firmware fault |
| **I** | Insufficiency of the intended function, mostly the learned policy | Out-of-distribution floor or push, sim-to-real gap, wrong arm swing near a person |
| **U** | Reasonably foreseeable misuse | Too fast near workers, untested policy run unsupported, untrained person in the cell |
| **A** | Attack | Rogue `/cmd_vel` publisher on the open DDS network, tampered adapter firmware or policy file |

Steps:

1. **Hazards** H-01…H-10 from ISO 12100 Annex B hazard types applied to the robot (§3), and from the functions of
   WP-C-01 §2.1 with the guide words no / unintended / excessive / late / stuck / wrong direction.
2. **Operational situations** OS-01…OS-08 (§2), from the intended use and the development rules.
3. **Hazardous events** (§4): hazard × situation, with causes, the worst credible harm, and the ISO 13849-1
   risk-graph parameters:

   | Parameter | 1 | 2 |
   |---|---|---|
   | S, severity | Slight, normally reversible injury | Serious, irreversible injury or death |
   | F, frequency or duration of exposure | Seldom to less often, or short | Frequent to continuous, or long |
   | P, possibility of avoiding | Possible under some conditions | Scarcely possible |

   PLr from the graph: S1F1P1 a · S1F1P2 b · S1F2P1 b · S1F2P2 c · S2F1P1 c · S2F1P2 d · S2F2P1 d · S2F2P2 e.
   ISO 13849-1:2023 allows one level lower where the hazardous event is rarely demanded; no such credit is taken here.
4. **Attack causes** carry an attack feasibility (high, medium, low, very low) from the access needed. A feasible
   attack is treated as a cause like any other: it does not lower the rating.
5. **Safety functions** SF-01…SF-10 (§5) are named for each event. Each takes the highest PLr of its events, and
   that PLr is what the safety concept (G1) must meet.
6. **Interactions** (§6): where a safety measure opens a security weakness or the reverse, recorded as on
   LionDriver's HATARA.

## 2. Operational situations

| ID | Situation | Notes |
|---|---|---|
| OS-01 | Walking in the cell, no worker within 2 m | Depends on DQ-013: zone separation makes this the normal case |
| OS-02 | Walking in the cell, a worker within 2 m | Shared space; the normal case if workers and robot mix freely |
| OS-03 | Enabled and standing, a worker within reach | Hand-over, inspection, adjustment |
| OS-04 | Enabling, resetting or disabling with the operator close by | Start-up and shut-down; robot often held or on the gantry |
| OS-05 | On the gantry or harness (development) | DQ-009 A; operator next to it |
| OS-06 | Handled while disabled or unpowered | Carrying, charging, maintenance |
| OS-07 | Fallen or falling, a worker moving in to help | After any fall |
| OS-08 | Battery charging or stored | Outside operation |

## 3. Hazards

| ID | Hazard | ISO 12100 type | Energy behind it |
|---|---|---|---|
| H-01 | Robot falls | Mechanical: loss of stability, falling object | 34 kg from about 1 m; head and shoulders reach about 5 m/s when it tips over rigidly |
| H-02 | Unintended or excessive limb motion | Mechanical: impact | Leg joints 120 N·m at up to 25 rad/s; arm joints 27 N·m at 8 rad/s (arm tip ≈ 3–4 m/s) |
| H-03 | Walks in an unintended direction, too fast, or keeps walking | Mechanical: impact, plus pushing the robot over (H-01) | 34 kg at up to 0.6 m/s |
| H-04 | Pinch or crush at a joint or between the robot and an object | Mechanical: crushing, shearing | Up to 120 N·m at the knee and hip |
| H-05 | A stop does not act, acts late, or causes a fall | Control: failure of the stop function | Whatever the stop should have ended |
| H-06 | Unexpected start: motion on enable, reset or resume while someone handles the robot | Control: unexpected start-up | As H-02, H-04 |
| H-07 | Collapse while being handled | Mechanical: falling object | 34 kg onto feet or hands |
| H-08 | Battery fire or thermal runaway | Thermal, fire | 720 Wh Li-ion |
| H-09 | Hot motor surfaces | Thermal: burn | Coil over-temperature |
| H-10 | Operator or worker believes the robot is disabled when it is enabled | Control: mode confusion; leads to H-04, H-06 | — |

## 4. Hazardous events and risk estimation

The lead chose **zone separation** (DQ-013 A): workers enter the robot's zone only when it has stopped. Ratings
below use it; the rating under **mixed** use (workers moving freely around a walking robot) is kept in brackets to
show why mixed use is outside the claim. A worker inside the zone of a walking robot is now foreseeable misuse or a
failure of the zone sensor, which is what OS-02 and OS-03 cover.

### 4.1 H-01 Robot falls

| HE | Situation | Harm | Causes | S | F | P | PLr | Rationale |
|---|---|---|---|---|---|---|---|---|
| HE-01.1 | OS-02 walking near a worker | Robot falls onto the worker | M: motor fault, CAN loss, IMU error, computer hang (limp on timeout). I: slip, push, obstacle outside training. U: speed too high near people. A: rogue `/cmd_vel` drives it into an obstacle | S2 | F1 (F2 mixed) | P2 | **d** (e mixed) | S2: 34 kg falling from 1 m onto the head or a knee can fracture. P2: a fall develops in under a second and gives no warning. Zone separation keeps people out of the fall zone while it walks, so exposure is short and rare (F1). Mixed use would make it frequent (F2), and PL e is not reachable on this hardware |
| HE-01.2 | OS-01 walking, nobody within 2 m | Damage only | As HE-01.1 | — | — | — | none | No person in reach. Accepted: a fall into a clear fall zone is an acceptable outcome (DQ-014 A) |
| HE-01.3 | OS-07 robot falling while a worker steps in to help | Robot or a flailing limb strikes the helper | M, I: policy fights the fall. U: worker reaches for the robot | S2 | F1 | P2 | **d** | Rare, short exposure. The safe stop damps the joints on fall detection (gap assessment §3.1) |
| HE-01.4 | OS-05 on the gantry, power cut | Robot swings or hits the frame; operator struck | U: harness slack too long | S1 | F2 | P1 | **b** | Development only; harness length is set per GT-11 |

### 4.2 H-02 Unintended or excessive limb motion

| HE | Situation | Harm | Causes | S | F | P | PLr | Rationale |
|---|---|---|---|---|---|---|---|---|
| HE-02.1 | OS-03 standing, worker within reach | Arm or leg strikes the worker's head or body | M: wrong target, motor runaway. I: policy output spike. A: injected command or tampered policy file | S2 | F1 (F2 mixed) | P2 | **d** (e mixed) | S2: a leg joint at 120 N·m can break bones; an arm at 3–4 m/s can injure the head. P2: sudden. In a separated cell workers come within reach only with the robot stopped |
| HE-02.2 | OS-02 walking near a worker | Swinging arm strikes a passer-by | I: arm swing wider than expected | S1 | F2 | P1 | **b** | Arm swing during walking is visible and slow enough to step back from; body-region contact limits (ISO 10218-2) to check at G1 |

### 4.3 H-03 Walks wrongly or keeps walking

| HE | Situation | Harm | Causes | S | F | P | PLr | Rationale |
|---|---|---|---|---|---|---|---|---|
| HE-03.1 | OS-02 | Robot walks into a worker; bump, trip, then H-01 | M: stale command, gamepad link lost (fixed in software by the 0.5 s input timeout). I: policy drifts. U: operator inattentive. A: rogue `/cmd_vel` (feasibility **high**: any host on the network, no authentication) | S1 | F2 | P1 | **b** | Direct impact at 0.6 m/s is about 6 J: bruising. The serious outcome is the fall it causes, rated in HE-01.1 |
| HE-03.2 | OS-01 | Robot leaves its zone into a worker area | As HE-03.1 | S2 | F1 | P1 | **c** | Worst case is H-01 in the worker area; the zone boundary itself is the protective measure (DQ-013) |

### 4.4 H-04 Pinch or crush

| HE | Situation | Harm | Causes | S | F | P | PLr | Rationale |
|---|---|---|---|---|---|---|---|---|
| HE-04.1 | OS-03, OS-04 hands near the knee, hip or ankle linkage while enabled | Finger or hand crushed | M, I: joint moves while held. U: handling while enabled. H-10 mode confusion | S2 | F1 | P2 | **d** | 120 N·m closes the knee far faster than a hand can withdraw |
| HE-04.2 | OS-06 handled while disabled | Pinch as a limp joint folds under gravity | U: lifting by a limb | S1 | F1 | P1 | **a** | Gravity only; information for use |

### 4.5 H-05 Stop fails, is late, or causes a fall

| HE | Situation | Harm | Causes | S | F | P | PLr | Rationale |
|---|---|---|---|---|---|---|---|---|
| HE-05.1 | Any, a stop demanded to end H-01…H-04 | The harm the stop should have ended | M: switch contact welded, wiring fault, software stop path hung. A: CPU starvation delays the software stop | S2 | F1 | P2 | **d** | A stop function takes the PLr of what it protects against. ISO 10218-1 also sets its own minimum for the emergency stop; to confirm against the 2025 text |
| HE-05.2 | OS-02 or OS-03, a stop demanded near a worker | The stop itself drops the robot onto the worker | Design: power cut is category 0 on a balancing robot (gap assessment F-08) | S2 | F1 (F2 mixed) | P2 | **d** (e mixed) | This is why the soft stop crouches before power is removed (DQ-006 A) and why the red button is used with the robot supported during development |

### 4.6 H-06 Unexpected start

| HE | Situation | Harm | Causes | S | F | P | PLr | Rationale |
|---|---|---|---|---|---|---|---|---|
| HE-06.1 | OS-04 operator holding the robot at enable or reset | Struck or pinched as joints move | M: stale targets replayed at enable (fixed in software: targets cleared). U: reset (A) pressed while someone holds it. A: reset service called remotely | S2 | F1 | P2 | **d** | Reset moves every joint over 4 s with 40 % gain; enabling should produce no motion at all |
| HE-06.2 | OS-03 walking resumed while a worker is in reach | As HE-02.1 | U: B pressed with a worker nearby. A: start service called remotely | S2 | F1 | P2 | **d** | — |

### 4.7 H-07 to H-10

| HE | Situation | Harm | Causes | S | F | P | PLr | Rationale |
|---|---|---|---|---|---|---|---|---|
| HE-07.1 | OS-04 disable or safe-stop end while held | Robot collapses onto feet or hands | U: X pressed twice while holding. M: command loss (limp in 200 ms) | S2 | F1 | P1 | **c** | 34 kg onto a foot can fracture toes; the drop is visible to the person holding it |
| HE-08.1 | OS-08 charging, or a damaged pack in use | Fire, burns, smoke | M: cell fault, no or failed battery management (AOU-03). U: damaged pack used | S2 | F1 | P2 | **d** | Not a control-system safety function unless the robot monitors the pack; handled through AOU-03 and the charging procedure first |
| HE-09.1 | OS-06 touching a motor after walking | Burn | M: over-temperature | S1 | F1 | P1 | **a** | Information for use and guarding |
| HE-10.1 | OS-03, OS-04 | Person handles an enabled robot believing it disabled; leads to HE-04.1, HE-06.1 | Design: no visible enabled indication; only the log says | S2 | F1 | P1 | **c** | An enabled-state lamp or sound is the measure (SF-10) |

## 5. Safety functions and required performance levels

| ID | Safety function | Events | PLr | Today |
|---|---|---|---|---|
| SF-01 | Joint envelope: position, speed and torque limits enforced outside the policy | HE-02.1, HE-04.1, HE-06.1 | d | Position clamp in software on the computer; no speed or torque limit; nothing outside the computer yet. Adapters first (DQ-007 A), second channel before G3 (DQ-012 A) |
| SF-02 | Command-loss stop: motors stop when commands stop | HE-01.1, HE-03.1, HE-05.1 | d | 200 ms motor timeout set; unverified on the motors (AOU-01) |
| SF-03 | Soft stop: crouch, then remove power | HE-05.2, HE-01.1 | d | Not built (F-08). The software safe stop damps the joints instead |
| SF-04 | Emergency stop: red switch removes motor power | HE-05.1 | d (and the ISO 10218-1 minimum) | Switch fitted; single channel; wiring unverified (AOU-04) |
| SF-05 | Protective stop when a worker enters the robot's zone (soft stop); 0.3 m/s while a worker is in the cell (DQ-013 A, DQ-015 A) | HE-01.1, HE-02.1, HE-03.2 | d | Not built; needs a safety-rated presence sensor (to choose) |
| SF-06 | Prevention of unexpected start: no motion on enable; reset and start only by a deliberate local action | HE-06.1, HE-06.2 | d | Targets cleared at enable (software); reset and start accept remote service calls |
| SF-07 | Fall response: detect the fall, damp the joints, keep the fall zone clear | HE-01.1, HE-01.3 | d | Tilt detection and damped safe stop in software; fall zone kept clear by SF-05 (DQ-014 A) |
| SF-08 | Only authorised sources may command motion | HE-01.1, HE-02.1, HE-03.1, HE-06 | d (as the functions it protects) | Not built: DDS without security (gap assessment F-10) |
| SF-09 | Battery protection | HE-08.1 | d, or covered by AOU-03 | Unknown (AOU-03) |
| SF-10 | Enabled-state indication | HE-10.1 | c | Not built |

**What the table says.** With zone separation (DQ-013 A) and a fall into a clear zone accepted (DQ-014 A), every
safety function needs PL d; mixed use would push the fall, limb and stop functions to PL e. PL d needs a two-channel
structure with diagnostics (category 3) for most of these functions, which the adapters alone do not give; the
second channel comes before the industrial claim (DQ-012 A).

## 6. Safety and security interactions

| ID | Interaction | Type | What follows |
|---|---|---|---|
| IX-01 | The command-loss stop (SF-02) is a lever for denial of service: whoever can stall the computer or flood the USB or CAN path can make every motor go limp | Antagonism, safety → security | Safe only while the stop is itself safe. Until the soft stop exists, a forced stop is a fall: keep workers out of the fall zone (SF-07) |
| IX-02 | The overrun trip of the safe stop can be triggered by loading the CPU | Antagonism, safety → security | As IX-01; process isolation on the computer (CPU reservation for the control threads) reduces both the fault and the attack |
| IX-03 | Installing the envelope in the adapters (DQ-007 A) needs a firmware update path; today it is unsigned USB DFU from the computer | Antagonism, safety → security | The envelope is only as trustworthy as its update path. Signed adapter firmware, and a lock against updates while enabled |
| IX-04 | Rejecting an unauthenticated command (SF-08) looks to the robot like command loss | Mutual reinforcement | It ends in the input timeout (zero velocity), which is already the safe reaction. Specify and verify once |
| IX-05 | Remote reset and start services make operation convenient, and give an attacker motion (HE-06) | Antagonism, safety → security | Reset and start should need a local, deliberate action; remote services only stop |

## 7. Open items

| ID | Item |
|---|---|
| HOI-01 | ~~Re-rate F once DQ-013 and DQ-014 are answered~~ done in v0.2 |
| HOI-02 | Check the 2025 texts of ISO 10218-1/-2 for the minimum PL of the emergency stop and protective stop, and for body-region contact limits (HE-02.2) |
| HOI-03 | Measure fall kinematics on the gantry (GT-11) to replace the 5 m/s estimate |
| HOI-04 | Extend to the policies outside the first claim, one at a time, with an impact analysis |
| HOI-05 | Add generators and CI checks for this analysis, as LionDriver has, once the ratings settle |
