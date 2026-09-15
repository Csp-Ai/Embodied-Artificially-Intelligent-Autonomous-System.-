# Project Rufus Wheel Odometry

## Purpose

A mobile robot needs an estimate of where it is. One of the simplest estimates comes from wheel motion.

If Rufus knows the left/right wheel speed and the drive geometry, differential-drive kinematics can estimate how the base moved over a short time interval. Repeating that process produces **wheel odometry**.

The critical rule is:

> **odometry is an estimate, not ground truth.**

A simulator or external localization system may know where the robot actually is. Rufus' wheel-derived estimate can drift away from that truth.

## Rufus v0 model

`WheelOdometry` maintains:

- current `Pose2D`
- elapsed time
- estimated traveled distance
- accumulated absolute rotation

For each update it receives:

- measured left/right wheel angular velocity
- time interval `dt`

It converts wheel motion to body twist through the existing `DifferentialDriveKinematics`, then integrates that twist into the next pose.

## Pose error

`pose_error(estimate, reference)` measures:

- 2D translation error in meters
- signed normalized yaw error in radians

Frame identity is mandatory. Rufus will not compare an `odom` pose directly against a `map` pose without an explicit transform.

## Why odometry drifts

The v0 math assumes wheel measurements and drive geometry are correct. Real robots violate those assumptions.

Common sources of drift include:

- wheel slip
- inaccurate wheel radius
- unequal tire wear
- axle-track calibration error
- encoder quantization/noise
- floor friction differences
- wheel deformation
- missed encoder counts
- timing error

Even a small systematic scale error accumulates with distance.

Example: if a robot physically travels `1.00 m` but wheel measurements imply `0.95 m`, wheel odometry is already `0.05 m` wrong after one meter.

## Ground truth vs odometry vs localization

Keep these concepts separate:

### Ground truth

Where the robot actually is according to the simulator/evaluation environment. Physical robots generally do not have access to true ground truth during deployment.

### Wheel odometry

A dead-reckoned estimate derived from wheel motion. It is locally useful but drifts over time.

### Localization estimate

A future fused estimate that may combine wheel odometry with IMU, camera, lidar, landmarks, GPS, or other observations.

Rufus should be able to compare these layers during simulation without silently substituting ground truth for the estimate available to the autonomy system.

## Operational relevance

This gives Rufus a measurable degraded-state signal.

Instead of only asking:

> Did the robot reach the target?

we can ask:

- How far did odometry drift from ground truth?
- Did error increase after turns or collisions?
- At what error threshold should confidence degrade?
- When should Rufus slow down, re-localize, or request help?

That moves localization from an invisible implementation detail into an operational reliability metric.

## Current limitations

Rufus v0 odometry does not yet estimate uncertainty/covariance and does not fuse external sensors. It assumes constant wheel velocity over each update interval.

Those are deliberate boundaries. The next localization milestone should introduce a second source of pose information and explicit confidence rather than pretending dead reckoning is sufficient.

## Next steps

1. Record wheel odometry and simulator ground truth together in physics runs.
2. Add controlled wheel scale/slip error.
3. Track translational/yaw error over time.
4. Define a localization health threshold.
5. Add an IMU or landmark observation model.
6. Build a small fused localization estimator only after the failure modes are observable.
