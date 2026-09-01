#!/usr/bin/env python3
"""
Run safe, schema-constrained Codex and Claude evaluation arms.

The runner loads deterministic behavior/trigger contracts, creates isolated
temporary fixtures, invokes a selected provider in read-only/no-tool mode,
parses the provider's structured response, grades it, and stores per-case JSON
plus summaries under the requested output directory. Inputs are provider,
suite, mode, case-selection, timeout, and output-directory CLI options; the
live path can incur provider charges and has no repository mutation authority.
Codex uses an ephemeral read-only command, while Claude uses a bare,
non-persistent command with tools disabled. Providers and credentials must be
available before a live run. The Claude cap defaults to ``0.20`` USD and can be
raised explicitly for a complex case with ``--max-budget-usd``. Example:
``python scripts/run_live_evals.py --provider claude --mode with_skill
--suite behavior --max-cases 1 --max-budget-usd 0.40``.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

try:
    from scripts.evaluate_behavior import (
        ContractError,
        grade_response,
        grade_trigger_response,
        load_behavior_cases,
        load_trigger_cases,
        summarize_results,
    )
except ModuleNotFoundError:  # Direct ``python scripts/run_live_evals.py`` invocation.
    from evaluate_behavior import (
        ContractError,
        grade_response,
        grade_trigger_response,
        load_behavior_cases,
        load_trigger_cases,
        summarize_results,
    )


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "engineeringworkflow"
BEHAVIOR_DATA = ROOT / "evals" / "behavior.json"
TRIGGER_DATA = ROOT / "evals" / "triggers.json"
RESPONSE_SCHEMA = ROOT / "evals" / "response.schema.json"
TRIGGER_SCHEMA = ROOT / "evals" / "trigger-response.schema.json"


def _provider_executable(provider: str) -> str:
    """Resolve a provider executable, preserving Windows ``.cmd`` shims when present."""
    return shutil.which(provider) or provider


def schema_for_suite(suite: str) -> Path:
    """Return the repository schema for a concrete behavior or trigger suite."""
    if suite == "behavior":
        return RESPONSE_SCHEMA
    if suite == "triggers":
        return TRIGGER_SCHEMA
    raise ValueError(f"suite requires a concrete schema: {suite}")


def _schema_text(schema: Path) -> str:
    """Serialize a provider schema inline, omitting Claude-incompatible ``$schema`` metadata."""
    value = json.loads(schema.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value.pop("$schema", None)
    return json.dumps(value, separators=(",", ":"))


def build_codex_command(mode: str, workspace: Path, schema: Path, output: Path) -> list[str]:
    """Build a Codex command that cannot write files or use user config."""
    command = [
        _provider_executable("codex"),
        "--ask-for-approval",
        "never",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--output-schema",
        str(schema.resolve()),
        "--output-last-message",
        str(output.resolve()),
        "-C",
        str(workspace.resolve()),
    ]
    if mode not in {"with_skill", "baseline"}:
        raise ValueError(f"unknown mode: {mode}")
    return command


def build_claude_command(mode: str, workspace: Path, schema: Path, max_budget_usd: float = 0.20) -> list[str]:
    """Build a Claude command with no tools, no persistence, and an explicit per-call budget cap."""
    if max_budget_usd <= 0:
        raise ValueError("max_budget_usd must be positive")
    command = [
        _provider_executable("claude"),
        "--print",
        "--bare",
        "--no-session-persistence",
        "--tools",
        "",
        "--permission-mode",
        "dontAsk",
        "--max-budget-usd",
        f"{max_budget_usd:.2f}",
        "--output-format",
        "json",
        "--json-schema",
        _schema_text(schema),
        "--setting-sources",
        "project,local",
        f"--add-dir={workspace.resolve()}",
    ]
    if mode == "with_skill":
        command.append(f"--plugin-dir={workspace.resolve()}")
    elif mode != "baseline":
        raise ValueError(f"unknown mode: {mode}")
    return command


def prepare_workspace(mode: str, workspace: Path) -> None:
    """Create an empty fixture, copying only the canonical Skill for the with-Skill arm."""
    workspace.mkdir(parents=True, exist_ok=True)
    if mode == "with_skill":
        (workspace / "skills").mkdir()
        shutil.copytree(SKILL_DIR, workspace / "skills" / "engineeringworkflow")
        shutil.copy2(ROOT / "AGENTS.md", workspace / "AGENTS.md")
        (workspace / ".claude-plugin").mkdir()
        shutil.copy2(ROOT / ".claude-plugin" / "plugin.json", workspace / ".claude-plugin" / "plugin.json")
    elif mode != "baseline":
        raise ValueError(f"unknown mode: {mode}")


def _parse_json_value(value: str) -> dict[str, Any]:
    """Normalize provider wrappers and return the structured response object."""
    parsed = json.loads(value)
    if isinstance(parsed, dict) and parsed.get("is_error") is True:
        raise ValueError(f"provider returned an error: {parsed.get('subtype', 'unknown')}")
    if isinstance(parsed, dict) and isinstance(parsed.get("structured_output"), dict):
        return parsed["structured_output"]
    if isinstance(parsed, dict) and isinstance(parsed.get("response"), dict):
        return parsed["response"]
    if isinstance(parsed, dict) and isinstance(parsed.get("result"), str):
        nested = json.loads(parsed["result"])
        if isinstance(nested, dict):
            return nested
    if isinstance(parsed, dict):
        return parsed
    raise ValueError("provider JSON response is not an object")


def parse_provider_output(provider: str, stdout: str, output_file: Path | None) -> dict[str, Any]:
    """Parse a structured provider response, preferring Codex's last-message file."""
    if provider == "codex" and output_file is not None and output_file.is_file():
        return _parse_json_value(output_file.read_text(encoding="utf-8"))
    if provider == "claude":
        if not stdout:
            raise ValueError(f"could not parse {provider} structured response: empty stdout")
        return _parse_json_value(stdout.strip())
    if not stdout:
        raise ValueError(f"could not parse {provider} structured response: empty stdout")
    for line in reversed([line for line in stdout.splitlines() if line.strip()]):
        try:
            return _parse_json_value(line)
        except (json.JSONDecodeError, ValueError):
            continue
    raise ValueError(f"could not parse {provider} structured response")


