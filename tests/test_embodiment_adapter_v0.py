import unittest

from rufus import DeterministicGridWorld, RufusBrain
from rufus.interfaces import EmbodimentAdapter, NavigationContext
from rufus.simulation import render_ascii, snapshot
from rufus.types import Action, ActionResult, MissionStatus, Position, WorldObservation


class DelegatingEmbodiment:
    def __init__(self, world: DeterministicGridWorld):
        self.world = world

    def observe(self) -> WorldObservation:
        return self.world.observe()

    def apply(self, action: Action) -> ActionResult:
        return self.world.apply(action)

    def navigation_context(self) -> NavigationContext:
        return self.world.navigation_context()


class RufusEmbodimentAdapterV0Tests(unittest.TestCase):
    def make_world(self, **overrides):
        values = dict(
            width=5,
            height=3,
            robot_position=Position(0, 1),
            object_position=Position(2, 1),
            destination=Position(4, 1),
            battery=100,
        )
        values.update(overrides)
        return DeterministicGridWorld(**values)

    def test_brain_runs_against_protocol_not_concrete_world(self):
        adapter = DelegatingEmbodiment(self.make_world())
        self.assertIsInstance(adapter, EmbodimentAdapter)
        report = RufusBrain().run(adapter)
        self.assertEqual(report.status, MissionStatus.COMPLETED)

    def test_navigation_context_is_explicit(self):
        world = self.make_world()
        self.assertEqual(world.navigation_context(), NavigationContext(5, 3))

    def test_ground_truth_remains_separate_from_masked_observation(self):
        world = self.make_world(unknown_observations={1: {"object_position"}})
        observed = world.observe()
        truth = snapshot(world)
        self.assertIsNone(observed.object_position.value)
        self.assertEqual(truth.object_position, Position(2, 1))

    def test_ascii_renderer_is_operator_only_view(self):
        world = self.make_world(obstacles={Position(1, 1)})
        frame = render_ascii(world)
        self.assertIn("R", frame)
        self.assertIn("O", frame)
        self.assertIn("D", frame)
        self.assertIn("#", frame)


if __name__ == "__main__":
    unittest.main()
