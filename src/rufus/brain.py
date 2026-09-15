from __future__ import annotations

from dataclasses import dataclass

from .planner import MissionPlanner
from .policy import SafetyPolicy
from .types import ActionKind, MissionEvent, MissionReport, MissionStatus
from .verifier import Verifier
from .world import DeterministicGridWorld


@dataclass
class RufusBrain:
    policy: SafetyPolicy = SafetyPolicy()
    max_steps: int = 100
    max_recoveries: int = 3

    def _recover_or_stop(self, events, recoveries, step, message):
        recoveries += 1
        events.append(MissionEvent(step, "recover", message, {
            "attempt": recoveries,
            "limit": self.max_recoveries,
        }))
        return recoveries, recoveries <= self.max_recoveries

    def run(self, world: DeterministicGridWorld) -> MissionReport:
        planner = MissionPlanner()
        events: list[MissionEvent] = []
        recoveries = 0

        for step in range(self.max_steps + 1):
            observation = world.observe()
            events.append(MissionEvent(step, "observe", "World state observed", {
                "robot": observation.robot_position.value,
                "object": observation.object_position.value,
                "battery": observation.battery.value,
                "carrying": observation.carrying.value,
                "delivered": observation.delivered.value,
                "unknown": [
                    name for name in observation.__dataclass_fields__
                    if getattr(observation, name).value is None
                ],
            }))

            if observation.delivered.value is True:
                return MissionReport(MissionStatus.COMPLETED, "Delivery verified", step, tuple(events), observation)

            action = planner.next_action(observation, world.width, world.height)
            events.append(MissionEvent(step, "plan", action.reason, {
                "action": action.kind.value,
                "target": action.target,
            }))

            if action.kind is ActionKind.ABORT:
                if "unknown" in action.reason.lower():
                    recoveries, can_retry = self._recover_or_stop(
                        events, recoveries, step, "Required state unknown; re-observe before deciding"
                    )
                    if can_retry:
                        continue
                    reason = "Perception uncertainty exceeded recovery budget"
                    events.append(MissionEvent(step, "abort", reason))
                    return MissionReport(MissionStatus.ABORTED, reason, step, tuple(events), observation)

                events.append(MissionEvent(step, "abort", action.reason))
                return MissionReport(MissionStatus.ABORTED, action.reason, step, tuple(events), observation)

            policy = self.policy.evaluate(action, observation)
            events.append(MissionEvent(step, "policy", policy.reason, {"allowed": policy.allowed}))
            if not policy.allowed:
                events.append(MissionEvent(step, "abort", policy.reason))
                return MissionReport(MissionStatus.ABORTED, policy.reason, step, tuple(events), observation)

            result = world.apply(action)
            events.append(MissionEvent(step, "act", result.message, {"success": result.success}))

            after = world.observe()
            verification = Verifier.verify(action, result, observation, after)
            events.append(MissionEvent(step, "verify", verification.message, {"success": verification.success}))

            if not verification.success:
                recoveries, can_retry = self._recover_or_stop(events, recoveries, step, "Re-observe and re-plan")
                if not can_retry:
                    return MissionReport(
                        MissionStatus.FAILED,
                        "Recovery budget exhausted",
                        step,
                        tuple(events),
                        after,
                    )

        final = world.observe()
        return MissionReport(MissionStatus.FAILED, "Maximum mission steps exceeded", self.max_steps, tuple(events), final)
