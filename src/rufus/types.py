from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class EpistemicStatus(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Position:
    x: int
    y: int

    def manhattan(self, other: "Position") -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)


@dataclass(frozen=True)
class Fact(Generic[T]):
    value: T | None
    status: EpistemicStatus
    source: str


@dataclass(frozen=True)
class WorldObservation:
    robot_position: Fact[Position]
    object_position: Fact[Position]
    destination: Fact[Position]
    battery: Fact[int]
    carrying: Fact[bool]
    delivered: Fact[bool]
    obstacles: Fact[frozenset[Position]]


class ActionKind(str, Enum):
    MOVE = "move"
    PICK_UP = "pick_up"
    DROP = "drop"
    ABORT = "abort"


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    target: Position | None = None
    reason: str = ""


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str


@dataclass(frozen=True)
class VerificationResult:
    success: bool
    message: str


class MissionStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


@dataclass(frozen=True)
class MissionEvent:
    step: int
    phase: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MissionReport:
    status: MissionStatus
    reason: str
    steps: int
    events: tuple[MissionEvent, ...]
    final_observation: WorldObservation
