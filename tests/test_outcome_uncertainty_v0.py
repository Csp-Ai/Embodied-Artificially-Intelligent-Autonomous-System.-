import unittest

from rufus import DeterministicGridWorld, RufusBrain
from rufus.types import ActionResult, MissionStatus, Position


class AmbiguousReceiptWorld(DeterministicGridWorld):
    def __post_init__(self):
        self.dispatch_count = 0

    def apply(self, action):
        self.dispatch_count = getattr(self, "dispatch_count", 0) + 1
        # The world changes despite a false/ambiguous executor receipt.
        super().apply(action)
        return ActionResult(
            False, "Executor response lost",
            outcome_uncertain=True, retry_prohibited=True,
        )


class ContradictoryReadbackWorld(DeterministicGridWorld):
    def apply(self, action):
        self.dispatch_count = getattr(self, "dispatch_count", 0) + 1
        # False success receipt without a physical effect.
        return ActionResult(True, "Executor claimed success", retry_prohibited=True)


def world_of(world_type):
    return world_type(
        width=5, height=3,
        robot_position=Position(0, 1),
        object_position=Position(2, 1),
        destination=Position(4, 1),
        battery=100,
    )


class OutcomeUncertaintyTests(unittest.TestCase):
    def test_ambiguous_effect_stops_without_redispaching(self):
        world = world_of(AmbiguousReceiptWorld)
        report = RufusBrain(max_recoveries=50).run(world)

        self.assertEqual(report.status, MissionStatus.ABORTED)
        self.assertEqual(world.dispatch_count, 1)
        self.assertEqual(world.robot_position, Position(1, 1))
        self.assertTrue(any(
            e.phase == "verify" and e.data.get("conclusive") is False
            for e in report.events
        ))

    def test_adapter_owned_recovery_stops_on_readback_disagreement(self):
        world = world_of(ContradictoryReadbackWorld)
        report = RufusBrain(max_recoveries=50).run(world)

        self.assertEqual(report.status, MissionStatus.ABORTED)
        self.assertEqual(world.dispatch_count, 1)
        self.assertEqual(world.robot_position, Position(0, 1))
        self.assertIn("redispatch prohibited", report.reason)


if __name__ == "__main__":
    unittest.main()
