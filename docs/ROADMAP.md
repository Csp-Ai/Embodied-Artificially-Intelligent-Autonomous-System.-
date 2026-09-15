# Project Rufus Roadmap

## Operating principle

The roadmap is intentionally **mission-driven and learning-driven**.

We do not add robotics technology because it is fashionable. We introduce each concept when Rufus needs it to complete a harder mission with better reliability.

The project should progress from an inspectable deterministic core toward learned embodied behavior while preserving safety, telemetry, and decision lineage.

---

## Phase 0 — Foundation

**Goal:** define the system before choosing the stack.

Build/learn:

- embodied autonomy loop,
- mission contracts,
- state representation,
- observation vs inference,
- action/result contracts,
- safety authority,
- recovery semantics,
- telemetry and mission lineage,
- evaluation methodology.

Deliverables:

- vision,
- architecture,
- Mission 001 specification,
- initial interfaces and types,
- simulator decision record.

Exit criteria:

- one coherent system model,
- no hidden simulator dependency in the core design,
- Mission 001 has explicit pass/fail criteria.

---

## Phase 1 — Rufus Brain v0

**Goal:** implement the autonomy loop without a sophisticated 3D world.

Build/learn:

- Python project structure and testing,
- typed state models,
- finite-state machines / behavior trees / simple planners,
- deterministic safety rules,
- event logging,
- recovery budgets,
- replayable mission traces.

Rufus should be able to operate against a minimal simulated body/world adapter that exposes discrete observations and actions.

Example actions:

- move to location,
- inspect location/object,
- pick,
- place,
- stop,
- return to charge,
- request assistance.

Exit criteria:

- Mission 001 completes under nominal conditions,
- every action produces an expected/actual transition record,
- unsafe conditions can block execution,
- mission trace can be replayed and audited.

---

## Phase 2 — Rufus World v1

**Goal:** introduce spatial/physical simulation.

Build/learn:

- robot coordinate frames,
- pose and localization concepts,
- kinematics fundamentals,
- collision and contact,
- sensors,
- path planning,
- simulator integration,
- deterministic environment randomization.

Candidate technologies to evaluate at this phase:

- MuJoCo,
- Isaac Lab / Isaac Sim,
- ROS 2 + simulator integration,
- lightweight custom environments for specific tests.

Selection criteria:

- learning value,
- hardware-transfer path,
- reproducibility,
- compute requirements,
- quality of sensor/actuator simulation,
- Python/ROS ecosystem fit.

Exit criteria:

- Mission 001 runs in a spatial simulator,
- Rufus core does not depend directly on simulator APIs,
- body adapter translates high-level actions to simulated execution,
- telemetry captures pose, health, action outcomes, and failures.

---

## Phase 3 — Failure & Recovery Lab

**Goal:** make Rufus robust to reality breaking the nominal plan.

Introduce a repeatable fault-injection harness.

Scenarios:

- route becomes blocked,
- object is moved,
- false or stale observation,
- localization confidence drops,
- energy falls below reserve,
- pick/grasp attempt fails,
- action times out,
- simulated sensor becomes unavailable,
- network/model dependency becomes unavailable,
- human/protected-zone condition invalidates the plan.

Build/learn:

- fault detection,
- uncertainty thresholds,
- replanning,
- retry budgets,
- safe-stop states,
- human escalation,
- degraded modes,
- scenario testing and reliability metrics.

Exit criteria:

- Rufus detects each supported injected failure,
- recovery behavior is explicit and bounded,
- unsafe/unsupported conditions fail closed,
- nominal mission success is no longer the only evaluation metric.

---

## Phase 4 — Perception & Semantic World State

**Goal:** replace perfect simulator truth with imperfect perception.

Build/learn:

- RGB/depth observations,
- object detection/segmentation,
- vision-language models where useful,
- semantic maps,
- object identity and persistence,
- uncertainty/calibration,
- sensor fusion fundamentals.

Key rule:

**Ground-truth simulator state is for evaluation, not for silently giving Rufus knowledge a real robot would not have.**

