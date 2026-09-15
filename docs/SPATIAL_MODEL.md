# Project Rufus Spatial Model

## Why this exists

The deterministic Mission 001 planner uses discrete `Position(x, y)` cells because they are easy to reason about, replay, and test.

A real simulator or robot does not live in integer grid cells. It lives in metric coordinate frames with continuous pose.

Project Rufus therefore treats these as two different layers:

- **planning state** — discrete cells and symbolic obstacles
- **embodiment state** — metric position/pose in a named coordinate frame

The conversion between them must be explicit.

## Core types

### `MetricPoint2D`

A planar point in meters with a required frame identity.

Example:

`MetricPoint2D(x_m=1.5, y_m=0.5, frame_id="map")`

### `Pose2D`

A planar body pose:

- x in meters
- y in meters
- yaw in radians
- frame ID

Angles are normalized to `[-pi, pi)` when requested.

### `GridTransform`

Defines how symbolic planning cells map into a metric frame:

- cell size in meters
- metric origin
- frame ID

Example:

`GridTransform(cell_size_m=0.5, origin_x_m=1.0, origin_y_m=-2.0, frame_id="map")`

Then planner cell `Position(3, 4)` maps to metric point `(2.5 m, 0.0 m)` in the `map` frame.

## Safety rule: frames are not interchangeable

Rufus must not silently compare coordinates from different frames.

A point in `map` and a point in `odom` may contain identical-looking numbers while referring to different physical locations. Cross-frame distance or conversion therefore fails unless an explicit transform exists.

The current v0 model intentionally does **not** implement a transform tree. That comes later with ROS 2 / richer simulation when multiple moving frames are needed.

## Planner vs embodiment

The planner may continue to reason over cells for Mission 001.

A simulator adapter should:

1. convert the planned cell to a metric target
2. execute motion in continuous simulator coordinates
3. observe the resulting metric pose
4. convert the pose back into planner state only when that abstraction is appropriate
5. preserve continuous pose in telemetry for evaluation

This prevents the planner from pretending that command issuance equals physical arrival.

## MuJoCo use

The first MuJoCo adapter currently contains local grid↔metric conversion logic. Once this spatial model lands, that adapter should use `GridTransform` instead so the conversion semantics have one authority.

## Later extensions

Add only when a mission requires them:

- 3D position and quaternion pose
- rigid transforms between frames
- timestamped transforms
- `map`, `odom`, `base_link`, sensor frames
- covariance / localization uncertainty
- velocity and acceleration state
- path representations in continuous space

The rule remains:

**symbolic planning state is not the same thing as physical state.**
