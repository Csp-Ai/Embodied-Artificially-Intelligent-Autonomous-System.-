from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .types import Action, ActionResult, WorldObservation


@dataclass(frozen=True)
class NavigationContext:
    """Minimal planner-facing representation of traversable 2D space."""

    width: int
    height: int


@runtime_checkable
class EmbodimentAdapter(Protocol):
    """Boundary between Rufus Brain and any simulated or physical embodiment."""

    def observe(self) -> WorldObservation:
        ...

    def apply(self, action: Action) -> ActionResult:
        ...

    def navigation_context(self) -> NavigationContext:
        ...
