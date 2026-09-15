from __future__ import annotations

from dataclasses import dataclass
import importlib
import math
from typing import Any

from ..interfaces import NavigationContext
from ..simulation import GroundTruthSnapshot
from ..spatial import GridTransform, MetricPoint2D, Pose2D
from ..types import (
    Action,
    ActionKind,
    ActionResult,
    EpistemicStatus,
    Fact,
    Position,
    WorldObservation,
)


class MuJoCoUnavailableError(RuntimeError):
    """Raised when the optional MuJoCo backend is requested but not installed."""


def _import_mujoco() -> Any:
    try:
        return importlib.import_module("mujoco")
    except ModuleNotFoundError as exc:
        raise MuJoCoUnavailableError(
            "MuJoCo is an optional Rufus backend. Install it with "
            "`python -m pip install -e '.[mujoco]'`."
        ) from exc


@dataclass(frozen=True)
class MuJoCoGridConfig:
    width: int
    height: int
    robot_position: Position
    object_position: Position
    destination: Position
    battery: int = 100
    obstacles: frozenset[Position] = frozenset()
    cell_size_m: float = 1.0
    origin_x_m: float = 0.0
    origin_y_m: float = 0.0
    frame_id: str = "world"
    move_cost: int = 1
    settle_steps: int = 250
    position_tolerance_m: float = 0.18
    actuator_kp: float = 80.0
    actuator_kv: float = 8.0

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("MuJoCo grid dimensions must be positive")
        if self.move_cost <= 0:
            raise ValueError("move_cost must be positive")
        if self.settle_steps <= 0:
            raise ValueError("settle_steps must be positive")
        if self.position_tolerance_m <= 0:
            raise ValueError("position_tolerance_m must be positive")
        self.grid_transform()
        for name, position in (
            ("robot_position", self.robot_position),
            ("object_position", self.object_position),
            ("destination", self.destination),
        ):
            if not self._in_bounds(position):
                raise ValueError(f"{name} is outside the configured world")
        for obstacle in self.obstacles:
            if not self._in_bounds(obstacle):
                raise ValueError("obstacle is outside the configured world")

    def _in_bounds(self, position: Position) -> bool:
        return 0 <= position.x < self.width and 0 <= position.y < self.height

    def grid_transform(self) -> GridTransform:
        return GridTransform(
            cell_size_m=self.cell_size_m,
            origin_x_m=self.origin_x_m,
            origin_y_m=self.origin_y_m,
            frame_id=self.frame_id,
        )


