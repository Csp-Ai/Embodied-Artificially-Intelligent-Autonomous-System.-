import math
import unittest

from rufus.kinematics import (
    DifferentialDriveGeometry,
    DifferentialDriveKinematics,
    WheelAngularVelocity,
)
from rufus.odometry import WheelOdometry, pose_error
from rufus.spatial import Pose2D


class OdometryV0Tests(unittest.TestCase):
    def kinematics(self) -> DifferentialDriveKinematics:
        return DifferentialDriveKinematics(
            DifferentialDriveGeometry(wheel_radius_m=0.1, axle_track_m=0.5)
        )

    def test_straight_wheel_odometry_advances_pose(self):
        odom = WheelOdometry(self.kinematics(), Pose2D(0.0, 0.0, 0.0, "odom"))

        sample = odom.update(WheelAngularVelocity(10.0, 10.0), 1.0)

        self.assertAlmostEqual(sample.pose.x_m, 1.0)
        self.assertAlmostEqual(sample.pose.y_m, 0.0)
        self.assertAlmostEqual(sample.pose.yaw_rad, 0.0)
        self.assertAlmostEqual(sample.estimated_distance_m, 1.0)
        self.assertAlmostEqual(sample.elapsed_s, 1.0)

    def test_rotation_accumulates_without_translation(self):
        odom = WheelOdometry(self.kinematics(), Pose2D(0.0, 0.0, 0.0))

        sample = odom.update(WheelAngularVelocity(-2.5, 2.5), 1.0)

        self.assertAlmostEqual(sample.pose.x_m, 0.0)
        self.assertAlmostEqual(sample.pose.y_m, 0.0)
        self.assertAlmostEqual(sample.pose.yaw_rad, 1.0)
        self.assertAlmostEqual(sample.estimated_distance_m, 0.0)
        self.assertAlmostEqual(sample.accumulated_abs_rotation_rad, 1.0)

    def test_multiple_updates_accumulate_distance_and_time(self):
        odom = WheelOdometry(self.kinematics(), Pose2D(0.0, 0.0))

        odom.update(WheelAngularVelocity(10.0, 10.0), 0.5)
        sample = odom.update(WheelAngularVelocity(10.0, 10.0), 0.5)

        self.assertAlmostEqual(sample.elapsed_s, 1.0)
        self.assertAlmostEqual(sample.estimated_distance_m, 1.0)
        self.assertAlmostEqual(sample.pose.x_m, 1.0)

    def test_pose_error_detects_wheel_scale_bias(self):
        truth_kinematics = self.kinematics()
        reference = truth_kinematics.integrate_wheels(
            Pose2D(0.0, 0.0, 0.0, "map"),
            WheelAngularVelocity(10.0, 10.0),
            1.0,
        )

        odom = WheelOdometry(
            self.kinematics(),
            Pose2D(0.0, 0.0, 0.0, "map"),
        )
        estimate = odom.update(WheelAngularVelocity(9.5, 9.5), 1.0).pose
        error = pose_error(estimate, reference)

        self.assertAlmostEqual(error.translation_m, 0.05)
        self.assertAlmostEqual(error.yaw_error_rad, 0.0)

    def test_pose_error_normalizes_heading_difference(self):
        error = pose_error(
            Pose2D(0.0, 0.0, math.radians(179.0)),
            Pose2D(0.0, 0.0, math.radians(-179.0)),
        )

        self.assertAlmostEqual(error.absolute_yaw_error_rad, math.radians(2.0))

    def test_pose_error_rejects_frame_mismatch(self):
        with self.assertRaises(ValueError):
            pose_error(
                Pose2D(0.0, 0.0, frame_id="odom"),
                Pose2D(0.0, 0.0, frame_id="map"),
            )

    def test_reset_clears_accumulated_state(self):
        odom = WheelOdometry(self.kinematics(), Pose2D(0.0, 0.0))
        odom.update(WheelAngularVelocity(10.0, 10.0), 1.0)

        odom.reset(Pose2D(3.0, 4.0, 3 * math.pi, "map"))

        self.assertEqual(odom.pose.frame_id, "map")
        self.assertAlmostEqual(odom.pose.yaw_rad, -math.pi)
        self.assertEqual(odom.elapsed_s, 0.0)
        self.assertEqual(odom.estimated_distance_m, 0.0)
        self.assertEqual(odom.accumulated_abs_rotation_rad, 0.0)

    def test_non_positive_dt_is_rejected(self):
        odom = WheelOdometry(self.kinematics(), Pose2D(0.0, 0.0))
        with self.assertRaises(ValueError):
            odom.update(WheelAngularVelocity(1.0, 1.0), 0.0)


if __name__ == "__main__":
    unittest.main()
