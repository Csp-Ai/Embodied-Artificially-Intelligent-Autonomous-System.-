from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from typing import Any

from .types import MissionReport


def _primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _primitive(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_primitive(item) for item in value]
    return value


class FlightRecorder:
    """Turns a mission report into an inspectable, replayable decision trace."""

    @staticmethod
    def export(report: MissionReport) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": report.status.value,
            "reason": report.reason,
            "steps": report.steps,
            "events": [_primitive(event) for event in report.events],
            "final_observation": _primitive(report.final_observation),
        }

    @classmethod
    def dumps(cls, report: MissionReport, *, indent: int = 2) -> str:
        return json.dumps(cls.export(report), indent=indent, sort_keys=True)

    @staticmethod
    def timeline(report: MissionReport) -> str:
        lines = [f"RUFUS MISSION — {report.status.value.upper()}: {report.reason}"]
        for event in report.events:
            details = ""
            if event.data:
                details = " | " + ", ".join(f"{k}={_primitive(v)}" for k, v in event.data.items())
            lines.append(f"[{event.step:03d}] {event.phase.upper():7} {event.message}{details}")
        return "\n".join(lines)

    @staticmethod
    def validate(report: MissionReport) -> tuple[bool, tuple[str, ...]]:
        problems: list[str] = []
        if not report.events:
            problems.append("mission trace has no events")
            return False, tuple(problems)
        if report.events[0].phase != "observe":
            problems.append("trace must begin with observation")
        for event in report.events:
            if event.step < 0:
                problems.append("event step cannot be negative")
        if report.status.value == "completed":
            if report.final_observation.delivered.value is not True:
                problems.append("completed mission lacks verified delivery")
            if not any(e.phase == "verify" and e.data.get("success") for e in report.events):
                problems.append("completed mission lacks successful verification")
        if report.status.value == "aborted" and not any(e.phase == "abort" for e in report.events):
            problems.append("aborted mission lacks abort event")
        return not problems, tuple(problems)
