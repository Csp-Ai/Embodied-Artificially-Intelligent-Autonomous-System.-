import importlib.util
import unittest
from unittest.mock import patch

from rufus.adapters.mujoco import (
    MuJoCoGridConfig,
    MuJoCoGridEmbodiment,
    MuJoCoUnavailableError,
)
from rufus.spatial import GridTransform
from rufus.brain import RufusBrain
from rufus.types import MissionStatus, Position


class MuJoCoAdapterV0Tests(unittest.TestCase):
    def config(self, **overrides):
        values = dict(
            width=5,
            height=3,
            robot_position=Position(0, 1),
            object_position=Position(2, 1),
            destination=Position(4, 1),
            battery=100,
        )
        values.update(overrides)
        return MuJoCoGridConfig(**values)

    def test_model_xml_declares_physics_body_and_servos(self):
        xml = MuJoCoGridEmbodiment.model_xml(
            self.config(obstacles=frozenset({Position(1, 0)}))
        )
        self.assertIn('model="rufus_mission_001"', xml)
        self.assertIn('name="robot_x_servo"', xml)
        self.assertIn('name="robot_y_servo"', xml)
        self.assertIn('name="obstacle_0"', xml)
        self.assertIn('integrator="implicitfast"', xml)

    def test_config_uses_shared_grid_transform_authority(self):
        config = self.config(
            cell_size_m=0.5,
            origin_x_m=1.0,
            origin_y_m=-2.0,
            frame_id="map",
        )
        transform = config.grid_transform()
        self.assertEqual(
            transform,
            GridTransform(
                cell_size_m=0.5,
                origin_x_m=1.0,
                origin_y_m=-2.0,
                frame_id="map",
            ),
        )
        point = transform.grid_to_metric(Position(2, 1))
        self.assertEqual((point.x_m, point.y_m, point.frame_id), (2.0, -1.5, "map"))

    def test_invalid_world_is_rejected_before_loading_mujoco(self):
        with self.assertRaises(ValueError):
            self.config(robot_position=Position(99, 99))

    def test_missing_optional_dependency_has_actionable_error(self):
        with patch(
            "rufus.adapters.mujoco.importlib.import_module",
            side_effect=ModuleNotFoundError("mujoco"),
        ):
            with self.assertRaises(MuJoCoUnavailableError) as caught:
                MuJoCoGridEmbodiment(self.config())
        self.assertIn(".[mujoco]", str(caught.exception))

    @unittest.skipUnless(
        importlib.util.find_spec("mujoco"),
        "MuJoCo optional dependency not installed",
    )
    def test_mission_001_completes_in_mujoco(self):
        world = MuJoCoGridEmbodiment(self.config())
        report = RufusBrain(max_steps=40).run(world)
        self.assertEqual(report.status, MissionStatus.COMPLETED)
        self.assertTrue(report.final_observation.delivered.value)
        self.assertTrue(world.ground_truth().delivered)
        self.assertEqual(world.metric_pose().frame_id, "world")


if __name__ == "__main__":
    unittest.main()
