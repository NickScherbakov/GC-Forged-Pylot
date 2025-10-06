# Telemetry Event Specification

Structured telemetry lets us replay autonomous cycles, visualize progress, and debug failures. This document outlines the event envelope emitted by planners, executors, and reviewers.

## Goals

- **Low overhead** – JSON lines that can be streamed to disk or sockets.
- **Composable** – every subsystem extends a shared envelope.
- **Privacy-aware** – payload redaction capabilities baked in.
- **Time-series friendly** – fields map cleanly to Grafana/Prometheus labels.

## Event Envelope

```jsonc
{
  "schema_version": "0.1",
  "timestamp": "2025-10-06T12:34:56.789Z",
  "source": "planner",
  "run_id": "2025-10-06T12-30-00Z/refactor-config-loader",
  "cycle": 2,
  "event": "plan.generated",
  "payload": {
    "steps": 5,
    "confidence": 0.61,
    "inputs": ["user_goal", "memory_context"],
    "redacted_fields": []
  },
  "tags": {
    "agent": "default",
    "environment": "workstation",
    "task": "refactor-config-loader"
  }
}
```

### Envelope Fields

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | string | Version of the telemetry contract. |
| `timestamp` | string | ISO 8601 timestamp in UTC. |
| `source` | string | `planner`, `executor`, `reviewer`, `memory`, `optimizer`, etc. |
| `run_id` | string | Unique identifier for the overall autonomous run. |
| `cycle` | integer | Improvement cycle number (starts at 1). |
| `event` | string | Namespaced event name (`module.action`). |
| `payload` | object | Event-specific data. |
| `tags` | object | Key/value pairs for filtering (environment, hardware, manifest, etc.). |

### Core Events

#### Planner
- `plan.generated` – includes step count, reasoning score, selected tools.
- `plan.step_started` – step index, tool, step description.
- `plan.step_completed` – duration_ms, result summary, status.

#### Executor
- `executor.command_started` – command name, arguments (redacted where necessary).
- `executor.command_completed` – exit code, stdout digest, stderr digest.
- `executor.error` – exception class, message, handled flag.

#### Reviewer
- `review.feedback_generated` – confidence_delta, comments, blocking_issues.
- `review.decision` – final verdict (`accept`, `revise`, `abort`).

#### Optimizer
- `optimizer.profile_selected` – hardware signature, profile name.
- `optimizer.benchmark_completed` – throughput tokens/s, latency ms.

### Redaction

Fields that must not be persisted should be replaced with hashes or the literal `"REDACTED"`. The `payload.redacted_fields` array lists the keys that were replaced.

### Transport

- **File:** default `logs/telemetry/<run_id>.jsonl`.
- **Socket:** optional ZeroMQ/TCP emitter (future work).
- **Metrics:** selected numeric fields can be mirrored to Prometheus via a sidecar process.

### Extensibility

Subsystems add new events by namespacing under their module and documenting the payload in-line or in dedicated spec files. Backwards-compatible additions must not break existing parsers.

### References

- Future implementation hooks will live in `src/core/planner.py`, `executor.py`, `self_improvement.py`.
- Grafana dashboards and replay tooling will consume this format.
