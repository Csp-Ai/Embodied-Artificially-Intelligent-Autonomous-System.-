from __future__ import annotations

from dataclasses import dataclass, field, replace

from .types import (
    Action,
    ActionKind,
    ActionResult,
    EpistemicStatus,
    Fact,
    Position,
    WorldObservation,
)


@dataclass
class DeterministicGridWorld:
    width: int
    height: int
    robot_position: Position
    object_position: Position
    destination: Position
    battery: int = 100
    obstacles: set[Position] = field(default_factory=set)
    carrying: bool = False
    delivered: bool = False
    pickup_failures_remaining: int = 0
    move_cost: int = 1
    obstacle_injections: dict[int, set[Position]] = field(default_factory=dict)
    unknown_observations: dict[int, set[str]] = field(default_factory=dict)
    _action_count: int = 0
    _observation_count: int = 0

    def _in_bounds(self, p: Position) -> bool:
        return 0 <= p.x < self.width and 0 <= p.y < self.height

    @staticmethod
    def _unknown(source: str):
        return Fact(None, EpistemicStatus.UNKNOWN, source)

    def observe(self) -> WorldObservation:
        self._observation_count += 1
        object_position = self.robot_position if self.carrying else self.object_position
        observation = WorldObservation(
            robot_position=Fact(self.robot_position, EpistemicStatus.OBSERVED, "world.robot_pose"),
            object_position=Fact(object_position, EpistemicStatus.OBSERVED, "world.object_pose"),
            destination=Fact(self.destination, EpistemicStatus.OBSERVED, "mission.destination"),
            battery=Fact(self.battery, EpistemicStatus.OBSERVED, "world.energy"),
            carrying=Fact(self.carrying, EpistemicStatus.OBSERVED, "world.gripper"),
            delivered=Fact(self.delivered, EpistemicStatus.OBSERVED, "world.delivery_state"),
            obstacles=Fact(frozenset(self.obstacles), EpistemicStatus.OBSERVED, "world.obstacle_map"),
        )
        hidden = self.unknown_observations.get(self._observation_count, set())
        valid = set(WorldObservation.__dataclass_fields__)
        unknown_kwargs = {
            name: self._unknown(getattr(observation, name).source)
            for name in hidden
            if name in valid
        }
        return replace(observation, **unknown_kwargs) if unknown_kwargs else observation

    def apply(self, action: Action) -> ActionResult:
        self._action_count += 1
        injected = self.obstacle_injections.get(self._action_count)
        if injected:
            self.obstacles.update(injected)

        if action.kind is ActionKind.ABORT:
            return ActionResult(True, action.reason or "Mission aborted")

        if action.kind is ActionKind.MOVE:
            if action.target is None:
                return ActionResult(False, "Move action missing target")
            if self.robot_position.manhattan(action.target) != 1:
                return ActionResult(False, "Move target is not adjacent")
            if not self._in_bounds(action.target):
                return ActionResult(False, "Move target is out of bounds")
            if action.target in self.obstacles:
                return ActionResult(False, "Move target is blocked")
            if self.battery < self.move_cost:
                return ActionResult(False, "Insufficient energy to move")
            self.robot_position = action.target
            self.battery -= self.move_cost
            if self.carrying:
                self.object_position = self.robot_position
            return ActionResult(True, f"Moved to {action.target}")

        if action.kind is ActionKind.PICK_UP:
            if self.carrying:
                return ActionResult(False, "Already carrying object")
            if self.robot_position != self.object_position:
                return ActionResult(False, "Object is not at robot position")
            if self.pickup_failures_remaining > 0:
                self.pickup_failures_remaining -= 1
                return ActionResult(False, "Injected pickup failure")
            self.carrying = True
            return ActionResult(True, "Object acquired")

        if action.kind is ActionKind.DROP:
            if not self.carrying:
                return ActionResult(False, "No object is being carried")
            if self.robot_position != self.destination:
                return ActionResult(False, "Robot is not at destination")
            self.carrying = False
            self.object_position = self.destination
            self.delivered = True
            return ActionResult(True, "Object delivered")

        return ActionResult(False, f"Unsupported action: {action.kind}")
