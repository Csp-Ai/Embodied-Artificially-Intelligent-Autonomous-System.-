import math
import unittest

from rufus.spatial import GridTransform, MetricPoint2D, Pose2D, normalize_angle
from rufus.types import Position


class SpatialModelV0Tests(unittest.TestCase):
    def test_grid_metric_round_trip(self):
        transform = GridTransform(cell_size_m=0.5, origin_x_m=1.0, origin_y_m=-2.0)
        grid = Position(3, 4)

        metric = transform.grid_to_metric(grid)
        recovered = transform.metric_to_grid(metric, width=10, height=10)

        self.assertEqual(metric, MetricPoint2D(2.5, 0.0, "world"))
        self.assertEqual(recovered, grid)

    def test_pose_normalizes_yaw(self):
        pose = Pose2D(1.0, 2.0, 3 * math.pi).normalized()

        self.assertAlmostEqual(pose.yaw_rad, -math.pi)
        self.assertEqual(pose.frame_id, "world")

    def test_cross_frame_distance_is_rejected(self):
        a = MetricPoint2D(0.0, 0.0, "map")
        b = MetricPoint2D(1.0, 0.0, "odom")

        with self.assertRaises(ValueError):
            a.distance_to(b)

    def test_metric_to_grid_rejects_out_of_bounds_by_default(self):
        transform = GridTransform(cell_size_m=1.0)

        with self.assertRaises(ValueError):
            transform.metric_to_grid(
                MetricPoint2D(10.0, 10.0),
                width=3,
                height=3,
            )

    def test_metric_to_grid_can_clamp_for_operator_views(self):
        transform = GridTransform(cell_size_m=1.0)

        grid = transform.metric_to_grid(
            MetricPoint2D(10.0, -4.0),
            width=3,
            height=3,
            clamp=True,
        )

        self.assertEqual(grid, Position(2, 0))

    def test_pose_for_grid_preserves_frame_and_units(self):
        transform = GridTransform(
            cell_size_m=0.25,
            origin_x_m=-1.0,
            origin_y_m=2.0,
            frame_id="map",
        )

        pose = transform.pose_for_grid(Position(4, 2), yaw_rad=2 * math.pi)

        self.assertEqual(pose, Pose2D(0.0, 2.5, 0.0, "map"))

    def test_normalize_angle_stays_in_half_open_interval(self):
        samples = [
            -9 * math.pi,
            -2 * math.pi,
            -math.pi,
            0.0,
            math.pi,
            2 * math.pi,
            9 * math.pi,
        ]
        for sample in samples:
            normalized = normalize_angle(sample)
            self.assertGreaterEqual(normalized, -math.pi)
            self.assertLess(normalized, math.pi)


if __name__ == "__main__":
    unittest.main()
