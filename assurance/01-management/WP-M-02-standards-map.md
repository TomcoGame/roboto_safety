# WP-M-02 Standards Map and Integrated Humanoid Assurance Profile

| Field | Value |
|---|---|
| Work product | WP-M-02 Standards map and integrated humanoid assurance profile |
| Version | 0.1 (first draft; 2026-10-26) |
| Status | Draft, I0 (AI-authored, not verified). Standard editions and draft stages must be checked against the ISO, IEC and EU catalogues before any claim relies on them |
| Author | Claude (AI assistant) |
| Decisions it depends on | Intended use and markets; integrated or separate tracks; functional-safety standard family (register DQ-001, DQ-003, DQ-004, DQ-005) |

## 1. The problem

No single standard covers a general-purpose humanoid. Road vehicles have ISO 26262 for malfunctions, ISO 21448 for
insufficiencies, ISO/SAE 21434 for attack and ISO/PAS 8800 for ML, and LionDriver integrates the four. Humanoids sit
across several machinery families at once:

- a **machine** (ISO 12100 risk assessment, EU Machinery Regulation),
- a **robot** with arms that can touch people (ISO 10218:2025 industrial, ISO 13482 personal care / service),
- a **mobile** machine (ISO 3691-4, ANSI/A3 R15.08),
- that is **dynamically stable**: it falls if control stops (ISO 25785-1, still a draft),
- driven by **learned policies** (no robot-specific ML safety standard; ISO/IEC TR 5469, EU AI Act),
- and **networked** (IEC 62443, EU Cyber Resilience Act).

The humanoid-specific gap is the last-but-two line: **for a balancing robot, removing power is not a safe state.**
Every classical machinery safety function (safe torque off, power-cut emergency stop) assumes the machine comes to
rest when de-energised. A biped instead falls. ISO 25785-1 is being written for exactly this; until it is published
the profile below has to define the fall and stop behaviour itself.

## 2. Standards map

Status as understood on 2026-10-26; **verify each against the publisher before relying on it**.

### 2.1 Foundation and regulation

| Standard / law | Status | Role for RPO |
|---|---|---|
| ISO 12100:2010 Machinery: risk assessment and risk reduction | Published | Backbone: hazard identification, risk estimation, the three-step method (inherently safe design, safeguards, information) |
| EU Machinery Regulation (EU) 2023/1230 | Applies from 20 Jan 2027 | Legal essential requirements in the EU, including mobile machinery, self-evolving (ML) behaviour and protection against corruption |
| EU AI Act (EU) 2024/1689 | In force; obligations for AI that is a safety component of machinery phase in later | ML policy acting as a safety component makes it high-risk AI |
| EU Cyber Resilience Act (EU) 2024/2847 | Reporting from Sep 2026, full from Dec 2027 | Products with digital elements: secure development, updates, vulnerability handling |
| IEC 60204-1 Electrical equipment of machines | Published | Stop categories 0, 1 and 2; emergency stop; electrical safety |

### 2.2 Robot type standards (which apply depends on intended use, DQ-001)

| Standard | Status | Role |
|---|---|---|
| ISO 25785-1 Industrial mobile robots with actively controlled stability (legged, wheeled balancing) | Draft, under development (stage reported variously as working draft or CD) | The closest humanoid standard: stability loss, fall, stop behaviour of balancing robots. Track it; design to its direction |
| ISO 10218-1 / -2:2025 Industrial robots / robot applications | Published Jan 2025; collaborative methods (former ISO/TS 15066) now in Part 2 | Industrial use; force and pressure limits for contact by body region; cybersecurity as a safety topic |
| ISO 13482 Personal care robots (revision as service robots, FprEN ISO 13482) | 2014 edition; revision near final | Home and service use: mobile servant and person-carrier hazards, stability, contact |
| ISO 3691-4 / ANSI/A3 R15.08 Driverless trucks / industrial mobile robots | Published | Mobility: speed, personnel detection, travel paths |
| ANSI/A3 TR R15.108 (humanoid / legged guidance) | In progress | US interim guidance |
| UL 3300 Service, communication, information, education and entertainment robots | Published | Consumer and commercial robots in North America |

### 2.3 Functional safety (DQ-005)

| Standard | Role |
|---|---|
| ISO 13849-1:2023 | Performance level (PL a–e) of safety-related control parts; the usual machinery route |
| IEC 62061:2021 | SIL for machinery control systems; better suited to complex programmable electronics |
| IEC 61508 (parts 1–7) | Generic basis for SIL; needed for developing a safety controller or safety firmware from scratch |
| IEC 61800-5-2 | Safe drive functions: STO, SS1, SS2, SOS, SLS, SLP, SLT. The vocabulary for joint-level safety |

### 2.4 Behaviour, ML and the autonomous-product argument

