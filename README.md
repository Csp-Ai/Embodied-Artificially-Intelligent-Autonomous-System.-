# Project Rufus

**A simulation-first research program for trustworthy embodied intelligence.**

Project Rufus explores how an autonomous embodied system can perceive an environment, maintain an explicit world state, pursue goals, choose actions under uncertainty, obey safety constraints, recover from failure, and learn from mission outcomes.

Rufus starts as a brain in simulation. The long-term goal is to preserve the same core interfaces as the system graduates into richer physics simulation and eventually a physical body.

## Core loop

`Observe → State → Goal → Plan → Safety/Policy → Act → Verify → Recover → Learn`

The project is intentionally not a humanoid-hardware company, an LLM wrapper around a robot, or a collection of visible "agents." The focus is the decision and operating system around autonomous behavior.

## Principles

- **Simulation first.** Hardware should not be required to learn or validate the architecture.
- **State, not vibes.** Rufus maintains an explicit, inspectable representation of what it believes about itself, its environment, and its mission.
- **Observation is not inference.** Sensor facts, derived measurements, model inferences, and unknowns remain distinguishable.
- **Safety outranks task completion.** The planner cannot silently override policy or uncertainty boundaries.
- **Recovery is a first-class capability.** A useful autonomous system must handle reality when the nominal plan breaks.
- **Decision-time lineage matters.** Mission review should reconstruct what Rufus knew when it acted, not judge only with hindsight.
- **Learning is reviewed, not self-authorizing.** Evaluation may propose improvements; production safety policy does not silently rewrite itself.
- **Simulator and hardware are adapters.** The core intelligence should not belong to one robot, simulator, model provider, or sensor stack.

## Mission 001 — Resilient Delivery

Rufus must move an object from an origin to a destination while handling controlled failures such as a blocked route, degraded perception, low energy, or an unsuccessful interaction.

Success means more than finishing the task. Rufus must preserve state, explain the action path, recover when appropriate, and stop safely when it cannot justify continuing.

## Run the current system

Project Rufus currently has no required runtime dependencies beyond Python 3.11+.

```bash
python -m pip install -e .
python -m rufus --scenario nominal
python -m rufus --scenario dynamic-obstacle
python -m rufus --scenario partial-observation
```

Run the operational baseline:

```bash
python -m rufus.benchmark
```

The benchmark evaluates eight deterministic Mission 001 scenarios and reports mission outcomes, safe aborts, recoveries, policy blocks, verification failures, uncertainty exposure, and trace validity.

## What exists on `main`

### Autonomy

- explicit observed / derived / inferred / unknown state
- deterministic Mission 001 planner
- independent safety policy
- action execution and verification
- bounded recovery
- safe abort behavior

### Truth and replay

- human-readable mission timeline
- machine-readable flight-recorder JSON
- trace validation
- simulator ground truth kept outside the Brain contract

### Embodiment boundary

Rufus Brain depends only on:

`observe() → WorldObservation`

`apply(Action) → ActionResult`

`navigation_context() → NavigationContext`

The deterministic grid, a future physics simulator, ROS, or a physical robot must implement this boundary rather than owning the autonomy loop.

### Mission Ops benchmark

The default benchmark covers:

1. nominal delivery
2. static blocked route
3. low-energy policy abort
4. failed pickup + recovery
5. impossible-route safe abort
6. dynamic obstacle + re-plan
7. transient perception loss + recovery
8. persistent perception loss + safe abort

### Mobility foundations

- metric points and planar poses with named frames
- explicit planning-grid ↔ metric-world transforms
- differential-drive forward/inverse kinematics
- ideal wheel odometry integration
- bounded waypoint controller
- pose-error measurement

### Localization operations

Localization quality is represented as:

- `healthy`
- `degraded`
- `unknown`
- `unusable`

Runtime policy uses estimator-reported uncertainty and freshness, not simulator ground-truth error.

## Current status

**Phase 1 — Autonomy + mobility foundations.**

The deterministic autonomy loop is established. Rufus now has the interfaces and math needed to begin moving from symbolic grid behavior toward a genuine mobile-robot embodiment.

The first MuJoCo physics adapter is implemented in PR #6 but intentionally remains unmerged until nominal Mission 001 is actually executed through MuJoCo. The current execution environment cannot install the optional simulator package, and GitHub Actions has a separate runner-allocation defect tracked in Issue #5. We do not treat an unexecuted physics path as validated.

## Next technical gate

The immediate goal is:

> **Run the unchanged Rufus Brain through a real physics-backed embodiment and verify Mission 001 end to end.**

After that:

1. replace direct x/y physics movement with a wheel-driven differential base,
2. record wheel odometry beside simulator ground truth,
3. inject slip, stale localization, and collision-induced failures,
4. derive sensor observations instead of reading simulator state directly,
5. add a second localization source before attempting sensor fusion,
6. replace kinematic package attachment with a real manipulation subsystem,
7. evaluate whether MuJoCo remains sufficient or an Isaac Lab adapter is justified.

## Repository map

- [`docs/VISION.md`](docs/VISION.md) — purpose and research thesis
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system boundaries and authority rules
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — staged learning/build plan
- [`docs/MISSION_001.md`](docs/MISSION_001.md) — first mission specification
- [`docs/SPATIAL_MODEL.md`](docs/SPATIAL_MODEL.md) — coordinate frames and metric transforms
- [`docs/MOBILE_KINEMATICS.md`](docs/MOBILE_KINEMATICS.md) — differential-drive model
- [`docs/MOTION_CONTROL.md`](docs/MOTION_CONTROL.md) — waypoint control layer
- [`docs/ODOMETRY.md`](docs/ODOMETRY.md) — wheel dead reckoning and pose error
- [`docs/LOCALIZATION_HEALTH.md`](docs/LOCALIZATION_HEALTH.md) — localization operating states
- `src/rufus/brain.py` — autonomy loop
- `src/rufus/interfaces.py` — simulator/hardware boundary
- `src/rufus/flight_recorder.py` — mission trace and replay
- `src/rufus/benchmark.py` — Mission Ops scorecard
- `src/rufus/spatial.py` — metric spatial model
- `src/rufus/kinematics.py` — differential-drive kinematics
- `src/rufus/control.py` — bounded waypoint controller
- `src/rufus/odometry.py` — wheel odometry
- `src/rufus/localization.py` — localization health policy

## Working definition of success

Rufus becomes credible when the same high-level autonomy loop can move from deterministic tests → physics simulation → physical hardware without rewriting the Brain around each embodiment.
