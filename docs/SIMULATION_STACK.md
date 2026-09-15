# Project Rufus Simulation Stack

## Decision

Project Rufus uses **MuJoCo as the first physics backend** and keeps the deterministic grid world as the fast fault-injection/test backend.

MuJoCo is an adapter, not the architecture. Rufus Brain continues to depend only on the `EmbodimentAdapter` contract:

`observe() -> WorldObservation`

`apply(Action) -> ActionResult`

`navigation_context() -> NavigationContext`

This keeps a future Isaac, ROS 2, LeRobot, or physical-hardware integration from owning the core autonomy loop.

## Why MuJoCo first

The first physics milestone needs:

- a Python-native path from the current Rufus package
- deterministic model construction
- contacts and rigid-body simulation
- actuator-driven motion
- a small enough stack to understand and debug directly
- no requirement for a GPU workstation

MuJoCo satisfies those needs while keeping the first robotics step narrow enough to reason about.

## Why not Isaac Lab first

Isaac Lab remains a likely later backend when Rufus needs large-scale parallel simulation, richer sensors, domain randomization, synthetic data, and GPU robot-learning workloads.

Starting there now would add substantial infrastructure before Rufus has earned the need for it.

## Two simulation lanes

### Deterministic grid world

Purpose: autonomy semantics, policy tests, degraded-state injection, fast regression tests, and mission trace validation.

Use it for:

- blocked routes
- missing observations
- injected action failures
- low-energy policy behavior
- recovery-budget behavior
- deterministic replay

### MuJoCo world

Purpose: begin replacing symbolic movement with physically stepped embodiment.

MuJoCo v0 models:

- a planar mobile body
- x/y position actuators
- simulation time stepping
- static collision geometry
- obstacle contacts
- physics-derived robot position
- package position in the simulated world
- energy consumption at the embodiment layer

## Explicit limitation: manipulation is not physical yet

Mission 001 still needs pickup and delivery. In MuJoCo v0, pickup is represented as a **kinematic attachment** once the robot and package occupy the same acquisition location. While carrying, the package state is synchronized to the robot. Drop releases it at the destination.

This is not claimed to be a robotic grasp.

Physical manipulation becomes a separate milestone requiring a manipulator, end-effector state, contact/grasp criteria, and a manipulation controller or learned policy.

## Truth boundary

MuJoCo may know more than Rufus does.

The adapter can expose operator/test ground truth, but Rufus Brain may only consume `WorldObservation`. Future sensor models should deliberately convert simulator truth into noisy, partial, stale, or unknown observations.

This preserves the rule:

**simulation truth is not automatically robot knowledge.**

## Installation

Core Rufus remains dependency-light:

```bash
python -m pip install -e .
```

MuJoCo is optional:

```bash
python -m pip install -e '.[mujoco]'
python -m rufus --backend mujoco --scenario nominal
```

## Validation strategy

The MuJoCo adapter has two levels of tests:

1. contract/configuration tests that run without MuJoCo installed
2. an integration test that automatically activates when the optional MuJoCo dependency is available

The integration gate for this milestone is:

> The unchanged Rufus Brain completes nominal Mission 001 through the MuJoCo embodiment adapter and produces a valid flight-recorder trace.

## Next physics milestones

1. Run nominal Mission 001 end-to-end in MuJoCo.
2. Add physics-visible obstacles and collision-induced execution failures.
3. Add sensor models so observations are derived from simulated sensors instead of direct state reads.
4. Add continuous pose/state alongside discrete planning state.
5. Replace kinematic package attachment with a real manipulation subsystem.
6. Introduce randomized mass, friction, sensor noise, and actuator variation.
7. Evaluate whether MuJoCo remains sufficient or a second adapter such as Isaac Lab is justified.