def _provider_version(provider: str) -> str:
    """Query a provider's version without making a live evaluation call."""
    try:
        completed = subprocess.run(
            [_provider_executable(provider), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"unavailable: {exc}"
    output = completed.stdout.strip() or completed.stderr.strip()
    if completed.returncode:
        return f"unavailable (exit {completed.returncode}): {output}"
    return output or "unknown"


def _behavior_prompt(case: dict[str, Any], mode: str, workspace: Path, provider: str) -> str:
    """Build a no-tool evaluation prompt with only the Skill context for the with-Skill arm."""
    skill_context = ""
    if mode == "with_skill" and provider in {"codex", "claude"}:
        skill = workspace / "skills" / "engineeringworkflow" / "SKILL.md"
        skill_instruction = f"Use the canonical Engineering Workflow Skill from {skill}."
        skill_context = "\n\nCANONICAL SKILL CONTENT:\n" + skill.read_text(encoding="utf-8")
        reference_names: set[str] = set()
        route = case.get("expect", {}).get("route")
        category = case.get("category")
        if route in {"Standard", "Strict", "Explore"}:
            reference_names.add("workflow-levels.md")
        if route == "Strict" or category in {"authorization", "dependencies", "trust"}:
            reference_names.add("safety-and-trust.md")
        if category in {"debugging", "evidence", "missing-infrastructure"}:
            reference_names.add("evidence-and-debugging.md")
        if category == "code-quality":
            reference_names.add("commenting.md")
        for name in sorted(reference_names):
            reference = skill.parent / "references" / name
            skill_context += f"\n\nREFERENCE {reference.name}:\n{reference.read_text(encoding='utf-8')}"
        classification_instruction = "Classify this repository task using the canonical Skill content below."
    elif mode == "baseline" and provider in {"codex", "claude"}:
        skill_instruction = "Do not use Engineering Workflow or any other repository-specific Skill."
        classification_instruction = "Classify this repository task without repository-specific workflow guidance."
    else:
        raise ValueError(f"unknown provider or mode: {provider}/{mode}")
    return (
        f"BEGIN TASK\n{case['prompt']}\nEND TASK\n\n"
        f"{skill_instruction} {classification_instruction} "
        "Return only a JSON object matching the supplied response schema. "
        "The field would_edit means whether the agent should edit now under the current authorization and safety gates; "
        "set it false when approval or a material decision is still required. "
        "The field requires_authorization means whether the hypothetical task needs approval before execution. "
        "Do not execute the task, call tools, or edit files during this evaluation. "
        "Choose the route, state whether authorization is required and whether the agent should edit now, "
        "then list next actions, prohibited actions, proving evidence, and residual risks."
        f"{skill_context}"
    )


def _skill_metadata(workspace: Path) -> str:
    """Extract only the canonical Skill's discovery metadata for trigger evaluation."""
    skill = workspace / "skills" / "engineeringworkflow" / "SKILL.md"
    lines = skill.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Skill frontmatter is missing")
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if separator and key.strip() in {"name", "description"}:
            values[key.strip()] = value.strip()
    if set(values) != {"name", "description"}:
        raise ValueError("Skill frontmatter must define name and description")
    return f"name: {values['name']}\ndescription: {values['description']}"


def _trigger_prompt(cases: list[dict[str, Any]], mode: str, workspace: Path) -> str:
    """Build the batched trigger-classification prompt for one evaluation arm."""
    payload = [{"id": case["id"], "query": case["query"]} for case in cases]
    if mode == "with_skill":
        metadata = f"Candidate Skill metadata:\n{_skill_metadata(workspace)}"
    elif mode == "baseline":
        metadata = "No candidate Skill metadata is available in this control arm."
    else:
        raise ValueError(f"unknown mode: {mode}")
    return (
        "Classify whether each user query should cause a dedicated software-repository engineering workflow Skill to load. "
        "Return only JSON matching this shape: {\"results\":[{\"id\":string,\"should_trigger\":boolean}]}. "
        "Use the candidate metadata when it is present; judge the control arm from the stated Skill category alone. "
        f"{metadata}\n"
        f"Queries: {json.dumps(payload, ensure_ascii=True)}"
    )


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    """Terminate a timed-out provider and its descendants so no evaluation process leaks."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    else:
        process.kill()


def _run_process(command: list[str], prompt: str, workspace: Path, timeout: int) -> dict[str, Any]:
    """Run one provider process, capture output, and terminate its process tree on timeout."""
    started = datetime.now(timezone.utc)
    try:
        process = subprocess.Popen(
            command,
            cwd=workspace,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            start_new_session=True,
        )
        stdout, stderr = process.communicate(prompt, timeout=timeout)
        return {
            "started_at": started.isoformat(),
            "duration_seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 3),
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }
    except subprocess.TimeoutExpired as exc:
        _terminate_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        return {
            "started_at": started.isoformat(),
            "duration_seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 3),
            "returncode": process.returncode,
            "stdout": stdout or "",
            "stderr": (stderr or "") + f"\n{exc}",
            "error": type(exc).__name__,
        }
    except OSError as exc:
        return {
            "started_at": started.isoformat(),
            "duration_seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 3),
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "error": type(exc).__name__,
        }


def _write_json(path: Path, value: Any) -> None:
    """Persist one evaluation record as UTF-8 indented JSON, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def run_behavior(
    provider: str,
    mode: str,
    cases: list[dict[str, Any]],
    output_dir: Path,
    timeout: int,
    max_budget_usd: float = 0.20,
) -> dict[str, Any]:
    """Execute and persist every selected behavior case for one provider/mode arm."""
    results: list[dict[str, Any]] = []
    provider_version = _provider_version(provider)
    for case in cases:
        run_dir = output_dir / "behavior" / provider / mode / case["id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"engineering-workflow-{provider}-", dir=output_dir) as temp:
            workspace = Path(temp)
            prepare_workspace(mode, workspace)
            last_message = run_dir / "codex-last-message.json"
            command = build_codex_command(mode, workspace, RESPONSE_SCHEMA, last_message) if provider == "codex" else build_claude_command(mode, workspace, RESPONSE_SCHEMA, max_budget_usd)
            execution = _run_process(command, _behavior_prompt(case, mode, workspace, provider), workspace, timeout)
            record: dict[str, Any] = {"provider": provider, "provider_version": provider_version, "mode": mode, "case_id": case["id"], "command": command, "execution": execution}
            try:
                response = parse_provider_output(provider, execution["stdout"], last_message if provider == "codex" else None)
                record["response"] = response
                record["grade"] = grade_response(case, response)
            except (ValueError, json.JSONDecodeError, ContractError) as exc:
                record["parse_error"] = str(exc)
                record["grade"] = {"passed": False, "assertion_count": 0, "passed_count": 0, "critical_failures": ["provider-output"]}
            _write_json(run_dir / "result.json", record)
            results.append(record["grade"])
    summary = summarize_results(results)
    summary.update({"provider": provider, "provider_version": provider_version, "mode": mode, "suite": "behavior"})
    _write_json(output_dir / "behavior" / provider / mode / "summary.json", summary)
    return summary


def run_triggers(
    provider: str,
    mode: str,
    cases: list[dict[str, Any]],
    output_dir: Path,
    timeout: int,
    max_budget_usd: float = 0.20,
) -> dict[str, Any]:
    """Execute and persist the batched trigger suite for one provider/mode arm."""
    run_dir = output_dir / "triggers" / provider / mode
    run_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"engineering-workflow-trigger-{provider}-", dir=output_dir) as temp:
        workspace = Path(temp)
        prepare_workspace(mode, workspace)
        last_message = run_dir / "codex-last-message.json"
        schema = schema_for_suite("triggers")
        command = build_codex_command(mode, workspace, schema, last_message) if provider == "codex" else build_claude_command(mode, workspace, schema, max_budget_usd)
        execution = _run_process(command, _trigger_prompt(cases, mode, workspace), workspace, timeout)
        provider_version = _provider_version(provider)
        record: dict[str, Any] = {"provider": provider, "provider_version": provider_version, "mode": mode, "command": command, "execution": execution}
        try:
            response = parse_provider_output(provider, execution["stdout"], last_message if provider == "codex" else None)
            record["response"] = response
            record["grade"] = grade_trigger_response(cases, response)
        except (ValueError, json.JSONDecodeError, ContractError) as exc:
            record["parse_error"] = str(exc)
            record["grade"] = {"case_count": len(cases), "correct_count": 0, "accuracy": 0.0, "mismatches": [case["id"] for case in cases]}
        _write_json(run_dir / "result.json", record)
    summary = record["grade"]
    summary.update({"provider": provider, "provider_version": provider_version, "mode": mode, "suite": "triggers"})
    _write_json(run_dir / "summary.json", summary)
    return summary


def _selected(values: list[str], all_value: str) -> list[str]:
    """Expand the CLI's ``both`` sentinel into the supported provider list."""
    return ["codex", "claude"] if all_value in values else values


def main(argv: list[str] | None = None) -> int:
    """Parse CLI options, run the requested arms, and return a process exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["codex", "claude", "both"], default="both")
    parser.add_argument("--suite", choices=["behavior", "triggers", "all"], default="all")
    parser.add_argument("--mode", choices=["with_skill", "baseline", "both"], default="both")
    parser.add_argument("--case", action="append", help="behavior case ID; repeat to select several")
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "evals" / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-budget-usd", type=float, default=0.20, help="Claude per-call budget cap (default: 0.20)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    providers = ["codex", "claude"] if args.provider == "both" else [args.provider]
    modes = ["with_skill", "baseline"] if args.mode == "both" else [args.mode]
    behavior_cases = load_behavior_cases(BEHAVIOR_DATA)
    if args.case:
        behavior_cases = [case for case in behavior_cases if case["id"] in set(args.case)]
    if args.max_cases:
        behavior_cases = behavior_cases[: args.max_cases]
    trigger_cases = load_trigger_cases(TRIGGER_DATA)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        for provider in providers:
            for mode in modes:
                workspace = args.output_dir / "dry-run" / provider / mode
                output = args.output_dir / "dry-run" / provider / mode / "last.json"
                for suite in (["behavior", "triggers"] if args.suite == "all" else [args.suite]):
                    schema = schema_for_suite(suite)
                    command = build_codex_command(mode, workspace, schema, output) if provider == "codex" else build_claude_command(mode, workspace, schema, args.max_budget_usd)
                    print(json.dumps({"provider": provider, "mode": mode, "suite": suite, "command": command}, ensure_ascii=True))
        return 0
    summaries = []
    for provider in providers:
        for mode in modes:
            if args.suite in {"behavior", "all"}:
                summaries.append(run_behavior(provider, mode, behavior_cases, args.output_dir, args.timeout, args.max_budget_usd))
            if args.suite in {"triggers", "all"}:
                summaries.append(run_triggers(provider, mode, trigger_cases, args.output_dir, args.timeout, args.max_budget_usd))
    _write_json(args.output_dir / "summary.json", {"generated_at": datetime.now(timezone.utc).isoformat(), "summaries": summaries})
    print(json.dumps({"output_dir": str(args.output_dir), "summaries": summaries}, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
