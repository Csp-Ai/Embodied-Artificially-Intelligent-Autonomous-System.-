# Project Rufus Architecture

## Architectural goal

Project Rufus should make the autonomy loop portable across simulation and physical hardware.

The core architecture therefore separates **decision logic** from **embodiment adapters**.

## Canonical loop

`Observe → State → Goal → Plan → Safety/Policy → Act → Verify → Recover → Learn`

Each stage should have an explicit contract so a future simulator, robot, model, or sensor provider can be swapped without rewriting the system around it.

## Core layers

### 1. Observation

Purpose: collect timestamped inputs from the body and world.

Examples:

- pose/localization,
- camera or depth observations,
- battery/energy state,
- actuator state,
- proximity/human-zone state,
- object detections,
- route/environment state,
- network/system health.

Requirements:

- preserve source and timestamp,
- distinguish missing from negative observations,
- support degraded/stale state,
- never promote an inference to an observation.

### 2. State

Purpose: maintain the best current representation of Rufus and its environment.

The state layer should merge observations and derived/inferred beliefs while retaining epistemic labels.

A future `WorldState` should likely contain:

- robot state,
- environment state,
- mission state,
- object/task state,
- health state,
- uncertainty,
- active constraints,
- provenance.

### 3. Goal / Mission

Purpose: represent the bounded objective and completion conditions.

A mission should define:

- desired outcome,
- preconditions,
- success criteria,
- prohibited conditions,
- resource constraints,
- timeout/abort criteria,
- allowed action space.

The mission is not the planner. It defines what success means.

### 4. Planner

Purpose: produce candidate action sequences from the current state and mission.

Early Rufus planning should be deterministic and inspectable where possible. More advanced planners or learned policies can be introduced after the contracts and telemetry are stable.

The planner proposes. It does not have final authority to execute.

### 5. Safety / Policy

Purpose: decide whether proposed actions are permitted under current state and uncertainty.

This layer should be independently testable.

It may:

- allow,
- deny,
- require additional observation,
- reduce speed/force/action scope,
- request human intervention,
- or abort the mission.

The planner must not bypass this layer.

### 6. Execution

Purpose: translate an approved abstract action into commands for a body adapter.

Examples:

- navigate to waypoint,
- stop,
- rotate/view,
- approach object,
- grasp/release,
- return to charge,
- signal/request assistance.

Execution should return structured results rather than only success/failure.

### 7. Verification

Purpose: compare the expected state transition with what was actually observed.

Every meaningful action should answer:

- What did we expect to change?
- What actually changed?
- Is the result verified, uncertain, or failed?

This prevents action issuance from being mistaken for task completion.

### 8. Recovery

Purpose: respond when verification shows that reality diverged from the plan.

Recovery may:

- retry within limits,
- re-observe,
- re-localize,
- replan,
- select an alternate action,
- enter a safe state,
- return to charge,
- request assistance,
- or abort.

Recovery should have budgets so Rufus cannot retry forever.

### 9. Evaluation / Mission Autopsy

Purpose: reconstruct the mission after completion or termination.

The evaluator should compare:

- decision-time state,
- expected transitions,
- actual transitions,
- binding constraints,
- recovery effectiveness,
- human interventions,
- outcome,
- counterfactual alternatives where methodologically defensible.

This layer produces learning data. It does not silently rewrite production policy.

## Epistemic model

Every material state value should eventually be representable with:

- value,
- epistemic class: `observed | derived | inferred | unknown`,
- source,
- timestamp,
- freshness,
- confidence/uncertainty where meaningful.

Confidence is not a substitute for provenance.

## Adapter boundary

The brain should interact with embodiment through interfaces rather than simulator-specific calls.

Conceptually:

```text
BodyAdapter
  observe() -> ObservationBatch
  execute(Action) -> ActionResult
  capabilities() -> CapabilitySet
  safeStop() -> StopResult
```

Future adapters may include:

- a lightweight custom simulation,
- MuJoCo,
- Isaac Lab / Isaac Sim,
- ROS 2,
- a mobile base,
- a robot arm,
- a mobile manipulator,
- eventually a humanoid platform.

No simulator or physical platform is canonical at Phase 0.

## Model boundary

Language, vision, VLM/VLA, learned policy, or foundation-model calls should also sit behind explicit interfaces.

A model may propose or infer. It should not acquire hidden authority over execution.

Examples:

```text
PerceptionModel
  infer(observations) -> Inferences

PlannerModel
  propose(state, mission) -> CandidatePlan[]

PolicyModel
  score(state, action) -> PolicyAssessment
```

Deterministic policy remains available around learned components.

## Suggested repository shape

This is directional, not yet a mandate:

```text
rufus/
  core/
    observation/
    state/
    missions/
    planning/
    policy/
    execution/
    verification/
    recovery/
    evaluation/
  adapters/
    simulation/
    hardware/
    models/
  telemetry/
  experiments/
  datasets/
  tests/
  docs/
```

Do not create empty architecture folders merely to look complete. Add them when Mission 001 requires them.

## Authority rules

1. Mission defines success and prohibited outcomes.
2. State is the canonical decision-time representation.
3. Planner proposes actions.
4. Safety/policy has veto authority.
5. Executor owns communication with the body.
6. Verification, not command issuance, determines whether an action worked.
7. Recovery owns bounded response to divergence.
8. Evaluation can recommend changes but cannot silently promote them.

## Early anti-patterns to avoid

- Direct LLM-to-motor control.
- Simulator APIs imported throughout the core.
- One global confidence score.
- Infinite retries.
- Treating a command acknowledgment as physical success.
- Hidden fallback behavior.
- Overly broad agent orchestration before one mission works.
- Training a learned policy before telemetry and evaluation are trustworthy.
- Building a dashboard before the autonomy loop exists.

## Definition of architectural success

The architecture is working when:

1. Mission 001 can run end-to-end in simulation.
2. Controlled failures produce explicit state transitions and bounded recovery.
3. Mission logs reconstruct why Rufus acted.
4. A second simulation/body adapter can be introduced without rewriting the brain.
5. A future physical body can implement the same high-level action/observation contracts.