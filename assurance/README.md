# RPO Humanoid Assurance

Safety-assurance work products for the ROBOTO_ORIGIN (RPO) humanoid, using the method LionDriver applies to
openpilot: a small verified envelope between the ML stack and the actuators, one integrated hazard analysis, a
living safety case, and every question for the project lead in one decision register.

> [!WARNING]
> Everything here is a **draft prepared for engineering review**. Nothing has been verified, confirmed or assessed.
> No claim is made that RPO is safe to operate near people.

## Start here

| Document | Why read it |
|---|---|
| [00-assessment/gap-assessment.md](00-assessment/gap-assessment.md) | The robot as found: how a command reaches the motors, and 14 findings |
| [01-management/WP-M-02-standards-map.md](01-management/WP-M-02-standards-map.md) | Which standards apply to a humanoid, the humanoid-specific gap, and the integrated profile (claims H1–H7) |
| [01-management/WP-M-01-assurance-strategy.md](01-management/WP-M-01-assurance-strategy.md) | Scope, safety architecture, gates G0–G4, what is reused from LionDriver |
| [02-concept/WP-C-01-item-definition.md](02-concept/WP-C-01-item-definition.md) | What the robot is, its functions, modes, interfaces and assumptions |
| [02-concept/WP-C-03-integrated-hazard-analysis.md](02-concept/WP-C-03-integrated-hazard-analysis.md) | One analysis of faults, AI misbehaviour, misuse and attack; required performance levels for ten safety functions |
| [06-validation/WP-V-01-gantry-test-procedure.md](06-validation/WP-V-01-gantry-test-procedure.md) | The first powered tests on the gantry, with pass criteria |
| [01-management/decisions/](01-management/decisions/README.md) | Questions waiting on the project lead |
