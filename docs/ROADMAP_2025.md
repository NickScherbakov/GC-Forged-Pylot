# GC-Forged-Pylot Roadmap 2025

## Vision

Position GC-Forged-Pylot as the go-to autonomous engineering platform for teams who demand on-prem control, adaptive tooling, and community-driven evolution.

## Guiding Principles

- **Local-first sovereignty:** Every new capability must keep data within the user’s boundary by default.
- **Explainable autonomy:** Plans, actions, and improvements stay inspectable and reproducible.
- **Composable growth:** Features ship as modules that agents and humans can remix.
- **Community acceleration:** Lower the barrier for newcomers to contribute meaningful improvements.

## Phase 1 – Foundations (Q4 2025)

| Workstream | Goals | Milestones |
| --- | --- | --- |
| Self-Improvement Gallery | Capture and replay high-value autonomous cycles |<ul><li>Define JSON schema for plans, diffs, metrics (`docs/case-studies/gallery.schema.json`)</li><li>Ship first curated case studies</li><li>Expose gallery via docs + landing page</li><li>Provide validation CLI (`python bin/validate_gallery.py`)</li></ul>|
| Tooling Marketplace | Standardize external tool manifests |<ul><li>Publish v1 spec (`docs/specs/tool_manifest.md`)</li><li>Reference implementations (Git, Docker, Terraform)</li><li>Automated validation command</li></ul>|
| Tooling Marketplace | Standardize external tool manifests |<ul><li>Publish v1 JSON/YAML spec (`docs/specs/tool_manifest.md`)</li><li>Reference implementations (Git, Docker, Terraform)</li><li>Automated validation command (`python bin/validate_tool_manifest.py`)</li></ul>|
| Telemetry & Observability | Visualize planner/executor traces |<ul><li>Emit structured telemetry events (`docs/specs/telemetry_events.md`)</li><li>Grafana-compatible dashboards</li><li>Trace replay script in docs</li></ul>|
| Dual-Agent Collaboration | Introduce reviewer/checker agent |<ul><li>Design reviewer protocol (`docs/specs/dual_agent_protocol.md`)</li><li>Pilot dual-agent demo task</li><li>Document best practices</li></ul>|
| Optimization Recipes | Simplify model deployment |<ul><li>Convert popular models to GGUF recipes</li><li>Benchmark harness with configurable profiles</li><li>Publish hardware leaderboard</li></ul>|

## Phase 2 – Expansion (Q1–Q2 2026)

- **Gallery Portal:** Lightweight web UI served by the project to browse cycles, diff improvements, and launch reruns locally.
- **Marketplace Registry:** Hosted index of community tools with automated CI checks and trust signals.
- **Live Telemetry Service:** Optional companion app for streaming traces to dashboards.
- **Collaborative Autonomy:** Support coordination between multiple on-prem agents sharing improvement memory snapshots.
- **Optimization Orchestrator:** Templates for multi-node benchmarking and automated fallback configurations.

## Phase 3 – Ecosystem (Q3 2026+)

- **Federated Knowledge Exchange:** Opt-in sharing of anonymized improvement patterns across installations.
- **Curriculum Mode:** Guided learning paths with assessments powered by the planner/memory stack.
- **Model Distillation Loop:** Export high-confidence cycles into datasets to train specialized copilots.
- **Edge Swarm Support:** Fleet management for distributed edge devices with offline/online sync.

## Cross-Cutting Initiatives

- **Documentation & Storytelling:** Every major milestone includes tutorials, architecture notes, and community showcases.
- **Security & Compliance:** Formalize threat models, audit trails, and runtime guardrails.
- **Testing Strategy:** Expand coverage to integration/acceptance tests for self-improvement and planner flows.
- **Developer Experience:** Improve CLI ergonomics, configuration defaults, and developer sandbox setups.

## Getting Involved

1. **Pick a workstream** – open an issue referencing the roadmap milestone.
2. **Share your cycles** – contribute to the gallery directory with reproducible data.
3. **Prototype tools** – submit manifests or telemetry adapters via pull requests.
4. **Host sessions** – run community demos or office hours; we’ll amplify through docs and socials.

Progress is tracked in the GitHub Projects board (to be linked). Contributions and feedback are welcome across code, docs, design, and research.
