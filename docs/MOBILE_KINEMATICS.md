# Project Rufus Mobile Kinematics

## Why this layer exists

Rufus Brain currently issues high-level actions such as moving toward the next planning cell. The first MuJoCo prototype can translate that into x/y position-servo targets, but a real mobile robot does not teleport its base to an x/y coordinate.

A common small mobile platform uses **differential drive**: one driven wheel on the left and one on the right. The body moves because of wheel rotation.

This module introduces that physical relationship without coupling Rufus to any simulator or motor controller.

## Model

For wheel radius `r`, axle track `L`, left wheel angular velocity `ω_l`, and right wheel angular velocity `ω_r`:

`v = r/2 * (ω_r + ω_l)`

`ω = r/L * (ω_r - ω_l)`

where:

- `v` is forward body velocity in meters/second
- `ω` is body yaw rate in radians/second

The inverse mapping is:

`ω_l = (v - ωL/2) / r`

`ω_r = (v + ωL/2) / r`

This gives Rufus a simulator-independent translation between a body-level motion command and wheel motion.

## Core types

### `DifferentialDriveGeometry`

Defines physical dimensions:

- wheel radius in meters
- axle track in meters

Invalid or non-finite geometry is rejected.

### `Twist2D`

Represents planar base motion:

- forward linear velocity (`m/s`)
- angular yaw velocity (`rad/s`)

### `WheelAngularVelocity`

Represents left/right wheel speed in radians/second.

### `DifferentialDriveKinematics`

Provides:

- body twist → wheel speeds
- wheel speeds → body twist
- ideal planar pose integration from twist
- ideal wheel-odometry integration

## What Rufus can learn from this

The distinction between these layers is important:

`mission target → path → body twist → wheel speeds → physical motion → measured pose`

A planner should not directly own motor speed. A motor controller should not decide the mission.

The layers communicate through explicit contracts.

## Assumptions in v0

This is **ideal kinematics**, not a localization system or full vehicle dynamics model.

It currently assumes:

- rigid wheels
- no wheel slip
- exact wheel radius and axle track
- constant wheel velocity during each integration interval
- planar motion
- no steering compliance
- no encoder quantization/noise
- no IMU drift
- no covariance estimate

Those simplifications are useful now because they make the geometry inspectable and testable.

Later, simulation can deliberately violate them.

## Why dead reckoning is not ground truth

Integrating wheel motion produces an estimate of where the robot should be. On real hardware, slip, calibration errors, surface changes, and sensor noise make that estimate drift.

Future Rufus state should therefore keep concepts such as these distinct:

- simulator/world ground truth
- wheel odometry
- localization estimate
- perception-derived state

They may disagree, and that disagreement is itself useful information.

## Next step

Once the first MuJoCo backend has executed successfully, replace its direct x/y position-servo locomotion with a differential-drive body or add a second MuJoCo drive-base adapter.

That milestone should introduce:

1. left/right wheel joints
2. wheel velocity actuation
3. continuous body pose
4. collision response
5. wheel-derived odometry
6. comparison between odometry and simulator ground truth

This will move Rufus from **physics-backed point movement** toward an actual mobile-robot embodiment.
