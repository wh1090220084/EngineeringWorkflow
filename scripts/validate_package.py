#!/usr/bin/env python3
"""
Validate the repository's portable Skill package contract.

The script reads manifests, canonical Skill files, linked Markdown references,
evaluation contracts, schemas, CI metadata, and README coverage; it reports
all discovered errors and exits non-zero when any contract is violated. It is
read-only and has no third-party dependencies or required configuration.
Run it from the repository root with ``python scripts/validate_package.py``;
successful validation prints ``Package validation passed.``.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    from scripts.evaluate_behavior import ContractError, RESPONSE_FIELDS, load_behavior_cases, load_trigger_cases
except ModuleNotFoundError:  # Direct ``python scripts/validate_package.py`` invocation.
    from evaluate_behavior import ContractError, RESPONSE_FIELDS, load_behavior_cases, load_trigger_cases


ROOT = Path(__file__).resolve().parents[1]

IMAGE_PATHS = (
    "docs/images/architecture.svg",
    "docs/images/workflow.svg",
    "docs/images/risk-levels.svg",
    "docs/images/evidence-ladder.svg",
    "docs/images/platform-installation.svg",
)

REQUIRED_PATHS = (
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    ".github/workflows/validate.yml",
    "gemini-extension.json",
    "GEMINI.md",
    "skills/engineeringworkflow/SKILL.md",
    "skills/engineeringworkflow/references/commenting.md",
    "skills/engineeringworkflow/agents/openai.yaml",
    "evals/behavior.json",
    "evals/triggers.json",
    "evals/response.schema.json",
    "evals/trigger-response.schema.json",
    "scripts/evaluate_behavior.py",
    "scripts/run_live_evals.py",
    "docs/validation.md",
    "docs/validation-results.md",
    "CHANGELOG.md",
    "README.md",
    "README_CN.md",
    *IMAGE_PATHS,
)


def _read_json(path: Path) -> dict[str, Any]:
    """Read a manifest/schema JSON object and reject non-object documents."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _check_markdown_links(root: Path, errors: list[str]) -> None:
    """Verify local Markdown references in the canonical Skill stay in-repository and resolve."""
    skill_root = root / "skills" / "engineeringworkflow"
    if not skill_root.is_dir():
        return
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for markdown in skill_root.rglob("*.md"):
        try:
            text = markdown.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"Cannot read {markdown.relative_to(root)}: {exc}")
            continue
        for raw_target in link_pattern.findall(text):
            target = raw_target.strip().strip("<>").split("#", 1)[0]
            if not target or "://" in target or not target.lower().endswith(".md"):
                continue
            resolved = (markdown.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"Markdown reference escapes the repository: {markdown.relative_to(root)} -> {target}")
                continue
            if not resolved.is_file():
                errors.append(f"Missing Markdown reference: {markdown.relative_to(root)} -> {target}")


def _validate_evaluations(root: Path, errors: list[str]) -> None:
    """Validate behavior/trigger contracts and their top-level response schemas."""
    behavior_path = root / "evals" / "behavior.json"
    trigger_path = root / "evals" / "triggers.json"
    if behavior_path.is_file():
        try:
            cases = load_behavior_cases(behavior_path)
            routes = {case["expect"]["route"] for case in cases}
            if routes != {"Quick", "Standard", "Strict", "Explore"}:
                errors.append("Behavior evaluations must cover Quick, Standard, Strict, and Explore")
        except ContractError as exc:
            errors.append(f"Invalid behavior evaluations: {exc}")
    if trigger_path.is_file():
        try:
            cases = load_trigger_cases(trigger_path)
            positives = sum(case["should_trigger"] for case in cases)
            if len(cases) != 20 or positives != 10:
                errors.append("Trigger evaluations must contain 20 balanced cases")
        except ContractError as exc:
            errors.append(f"Invalid trigger evaluations: {exc}")

    expected_schemas = {
        "response.schema.json": list(RESPONSE_FIELDS),
        "trigger-response.schema.json": ["results"],
    }
    for filename, required in expected_schemas.items():
        path = root / "evals" / filename
        if not path.is_file():
            continue
        try:
            schema = _read_json(path)
            if schema.get("type") != "object" or schema.get("required") != required:
                errors.append(f"{filename} has an unexpected top-level contract")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid evaluation schema {filename}: {exc}")


