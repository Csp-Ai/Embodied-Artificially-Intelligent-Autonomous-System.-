from __future__ import annotations

from dataclasses import dataclass

from .types import Position
from .world import DeterministicGridWorld


@dataclass(frozen=True)
class GroundTruthSnapshot:
    robot_position: Position
    object_position: Position
    destination: Position
    battery: int
    obstacles: frozenset[Position]
    carrying: bool
    delivered: bool


def snapshot(world: DeterministicGridWorld) -> GroundTruthSnapshot:
    """Simulation-only ground truth. The brain must never consume this directly."""

    return GroundTruthSnapshot(
        robot_position=world.robot_position,
        object_position=world.object_position,
        destination=world.destination,
        battery=world.battery,
        obstacles=frozenset(world.obstacles),
        carrying=world.carrying,
        delivered=world.delivered,
    )


def render_ascii(world: DeterministicGridWorld) -> str:
    """Render simulation truth for a human operator without feeding it to Rufus Brain."""

    truth = snapshot(world)
    rows: list[str] = []
    for y in range(world.height):
        row: list[str] = []
        for x in range(world.width):
            p = Position(x, y)
            symbol = "."
            if p in truth.obstacles:
                symbol = "#"
            if p == truth.destination:
                symbol = "D"
            if not truth.carrying and p == truth.object_position:
                symbol = "O"
            if p == truth.robot_position:
                symbol = "R" if not truth.carrying else "B"
            row.append(symbol)
        rows.append(" ".join(row))
    return "\n".join(rows)
