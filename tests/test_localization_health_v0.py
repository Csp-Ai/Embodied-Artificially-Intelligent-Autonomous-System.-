import math
import unittest

from rufus.localization import (
    LocalizationDiagnostics,
    LocalizationHealth,
    LocalizationHealthPolicy,
    LocalizationHealthThresholds,
)


class LocalizationHealthV0Tests(unittest.TestCase):
    def policy(self) -> LocalizationHealthPolicy:
        return LocalizationHealthPolicy(
            LocalizationHealthThresholds(
                healthy_position_uncertainty_m=0.10,
                max_position_uncertainty_m=0.30,
                healthy_yaw_uncertainty_rad=math.radians(5),
                max_yaw_uncertainty_rad=math.radians(15),
                healthy_age_s=0.25,
                max_age_s=1.0,
                degraded_speed_scale=0.4,
            )
        )

    def test_healthy_localization_allows_full_speed(self):
        decision = self.policy().evaluate(
            LocalizationDiagnostics(True, 0.05, math.radians(2), 0.10, "wheel+imu")
        )

        self.assertEqual(decision.health, LocalizationHealth.HEALTHY)
        self.assertTrue(decision.navigation_allowed)
        self.assertEqual(decision.speed_scale, 1.0)

    def test_degraded_localization_allows_reduced_speed(self):
        decision = self.policy().evaluate(
            LocalizationDiagnostics(True, 0.20, math.radians(8), 0.40, "wheel+imu")
        )

        self.assertEqual(decision.health, LocalizationHealth.DEGRADED)
        self.assertTrue(decision.navigation_allowed)
        self.assertEqual(decision.speed_scale, 0.4)

    def test_excessive_uncertainty_blocks_navigation(self):
        decision = self.policy().evaluate(
            LocalizationDiagnostics(True, 0.31, math.radians(3), 0.10)
        )

        self.assertEqual(decision.health, LocalizationHealth.UNUSABLE)
        self.assertFalse(decision.navigation_allowed)
        self.assertEqual(decision.speed_scale, 0.0)
        self.assertIn("position uncertainty", decision.reason)

    def test_stale_pose_blocks_navigation(self):
        decision = self.policy().evaluate(
            LocalizationDiagnostics(True, 0.05, math.radians(2), 1.01)
        )

        self.assertEqual(decision.health, LocalizationHealth.UNUSABLE)
        self.assertFalse(decision.navigation_allowed)
        self.assertIn("stale", decision.reason)

    def test_unknown_quality_holds_instead_of_guessing(self):
        decision = self.policy().evaluate(
            LocalizationDiagnostics(True, None, math.radians(2), 0.10)
        )

        self.assertEqual(decision.health, LocalizationHealth.UNKNOWN)
        self.assertFalse(decision.navigation_allowed)
        self.assertIn("unknown", decision.reason.lower())

    def test_unavailable_localization_blocks_navigation(self):
        decision = self.policy().evaluate(
            LocalizationDiagnostics(False, None, None, None, "localizer")
        )

        self.assertEqual(decision.health, LocalizationHealth.UNUSABLE)
        self.assertFalse(decision.navigation_allowed)
        self.assertIn("unavailable", decision.reason.lower())

    def test_threshold_boundaries_are_inclusive_for_healthier_state(self):
        thresholds = self.policy().thresholds
        healthy = self.policy().evaluate(
            LocalizationDiagnostics(
                True,
                thresholds.healthy_position_uncertainty_m,
                thresholds.healthy_yaw_uncertainty_rad,
                thresholds.healthy_age_s,
            )
        )
        degraded_at_max = self.policy().evaluate(
            LocalizationDiagnostics(
                True,
                thresholds.max_position_uncertainty_m,
                thresholds.max_yaw_uncertainty_rad,
                thresholds.max_age_s,
            )
        )

        self.assertEqual(healthy.health, LocalizationHealth.HEALTHY)
        self.assertEqual(degraded_at_max.health, LocalizationHealth.DEGRADED)

    def test_invalid_diagnostics_and_thresholds_are_rejected(self):
        with self.assertRaises(ValueError):
            LocalizationDiagnostics(True, -0.1, 0.1, 0.1)
        with self.assertRaises(ValueError):
            LocalizationHealthThresholds(
                healthy_position_uncertainty_m=0.3,
                max_position_uncertainty_m=0.2,
            )


if __name__ == "__main__":
    unittest.main()