def validate(root: Path) -> list[str]:
    """Return every package validation error found below ``root`` without changing files."""
    root = root.resolve()
    errors: list[str] = []
    for relative in REQUIRED_PATHS:
        if not (root / relative).is_file():
            errors.append(f"Missing required file: {relative}")

    manifests: dict[str, dict[str, Any]] = {}
    manifest_paths = {
        "Codex": ".codex-plugin/plugin.json",
        "Claude Code": ".claude-plugin/plugin.json",
        "Copilot": ".agents/plugins/marketplace.json",
        "Gemini": "gemini-extension.json",
    }
    for label, relative in manifest_paths.items():
        path = root / relative
        if not path.is_file():
            continue
        try:
            manifests[label] = _read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid {label} manifest: {exc}")

    for label in ("Codex", "Claude Code"):
        manifest = manifests.get(label)
        if not manifest:
            continue
        if manifest.get("name") != "engineering-workflow":
            errors.append(f"{label} manifest name must be engineering-workflow")
        if manifest.get("skills") != "./skills/":
            errors.append(f"{label} manifest must expose ./skills/")

    versions = {
        label: manifests[label].get("version")
        for label in ("Codex", "Claude Code", "Gemini")
        if label in manifests
    }
    if versions and (any(not version for version in versions.values()) or len(set(versions.values())) != 1):
        errors.append(f"Manifest versions must agree: {versions}")

    codex = manifests.get("Codex", {})
    author = codex.get("author")
    if codex and not (isinstance(author, dict) and author.get("name")):
        errors.append("Codex manifest must identify an author")
    interface = codex.get("interface")
    if codex and not isinstance(interface, dict):
        errors.append("Codex manifest must contain interface metadata")
    elif isinstance(interface, dict):
        for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
            if not interface.get(field):
                errors.append(f"Codex interface must define {field}")

    marketplace = manifests.get("Copilot", {})
    if marketplace and marketplace.get("name") != "engineering-workflow":
        errors.append("Copilot marketplace name must be engineering-workflow")
    plugins = marketplace.get("plugins")
    if marketplace and not (isinstance(plugins, list) and len(plugins) == 1):
        errors.append("Copilot marketplace must expose exactly one plugin")
    elif isinstance(plugins, list) and len(plugins) == 1:
        if plugins[0].get("name") != "engineering-workflow":
            errors.append("Copilot plugin name must be engineering-workflow")
        if plugins[0].get("source") != {"source": "url", "url": "./"}:
            errors.append("Copilot plugin source must be the repository root")

    gemini = manifests.get("Gemini", {})
    if gemini and gemini.get("name") != "engineering-workflow":
        errors.append("Gemini extension name must be engineering-workflow")
    if gemini and gemini.get("contextFileName") != "GEMINI.md":
        errors.append("Gemini extension must use GEMINI.md")
    gemini_context = root / "GEMINI.md"
    if gemini_context.is_file():
        try:
            if gemini_context.read_text(encoding="utf-8").strip() != "@./skills/engineeringworkflow/SKILL.md":
                errors.append("GEMINI.md must import only the canonical Skill")
        except OSError as exc:
            errors.append(f"Cannot read GEMINI.md: {exc}")

    skill = root / "skills" / "engineeringworkflow" / "SKILL.md"
    if skill.is_file():
        try:
            skill_text = skill.read_text(encoding="utf-8")
            if "name: engineering-workflow" not in skill_text:
                errors.append("Canonical SKILL.md must identify engineering-workflow")
            if "# Engineering Workflow" not in skill_text:
                errors.append("Canonical SKILL.md must contain the Engineering Workflow heading")
        except OSError as exc:
            errors.append(f"Cannot read canonical SKILL.md: {exc}")

    _check_markdown_links(root, errors)
    _validate_evaluations(root, errors)

    readmes = {"README.md": "# Engineering Workflow", "README_CN.md": "# Engineering Workflow（中文）"}
    for filename, title in readmes.items():
        path = root / filename
        if not path.is_file():
            continue
        try:
            readme_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"Cannot read {filename}: {exc}")
            continue
        for platform in ("Codex", "Claude Code", "Gemini CLI", "GitHub Copilot CLI"):
            if platform not in readme_text:
                errors.append(f"{filename} must document {platform}")
        if "single source of truth" not in readme_text:
            errors.append(f"{filename} must state the canonical-source rule")
        if title not in readme_text:
            errors.append(f"{filename} must contain its expected title")
        for image_path in IMAGE_PATHS:
            if image_path not in readme_text:
                errors.append(f"{filename} must reference {image_path}")

    return errors


def main() -> int:
    """Run validation for the checkout root and map errors to a process exit code."""
    errors = validate(ROOT)
    if errors:
        print("Package validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Package validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
