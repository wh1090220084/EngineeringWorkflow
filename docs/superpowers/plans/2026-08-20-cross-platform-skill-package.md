# Cross-Platform Skill Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the canonical `engineering-workflow` skill for Codex, Claude Code, Gemini CLI, and GitHub Copilot CLI without duplicating its instructions.

**Architecture:** `skills/engineeringworkflow/` remains the sole behavioral source. Root-level platform manifests expose that same `skills/` directory, while Gemini uses a tiny `GEMINI.md` import. A standard-library Python validator verifies the package contract offline; `README.md` documents installation, invocation, scope, and validation without claiming unrun platform tests.

**Tech Stack:** Markdown, JSON, YAML (existing metadata), Python 3 standard library.

---

## File Structure

| File | Responsibility |
|---|---|
| `.codex-plugin/plugin.json` | Codex package metadata exposing `./skills/`. |
| `.claude-plugin/plugin.json` | Claude Code package metadata exposing `./skills/`. |
| `.agents/plugins/marketplace.json` | GitHub Copilot CLI local-marketplace entry. |
| `gemini-extension.json` | Gemini CLI extension metadata pointing to `GEMINI.md`. |
| `GEMINI.md` | Imports the canonical Skill, with no copied workflow text. |
| `scripts/validate_package.py` | Validates JSON syntax, required package fields, path contracts, Gemini import, and README support claims. |
| `README.md` | Explains package architecture and local installation/use for all four platforms. |

### Task 1: Create Thin Platform Adapters

**Files:**
- Create: `.codex-plugin/plugin.json`
- Create: `.claude-plugin/plugin.json`
- Create: `.agents/plugins/marketplace.json`
- Create: `gemini-extension.json`
- Create: `GEMINI.md`
- Test: `scripts/validate_package.py`

- [ ] **Step 1: Write a failing package-contract validator**

Create `scripts/validate_package.py` with the `required_files` and `read_json` checks below, before any adapter files exist:

```python
#!/usr/bin/env python3
"""Validate the repository's portable skill package contract."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "engineeringworkflow" / "SKILL.md"
README = ROOT / "README.md"

REQUIRED_FILES = (
    ROOT / ".codex-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".agents" / "plugins" / "marketplace.json",
    ROOT / "gemini-extension.json",
    ROOT / "GEMINI.md",
    SKILL,
    README,
)


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    try:
        for path in REQUIRED_FILES:
            require(path.is_file(), f"Missing required file: {path.relative_to(ROOT)}")

        codex = read_json(ROOT / ".codex-plugin" / "plugin.json")
        claude = read_json(ROOT / ".claude-plugin" / "plugin.json")
        marketplace = read_json(ROOT / ".agents" / "plugins" / "marketplace.json")
        gemini = read_json(ROOT / "gemini-extension.json")

        for label, manifest in (("Codex", codex), ("Claude Code", claude)):
            require(manifest.get("name") == "engineering-workflow", f"{label} manifest name must be engineering-workflow")
            require(manifest.get("skills") == "./skills/", f"{label} manifest must expose ./skills/")

        require(marketplace.get("name") == "engineering-workflow", "Copilot marketplace name must be engineering-workflow")
        plugins = marketplace.get("plugins")
        require(isinstance(plugins, list) and len(plugins) == 1, "Copilot marketplace must expose exactly one plugin")
        require(plugins[0].get("name") == "engineering-workflow", "Copilot plugin name must be engineering-workflow")
        require(plugins[0].get("source") == {"source": "url", "url": "./"}, "Copilot plugin source must be the repository root")

        require(gemini.get("name") == "engineering-workflow", "Gemini extension name must be engineering-workflow")
        require(gemini.get("contextFileName") == "GEMINI.md", "Gemini extension must use GEMINI.md")

        gemini_context = (ROOT / "GEMINI.md").read_text(encoding="utf-8").strip()
        require(gemini_context == "@./skills/engineeringworkflow/SKILL.md", "GEMINI.md must import only the canonical Skill")

        readme = README.read_text(encoding="utf-8")
        for platform in ("Codex", "Claude Code", "Gemini CLI", "GitHub Copilot CLI"):
            require(platform in readme, f"README.md must document {platform}")
        require("single source of truth" in readme, "README.md must state the canonical-source rule")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Package validation failed: {error}", file=sys.stderr)
        return 1

    print("Package validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the validator and verify the expected failure**

Run: `python scripts/validate_package.py`

Expected: exit code `1` and `Package validation failed: Missing required file: .codex-plugin/plugin.json`.

- [ ] **Step 3: Create the platform adapter files**

Create `.codex-plugin/plugin.json`:

```json
{
  "name": "engineering-workflow",
  "version": "0.1.0",
  "description": "Risk-proportionate, evidence-driven workflow skill for software repositories.",
  "license": "UNLICENSED",
  "skills": "./skills/",
  "interface": {
    "displayName": "Engineering Workflow",
    "shortDescription": "Evidence-driven software delivery workflow",
    "longDescription": "A portable skill for planning, implementing, debugging, reviewing, validating, and operating on software repositories with risk-proportionate evidence and safety gates.",
    "developerName": "Local package",
    "category": "Developer Tools",
    "capabilities": ["Read", "Write"],
    "defaultPrompt": ["Use engineering-workflow to handle this repository task."]
  }
}
```

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "engineering-workflow",
  "description": "Risk-proportionate, evidence-driven workflow skill for software repositories.",
  "version": "0.1.0",
  "license": "UNLICENSED",
  "keywords": ["skills", "engineering", "testing", "debugging", "verification"],
  "skills": "./skills/"
}
```

