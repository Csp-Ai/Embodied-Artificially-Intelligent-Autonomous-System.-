# Project Rufus

**A simulation-first research program for trustworthy embodied intelligence.**

Project Rufus explores how an autonomous embodied system can perceive an environment, maintain an explicit world state, pursue goals, choose actions under uncertainty, obey safety constraints, recover from failure, and learn from mission outcomes.

Rufus starts as a brain in simulation. The long-term goal is to preserve the same core interfaces as the system graduates into a physical body.

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

## Initial mission

**Mission 001: Resilient Delivery**

Rufus must move an object from an origin to a destination in simulation while handling controlled failures such as a blocked route, degraded perception, low energy, or an unsuccessful interaction. Success means more than finishing the task: Rufus must preserve state, explain the action path, recover when appropriate, and stop safely when it cannot justify continuing.

## Run Rufus

Core Rufus has no runtime dependencies beyond Python 3.11+:

```bash
python -m pip install -e .
python -m rufus --backend grid --scenario nominal
python -m rufus --backend grid --scenario dynamic-obstacle
python -m rufus --backend grid --scenario partial-observation
```

For the first physics-backed embodiment:

```bash
python -m pip install -e '.[mujoco]'
python -m rufus --backend mujoco --scenario nominal
```

The MuJoCo v0 backend physically steps planar motion and collision/contact behavior. Package pickup is still explicitly modeled as a **kinematic attachment**, not a physical robotic grasp.

## Repository map

- [`docs/VISION.md`](docs/VISION.md) — purpose and research thesis
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system boundaries and contracts
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — staged learning/build plan
- [`docs/MISSION_001.md`](docs/MISSION_001.md) — first executable mission specification
- [`docs/SIMULATION_STACK.md`](docs/SIMULATION_STACK.md) — simulator decision, truth boundary, and physics roadmap
- `src/rufus/brain.py` — autonomy loop
- `src/rufus/interfaces.py` — simulator/hardware boundary
- `src/rufus/flight_recorder.py` — mission trace and replay
- `src/rufus/adapters/` — optional simulation and future hardware adapters

## Status

**Phase 1 — Simulation-backed embodiment.** Rufus Brain, recovery, flight recording, and the simulator-neutral embodiment contract are established. The current milestone is moving Mission 001 from the deterministic grid into MuJoCo without changing the Brain.

## Working definition of success

Rufus becomes credible when the same high-level autonomy loop can move from deterministic tests → physics simulation → a real body without rewriting the brain around the hardware.
