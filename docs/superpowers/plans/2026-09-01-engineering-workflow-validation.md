# Engineering Workflow Validation Implementation Plan

> **For agentic workers:** Execute inline in this session. Subagent dispatch is disabled. Do not commit, push, publish, bump versions, or select a license without separate authorization.

**Goal:** Add deterministic offline evaluation, safe live Codex/Claude evaluation, CI, and auditable validation records for the Engineering Workflow Skill.

**Architecture:** JSON files define behavior and trigger contracts. Standard-library Python modules validate, grade, and run provider calls. Offline unit tests and CI protect repository contracts; live results are generated separately and summarized in documentation.

**Tech Stack:** Python 3 standard library, `unittest`, JSON, GitHub Actions, Codex CLI, Claude CLI.

**Spec:** `docs/superpowers/specs/2026-09-01-engineering-workflow-validation-design.md`

## Global Constraints

- Preserve all current working-tree changes and the untracked `docs/engineering-workflow-wechat.md` file.
- Use no third-party Python dependency.
- Keep live agents read-only and do not persist plugin configuration.
- Treat 95% behavior assertions, zero critical failures, and 90% trigger accuracy per available provider as acceptance thresholds.
- Record unavailable Gemini and Copilot runtime checks instead of inventing results.
- Do not commit or push.

### Task 1: Evaluation Contracts And Grader

**Files:**
- Create: `evals/behavior.json`
- Create: `evals/triggers.json`
- Create: `evals/response.schema.json`
- Create: `scripts/evaluate_behavior.py`
- Create: `tests/test_evaluate_behavior.py`

**Interfaces:**
- `load_behavior_cases(path: Path) -> list[dict]`
- `load_trigger_cases(path: Path) -> list[dict]`
- `grade_response(case: dict, response: dict) -> dict`
- `summarize_results(results: list[dict]) -> dict`

- [ ] Write unit tests for valid/invalid contracts, route checks, keyword alternatives, forbidden concepts, critical failures, and summary percentages.
- [ ] Run `python -m unittest tests.test_evaluate_behavior -v` and confirm failures because the module and data do not exist.
- [ ] Add eight behavior cases, twenty trigger queries, the response schema, and the minimal grader implementation.
- [ ] Rerun the focused tests and confirm they pass.

### Task 2: Safe Live Provider Runner

**Files:**
- Create: `scripts/run_live_evals.py`
- Create: `tests/test_run_live_evals.py`
- Create: `.gitignore`

**Interfaces:**
- `build_codex_command(mode: str, workspace: Path, schema: Path, output: Path) -> list[str]`
- `build_claude_command(mode: str, workspace: Path, schema: Path) -> list[str]`
- `parse_provider_output(provider: str, stdout: str, output_file: Path | None) -> dict`
- CLI options: `--provider`, `--suite`, `--mode`, `--case`, `--output-dir`, `--dry-run`, `--max-cases`.

- [ ] Write tests that prove both providers are read-only, ephemeral/non-persistent, schema constrained, and isolated between with-Skill and baseline arms.
- [ ] Run `python -m unittest tests.test_run_live_evals -v` and confirm expected failures.
- [ ] Implement temporary fixtures, provider adapters, response parsing, result metadata, and dry-run output.
- [ ] Ignore `evals/runs/` and rerun focused tests.

### Task 3: Package Validator And CI

**Files:**
- Modify: `scripts/validate_package.py`
- Create: `tests/test_validate_package.py`
- Create: `.github/workflows/validate.yml`

**Interfaces:**
- `validate(root: Path) -> list[str]` returns validation errors without exiting.
- Existing CLI behavior remains exit 0 with `Package validation passed.` or exit 1 with one or more errors.

- [ ] Write tests for missing references, manifest version drift, malformed evaluation data, and the valid repository.
- [ ] Run the validator tests and confirm they fail against the current implementation.
- [ ] Refactor the validator minimally to expose `validate`, add the new contracts, and preserve command output.
- [ ] Add Windows/Ubuntu CI steps for unit tests and package validation.
- [ ] Run all unit tests and `python scripts/validate_package.py`.

### Task 4: Validation Documentation

**Files:**
- Create: `docs/validation.md`
- Create: `docs/validation-results.md`
- Create: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `README_CN.md`

- [ ] Document methodology, thresholds, commands, cost controls, platform coverage, and limitations.
- [ ] Add an Unreleased changelog section without changing package versions.
- [ ] Link validation documents from both READMEs and distinguish static from live verification.
- [ ] Run package validation and unit tests.

### Task 5: Live Evaluation And Evidence

**Files:**
- Generate ignored raw files under `evals/runs/2026-09-01/`
- Modify: `docs/validation-results.md`

- [ ] Run one dry-run for each provider and arm; inspect commands for read-only isolation.
- [ ] Run one live smoke case for Codex and Claude with the Skill, then the matching baselines.
- [ ] If authentication and network succeed, run all behavior cases for both arms and both providers.
- [ ] Run batched trigger classification for both providers.
- [ ] Grade results, verify the 95%/zero-critical/90% thresholds, and diagnose any failing case before changing Skill behavior.
- [ ] Record provider versions, scores, failures, unavailable Gemini/Copilot checks, and residual limitations.

### Task 6: Final Verification

**Files:** All changed files.

- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `python scripts/validate_package.py`.
- [ ] Run `git diff --check`.
- [ ] Inspect `git diff --stat`, `git status --short`, generated artifacts, and raw outputs for secrets or accidental files.
- [ ] Re-score the project against the documented 95-point criteria and report any unmet item without rounding it away.