Create `.agents/plugins/marketplace.json`:

```json
{
  "name": "engineering-workflow",
  "interface": {
    "displayName": "Engineering Workflow"
  },
  "plugins": [
    {
      "name": "engineering-workflow",
      "source": {
        "source": "url",
        "url": "./"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Developer Tools"
    }
  ]
}
```

Create `gemini-extension.json`:

```json
{
  "name": "engineering-workflow",
  "description": "Risk-proportionate, evidence-driven workflow skill for software repositories.",
  "version": "0.1.0",
  "contextFileName": "GEMINI.md"
}
```

Create `GEMINI.md`:

```markdown
@./skills/engineeringworkflow/SKILL.md
```

- [ ] **Step 4: Run the package validator and verify it passes**

Run: `python scripts/validate_package.py`

Expected: exit code `0` and `Package validation passed.`

### Task 2: Document Installation and Use

**Files:**
- Create: `README.md`
- Modify: `scripts/validate_package.py`
- Test: `scripts/validate_package.py`

- [ ] **Step 1: Extend the failing documentation contract**

Add the `README.md` checks shown in Task 1 to `scripts/validate_package.py`, then run the validator while `README.md` is absent.

Run: `python scripts/validate_package.py`

Expected: exit code `1` and `Package validation failed: Missing required file: README.md`.

- [ ] **Step 2: Write README.md with the exact package and support boundaries**

Create `README.md` with these sections and statements:

```markdown
# Engineering Workflow

Engineering Workflow is a portable, risk-proportionate software-engineering Skill. It guides planning, implementation, debugging, reviews, validation, and repository operations with evidence appropriate to the change's risk.

## Architecture

`skills/engineeringworkflow/` is the **single source of truth** for behavior. `SKILL.md` contains the shared routing rules and `references/` contains context-specific procedures. Platform files at the repository root only register or import that directory; they do not copy the workflow instructions.

## Supported Platforms

| Platform | Package entry | How the Skill is loaded |
| --- | --- | --- |
| Codex | `.codex-plugin/plugin.json` | The plugin exposes `./skills/`; Codex discovers `engineering-workflow`. |
| Claude Code | `.claude-plugin/plugin.json` | The plugin exposes `./skills/`; Claude Code discovers `engineering-workflow`. |
| Gemini CLI | `gemini-extension.json` and `GEMINI.md` | `GEMINI.md` imports the canonical `SKILL.md`. |
| GitHub Copilot CLI | `.agents/plugins/marketplace.json` | A local marketplace entry exposes this package. |

## Install and Use

### Codex

Install this local package with the Codex plugin UI or CLI, selecting the repository directory. Verify that **Engineering Workflow** appears under installed plugins or skills. In a repository task, invoke `$engineering-workflow` explicitly when needed; normal automatic selection depends on the active Codex environment and the Skill description.

### Claude Code

Install this local directory as a Claude Code plugin. Confirm the plugin manager lists **engineering-workflow**, then invoke `/engineering-workflow` or ask Claude Code to use the engineering-workflow Skill for a repository task. Skill discovery and automatic selection are controlled by the active Claude Code version and configuration.

### Gemini CLI

From the parent directory of this checkout, install the extension using the local path:

```bash
gemini extensions install ./EngineeringWorkflow
```

Confirm that Gemini CLI lists `engineering-workflow`, then start a repository task and request the engineering-workflow instructions. Gemini loads `GEMINI.md`, which imports the canonical Skill from this repository.

### GitHub Copilot CLI

Register this checkout as a local plugin marketplace, then install the `engineering-workflow` entry using the commands supported by your Copilot CLI version. Confirm the installed plugin list includes `engineering-workflow`; use the Skill explicitly for a repository task when automatic discovery is not available.

## Validate the Package

Run the offline package validator from the repository root:

```bash
python scripts/validate_package.py
```

It validates manifest JSON, shared-skill path contracts, the Gemini import, and README platform coverage. It does not start Codex, Claude Code, Gemini CLI, or GitHub Copilot CLI, so it cannot prove runtime behavior in those tools.

For a platform-level smoke test, install the package in that platform, begin a repository task, and ask it to use `engineering-workflow`. Confirm that it reads `skills/engineeringworkflow/SKILL.md` and applies the requested task route without copying platform-specific instructions.

## Maintaining the Skill

Change workflow behavior only in `skills/engineeringworkflow/SKILL.md` or its linked `references/` files. Follow the Skill's `Validation` section and run the matching read-only scenario in `skills/engineeringworkflow/references/pressure-scenarios.md`. Then run `python scripts/validate_package.py` to ensure all platform adapters still point at the canonical source.

This repository contains local package metadata only. Remote marketplace publication, release signing, version promotion, and license selection require the repository owner's separate approval.
```

