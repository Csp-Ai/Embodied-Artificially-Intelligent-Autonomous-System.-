from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class LocalizationHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    UNUSABLE = "unusable"


@dataclass(frozen=True)
class LocalizationDiagnostics:
    """Runtime diagnostics reported by a localization subsystem.

    These are estimator-reported properties, not simulator ground-truth error.
    """

    available: bool
    position_uncertainty_m: float | None
    yaw_uncertainty_rad: float | None
    age_s: float | None
    source: str = "localization"

    def __post_init__(self) -> None:
        for name, value in (
            ("position_uncertainty_m", self.position_uncertainty_m),
            ("yaw_uncertainty_rad", self.yaw_uncertainty_rad),
            ("age_s", self.age_s),
        ):
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError(f"{name} must be a finite non-negative value or None")
        if not self.source:
            raise ValueError("source must not be empty")


@dataclass(frozen=True)
class LocalizationHealthThresholds:
    healthy_position_uncertainty_m: float = 0.10
    max_position_uncertainty_m: float = 0.30
    healthy_yaw_uncertainty_rad: float = math.radians(5.0)
    max_yaw_uncertainty_rad: float = math.radians(15.0)
    healthy_age_s: float = 0.25
    max_age_s: float = 1.0
    degraded_speed_scale: float = 0.5

    def __post_init__(self) -> None:
        pairs = (
            (
                "position uncertainty",
                self.healthy_position_uncertainty_m,
                self.max_position_uncertainty_m,
            ),
            (
                "yaw uncertainty",
                self.healthy_yaw_uncertainty_rad,
                self.max_yaw_uncertainty_rad,
            ),
            ("pose age", self.healthy_age_s, self.max_age_s),
        )
        for label, healthy, maximum in pairs:
            if not math.isfinite(healthy) or healthy < 0:
                raise ValueError(f"healthy {label} threshold must be finite and non-negative")
            if not math.isfinite(maximum) or maximum <= healthy:
                raise ValueError(f"max {label} threshold must be finite and greater than healthy threshold")
        if not math.isfinite(self.degraded_speed_scale) or not (0 < self.degraded_speed_scale <= 1):
            raise ValueError("degraded_speed_scale must be in (0, 1]")


@dataclass(frozen=True)
class LocalizationHealthDecision:
    health: LocalizationHealth
    navigation_allowed: bool
    speed_scale: float
    reason: str


@dataclass(frozen=True)
class LocalizationHealthPolicy:
    thresholds: LocalizationHealthThresholds = LocalizationHealthThresholds()

    def evaluate(self, diagnostics: LocalizationDiagnostics) -> LocalizationHealthDecision:
        if not diagnostics.available:
            return LocalizationHealthDecision(
                health=LocalizationHealth.UNUSABLE,
                navigation_allowed=False,
                speed_scale=0.0,
                reason=f"Localization unavailable from {diagnostics.source}",
            )

        values = (
            diagnostics.position_uncertainty_m,
            diagnostics.yaw_uncertainty_rad,
            diagnostics.age_s,
        )
        if any(value is None for value in values):
            return LocalizationHealthDecision(
                health=LocalizationHealth.UNKNOWN,
                navigation_allowed=False,
                speed_scale=0.0,
                reason="Localization quality is unknown; hold and re-observe",
            )

        position = diagnostics.position_uncertainty_m
        yaw = diagnostics.yaw_uncertainty_rad
        age = diagnostics.age_s
        assert position is not None and yaw is not None and age is not None

        failures: list[str] = []
        if position > self.thresholds.max_position_uncertainty_m:
            failures.append("position uncertainty exceeds maximum")
        if yaw > self.thresholds.max_yaw_uncertainty_rad:
            failures.append("yaw uncertainty exceeds maximum")
        if age > self.thresholds.max_age_s:
            failures.append("pose estimate is too stale")

        if failures:
            return LocalizationHealthDecision(
                health=LocalizationHealth.UNUSABLE,
                navigation_allowed=False,
                speed_scale=0.0,
                reason="; ".join(failures),
            )

        degraded: list[str] = []
        if position > self.thresholds.healthy_position_uncertainty_m:
            degraded.append("position uncertainty above healthy range")
        if yaw > self.thresholds.healthy_yaw_uncertainty_rad:
            degraded.append("yaw uncertainty above healthy range")
        if age > self.thresholds.healthy_age_s:
            degraded.append("pose estimate older than healthy range")

        if degraded:
            return LocalizationHealthDecision(
                health=LocalizationHealth.DEGRADED,
                navigation_allowed=True,
                speed_scale=self.thresholds.degraded_speed_scale,
                reason="; ".join(degraded),
            )

        return LocalizationHealthDecision(
            health=LocalizationHealth.HEALTHY,
            navigation_allowed=True,
            speed_scale=1.0,
            reason="Localization within configured healthy thresholds",
        )
