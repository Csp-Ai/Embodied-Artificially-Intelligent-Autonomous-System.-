# Project Rufus Motion Control

## Purpose

The planner can decide **where** Rufus should go. Differential-drive kinematics explain **how wheel motion relates to body motion**. A controller is the layer between those two concerns.

Rufus v0 now has a simple point-following controller:

`target point + current pose → bounded body twist → wheel speeds`

This is intentionally separate from mission planning and from any simulator API.

## Control behavior

Given current `Pose2D` and a target `MetricPoint2D`, the controller computes:

- distance to target
- desired heading
- normalized heading error
- bounded angular velocity
- bounded forward velocity

When heading error is large, Rufus rotates in place before driving forward.

When the target is sufficiently in front of the robot, Rufus drives forward while correcting heading.

When the robot enters the configured position tolerance, the command becomes zero velocity.

## Why no reverse in v0

The first controller deliberately avoids commanding reverse motion. A target behind the robot causes an in-place turn instead.

This makes early behavior easier to inspect and avoids introducing reverse-driving policy/sensor assumptions before a mission requires them.

Reverse motion can be added later as an explicit capability with its own safety constraints.

## Limits

`VelocityLimits` defines independent bounds for:

- maximum linear velocity in meters/second
- maximum angular velocity in radians/second

The controller cannot request motion outside these limits.

Hardware will eventually need additional limits such as acceleration, jerk, motor current, traction, stopping distance, and platform-specific safety envelopes.

## Current control law

The v0 controller is proportional:

- linear command scales with target distance
- angular command scales with heading error
- forward velocity is reduced as heading alignment worsens
- large heading error switches to rotate-in-place behavior

This is sufficient to learn the control loop and produce a bounded command interface. It is not claimed to be an optimal navigation controller.

## Validation

The tests cover:

- straight-ahead target
- large heading error
- target behind the robot
- stop within target tolerance
- coordinate-frame mismatch rejection
- linear/angular velocity saturation
- integration with differential-drive wheel kinematics
- closed-loop convergence in the ideal kinematic model

A reference convergence scenario begins at `(0, 0)` facing `pi/2` radians and drives toward `(2.0 m, 0.5 m)` using a 20 Hz control loop.

## What this still does not model

The controller currently assumes the pose estimate is correct and immediately available. It does not yet include:

- acceleration limits
- actuator lag
- wheel slip
- collision avoidance at the control layer
- dynamic obstacle prediction
- localization uncertainty
- path curvature/trajectory planning
- control latency
- emergency braking

Those should be introduced as Rufus moves from an ideal drive model into a real physics-backed mobile base.

## Layering rule

Keep the responsibilities separate:

`Mission → Planner → Waypoint → Motion Controller → Twist → Drive Kinematics → Wheel Command → Embodiment`

Then observations flow back in the other direction:

`Sensors / Simulator → Pose Estimate → State → Verification / Planner`

That separation is what will let Rufus replace a simulator with physical hardware without moving mission logic into a motor controller.