- [ ] **Step 3: Run the documentation contract and inspect the README**

Run: `python scripts/validate_package.py`

Expected: exit code `0` and `Package validation passed.`

Inspect: `README.md` contains each supported platform, the single-source statement, instructions that distinguish local package validation from runtime platform verification, and no claim that any platform was exercised.

### Task 3: Validate Canonical-Skill Integrity and Documentation

**Files:**
- Modify: `README.md`
- Modify: `scripts/validate_package.py`
- Test: `scripts/validate_package.py`

- [ ] **Step 1: Add a failing canonical-content guard**

Add this check after reading `gemini_context` in `scripts/validate_package.py`:

```python
        skill_text = SKILL.read_text(encoding="utf-8")
        require("name: engineering-workflow" in skill_text, "Canonical SKILL.md must identify engineering-workflow")
        require("# Engineering Workflow" in skill_text, "Canonical SKILL.md must contain the Engineering Workflow heading")
```

Temporarily change the first line of `GEMINI.md` to `# copied workflow` without saving other changes, then run:

```bash
python scripts/validate_package.py
```

Expected: exit code `1` and `Package validation failed: GEMINI.md must import only the canonical Skill`.

- [ ] **Step 2: Restore the canonical Gemini import and run the full validator**

Restore `GEMINI.md` to this exact content:

```markdown
@./skills/engineeringworkflow/SKILL.md
```

Run: `python scripts/validate_package.py`

Expected: exit code `0` and `Package validation passed.`

- [ ] **Step 3: Apply the skill-maintenance pressure checks as read-only review**

Read `skills/engineeringworkflow/references/pressure-scenarios.md` and verify the package documentation does not change the expected behavior for these scenarios:

```text
Quick Local Fix: retain Quick as a minimal local route.
Legacy Code Without Tests: retain Standard with the evidence ladder.
High-Risk Shortcut: retain Strict and pause before install or overwrite.
```

Expected: the README describes only package discovery and validation, while all behavior remains in the canonical Skill and its references.

### Task 4: Final Scope and Artifact Review

**Files:**
- Inspect: `AGENTS.md`
- Inspect: `README.md`
- Inspect: `.codex-plugin/plugin.json`
- Inspect: `.claude-plugin/plugin.json`
- Inspect: `.agents/plugins/marketplace.json`
- Inspect: `gemini-extension.json`
- Inspect: `GEMINI.md`
- Inspect: `scripts/validate_package.py`
- Test: `scripts/validate_package.py`

- [ ] **Step 1: Verify all manifest references resolve to the shared source**

Run:

```powershell
python scripts/validate_package.py
Test-Path skills\engineeringworkflow\SKILL.md
Test-Path skills\engineeringworkflow\references\pressure-scenarios.md
```

Expected: validator exits `0` with `Package validation passed.`, followed by two `True` lines.

- [ ] **Step 2: Review scope and sensitive artifacts**

Run:

```powershell
Get-ChildItem -Force .codex-plugin,.claude-plugin,.agents,skills,scripts,docs | Select-Object FullName
```

Expected: only planned manifests, the canonical Skill, documentation, and the standard-library validator are present; no copied Skill text, credentials, platform caches, dependency lockfiles, or downloaded artifacts appear.

- [ ] **Step 3: Report verification boundaries accurately**

Record that the final validator proves package structure and canonical-source links. Record whether Codex, Claude Code, Gemini CLI, and GitHub Copilot CLI runtime smoke tests were actually run; if a platform executable or local installation is unavailable, list it as unrun rather than inferred.