| Standard | Role |
|---|---|
| ISO 21448 (SOTIF) concepts | Not robot-specific, but its method (triggering conditions, known and unknown unsafe scenarios, validation targets) transfers to learned locomotion |
| ISO/IEC TR 5469:2024 AI and functional safety | How ML can sit in or near safety functions |
| ISO/IEC TS 22440 (in development) | AI in safety-related systems |
| ISO/PAS 8800:2024 concepts | Data and model lifecycle, AI safety argument; written for road vehicles, transferable |
| ISO/IEC 42001, ISO/IEC 23894 | AI management system and AI risk management |
| UL 4600 | Safety-case structure for autonomous products: claims, evidence, defeaters (LionDriver's Living Safety Case uses it) |

### 2.5 Cybersecurity, electrical, battery

| Standard | Role |
|---|---|
| IEC 62443-4-1 / -4-2 / -3-3 | Secure development; component and system security levels |
| ETSI EN 303 645 | Consumer IoT baseline (home use) |
| IEC 62133-2, UN 38.3 | Li-ion battery safety and transport (48 V 15 Ah pack) |
| IEC 61000-6-x | EMC |

## 3. The integrated profile

One lifecycle, one hazard analysis, one safety case. The disciplines differ in **cause** (fault, insufficiency,
misuse, attack); they share the same hazards (fall, strike, crush, pinch, battery fire) and the same safety
functions. Running them as separate tracks duplicates the hazard list and leaves gaps at the seams, which is why
LionDriver merged its HARA and TARA into one HATARA. The profile does the same and adds the humanoid-specific claims.

### 3.1 Claim structure

> **G0**: The RPO reference configuration, operated within its declared use and operating envelope, does not pose
> unreasonable risk to operators, bystanders or property.

| Sub-claim | Covers | Draws on | LionDriver counterpart |
|---|---|---|---|
| **H1 Hazards identified and risk assessed** | One integrated analysis: malfunction, ML insufficiency, foreseeable misuse, attack | ISO 12100, STPA, HATARA method | HARA + TARA → HATARA |
| **H2 Safety functions meet their integrity** | Joint envelope, stops, speed and force limits, command watchdog | ISO 13849-1 or IEC 62061 / 61508, IEC 61800-5-2 | G1 functional safety |
| **H3 Stability and fall safety** | Every stop path ends in a defined posture or a managed fall; fall zone kept clear | ISO 25785-1 (draft), IEC 60204-1 stop categories | *new* |
| **H4 Contact with people stays within limits** | Force, pressure, speed near people; pinch points | ISO 10218-2:2025 body-region limits, ISO 13482 | *new* (driver controllability has no equivalent) |
| **H5 Learned behaviour is bounded and validated** | Policies stay inside the envelope; out-of-distribution detection; sim-to-real validation targets | SOTIF method, ISO/IEC TR 5469, ISO/PAS 8800 concepts, AI Act | G2 SOTIF + G3 AI |
| **H6 Security does not undermine safety** | Command authentication, update integrity, teleop link | IEC 62443, CRA | G4 cybersecurity |
| **H7 Competent people, controlled process, independent review** | Plans, change control, reviews, assessor | IEC 61508-1 / ISO 13849-2 management, ASPICE as yardstick | G5 process |

### 3.2 The safety architecture the claims rest on

The envelope pattern carries over from LionDriver: a small element between the ML stack and the actuators enforces
limits whatever the policy commands. For RPO it has three layers:

1. **Joint envelope** (H2): per-joint position, velocity and torque limits; command-stream heartbeat; motor enable
   only in an allowed mode. Location is DQ-007 (adapter firmware, dedicated controller, or software only).
2. **Stop ladder** (H3): protective stop that keeps balance (category 2) → controlled crouch or sit, then power off
   (category 1) → power cut with the robot supported (category 0). Which ones exist and what the red button does is
   DQ-006.
3. **Operating envelope** (H4, H5): where the robot may be used and how close people may come: gantry or harness,
   exclusion zone, speed caps. Development-phase rules are DQ-009.

### 3.3 How it would become a standard

If the profile works on RPO, it can be written up as a project-independent "integrated humanoid assurance profile":
the claim structure of §3.1, the stop ladder of §3.2, and the mapping of §2, with RPO as the worked example. That is
a later choice; nothing here depends on it.

## 4. What is missing from every standard (to watch)

- Acceptance criteria for a fall: when is a fall of the robot, with no person struck, an acceptable outcome of a safe state?
- Integrity for a balance-keeping protective stop: it needs active control, so it cannot be a passive STO.
- Validation targets for learned locomotion: how many hours or scenarios show a policy is good enough.
- Contact limits for a robot that is itself moving and can fall onto a person, not only reach out to them.
