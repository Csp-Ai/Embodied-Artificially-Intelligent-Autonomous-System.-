from __future__ import annotations

from dataclasses import dataclass
import math

from .types import Position


def normalize_angle(radians: float) -> float:
    """Normalize an angle to the interval [-pi, pi)."""

    return (radians + math.pi) % (2.0 * math.pi) - math.pi


@dataclass(frozen=True)
class MetricPoint2D:
    """Point in a named metric coordinate frame."""

    x_m: float
    y_m: float
    frame_id: str = "world"

    def distance_to(self, other: "MetricPoint2D") -> float:
        if self.frame_id != other.frame_id:
            raise ValueError(
                f"Cannot compare points across frames: {self.frame_id!r} != {other.frame_id!r}"
            )
        return math.hypot(self.x_m - other.x_m, self.y_m - other.y_m)


@dataclass(frozen=True)
class Pose2D:
    """Planar robot pose in meters/radians within one named frame."""

    x_m: float
    y_m: float
    yaw_rad: float = 0.0
    frame_id: str = "world"

    def normalized(self) -> "Pose2D":
        return Pose2D(
            x_m=self.x_m,
            y_m=self.y_m,
            yaw_rad=normalize_angle(self.yaw_rad),
            frame_id=self.frame_id,
        )

    @property
    def point(self) -> MetricPoint2D:
        return MetricPoint2D(self.x_m, self.y_m, self.frame_id)


@dataclass(frozen=True)
class GridTransform:
    """Maps discrete planning cells to positions in one metric world frame.

    A grid Position remains the planner's symbolic representation. This
    transform makes the conversion to embodiment coordinates explicit instead
    of assuming that integer cells are physical coordinates.
    """

    cell_size_m: float = 1.0
    origin_x_m: float = 0.0
    origin_y_m: float = 0.0
    frame_id: str = "world"

    def __post_init__(self) -> None:
        if self.cell_size_m <= 0:
            raise ValueError("cell_size_m must be positive")
        if not self.frame_id:
            raise ValueError("frame_id must not be empty")

    def grid_to_metric(self, position: Position) -> MetricPoint2D:
        return MetricPoint2D(
            x_m=self.origin_x_m + position.x * self.cell_size_m,
            y_m=self.origin_y_m + position.y * self.cell_size_m,
            frame_id=self.frame_id,
        )

    def pose_for_grid(self, position: Position, *, yaw_rad: float = 0.0) -> Pose2D:
        point = self.grid_to_metric(position)
        return Pose2D(
            x_m=point.x_m,
            y_m=point.y_m,
            yaw_rad=normalize_angle(yaw_rad),
            frame_id=self.frame_id,
        )

    def metric_to_grid(
        self,
        point: MetricPoint2D,
        *,
        width: int,
        height: int,
        clamp: bool = False,
    ) -> Position:
        if point.frame_id != self.frame_id:
            raise ValueError(
                f"Point frame {point.frame_id!r} does not match transform frame {self.frame_id!r}"
            )
        if width <= 0 or height <= 0:
            raise ValueError("grid dimensions must be positive")

        grid_x = round((point.x_m - self.origin_x_m) / self.cell_size_m)
        grid_y = round((point.y_m - self.origin_y_m) / self.cell_size_m)

        if clamp:
            grid_x = min(max(grid_x, 0), width - 1)
            grid_y = min(max(grid_y, 0), height - 1)
        elif not (0 <= grid_x < width and 0 <= grid_y < height):
            raise ValueError(
                f"Metric point maps outside grid bounds: ({grid_x}, {grid_y})"
            )

        return Position(grid_x, grid_y)
