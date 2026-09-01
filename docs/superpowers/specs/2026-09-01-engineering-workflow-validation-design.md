# Engineering Workflow Validation Design

Status: approved on 2026-09-01

## Goal

Raise the project from a well-designed instruction package to an evidence-backed Skill whose routing, safety, verification, and complexity behavior can be tested repeatedly. The target is a 95/100 readiness standard, supported by fresh offline checks and live Codex and Claude evidence.

## Success Criteria

The project may claim the 95-point standard only when all of these hold:

1. The offline package validator and unit tests pass in a clean Python environment without third-party dependencies.
2. Structured behavior cases cover Quick, Standard, Strict, Explore, debugging, missing infrastructure, native capability, and untrusted embedded instructions.
3. Live Codex and Claude with-Skill runs achieve at least 95% of deterministic behavior assertions with zero critical safety violations.
4. Baseline runs are recorded for comparison and use the same prompts and output schema.
5. Trigger-description queries include realistic positive and near-miss negative cases, with at least 90% classification accuracy on each available live provider.
6. Codex and Claude loading paths receive live smoke coverage. Gemini CLI and Copilot CLI remain static-only when their executables are unavailable, and the report says so.
7. CI runs all offline checks and does not require secrets or external model access.
8. Documentation states exactly what was run, what passed, what was unavailable, and what remains unknown.

## Non-Goals

- Do not publish a marketplace release, bump the package version, select a license, commit, or push.
- Do not modify user-level plugin configuration.
- Do not claim that deterministic cases prove production safety.
- Do not add more workflow rules unless a failing evaluation demonstrates a specific gap.
- Do not add third-party Python packages.

## Evaluation Model

`evals/behavior.json` is the canonical behavior case set. Each case contains:

- a stable ID and category;
- the user prompt;
- expected task type and route;
- expected authorization and edit decisions;
- required concepts expressed as alternative keyword groups;
- forbidden concepts;
- a critical flag for assertions that represent safety or authorization failures.

Providers return JSON matching `evals/response.schema.json`:

- `task_type`
- `route`
- `requires_authorization`
- `would_edit`
- `next_actions`
- `prohibited_actions`
- `evidence`
- `residual_risks`

The grader normalizes response text, checks exact structured fields, checks required keyword groups, and rejects forbidden concepts. It writes per-case results plus aggregate assertion and critical-failure totals.

`evals/triggers.json` contains 20 realistic queries: 10 expected to trigger the Skill and 10 near-miss negatives. A live provider classifies the batch from Skill metadata only. This measures description quality without changing user plugin configuration; it is not represented as proof of host auto-invocation.

## Live Runner

`scripts/run_live_evals.py` supports `codex` and `claude` providers, `with_skill` and `baseline` arms, behavior and trigger suites, selected cases, dry-run inspection, and an explicit output directory.

- Codex runs ephemerally in a temporary read-only fixture. The with-Skill fixture contains the canonical Skill and a local `AGENTS.md`; the baseline fixture contains neither.
- Claude runs non-interactively with tools disabled. The with-Skill arm loads the repository with `--plugin-dir`; the baseline arm runs in a temporary directory without the plugin.
- Both providers receive the same prompt and response schema.
- Raw outputs live under ignored `evals/runs/`; only reviewed aggregate evidence is documented.
- Claude calls use a per-call dollar cap. Provider version, command shape, duration, exit status, and parse errors are recorded.

## Offline Validation

Unit tests cover case-schema validation, response grading, critical failures, summary math, provider command construction, malformed provider output, and package validation. `scripts/validate_package.py` additionally checks:

- canonical references and evaluation files exist;
- manifest versions agree;
- referenced Markdown files resolve;
- behavior and trigger data satisfy their schema contracts;
- CI and validation documentation exist.

GitHub Actions runs Python unit tests, package validation, and `git diff --check` on Windows and Ubuntu where practical. It never runs live model calls.

## Documentation And Evidence

`docs/validation.md` explains the methodology, thresholds, local commands, cost and safety controls, and limitations. `docs/validation-results.md` records dated provider versions, case counts, scores, critical failures, and unavailable platform checks. README files link to these records without claiming unrun coverage.

## Safety And Rollback

Live evaluation prompts contain synthetic repository scenarios only. Agents receive no credentials or user data, run without write tools, and use temporary directories. Generated raw runs can be deleted without affecting the package. Every repository change is ordinary text or Python and can be reverted per file; no external configuration mutation is part of the design.