class MuJoCoGridEmbodiment:
    """Mission 001 embodiment backed by MuJoCo physics.

    Navigation is physically stepped through MuJoCo position servos. The v0
    package "grasp" is deliberately kinematic: once acquired, package position
    is synchronized to the robot. Physical manipulation is a later milestone.
    """

    def __init__(self, config: MuJoCoGridConfig):
        self.config = config
        self.width = config.width
        self.height = config.height
        self.battery = config.battery
        self.obstacles = set(config.obstacles)
        self.carrying = False
        self.delivered = False
        self.transform = config.grid_transform()

        self._mj = _import_mujoco()
        self.model = self._mj.MjModel.from_xml_string(self.model_xml(config))
        self.data = self._mj.MjData(self.model)

        robot = self.transform.grid_to_metric(config.robot_position)
        package = self.transform.grid_to_metric(config.object_position)
        self.data.qpos[0] = robot.x_m
        self.data.qpos[1] = robot.y_m
        self.data.qpos[2] = package.x_m
        self.data.qpos[3] = package.y_m
        self.data.ctrl[0] = robot.x_m
        self.data.ctrl[1] = robot.y_m
        self._mj.mj_forward(self.model, self.data)

    def navigation_context(self) -> NavigationContext:
        return NavigationContext(width=self.width, height=self.height)

    def _robot_xy(self) -> tuple[float, float]:
        return float(self.data.qpos[0]), float(self.data.qpos[1])

    def _package_xy(self) -> tuple[float, float]:
        return float(self.data.qpos[2]), float(self.data.qpos[3])

    def _metric_to_grid(self, x_m: float, y_m: float) -> Position:
        return self.transform.metric_to_grid(
            MetricPoint2D(x_m=x_m, y_m=y_m, frame_id=self.transform.frame_id),
            width=self.width,
            height=self.height,
        )

    def metric_pose(self) -> Pose2D:
        """Operator/evaluation pose measured from MuJoCo joint state."""

        x_m, y_m = self._robot_xy()
        return Pose2D(
            x_m=x_m,
            y_m=y_m,
            yaw_rad=0.0,
            frame_id=self.transform.frame_id,
        )

    def _sync_carried_package(self) -> None:
        if not self.carrying:
            return
        self.data.qpos[2] = self.data.qpos[0]
        self.data.qpos[3] = self.data.qpos[1]
        self.data.qvel[2] = self.data.qvel[0]
        self.data.qvel[3] = self.data.qvel[1]

    def observe(self) -> WorldObservation:
        robot = self._metric_to_grid(*self._robot_xy())
        package = self._metric_to_grid(*self._package_xy())
        return WorldObservation(
            robot_position=Fact(robot, EpistemicStatus.OBSERVED, "mujoco.robot_joint_state"),
            object_position=Fact(package, EpistemicStatus.OBSERVED, "mujoco.package_joint_state"),
            destination=Fact(self.config.destination, EpistemicStatus.OBSERVED, "mission.destination"),
            battery=Fact(self.battery, EpistemicStatus.OBSERVED, "embodiment.energy_model"),
            carrying=Fact(self.carrying, EpistemicStatus.OBSERVED, "embodiment.grasp_state"),
            delivered=Fact(self.delivered, EpistemicStatus.OBSERVED, "mission.delivery_state"),
            obstacles=Fact(frozenset(self.obstacles), EpistemicStatus.OBSERVED, "mujoco.obstacle_map"),
        )

    def apply(self, action: Action) -> ActionResult:
        if action.kind is ActionKind.ABORT:
            return ActionResult(True, action.reason or "Mission aborted")
        if action.kind is ActionKind.MOVE:
            return self._move(action)
        if action.kind is ActionKind.PICK_UP:
            robot = self._metric_to_grid(*self._robot_xy())
            package = self._metric_to_grid(*self._package_xy())
            if self.carrying:
                return ActionResult(False, "Already carrying object")
            if robot != package:
                return ActionResult(False, "Object is not at robot position")
            self.carrying = True
            self._sync_carried_package()
            self._mj.mj_forward(self.model, self.data)
            return ActionResult(True, "Package attached (kinematic grasp v0)")
        if action.kind is ActionKind.DROP:
            robot = self._metric_to_grid(*self._robot_xy())
            if not self.carrying:
                return ActionResult(False, "No object is being carried")
            if robot != self.config.destination:
                return ActionResult(False, "Robot is not at destination")
            target = self.transform.grid_to_metric(self.config.destination)
            self.data.qpos[2] = target.x_m
            self.data.qpos[3] = target.y_m
            self.data.qvel[2] = 0.0
            self.data.qvel[3] = 0.0
            self.carrying = False
            self.delivered = True
            self._mj.mj_forward(self.model, self.data)
            return ActionResult(True, "Package released at destination")
        return ActionResult(False, f"Unsupported action: {action.kind}")

    def _move(self, action: Action) -> ActionResult:
        if action.target is None:
            return ActionResult(False, "Move action missing target")
        current = self._metric_to_grid(*self._robot_xy())
        if current.manhattan(action.target) != 1:
            return ActionResult(False, "Move target is not adjacent")
        if not (0 <= action.target.x < self.width and 0 <= action.target.y < self.height):
            return ActionResult(False, "Move target is out of bounds")
        if action.target in self.obstacles:
            return ActionResult(False, "Move target is blocked")
        if self.battery < self.config.move_cost:
            return ActionResult(False, "Insufficient energy to move")

        target = self.transform.grid_to_metric(action.target)
        self.data.ctrl[0] = target.x_m
        self.data.ctrl[1] = target.y_m
        self.battery -= self.config.move_cost
        for _ in range(self.config.settle_steps):
            self._sync_carried_package()
            self._mj.mj_step(self.model, self.data)
        self._sync_carried_package()
        self._mj.mj_forward(self.model, self.data)

        pose = self.metric_pose()
        error = pose.point.distance_to(target)
        if error > self.config.position_tolerance_m:
            return ActionResult(False, f"Physics move did not settle at target (error={error:.3f} m)")
        return ActionResult(True, f"Physics move reached {action.target}")

    def ground_truth(self) -> GroundTruthSnapshot:
        """Operator/test-only state; Rufus Brain must not consume this method."""

        return GroundTruthSnapshot(
            robot_position=self._metric_to_grid(*self._robot_xy()),
            object_position=self._metric_to_grid(*self._package_xy()),
            destination=self.config.destination,
            battery=self.battery,
            obstacles=frozenset(self.obstacles),
            carrying=self.carrying,
            delivered=self.delivered,
        )

    @staticmethod
    def model_xml(config: MuJoCoGridConfig) -> str:
        transform = config.grid_transform()
        lower = transform.grid_to_metric(Position(0, 0))
        upper = transform.grid_to_metric(Position(config.width - 1, config.height - 1))
        span_x = max(abs(upper.x_m - lower.x_m), config.cell_size_m)
        span_y = max(abs(upper.y_m - lower.y_m), config.cell_size_m)
        center_x = (lower.x_m + upper.x_m) / 2.0
        center_y = (lower.y_m + upper.y_m) / 2.0

        obstacle_xml = "\n".join(
            (
                f'<geom name="obstacle_{index}" type="box" '
                f'pos="{point.x_m} {point.y_m} 0.2" '
                'size="0.30 0.30 0.20" rgba="0.35 0.35 0.35 1"/>'
            )
            for index, position in enumerate(sorted(config.obstacles, key=lambda p: (p.x, p.y)))
            for point in (transform.grid_to_metric(position),)
        )
        destination = transform.grid_to_metric(config.destination)
        return f"""<mujoco model="rufus_mission_001">
  <compiler angle="radian"/>
  <option timestep="0.01" integrator="implicitfast"/>
  <default>
    <joint damping="4"/>
    <geom friction="1 0.1 0.1"/>
  </default>
  <worldbody>
    <geom name="floor" type="plane"
          pos="{center_x} {center_y} 0"
          size="{span_x + config.cell_size_m} {span_y + config.cell_size_m} 0.1"
          rgba="0.9 0.9 0.9 1"/>
    <site name="destination" type="cylinder"
          pos="{destination.x_m} {destination.y_m} 0.01"
          size="0.28 0.01" rgba="0.1 0.7 0.2 0.45"/>
    {obstacle_xml}
    <body name="robot" pos="0 0 0.13">
      <joint name="robot_x" type="slide" axis="1 0 0"/>
      <joint name="robot_y" type="slide" axis="0 1 0"/>
      <geom name="robot_geom" type="cylinder" size="0.22 0.12"
            mass="5" rgba="0.15 0.35 0.8 1"/>
    </body>
    <body name="package" pos="0 0 0.11">
      <joint name="package_x" type="slide" axis="1 0 0"/>
      <joint name="package_y" type="slide" axis="0 1 0"/>
      <geom name="package_geom" type="box" size="0.15 0.15 0.10"
            mass="1" contype="0" conaffinity="0" rgba="0.8 0.45 0.1 1"/>
    </body>
  </worldbody>
  <actuator>
    <position name="robot_x_servo" joint="robot_x" kp="{config.actuator_kp}" kv="{config.actuator_kv}"/>
    <position name="robot_y_servo" joint="robot_y" kp="{config.actuator_kp}" kv="{config.actuator_kv}"/>
  </actuator>
</mujoco>"""
