import unittest

from rufus import DeterministicGridWorld, RufusBrain, SafetyPolicy
from rufus.types import MissionStatus, Position


class RufusBrainV0Tests(unittest.TestCase):
    def test_nominal_delivery_completes(self) -> None:
        world = DeterministicGridWorld(
            width=5,
            height=3,
            robot_position=Position(0, 1),
            object_position=Position(2, 1),
            destination=Position(4, 1),
            battery=100,
        )

        report = RufusBrain().run(world)

        self.assertEqual(report.status, MissionStatus.COMPLETED)
        self.assertTrue(report.final_observation.delivered.value)
        self.assertTrue(any(event.phase == "verify" for event in report.events))

    def test_plans_around_blocked_route(self) -> None:
        world = DeterministicGridWorld(
            width=5,
            height=3,
            robot_position=Position(0, 1),
            object_position=Position(2, 1),
            destination=Position(4, 1),
            battery=100,
            obstacles={Position(1, 1)},
        )

        report = RufusBrain().run(world)

        self.assertEqual(report.status, MissionStatus.COMPLETED)
        visited_targets = {
            event.data.get("target")
            for event in report.events
            if event.phase == "plan" and event.data.get("target") is not None
        }
        self.assertNotIn(Position(1, 1), visited_targets)

    def test_low_energy_is_safely_aborted(self) -> None:
        world = DeterministicGridWorld(
            width=5,
            height=3,
            robot_position=Position(0, 1),
            object_position=Position(2, 1),
            destination=Position(4, 1),
            battery=5,
        )

        report = RufusBrain(policy=SafetyPolicy(energy_reserve=5)).run(world)

        self.assertEqual(report.status, MissionStatus.ABORTED)
        self.assertIn("energy reserve", report.reason.lower())
        self.assertEqual(world.robot_position, Position(0, 1))

    def test_failed_pickup_recovers_and_retries(self) -> None:
        world = DeterministicGridWorld(
            width=4,
            height=3,
            robot_position=Position(0, 1),
            object_position=Position(1, 1),
            destination=Position(3, 1),
            battery=100,
            pickup_failures_remaining=1,
        )

        report = RufusBrain(max_recoveries=2).run(world)

        self.assertEqual(report.status, MissionStatus.COMPLETED)
        self.assertTrue(any(event.phase == "recover" for event in report.events))

    def test_impossible_route_aborts(self) -> None:
        world = DeterministicGridWorld(
            width=3,
            height=3,
            robot_position=Position(0, 1),
            object_position=Position(2, 1),
            destination=Position(2, 2),
            battery=100,
            obstacles={Position(1, 0), Position(1, 1), Position(1, 2)},
        )

        report = RufusBrain().run(world)

        self.assertEqual(report.status, MissionStatus.ABORTED)
        self.assertIn("no safe route", report.reason.lower())


if __name__ == "__main__":
    unittest.main()
