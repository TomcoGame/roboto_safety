# WP-M-01 Assurance Strategy

| Field | Value |
|---|---|
| Work product | WP-M-01 Assurance strategy and lifecycle tailoring |
| Version | 0.1 (first draft; 2026-10-26) |
| Status | Draft, I0 (AI-authored, not verified). Most choices below wait on the lead (§6) |
| Author | Claude (AI assistant) |
| Approver | Project lead (safety authority) |

## 1. Purpose

The assurance path for the RPO humanoid: what we will claim and for which configuration, the architecture that makes
the claim reachable, how the standards are applied ([WP-M-02](WP-M-02-standards-map.md)), the phases and gates, and
what we reuse from LionDriver. The starting point is the [gap assessment](../00-assessment/gap-assessment.md).

## 2. Starting point

- RPO is a 23-joint open-source biped from Roboparty. Its RL policies send joint targets straight to the motors; no
  element in the chain has a safety job (gap assessment F-01…F-09).
- The only stop is a power cut, which makes a balancing robot fall (F-08).
- No requirements, hazard analysis, tests or reviews exist (F-13). The code is a daily snapshot of upstream
  repositories we do not control (F-14).
- The hardware is low-cost COTS: a Linux SBC, four STM32 USB-to-CAN adapters, hobby-grade joint motors with closed
  firmware, a 48 V Li-ion pack.

## 3. What we will claim (proposed)

### 3.1 Reference configuration

| Element | Proposed reference (DQ-008) |
|---|---|
| Robot | RPO V2.0 mechanics, 23 DM joint motors on 4 CAN buses, HiPNUC IMU (`robots/rpo/robot.yaml`) |
| Compute | RDK X5 8 GB, the board image built from `roboparty_firmware` at a pinned commit |
| Software | A tagged `roboto_safety` release pinning every module by commit |
| Function | Walking on flat ground under gamepad velocity command, default policy only (`configs/default.yaml`) |
| Use | Development phase: indoors, lab, trained operators, robot on a gantry or harness until the stop ladder is verified (DQ-009) |

Other policies (parkour, get-up, motion imitation, interrupt), teleoperation and navigation join the claim one at a
time through an impact analysis, as LionDriver adds vehicles.

### 3.2 Top-level claim

G0 and sub-claims H1–H7 are in [WP-M-02 §3.1](WP-M-02-standards-map.md#31-claim-structure). No claim is made for
use among untrained people, in homes, or outside the operating envelope, until the lead chooses an intended use
(DQ-001) and the evidence exists.

## 4. Safety architecture argument

![Figure 4-1: where the joint envelope could run](decisions/figures/dq-007.svg)

*Figure 4-1.* The command chain from policy to motors, and the three places the joint envelope could run (DQ-007).

The argument has the same shape as LionDriver's: keep the ML stack QM and SOTIF-managed, and concentrate integrity
work on a small envelope that is the only path to the actuators.

1. **Envelope.** Per-joint limits, heartbeat timeout, mode gating, and a commanded damped state on any fault. The
   adapters already sit on every bus and run 586 lines of open Zephyr code; adding the envelope there costs no new
   hardware. Their weakness is that each adapter sees one bus, so a whole-body stop needs a cross-bus signal.
2. **Stop ladder.** The power-cut button stays as the last resort; above it, a controlled stop that lowers the robot
   before removing power, and a protective stop that holds balance (DQ-006).
3. **Freedom from interference.** As on LionDriver, the hinge: the SBC must not be able to reconfigure or bypass the
   envelope (firmware update path, limit tables, mode selection).
4. **Motor assumptions.** The joint motors' own behaviour on CAN timeout and fault becomes an assumption of use that
   is verified by test, since the vendor gives no evidence (gap assessment F-03).

## 5. Phases and gates

| Gate | Exit criterion | Main work products |
|---|---|---|
| **G0 Plan** | Intended use, scope, standards and framework decided; this strategy and the safety plan reviewed | WP-M-01, WP-M-02, safety plan, decision batch 1 answered |
| **G1 Concept** | Integrated hazard analysis done; safety goals; safety concept naming the envelope and stop ladder | Item definition, operating envelope, HATARA, safety concept |
| **G2 Envelope** | Envelope and stop ladder implemented and verified on a bench and on the gantry | Requirements, design, unit and bench tests, motor characterisation |
| **G3 Lab validation** | Walking validated in the lab envelope against targets set at G1; fall and stop tests passed | Validation plan and report, residual-risk argument |
| **G4 Release** | Safety case reviewed; independent confirmation as decided (DQ-010) | Safety case, confirmation reviews |

## 6. Decisions for the lead

Asked in the [decision register](decisions/register.yaml), batch 1:

| Question | Recommendation |
|---|---|
| What will the robot be used for, and by whom? | Lab and research with trained operators first |
| Do we assure upstream RPO as-is, or a fork we control? | Our own fork, pinned, with upstream merged by review |
| Which markets' rules do we design to? | EU Machinery Regulation first, US alongside |
| One integrated analysis, or a separate track per standard? | Integrated, reusing LionDriver's HATARA method |
| Which functional-safety standard family? | ISO 13849-1 with IEC 61800-5-2 functions |
| What should the stop button do? | Two tiers: soft stop that lowers the robot, red button cuts power |
| Where does the joint envelope run? | In the USB-to-CAN adapter firmware |
| Which configuration do claims cover? | RPO V2.0, RDK X5, DM motors, default walking policy |
| Development-phase operating rules | Gantry or harness for anything untested; exclusion zone; trained operators |
| Independent assessor | None yet; external reviewer at G1 |

## 7. Reuse from LionDriver

| LionDriver asset | Use here | When |
|---|---|---|
| Decision register, checker, inbox page (`01-management/decisions/`) | Ported as is (this commit) | Now |
| Working agreement (`CLAUDE.md`), AI work as I0, independence rules (WP-M-01 T-09) | Ported | Now |
| HATARA integrated hazard and threat analysis method (`02-concept/hatara`) | Template for H1 | G1 |
| Living Safety Case records, schema and validator (`case/`) | Claims H1–H7 instead of G1–G5 | After G0 |
| Requirements trace tooling and terms registry (`trace/`) | Requirements for envelope and stop ladder | G1–G2 |
| Upstream management (WP-M-11) and impact analysis (WP-M-12) | Roboparty as upstream | G0 |
| STPA control-structure analysis | Gamepad / policy / envelope / motor loops | G1 |
| ISO 26262 ASIL machinery | Replaced by PL or SIL | — |
