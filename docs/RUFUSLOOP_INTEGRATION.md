# Project Rufus + RufusLoop: simulation-first integration contract

**Status:** Experimental, opt-in, proposed for review. This does **not** merge the
two repositories, connect to a robot or certify either repository for production.

## Ownership and architecture

- **Project Rufus (this public repository)**: mission, planner, policy, embodiment
  interface, flight recorder, and simulated robot/world.
- **RufusLoop (private research repository)**: independent readback, evidence
  contracts, persistent operation identity, attempt reservation and conservative
  recovery. Its source and experiments remain private.
- **Integration adapter (in RufusLoop)**: implements Rufus's existing
  `EmbodimentAdapter` by delegating state observations to a test simulator and
  each approved action to RufusLoop's `run_durable` evidence-first runner.

The adapter is **simulation-only**. A simulator's externally queried state is
independent of the **action receipt**, not proof of independence from the
simulator itself, physical safety or authenticity of real-world sensors.

## Interface change

`ActionResult` preserves the old `success` and `message` constructor arguments.
Two opt-in flags default to False:

- `outcome_uncertain=True`: the adapter cannot establish the action effect.
  Rufus emits an inconclusive verification event, aborts, and does **not** redispatch.
- `retry_prohibited=True`: the adapter manages recovery. Even if Rufus's
  original readback verifier disagrees with the result, Rufus must abort rather
  than re-issue the action.

When RufusLoop verifies the **effect** despite a false-negative executor
receipt, it returns `success=True, retry_prohibited=True` to Rufus. A negative
executor receipt alone is never adequate proof of a failed effect.

## Contract and hazards

1. Preserve Rufus's independent safety-policy veto **before** the adapter call.
2. Let RufusLoop reserve an attempt before applying a side effect; use
   `EvidencePolicy` and `SourceContract` for all verification.
3. Distinguish an observed successful **action** from successful **mission**
   acceptance. The current brain has its own delivery-completion predicate,
   which is not yet RufusLoop's independently verified parent-goal criterion.
4. Never interpret an unknown, missing, stale or conflicting observation as
   authorization to repeat a command.
5. Keep action identity stable across a resumed mission **before** enabling
   crash-resumable operation or real hardware. The current integration demo
   uses an in-process mission ID + monotonic action sequence; this is not yet
   sufficient for restarts or concurrent mission workers.
6. Do not use real actuators, employer systems, live accounts, private keys or
   unreviewed external providers.
7. RufusLoop's preexisting GitHub Actions startup failure and exact-tree
   release gate remain unresolved. No green hosted validation is implied.

## Local demo procedure (after both PRs are reviewed)

In a test workspace with Python 3.11+, install both checkouts:

```bash
python -m pip install -e /path/to/project-rufus
python -m pip install -e "/path/to/RufusLoop[dev]"
RUFUS_BRIDGE_REQUIRED=1 python -m pytest -q /path/to/RufusLoop/tests/test_rufus_bridge.py
```

Run the original Rufus regression tests separately before merging.

## First release criteria

- Existing Rufus missions pass unmodified.
- False-negative receipts with a completed simulated physical effect are
  verified by readback, without duplicate action dispatch.
- Unknown outcomes safely stop, regardless of planner retry budgets.
- No process retry or redispatch on a repeated logical operation.
- Full clean-checkout regression suite and real CI job succeed, not just
  locally reconstructed test counts.
- Real-world integrations remain out of scope until distinct, independently
  instrumented sandbox tests and safety review.
