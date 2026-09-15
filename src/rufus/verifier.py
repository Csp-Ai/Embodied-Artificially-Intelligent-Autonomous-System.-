from __future__ import annotations

from .types import Action, ActionKind, ActionResult, VerificationResult, WorldObservation


class Verifier:
    @staticmethod
    def verify(
        action: Action,
        result: ActionResult,
        before: WorldObservation,
        after: WorldObservation,
    ) -> VerificationResult:
        if not result.success:
            return VerificationResult(False, result.message)

        if action.kind is ActionKind.MOVE:
            ok = after.robot_position.value == action.target
            return VerificationResult(ok, "Move verified" if ok else "Robot did not reach commanded target")
        if action.kind is ActionKind.PICK_UP:
            ok = after.carrying.value is True
            return VerificationResult(ok, "Pickup verified" if ok else "Object acquisition not observed")
        if action.kind is ActionKind.DROP:
            ok = after.delivered.value is True
            return VerificationResult(ok, "Delivery verified" if ok else "Delivery state not observed")
        if action.kind is ActionKind.ABORT:
            return VerificationResult(True, "Abort acknowledged")
        return VerificationResult(False, "Unknown action type")
