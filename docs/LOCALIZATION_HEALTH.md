# Project Rufus Localization Health

## Purpose

Wheel odometry gives Rufus a pose estimate, but an autonomy system also needs to know whether that estimate is trustworthy enough to act on.

Project Rufus therefore treats localization health as an explicit operational state rather than assuming that any available pose is good enough.

## Critical truth boundary

Runtime localization health must be based on information a real robot could have from its estimator:

- whether a pose estimate is available
- estimator-reported position uncertainty
- estimator-reported yaw uncertainty
- age/freshness of the estimate
- provenance/source

It must **not** depend on simulator ground-truth pose error during deployment.

Simulator truth is still useful for evaluation: it can tell us whether the estimator's own confidence was calibrated. But it is not silently available to Rufus Brain.

## Health states

### Healthy

The estimate is available, fresh, and within configured healthy uncertainty thresholds.

Default action:

- navigation allowed
- normal speed scale (`1.0`)

### Degraded

The estimate remains within the configured maximum operating envelope but is outside the healthy range.

Default action:

- navigation allowed
- reduced speed according to policy
- preserve the degraded reason in telemetry

This models a controlled degraded mode rather than pretending all pose quality is binary.

### Unknown

The localizer says a pose is available, but one or more quality signals are missing.

Default action:

- navigation blocked
- hold/re-observe rather than inventing confidence

### Unusable

Localization is unavailable, too stale, or outside the maximum uncertainty envelope.

Default action:

- navigation blocked
- speed scale `0`
- recovery/re-localization or human intervention should be considered by higher-level policy

## Threshold policy

`LocalizationHealthThresholds` separates the healthy range from the maximum operating range for:

- position uncertainty in meters
- yaw uncertainty in radians
- pose age in seconds

It also defines the speed scale used in degraded mode.

The default values are engineering placeholders, not validated universal safety limits. A physical platform must derive its thresholds from vehicle geometry, stopping distance, sensor performance, mission environment, and risk analysis.

## Why this is operationally useful

A localization problem should not appear only as a generic mission failure.

Rufus can now represent a state like:

`localization = degraded`

with a reason such as:

`position uncertainty above healthy range; pose estimate older than healthy range`

That creates a measurable operating condition which can be counted across missions:

- time spent degraded
- number of localization holds
- localization-caused safe aborts
- recovery success rate
- error vs reported uncertainty in simulation

## Relationship to future sensor fusion

Rufus does not yet perform sensor fusion.

A future localization estimator may combine:

- wheel odometry
- IMU
- camera/visual odometry
- lidar
- GPS/GNSS where appropriate
- known landmarks

That estimator should emit pose plus quality diagnostics. `LocalizationHealthPolicy` should remain a separate consumer so an estimator cannot unilaterally redefine what is safe enough for navigation.

## Next steps

1. Generate localization diagnostics from simulated odometry.
2. Inject wheel slip and stale updates.
3. Record health transitions in the mission flight recorder.
4. Let safety policy reduce speed or block movement based on localization state.
5. Add a second sensor source.
6. Compare estimator confidence against simulator ground truth to test calibration.
