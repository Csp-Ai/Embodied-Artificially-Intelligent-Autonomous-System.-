import math
import unittest

from rufus.control import PointControllerConfig, PointFollower, VelocityLimits
from rufus.kinematics import DifferentialDriveGeometry, DifferentialDriveKinematics
from rufus.spatial import MetricPoint2D, Pose2D


class MotionControllerV0Tests(unittest.TestCase):
    def controller(self) -> PointFollower:
        return PointFollower(
            limits=VelocityLimits(max_linear_mps=1.0, max_angular_rps=1.5),
            config=PointControllerConfig(
                linear_gain=1.2,
                angular_gain=2.5,
                position_tolerance_m=0.05,
                rotate_in_place_threshold_rad=math.radians(60.0),
            ),
        )

    def test_target_ahead_commands_forward_motion(self):
        twist = self.controller().command(
            Pose2D(0.0, 0.0, 0.0),
            MetricPoint2D(1.0, 0.0),
        )

        self.assertGreater(twist.linear_mps, 0.0)
        self.assertAlmostEqual(twist.angular_rps, 0.0)
        self.assertLessEqual(twist.linear_mps, 1.0)

    def test_large_heading_error_rotates_in_place(self):
        twist = self.controller().command(
            Pose2D(0.0, 0.0, 0.0),
            MetricPoint2D(0.0, 1.0),
        )

        self.assertEqual(twist.linear_mps, 0.0)
        self.assertGreater(twist.angular_rps, 0.0)
        self.assertLessEqual(abs(twist.angular_rps), 1.5)

    def test_target_behind_does_not_command_reverse(self):
        twist = self.controller().command(
            Pose2D(0.0, 0.0, 0.0),
            MetricPoint2D(-1.0, 0.0),
        )

        self.assertEqual(twist.linear_mps, 0.0)
        self.assertNotEqual(twist.angular_rps, 0.0)

    def test_within_tolerance_stops(self):
        controller = self.controller()
        pose = Pose2D(0.0, 0.0, 1.0)
        target = MetricPoint2D(0.02, 0.01)

        self.assertTrue(controller.at_target(pose, target))
        self.assertEqual(controller.command(pose, target).linear_mps, 0.0)
        self.assertEqual(controller.command(pose, target).angular_rps, 0.0)

    def test_frame_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            self.controller().command(
                Pose2D(0.0, 0.0, 0.0, "odom"),
                MetricPoint2D(1.0, 0.0, "map"),
            )

    def test_velocity_limits_are_enforced(self):
        twist = self.controller().command(
            Pose2D(0.0, 0.0, 0.0),
            MetricPoint2D(100.0, 10.0),
        )

        self.assertLessEqual(twist.linear_mps, 1.0)
        self.assertLessEqual(abs(twist.angular_rps), 1.5)

    def test_controller_converges_with_ideal_differential_drive(self):
        controller = self.controller()
        kinematics = DifferentialDriveKinematics(
            DifferentialDriveGeometry(wheel_radius_m=0.1, axle_track_m=0.5)
        )
        pose = Pose2D(0.0, 0.0, math.pi / 2.0)
        target = MetricPoint2D(2.0, 0.5)
        dt_s = 0.05

        for _ in range(500):
            if controller.at_target(pose, target):
                break
            twist = controller.command(pose, target)
            wheels = kinematics.twist_to_wheels(twist)
            pose = kinematics.integrate_wheels(pose, wheels, dt_s)

        self.assertTrue(controller.at_target(pose, target))
        self.assertLessEqual(pose.point.distance_to(target), 0.05)

    def test_invalid_limits_and_controller_config_are_rejected(self):
        with self.assertRaises(ValueError):
            VelocityLimits(max_linear_mps=0.0, max_angular_rps=1.0)
        with self.assertRaises(ValueError):
            PointControllerConfig(linear_gain=-1.0)


if __name__ == "__main__":
    unittest.main()
