from __future__ import annotations

import argparse

from .brain import RufusBrain
from .flight_recorder import FlightRecorder
from .types import Position
from .world import DeterministicGridWorld


def build_scenario(name: str) -> DeterministicGridWorld:
    common = dict(
        width=5,
        height=3,
        robot_position=Position(0, 1),
        object_position=Position(2, 1),
        destination=Position(4, 1),
        battery=100,
    )
    if name == "dynamic-obstacle":
        return DeterministicGridWorld(**common, obstacle_injections={1: {Position(1, 1)}})
    if name == "partial-observation":
        return DeterministicGridWorld(**common, unknown_observations={1: {"object_position"}})
    return DeterministicGridWorld(**common)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run and replay Project Rufus Mission 001")
    parser.add_argument("--scenario", choices=("nominal", "dynamic-obstacle", "partial-observation"), default="nominal")
    parser.add_argument("--json", action="store_true", help="emit machine-readable flight-recorder JSON")
    args = parser.parse_args()

    report = RufusBrain().run(build_scenario(args.scenario))
    ok, problems = FlightRecorder.validate(report)
    print(FlightRecorder.dumps(report) if args.json else FlightRecorder.timeline(report))
    if not ok:
        raise SystemExit("Invalid mission trace: " + "; ".join(problems))


if __name__ == "__main__":
    main()
