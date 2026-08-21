#!/usr/bin/env python3
"""Validate the repository's portable skill package contract."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "engineeringworkflow" / "SKILL.md"
README = ROOT / "README.md"
README_CN = ROOT / "README_CN.md"

IMAGE_FILES = (
    ROOT / "docs" / "images" / "architecture.svg",
    ROOT / "docs" / "images" / "workflow.svg",
    ROOT / "docs" / "images" / "risk-levels.svg",
    ROOT / "docs" / "images" / "evidence-ladder.svg",
    ROOT / "docs" / "images" / "platform-installation.svg",
)

REQUIRED_FILES = (
    ROOT / ".codex-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".agents" / "plugins" / "marketplace.json",
    ROOT / "gemini-extension.json",
    ROOT / "GEMINI.md",
    SKILL,
    README,
    README_CN,
    *IMAGE_FILES,
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
            require(
                manifest.get("name") == "engineering-workflow",
                f"{label} manifest name must be engineering-workflow",
            )
            require(manifest.get("skills") == "./skills/", f"{label} manifest must expose ./skills/")

        author = codex.get("author")
        require(isinstance(author, dict) and author.get("name"), "Codex manifest must identify an author")
        interface = codex.get("interface")
        require(isinstance(interface, dict), "Codex manifest must contain interface metadata")
        for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
            require(interface.get(field), f"Codex interface must define {field}")

        require(
            marketplace.get("name") == "engineering-workflow",
            "Copilot marketplace name must be engineering-workflow",
        )
        plugins = marketplace.get("plugins")
        require(
            isinstance(plugins, list) and len(plugins) == 1,
            "Copilot marketplace must expose exactly one plugin",
        )
        require(plugins[0].get("name") == "engineering-workflow", "Copilot plugin name must be engineering-workflow")
        require(
            plugins[0].get("source") == {"source": "url", "url": "./"},
            "Copilot plugin source must be the repository root",
        )

        require(gemini.get("name") == "engineering-workflow", "Gemini extension name must be engineering-workflow")
        require(gemini.get("contextFileName") == "GEMINI.md", "Gemini extension must use GEMINI.md")

        gemini_context = (ROOT / "GEMINI.md").read_text(encoding="utf-8").strip()
        require(
            gemini_context == "@./skills/engineeringworkflow/SKILL.md",
            "GEMINI.md must import only the canonical Skill",
        )

        skill_text = SKILL.read_text(encoding="utf-8")
        require("name: engineering-workflow" in skill_text, "Canonical SKILL.md must identify engineering-workflow")
        require("# Engineering Workflow" in skill_text, "Canonical SKILL.md must contain the Engineering Workflow heading")

        readme = README.read_text(encoding="utf-8")
        readme_cn = README_CN.read_text(encoding="utf-8")
        for platform in ("Codex", "Claude Code", "Gemini CLI", "GitHub Copilot CLI"):
            require(platform in readme, f"README.md must document {platform}")
            require(platform in readme_cn, f"README_CN.md must document {platform}")
        require("single source of truth" in readme, "README.md must state the canonical-source rule")
        require("# Engineering Workflow" in readme, "README.md must contain the English title")
        require("# Engineering Workflow（中文）" in readme_cn, "README_CN.md must contain the Chinese title")
        for image_path in IMAGE_FILES:
            image_link = image_path.relative_to(ROOT).as_posix()
            require(image_link in readme, f"README.md must reference {image_link}")
            require(image_link in readme_cn, f"README_CN.md must reference {image_link}")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Package validation failed: {error}", file=sys.stderr)
        return 1

    print("Package validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

