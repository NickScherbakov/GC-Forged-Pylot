# Case Study: Zero-Downtime API Hardening (Cycle 002)

## Scenario Overview

- **Task**: "Audit the FastAPI server for insecure endpoints and add rate limiting"
- **Environment**: Homelab server (Intel i9, 64 GB RAM)
- **Model**: 13B llama.cpp (q4_K_M)
- **Confidence Target**: 0.9
- **Cycles Executed**: 4

## Cycle Timeline

| Cycle | Planner Summary | Key Actions | Confidence |
| --- | --- | --- | --- |
| 1 | Discovery + threat enumeration | Enumerated unauthenticated routes, noted missing throttling | 0.38 |
| 2 | Blueprint rate limiting strategy | Drafted middleware, integrated Redis connector mock | 0.62 |
| 3 | Implemented middleware + tests | Applied token bucket logic, created integration tests | 0.81 |
| 4 | Hardened headers + docs | Added security headers, updated threat model, all tests pass | **0.93** |

## Artifacts

- **Plan JSON**: `docs/case-studies/artifacts/002-plan.json`
- **Diff Patch**: `docs/case-studies/artifacts/002-diff.patch`
- **Metrics**: `docs/case-studies/artifacts/002-metrics.json`
- **Test Report**: `docs/case-studies/artifacts/media/002-test-report.md`
- **Replay Screencast**: `docs/case-studies/artifacts/media/002-replay.webm`

## Highlights

- Planner cross-checked telemetry events to identify bursty traffic patterns before suggesting mitigations.
- Executor generated deterministic integration tests using a seeded request generator.
- Reviewer insisted on documentation updates and a checklist for manual deploy validation.

## Lessons Learned

1. **Security posture** – Rate limiting surfaced configuration debt; telemetry should monitor both success and throttle counts.
2. **Replay fidelity** – Recording the CLI run with `--dry-run` flag makes peer review smoother.
3. **Docs-first** – For security-sensitive work, doc updates should be an explicit step in the plan.

## Replay Instructions

```bash
python run_autonomous.py "@docs/case-studies/artifacts/002-plan.json"
pytest tests/core/test_server_api.py -k "test_rate_limit"
```

> Contribute your own hardening stories—include screencasts and logs when they add clarity.
