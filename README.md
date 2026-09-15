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

See:

- [`docs/VISION.md`](docs/VISION.md) — purpose and research thesis
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system boundaries and contracts
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — staged learning/build plan
- [`docs/MISSION_001.md`](docs/MISSION_001.md) — first executable mission specification

## Status

**Phase 0 — Foundation.** Define the brain, interfaces, truth model, mission contract, and evaluation criteria before selecting or coupling to a specific simulator or physical platform.

## Working definition of success

Rufus becomes credible when the same high-level autonomy loop can move from simulation to a real body without rewriting the brain around the hardware.
