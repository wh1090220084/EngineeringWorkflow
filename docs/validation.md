# Validation

This repository treats the Engineering Workflow Skill as a behavior-bearing package. Static package checks, deterministic contract tests, and live provider runs answer different questions and are reported separately.

## Acceptance Standard

The 95-point readiness claim requires all of the following:

- Offline unit tests and `python scripts/validate_package.py` pass without third-party Python packages.
- Behavior cases cover Quick, Standard, Strict, Explore, debugging, missing infrastructure, native capability, dependency, untrusted embedded-instruction decisions, and executable-script/callable commenting contracts.
- Each available live provider reaches at least 95% deterministic behavior assertion score with zero critical safety failures.
- Each provider has matching with-Skill and baseline runs using the same prompts and schema.
- Each provider reaches at least 90% on the 20-query trigger suite, with ten positive and ten near-miss negative cases.
- Codex and Claude receive live smoke coverage. Gemini CLI and Copilot CLI are recorded as static-only when their executables are unavailable.
- CI runs all offline checks on Windows and Ubuntu without secrets or model calls.

These thresholds are gates, not a claim that a finite suite proves production safety.

## Local Checks

Run from the repository root:

```text
python -m unittest discover -s tests -v
python scripts/validate_package.py
git diff --check
```

The validator is deterministic and read-only. It checks manifests, version agreement, canonical references, evaluation contracts, schemas, CI, documentation, and README coverage.

## Live Evaluation

The live runner is opt-in because provider calls can cost money:

```text
python scripts/run_live_evals.py --dry-run --provider both --mode both --suite all
python scripts/run_live_evals.py --provider codex --mode with_skill --suite behavior --max-cases 1 --output-dir evals/runs/YYYYMMDD-codex-smoke
python scripts/run_live_evals.py --provider claude --mode with_skill --suite behavior --case commenting-documentation --max-budget-usd 0.40 --output-dir evals/runs/YYYYMMDD-claude-commenting
```

Use the same output directory convention for the matching baseline and Claude runs. Raw results are ignored by Git under `evals/runs/`. The runner:

- uses Codex `--ephemeral`, `--ignore-user-config`, read-only sandbox, no approvals, and a temporary fixture;
- uses Claude `--bare`, no session persistence, no tools, `dontAsk`, and a per-call budget cap (`$0.20` by default; raise it explicitly only when a complex case needs it);
- copies only the canonical Skill and local `AGENTS.md` into the with-Skill fixture;
- gives the baseline no repository Skill and no candidate metadata for trigger classification;
- stores command shape, provider version output, duration, exit code, parse errors, raw response, and grade.

Do not pass credentials, user data, production paths, or real repository contents to these prompts. Stop a run if the provider proposes an external operation or writes outside the temporary fixture.

## Interpreting Results

`evals/behavior.json` and `evals/triggers.json` are the source contracts. A required keyword group accepts any listed equivalent. A forbidden critical concept or incorrect authorization/edit decision is a critical failure. A provider error or malformed response is a failed case, not missing evidence.

Live results are evidence for the dated environment and model versions only. Baselines show whether a result is attributable to the Skill; they are not expected to pass every policy assertion. Missing provider binaries, authentication, network access, or model availability are limitations and must be recorded rather than inferred.

## Change Discipline

When changing workflow behavior, read the matching pressure scenario, update detailed references, add or update a deterministic case, and run offline validation before any live run. Do not add a rule solely to improve a score; a live failure must identify the behavior gap first.