Exit criteria:

- Rufus performs Mission 001 from sensor-derived state,
- observed and inferred values remain distinguishable,
- evaluation can compare Rufus beliefs against simulation ground truth,
- degraded perception changes policy appropriately.

---

## Phase 5 — Learned Behavior

**Goal:** introduce machine-learned policies only after the operating loop is trustworthy.

Build/learn:

- demonstrations and dataset collection,
- imitation learning,
- reinforcement learning fundamentals,
- policy evaluation,
- sim-to-real considerations,
- VLA / robot foundation model interfaces,
- offline evaluation and model versioning.

Possible ecosystem integrations:

- LeRobot,
- Isaac Lab learning workflows,
- compatible VLA/foundation models,
- custom learned recovery policies.

Rule:

A learned component can replace or augment a subsystem only when Rufus can measure whether it improved that subsystem.

Exit criteria:

- learned vs deterministic policies can be compared reproducibly,
- policy/model versions are preserved in mission lineage,
- safety authority remains external to opaque learned behavior where required.

---

## Phase 6 — First Physical Body

**Goal:** cross the simulation-to-reality boundary.

The first body should be affordable, observable, and easy to recover—not impressive for its own sake.

Potential forms:

- small mobile base,
- desktop robot arm,
- mobile manipulator,
- supported educational/research robot.

Build/learn:

- ROS 2 integration,
- real sensors and actuators,
- calibration,
- latency and networking,
- hardware safety,
- emergency stop,
- real battery/charging behavior,
- real-world perception noise,
- deployment and logs.

Exit criteria:

- a physical adapter implements the same Rufus contracts,
- Mission 001 or an equivalent bounded mission runs on hardware,
- core brain changes are limited to legitimate embodiment differences,
- safe stop is independently reliable.

---

## Phase 7 — Continuous Embodied Intelligence

**Goal:** move from scripted missions to persistent operation.

Research areas:

- long-horizon planning,
- memory across missions,
- continual world models,
- multi-step manipulation,
- dynamic human environments,
- battery/charging autonomy,
- task scheduling,
- self-diagnostics,
- human-robot collaboration,
- calibration over operational history.

At this point Rufus may support richer bodies, including humanoid platforms, if the mission requires them.

---

## Learning track

The project doubles as a robotics curriculum.

Suggested sequence:

1. Python engineering, testing, state machines, telemetry.
2. Robotics coordinate frames, transforms, kinematics, sensors.
3. Simulation and path planning.
4. ROS 2 concepts and messaging.
5. Perception and sensor fusion.
6. Control fundamentals.
7. Manipulation/navigation depending on body.
8. Imitation and reinforcement learning.
9. VLA / embodied foundation models.
10. Sim-to-real and hardware operations.

Theory should be learned when it becomes necessary to explain, build, or debug Rufus behavior.

---

## Metrics that matter

Do not optimize only for task success rate.

Track over time:

- mission success rate,
- safe abort rate,
- unsafe action attempts blocked,
- false safety blocks,
- recovery success rate,
- average recovery attempts,
- human interventions per mission,
- energy efficiency,
- time to mission completion,
- perception/state calibration,
- expected vs actual transition accuracy,
- failure-mode coverage,
- replay/reproducibility rate.

Later, measure transfer:

- simulation performance vs physical performance,
- policy degradation across embodiments,
- number of core changes required to support a new body.

---

## Near-term execution queue

1. Merge the foundation docs.
2. Select language/runtime conventions; default candidate is Python.
3. Implement core domain types: observations, epistemic values, world state, mission, action, result, policy decision, mission event.
4. Implement a minimal deterministic `BodyAdapter` and grid/world simulation.
5. Run Mission 001 nominally.
6. Add mission trace/replay.
7. Add one fault at a time: blocked route, low energy, failed interaction, degraded observation.
8. Only after that, choose the first full robotics simulator.

The first milestone is **not** a humanoid demo.

It is a Rufus trace that proves the system can act, detect when reality disagrees, recover or stop, and explain why.