from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .brain import RufusBrain
from .flight_recorder import FlightRecorder
from .interfaces import EmbodimentAdapter
from .types import MissionStatus, Position
from .world import DeterministicGridWorld


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    world_factory: Callable[[], EmbodimentAdapter]
    expected_status: MissionStatus
    expected_min_recoveries: int = 0


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    status: MissionStatus
    reason: str
    steps: int
    recoveries: int
    policy_blocks: int
    verification_failures: int
    uncertain_observations: int
    trace_valid: bool
    expected_pass: bool


@dataclass(frozen=True)
class BenchmarkSummary:
    results: tuple[ScenarioResult, ...]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def completed(self) -> int:
        return sum(result.status is MissionStatus.COMPLETED for result in self.results)

    @property
    def safe_aborts(self) -> int:
        return sum(result.status is MissionStatus.ABORTED for result in self.results)

    @property
    def failed(self) -> int:
        return sum(result.status is MissionStatus.FAILED for result in self.results)

    @property
    def expected_passes(self) -> int:
        return sum(result.expected_pass for result in self.results)

    @property
    def total_recoveries(self) -> int:
        return sum(result.recoveries for result in self.results)

    @property
    def trace_valid_rate(self) -> float:
        if not self.results:
            return 1.0
        return sum(result.trace_valid for result in self.results) / len(self.results)

    @property
    def expected_pass_rate(self) -> float:
        if not self.results:
            return 1.0
        return self.expected_passes / len(self.results)


def evaluate_scenario(
    spec: ScenarioSpec,
    *,
    brain_factory: Callable[[], RufusBrain] = RufusBrain,
) -> ScenarioResult:
    world = spec.world_factory()
    report = brain_factory().run(world)
    trace_valid, _ = FlightRecorder.validate(report)

    recoveries = sum(event.phase == "recover" for event in report.events)
    policy_blocks = sum(
        event.phase == "policy" and event.data.get("allowed") is False
        for event in report.events
    )
    verification_failures = sum(
        event.phase == "verify" and event.data.get("success") is False
        for event in report.events
    )
    uncertain_observations = sum(
        event.phase == "observe" and bool(event.data.get("unknown"))
        for event in report.events
    )
    expected_pass = (
        report.status is spec.expected_status
        and recoveries >= spec.expected_min_recoveries
        and trace_valid
    )

    return ScenarioResult(
        name=spec.name,
        status=report.status,
        reason=report.reason,
        steps=report.steps,
        recoveries=recoveries,
        policy_blocks=policy_blocks,
        verification_failures=verification_failures,
        uncertain_observations=uncertain_observations,
        trace_valid=trace_valid,
        expected_pass=expected_pass,
    )


def run_suite(
    scenarios: Iterable[ScenarioSpec],
    *,
    brain_factory: Callable[[], RufusBrain] = RufusBrain,
) -> BenchmarkSummary:
    return BenchmarkSummary(
        tuple(
            evaluate_scenario(scenario, brain_factory=brain_factory)
            for scenario in scenarios
        )
    )


def default_suite() -> tuple[ScenarioSpec, ...]:
    def base_world(**overrides) -> DeterministicGridWorld:
        values = dict(
            width=5,
            height=3,
            robot_position=Position(0, 1),
            object_position=Position(2, 1),
            destination=Position(4, 1),
            battery=100,
        )
        values.update(overrides)
        return DeterministicGridWorld(**values)

    return (
        ScenarioSpec(
            "nominal_delivery",
            lambda: base_world(),
            MissionStatus.COMPLETED,
        ),
        ScenarioSpec(
            "static_blocked_route",
            lambda: base_world(obstacles={Position(1, 1)}),
            MissionStatus.COMPLETED,
        ),
        ScenarioSpec(
            "low_energy_policy_abort",
            lambda: base_world(battery=5),
            MissionStatus.ABORTED,
        ),
        ScenarioSpec(
            "pickup_failure_recovery",
            lambda: base_world(pickup_failures_remaining=1),
            MissionStatus.COMPLETED,
            expected_min_recoveries=1,
        ),
        ScenarioSpec(
            "impossible_route_abort",
            lambda: DeterministicGridWorld(
                width=3,
                height=3,
                robot_position=Position(0, 1),
                object_position=Position(2, 1),
                destination=Position(2, 2),
                battery=100,
                obstacles={Position(1, 0), Position(1, 1), Position(1, 2)},
            ),
            MissionStatus.ABORTED,
        ),
        ScenarioSpec(
            "dynamic_obstacle_recovery",
            lambda: base_world(obstacle_injections={1: {Position(1, 1)}}),
            MissionStatus.COMPLETED,
            expected_min_recoveries=1,
        ),
        ScenarioSpec(
            "transient_perception_recovery",
            lambda: base_world(unknown_observations={1: {"object_position"}}),
            MissionStatus.COMPLETED,
            expected_min_recoveries=1,
        ),
        ScenarioSpec(
            "persistent_perception_abort",
            lambda: base_world(
                unknown_observations={
                    1: {"object_position"},
                    2: {"object_position"},
                    3: {"object_position"},
                    4: {"object_position"},
                }
            ),
            MissionStatus.ABORTED,
            expected_min_recoveries=1,
        ),
    )


def format_scorecard(summary: BenchmarkSummary) -> str:
    lines = [
        "RUFUS MISSION OPS SCORECARD",
        (
            f"Scenarios: {summary.total} | "
            f"Expected pass: {summary.expected_passes}/{summary.total} "
            f"({summary.expected_pass_rate:.0%}) | "
            f"Completed: {summary.completed} | "
            f"Safe aborts: {summary.safe_aborts} | "
            f"Failed: {summary.failed}"
        ),
        (
            f"Recoveries: {summary.total_recoveries} | "
            f"Trace validity: {summary.trace_valid_rate:.0%}"
        ),
        "",
    ]
    for result in summary.results:
        marker = "PASS" if result.expected_pass else "FAIL"
        lines.append(
            f"[{marker}] {result.name}: {result.status.value} | "
            f"steps={result.steps} recoveries={result.recoveries} "
            f"policy_blocks={result.policy_blocks} "
            f"verify_failures={result.verification_failures} "
            f"uncertain_obs={result.uncertain_observations}"
        )
    return "\n".join(lines)


def main() -> None:
    summary = run_suite(default_suite())
    print(format_scorecard(summary))
    if summary.expected_pass_rate < 1.0 or summary.trace_valid_rate < 1.0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
