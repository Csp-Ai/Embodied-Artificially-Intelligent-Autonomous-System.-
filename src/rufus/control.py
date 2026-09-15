from __future__ import annotations

from dataclasses import dataclass
import math

from .kinematics import Twist2D
from .spatial import MetricPoint2D, Pose2D, normalize_angle


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


@dataclass(frozen=True)
class VelocityLimits:
    max_linear_mps: float
    max_angular_rps: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.max_linear_mps) or self.max_linear_mps <= 0:
            raise ValueError("max_linear_mps must be a positive finite value")
        if not math.isfinite(self.max_angular_rps) or self.max_angular_rps <= 0:
            raise ValueError("max_angular_rps must be a positive finite value")


@dataclass(frozen=True)
class PointControllerConfig:
    linear_gain: float = 1.0
    angular_gain: float = 2.0
    position_tolerance_m: float = 0.05
    rotate_in_place_threshold_rad: float = math.radians(60.0)

    def __post_init__(self) -> None:
        for name, value in (
            ("linear_gain", self.linear_gain),
            ("angular_gain", self.angular_gain),
            ("position_tolerance_m", self.position_tolerance_m),
            ("rotate_in_place_threshold_rad", self.rotate_in_place_threshold_rad),
        ):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite value")
        if self.rotate_in_place_threshold_rad > math.pi:
            raise ValueError("rotate_in_place_threshold_rad must be <= pi")


@dataclass(frozen=True)
class PointFollower:
    """Simple bounded controller for driving a planar base toward a point.

    The controller turns in place when the heading error is large. Once the
    target is sufficiently in front of the robot, it drives forward while
    continuing to correct heading. It intentionally does not command reverse
    motion in v0.
    """

    limits: VelocityLimits
    config: PointControllerConfig = PointControllerConfig()

    def command(self, pose: Pose2D, target: MetricPoint2D) -> Twist2D:
        if pose.frame_id != target.frame_id:
            raise ValueError(
                f"Pose frame {pose.frame_id!r} does not match target frame {target.frame_id!r}"
            )

        dx = target.x_m - pose.x_m
        dy = target.y_m - pose.y_m
        distance = math.hypot(dx, dy)

        if distance <= self.config.position_tolerance_m:
            return Twist2D(0.0, 0.0)

        desired_heading = math.atan2(dy, dx)
        heading_error = normalize_angle(desired_heading - pose.yaw_rad)
        angular = _clamp(
            self.config.angular_gain * heading_error,
            -self.limits.max_angular_rps,
            self.limits.max_angular_rps,
        )

        if abs(heading_error) >= self.config.rotate_in_place_threshold_rad:
            return Twist2D(0.0, angular)

        # Reduce forward speed as heading error grows so the robot does not
        # cut aggressively across a waypoint while it is still turning.
        alignment = max(0.0, math.cos(heading_error))
        linear = _clamp(
            self.config.linear_gain * distance * alignment,
            0.0,
            self.limits.max_linear_mps,
        )
        return Twist2D(linear, angular)

    def at_target(self, pose: Pose2D, target: MetricPoint2D) -> bool:
        return pose.point.distance_to(target) <= self.config.position_tolerance_m
