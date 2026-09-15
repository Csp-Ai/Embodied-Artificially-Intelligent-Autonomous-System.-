from __future__ import annotations

from dataclasses import dataclass

from .types import Action, ActionKind, PolicyDecision, WorldObservation


@dataclass(frozen=True)
class SafetyPolicy:
    energy_reserve: int = 5
    move_cost: int = 1

    def evaluate(self, action: Action, observation: WorldObservation) -> PolicyDecision:
        if action.kind is ActionKind.ABORT:
            return PolicyDecision(True, "Abort is always allowed")

        battery = observation.battery.value
        if battery is None:
            return PolicyDecision(False, "Battery state is unknown")

        if action.kind is ActionKind.MOVE and battery - self.move_cost < self.energy_reserve:
            return PolicyDecision(
                False,
                f"Move would violate energy reserve ({battery}% -> {battery - self.move_cost}% < {self.energy_reserve}%)",
            )

        return PolicyDecision(True, "Action is within current safety policy")
