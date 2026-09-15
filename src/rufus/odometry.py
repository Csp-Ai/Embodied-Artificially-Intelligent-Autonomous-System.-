from __future__ import annotations

from dataclasses import dataclass
import math

from .kinematics import DifferentialDriveKinematics, Twist2D, WheelAngularVelocity
from .spatial import Pose2D, normalize_angle


@dataclass(frozen=True)
class PoseError2D:
    """Difference between an estimated pose and a reference pose."""

    translation_m: float
    yaw_error_rad: float

    @property
    def absolute_yaw_error_rad(self) -> float:
        return abs(self.yaw_error_rad)


@dataclass(frozen=True)
class OdometrySample:
    """One wheel-odometry state transition."""

    elapsed_s: float
    dt_s: float
    pose: Pose2D
    wheels: WheelAngularVelocity
    twist: Twist2D
    estimated_distance_m: float
    accumulated_abs_rotation_rad: float


@dataclass
class WheelOdometry:
    """Dead-reckoned pose from differential-drive wheel velocities.

    This estimator intentionally knows nothing about simulator or world ground
    truth. It predicts pose only from the drive model and wheel measurements.
    """

    kinematics: DifferentialDriveKinematics
    pose: Pose2D
    elapsed_s: float = 0.0
    estimated_distance_m: float = 0.0
    accumulated_abs_rotation_rad: float = 0.0

    def update(self, wheels: WheelAngularVelocity, dt_s: float) -> OdometrySample:
        if not math.isfinite(dt_s) or dt_s <= 0:
            raise ValueError("dt_s must be a positive finite value")

        twist = self.kinematics.wheels_to_twist(wheels)
        self.pose = self.kinematics.integrate_pose(self.pose, twist, dt_s)
        self.elapsed_s += dt_s
        self.estimated_distance_m += abs(twist.linear_mps) * dt_s
        self.accumulated_abs_rotation_rad += abs(twist.angular_rps) * dt_s

        return OdometrySample(
            elapsed_s=self.elapsed_s,
            dt_s=dt_s,
            pose=self.pose,
            wheels=wheels,
            twist=twist,
            estimated_distance_m=self.estimated_distance_m,
            accumulated_abs_rotation_rad=self.accumulated_abs_rotation_rad,
        )

    def reset(self, pose: Pose2D) -> None:
        self.pose = pose.normalized()
        self.elapsed_s = 0.0
        self.estimated_distance_m = 0.0
        self.accumulated_abs_rotation_rad = 0.0


def pose_error(estimate: Pose2D, reference: Pose2D) -> PoseError2D:
    """Compare an estimate with reference/ground-truth pose in the same frame."""

    if estimate.frame_id != reference.frame_id:
        raise ValueError(
            f"Estimate frame {estimate.frame_id!r} does not match reference frame {reference.frame_id!r}"
        )

    return PoseError2D(
        translation_m=estimate.point.distance_to(reference.point),
        yaw_error_rad=normalize_angle(estimate.yaw_rad - reference.yaw_rad),
    )
