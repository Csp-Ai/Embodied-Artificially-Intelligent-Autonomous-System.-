from __future__ import annotations

from dataclasses import dataclass
import math

from .spatial import Pose2D, normalize_angle


@dataclass(frozen=True)
class Twist2D:
    """Planar body velocity expressed at the robot base frame."""

    linear_mps: float
    angular_rps: float


@dataclass(frozen=True)
class WheelAngularVelocity:
    """Left/right wheel angular velocity in radians per second."""

    left_rad_s: float
    right_rad_s: float


@dataclass(frozen=True)
class DifferentialDriveGeometry:
    """Physical geometry of a differential-drive mobile base."""

    wheel_radius_m: float
    axle_track_m: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.wheel_radius_m) or self.wheel_radius_m <= 0:
            raise ValueError("wheel_radius_m must be a positive finite value")
        if not math.isfinite(self.axle_track_m) or self.axle_track_m <= 0:
            raise ValueError("axle_track_m must be a positive finite value")


@dataclass(frozen=True)
class DifferentialDriveKinematics:
    """Forward/inverse kinematics and dead-reckoning for a two-wheel base."""

    geometry: DifferentialDriveGeometry

    def twist_to_wheels(self, twist: Twist2D) -> WheelAngularVelocity:
        """Convert desired body twist to wheel angular velocities."""

        self._validate_twist(twist)
        radius = self.geometry.wheel_radius_m
        half_track = self.geometry.axle_track_m / 2.0
        return WheelAngularVelocity(
            left_rad_s=(twist.linear_mps - twist.angular_rps * half_track) / radius,
            right_rad_s=(twist.linear_mps + twist.angular_rps * half_track) / radius,
        )

    def wheels_to_twist(self, wheels: WheelAngularVelocity) -> Twist2D:
        """Convert measured wheel angular velocities to body twist."""

        self._validate_wheels(wheels)
        radius = self.geometry.wheel_radius_m
        track = self.geometry.axle_track_m
        left_linear = wheels.left_rad_s * radius
        right_linear = wheels.right_rad_s * radius
        return Twist2D(
            linear_mps=(left_linear + right_linear) / 2.0,
            angular_rps=(right_linear - left_linear) / track,
        )

    def integrate_pose(self, pose: Pose2D, twist: Twist2D, dt_s: float) -> Pose2D:
        """Integrate constant body twist exactly over a planar time interval.

        This is ideal differential-drive dead reckoning. It deliberately does
        not model wheel slip, encoder noise, or localization covariance yet.
        """

        self._validate_twist(twist)
        if not math.isfinite(dt_s) or dt_s < 0:
            raise ValueError("dt_s must be a finite non-negative value")
        if dt_s == 0:
            return pose.normalized()

        theta = pose.yaw_rad
        linear = twist.linear_mps
        angular = twist.angular_rps
        delta_theta = angular * dt_s

        if abs(angular) < 1e-12:
            next_x = pose.x_m + linear * math.cos(theta) * dt_s
            next_y = pose.y_m + linear * math.sin(theta) * dt_s
        else:
            radius = linear / angular
            next_theta = theta + delta_theta
            next_x = pose.x_m + radius * (math.sin(next_theta) - math.sin(theta))
            next_y = pose.y_m - radius * (math.cos(next_theta) - math.cos(theta))

        return Pose2D(
            x_m=next_x,
            y_m=next_y,
            yaw_rad=normalize_angle(theta + delta_theta),
            frame_id=pose.frame_id,
        )

    def integrate_wheels(
        self,
        pose: Pose2D,
        wheels: WheelAngularVelocity,
        dt_s: float,
    ) -> Pose2D:
        """Integrate measured wheel velocities into planar dead-reckoned pose."""

        return self.integrate_pose(pose, self.wheels_to_twist(wheels), dt_s)

    @staticmethod
    def _validate_twist(twist: Twist2D) -> None:
        if not math.isfinite(twist.linear_mps):
            raise ValueError("linear_mps must be finite")
        if not math.isfinite(twist.angular_rps):
            raise ValueError("angular_rps must be finite")

    @staticmethod
    def _validate_wheels(wheels: WheelAngularVelocity) -> None:
        if not math.isfinite(wheels.left_rad_s):
            raise ValueError("left_rad_s must be finite")
        if not math.isfinite(wheels.right_rad_s):
            raise ValueError("right_rad_s must be finite")
