from __future__ import annotations

from collections import deque

from .interfaces import NavigationContext
from .types import Action, ActionKind, Position, WorldObservation


class MissionPlanner:
    """Deterministic planner for Mission 001."""

    @staticmethod
    def _neighbors(position: Position, context: NavigationContext) -> tuple[Position, ...]:
        candidates = (
            Position(position.x + 1, position.y),
            Position(position.x - 1, position.y),
            Position(position.x, position.y + 1),
            Position(position.x, position.y - 1),
        )
        return tuple(p for p in candidates if 0 <= p.x < context.width and 0 <= p.y < context.height)

    @classmethod
    def shortest_path(
        cls,
        start: Position,
        goal: Position,
        obstacles: frozenset[Position],
        context: NavigationContext,
    ) -> list[Position] | None:
        if start == goal:
            return [start]
        queue = deque([start])
        previous: dict[Position, Position | None] = {start: None}
        while queue:
            current = queue.popleft()
            for nxt in cls._neighbors(current, context):
                if nxt in obstacles or nxt in previous:
                    continue
                previous[nxt] = current
                if nxt == goal:
                    path = [goal]
                    while path[-1] != start:
                        parent = previous[path[-1]]
                        if parent is None:
                            break
                        path.append(parent)
                    path.reverse()
                    return path
                queue.append(nxt)
        return None

    def next_action(self, observation: WorldObservation, context: NavigationContext) -> Action:
        required = (
            observation.robot_position.value,
            observation.object_position.value,
            observation.destination.value,
            observation.carrying.value,
            observation.obstacles.value,
        )
        if any(value is None for value in required):
            return Action(ActionKind.ABORT, reason="Required world state is unknown")

        robot = observation.robot_position.value
        object_position = observation.object_position.value
        destination = observation.destination.value
        carrying = bool(observation.carrying.value)
        obstacles = observation.obstacles.value

        assert robot is not None and object_position is not None and destination is not None
        assert obstacles is not None

        if carrying and robot == destination:
            return Action(ActionKind.DROP, reason="Object and robot are at destination")
        if not carrying and robot == object_position:
            return Action(ActionKind.PICK_UP, reason="Object is within acquisition position")

        goal = destination if carrying else object_position
        path = self.shortest_path(robot, goal, obstacles, context)
        if path is None or len(path) < 2:
            return Action(ActionKind.ABORT, reason="No safe route to current mission goal")
        return Action(ActionKind.MOVE, target=path[1], reason=f"Advance toward {goal}")
