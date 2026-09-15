import math
import unittest

from rufus.kinematics import (
    DifferentialDriveGeometry,
    DifferentialDriveKinematics,
    Twist2D,
    WheelAngularVelocity,
)
from rufus.spatial import Pose2D


class MobileKinematicsV0Tests(unittest.TestCase):
    def model(self) -> DifferentialDriveKinematics:
        return DifferentialDriveKinematics(
            DifferentialDriveGeometry(wheel_radius_m=0.1, axle_track_m=0.5)
        )

    def test_straight_motion_commands_equal_wheel_speeds(self):
        wheels = self.model().twist_to_wheels(Twist2D(1.0, 0.0))

        self.assertAlmostEqual(wheels.left_rad_s, 10.0)
        self.assertAlmostEqual(wheels.right_rad_s, 10.0)

    def test_in_place_rotation_commands_opposing_wheels(self):
        wheels = self.model().twist_to_wheels(Twist2D(0.0, 1.0))

        self.assertAlmostEqual(wheels.left_rad_s, -2.5)
        self.assertAlmostEqual(wheels.right_rad_s, 2.5)

    def test_twist_wheel_round_trip(self):
        model = self.model()
        desired = Twist2D(linear_mps=0.7, angular_rps=-0.4)

        recovered = model.wheels_to_twist(model.twist_to_wheels(desired))

        self.assertAlmostEqual(recovered.linear_mps, desired.linear_mps)
        self.assertAlmostEqual(recovered.angular_rps, desired.angular_rps)

    def test_straight_pose_integration_respects_heading(self):
        pose = Pose2D(1.0, 2.0, math.pi / 2.0, "map")

        result = self.model().integrate_pose(pose, Twist2D(2.0, 0.0), 0.5)

        self.assertAlmostEqual(result.x_m, 1.0)
        self.assertAlmostEqual(result.y_m, 3.0)
        self.assertAlmostEqual(result.yaw_rad, math.pi / 2.0)
        self.assertEqual(result.frame_id, "map")

    def test_arc_pose_integration_uses_exact_constant_twist_solution(self):
        pose = Pose2D(0.0, 0.0, 0.0)

        result = self.model().integrate_pose(
            pose,
            Twist2D(linear_mps=1.0, angular_rps=math.pi / 2.0),
            1.0,
        )

        radius = 1.0 / (math.pi / 2.0)
        self.assertAlmostEqual(result.x_m, radius, places=7)
        self.assertAlmostEqual(result.y_m, radius, places=7)
        self.assertAlmostEqual(result.yaw_rad, math.pi / 2.0, places=7)

    def test_wheel_odometry_can_rotate_in_place(self):
        result = self.model().integrate_wheels(
            Pose2D(0.0, 0.0, 0.0),
            WheelAngularVelocity(left_rad_s=-2.5, right_rad_s=2.5),
            1.0,
        )

        self.assertAlmostEqual(result.x_m, 0.0)
        self.assertAlmostEqual(result.y_m, 0.0)
        self.assertAlmostEqual(result.yaw_rad, 1.0)

    def test_invalid_drive_geometry_is_rejected(self):
        with self.assertRaises(ValueError):
            DifferentialDriveGeometry(wheel_radius_m=0.0, axle_track_m=0.5)
        with self.assertRaises(ValueError):
            DifferentialDriveGeometry(wheel_radius_m=0.1, axle_track_m=-1.0)

    def test_invalid_time_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            self.model().integrate_pose(
                Pose2D(0.0, 0.0),
                Twist2D(1.0, 0.0),
                -0.1,
            )


if __name__ == "__main__":
    unittest.main()
