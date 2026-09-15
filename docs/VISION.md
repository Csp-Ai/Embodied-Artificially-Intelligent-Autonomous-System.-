# Project Rufus Vision

## Thesis

Embodied intelligence is not only the ability to produce a good plan. A useful autonomous system must continuously reconcile what it wants to do with what the physical world actually permits.

Project Rufus is a simulation-first research program for studying that problem.

The central question is:

> **How should an embodied autonomous system represent uncertainty, identify the constraint that matters now, choose an action, recover when reality breaks the plan, know when not to act, and learn from the episode without silently rewriting its own safety boundaries?**

Rufus begins in simulation so the architecture can be learned, tested, broken, and instrumented safely. The long-term objective is to transfer the same autonomy contracts to a physical body.

## What Rufus is

Rufus is an **embodied decision system**.

It should eventually be capable of:

1. observing itself and its environment,
2. representing an explicit belief/state,
3. receiving or selecting a bounded goal,
4. generating candidate plans,
5. evaluating constraints and safety policy,
6. executing actions through a body adapter,
7. verifying whether the world changed as expected,
8. recovering from failure or abstaining safely,
9. recording decision-time lineage,
10. evaluating the mission afterward,
11. improving through reviewed experiments and learned policies.

## What Rufus is not

At least initially, Rufus is not:

- a humanoid hardware startup,
- a custom actuator or robot-arm project,
- an LLM connected directly to motor commands,
- a chat interface pretending to be embodied intelligence,
- a swarm of anthropomorphized software agents,
- an autonomous system allowed to rewrite its own safety policy,
- a benchmark-chasing reinforcement-learning project with no operating model,
- or a polished simulation whose failures are scripted away.

## Research posture

Rufus should remain explicit about epistemic state.

Every important belief should be classifiable as one of:

- **Observed** — directly reported by a sensor, simulator, trusted system interface, or operator.
- **Derived** — deterministically calculated from observed data.
- **Inferred** — estimated by a model or probabilistic process.
- **Unknown** — not supported strongly enough to justify a belief.

These categories should influence policy. A high-risk action that depends on an unknown or weak inference should be treated differently from one grounded in verified state.

## State over score

Rufus should not compress autonomy into one confidence number.

A conceptual robot state may include:

`R(t) = [pose, localization confidence, energy, sensor health, actuator health, mission progress, object state, route state, human proximity, network state, uncertainty, active constraints]`

The exact schema will evolve. The principle should not: **the shape of the state matters, and a severe constraint should not be averaged away by otherwise healthy dimensions.**

## Binding constraints

At any point, Rufus should be able to answer:

> **What currently prevents or threatens safe mission completion?**

Examples:

- insufficient energy reserve,
- uncertain localization,
- blocked route,
- object identity not verified,
- actuator unavailable,
- human occupancy in a protected zone,
- perception degraded below execution threshold.

This constraint should influence planning and recovery more strongly than a generic aggregate score.

## Recovery as intelligence

Nominal task completion is only one part of autonomy.

Rufus should be intentionally exposed to controlled failures:

- route obstruction,
- stale or conflicting observations,
- low energy,
- missed grasp or failed interaction,
- sensor degradation,
- action timeout,
- unexpected object movement,
- loss of network/service dependency,
- goal becoming impossible or unsafe.

The research question is not merely whether Rufus still succeeds. It is whether Rufus:

1. detects the discrepancy,
2. updates its state,
3. identifies the relevant constraint,
4. chooses an appropriate recovery strategy,
5. verifies the recovery,
6. or stops safely when continuation cannot be justified.

## Decision-time lineage

Mission evaluation must preserve what Rufus knew **when the decision was made**.

A useful mission record should eventually include:

- mission and run identity,
- goal and constraints,
- state snapshot,
- observation provenance,
- uncertainty representation,
- candidate actions or plan,
- selected action and rationale,
- safety/policy decision,
- expected state transition,
- actual state transition,
- recovery attempts,
- human interventions,
- outcome,
- post-mission evaluation,
- relevant software/model/policy versions.

This makes it possible to distinguish a bad decision from a good decision followed by bad luck or an unrelated downstream failure.

## Learning philosophy

Rufus should become **self-calibrating, not self-authorizing**.

The system may learn:

- which observations are reliable,
- which recovery strategies work under which conditions,
- where its predictions are poorly calibrated,
- which plans repeatedly fail,
- which uncertainty thresholds are too permissive or too conservative,
- and eventually policies from demonstrations or reinforcement learning.

But changes that alter safety authority or production behavior should be versioned, evaluated, and deliberately promoted.

## Simulation-to-body principle

Rufus should separate:

**Brain** — state, planning, policy, recovery, evaluation

from

**Body** — sensors, actuators, kinematics, simulator or hardware interfaces.

The core test of this architecture is transfer:

> Can a mission defined against Rufus interfaces run in simulation and later run against a physical robot with minimal changes to the decision system?

## Long-term destination

The long-term ambition is not simply "a robot that moves."

It is a trustworthy embodied system that can operate continuously under imperfect information and physical uncertainty while remaining inspectable enough to understand why it acted.

A mature Rufus should support the loop:

`Perception → State → Constraint → Decision → Safety → Action → Verification → Recovery → Mission Autopsy → Learning`

That loop is the project.