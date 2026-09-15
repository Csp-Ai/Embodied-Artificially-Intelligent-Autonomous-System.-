import unittest

from rufus.benchmark import default_suite, format_scorecard, run_suite
from rufus.types import MissionStatus


class MissionBenchmarkV0Tests(unittest.TestCase):
    def test_default_suite_matches_expected_outcomes(self):
        summary = run_suite(default_suite())

        self.assertEqual(summary.total, 8)
        self.assertEqual(summary.expected_passes, 8)
        self.assertEqual(summary.completed, 5)
        self.assertEqual(summary.safe_aborts, 3)
        self.assertEqual(summary.failed, 0)
        self.assertEqual(summary.expected_pass_rate, 1.0)
        self.assertEqual(summary.trace_valid_rate, 1.0)

    def test_benchmark_exposes_operational_signals(self):
        summary = run_suite(default_suite())
        by_name = {result.name: result for result in summary.results}

        self.assertGreaterEqual(
            by_name["dynamic_obstacle_recovery"].recoveries,
            1,
        )
        self.assertGreaterEqual(
            by_name["pickup_failure_recovery"].verification_failures,
            1,
        )
        self.assertGreaterEqual(
            by_name["low_energy_policy_abort"].policy_blocks,
            1,
        )
        self.assertGreaterEqual(
            by_name["persistent_perception_abort"].uncertain_observations,
            1,
        )
        self.assertEqual(
            by_name["persistent_perception_abort"].status,
            MissionStatus.ABORTED,
        )

    def test_scorecard_is_human_readable(self):
        scorecard = format_scorecard(run_suite(default_suite()))

        self.assertIn("RUFUS MISSION OPS SCORECARD", scorecard)
        self.assertIn("Expected pass: 8/8 (100%)", scorecard)
        self.assertIn("[PASS] dynamic_obstacle_recovery", scorecard)


if __name__ == "__main__":
    unittest.main()
