import json
import unittest

from rufus import DeterministicGridWorld, FlightRecorder, RufusBrain
from rufus.types import MissionStatus, Position


class RufusFlightRecorderV0Tests(unittest.TestCase):
    def base_world(self, **overrides):
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

    def test_dynamic_obstacle_forces_recovery_and_replan(self):
        world = self.base_world(obstacle_injections={1: {Position(1, 1)}})
        report = RufusBrain(max_recoveries=3).run(world)
        self.assertEqual(report.status, MissionStatus.COMPLETED)
        self.assertTrue(any(e.phase == "recover" for e in report.events))
        self.assertIn(Position(1, 1), report.final_observation.obstacles.value)

    def test_transient_unknown_state_is_reobserved(self):
        world = self.base_world(unknown_observations={1: {"object_position"}})
        report = RufusBrain(max_recoveries=2).run(world)
        self.assertEqual(report.status, MissionStatus.COMPLETED)
        self.assertTrue(any(e.phase == "recover" and "unknown" in e.message.lower() for e in report.events))

    def test_persistent_unknown_state_safely_aborts(self):
        world = self.base_world(
            unknown_observations={1: {"object_position"}, 2: {"object_position"}, 3: {"object_position"}}
        )
        report = RufusBrain(max_recoveries=2).run(world)
        self.assertEqual(report.status, MissionStatus.ABORTED)
        self.assertIn("uncertainty", report.reason.lower())

    def test_flight_recorder_exports_valid_json(self):
        report = RufusBrain().run(self.base_world())
        payload = json.loads(FlightRecorder.dumps(report))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "completed")
        self.assertTrue(payload["events"])

    def test_completed_trace_validates(self):
        report = RufusBrain().run(self.base_world())
        ok, problems = FlightRecorder.validate(report)
        self.assertTrue(ok)
        self.assertEqual(problems, ())
        timeline = FlightRecorder.timeline(report)
        self.assertIn("RUFUS MISSION", timeline)
        self.assertIn("VERIFY", timeline)


if __name__ == "__main__":
    unittest.main()
