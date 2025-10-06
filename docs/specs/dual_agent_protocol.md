# Dual-Agent Collaboration Protocol

This protocol defines how a "builder" agent and a "reviewer" agent coordinate when tackling autonomous tasks. It enables higher confidence outputs without manual intervention.

## Actors

- **Builder** – primary executor/planner responsible for proposing changes.
- **Reviewer** – independent agent (can be lighter-weight) focused on validation, critique, and escalation.

## Lifecycle

1. **Session Start**
   - Builder announces `run_id`, task goal, and context bundle.
   - Reviewer acknowledges and may request additional telemetry subscriptions.

2. **Planning Phase**
   - Builder emits plan to shared mailbox (JSON message or file).
   - Reviewer scores risk level (`low`, `medium`, `high`) and may append mitigation notes.

3. **Execution Phase**
   - Builder performs steps, attaching diffs and test results per step.
   - Reviewer tracks progress, triggers early-stop if critical regression detected.

4. **Review Phase**
   - Builder submits final diff + metrics packet.
   - Reviewer responds with decision:
     - `accept` – artifact approved, ready for merge.
     - `revise` – builder must address comments.
     - `abort` – task halted; escalate to human (with rationale).

5. **Closure**
   - Both agents log summary artifacts (telemetry, plan, decision) into gallery storage.

## Message Schema

Messages are JSON documents exchanged via disk (`dual-agent/mailbox/`) or any message bus. Minimal schema:

```jsonc
{
  "schema_version": "0.1",
  "timestamp": "2025-10-06T13:00:00Z",
  "sender": "builder",
  "run_id": "2025-10-06-refactor-config-loader",
  "message_type": "plan.proposed",
  "body": {
    "plan_path": "runs/2025-10-06-refactor/plan.json",
    "summary": "3-step refactor plan",
    "confidence": 0.58
  }
}
```

### Message Types

| Type | Sender | Description |
| --- | --- | --- |
| `session.start` | builder | Announces new collaboration session. |
| `session.ack` | reviewer | Reviewer ready to participate. |
| `plan.proposed` | builder | Plan generated; includes steps, tools, estimations. |
| `plan.feedback` | reviewer | Risk assessment, additional checks, modifications. |
| `execution.update` | builder | Periodic status updates (step complete, metrics). |
| `execution.alert` | reviewer | Critical issue detected; may request halt. |
| `review.decision` | reviewer | Final decision (`accept`, `revise`, `abort`). |
| `session.end` | builder | Records closure status, artifacts produced. |

## Storage Layout

Suggested directory for a run:

```
runs/
  2025-10-06-refactor/
    plan.json
    builder-log.jsonl
    reviewer-log.jsonl
    diffs/
      cycle-1.patch
    decisions/
      final.json
```

## Implementation Hooks

- Builder side integrated into `src/pylot-agent/agent.py` planning/execution sequence.
- Reviewer implemented via lightweight loop in `src/pylot-agent/reviewer.py` (to be created).
- Shared mailbox abstraction under `src/pylot-agent/collab/` (future module).

## Open Questions

- Authentication for distributed agents across machines.
- Conflict resolution when reviewer requests alternative plan instead of revisions.
- Metrics for reviewer effectiveness (false positive/negative rate).

Contributions are welcome—open a discussion if you intend to prototype parts of the protocol.
