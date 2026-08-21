# Cross-Platform Skill Package Design

## Goal

Package `engineering-workflow` as one portable skill that can be discovered by Codex, Claude Code, Gemini CLI, and GitHub Copilot CLI without copying the skill instructions for each platform.

## Scope

The canonical behavior remains in `skills/engineeringworkflow/`. Platform files describe the package or load that directory; they do not restate workflow policy. The project will add a root README that explains the package and local installation/use on every supported platform.

The implementation adds these files:

| File | Responsibility |
|---|---|
| `.codex-plugin/plugin.json` | Codex plugin metadata and `skills/` discovery declaration. |
| `.claude-plugin/plugin.json` | Claude Code plugin metadata and `skills/` discovery declaration. |
| `.agents/plugins/marketplace.json` | GitHub Copilot CLI-compatible local marketplace entry that exposes this package. |
| `gemini-extension.json` | Gemini CLI extension metadata and `GEMINI.md` context entry declaration. |
| `GEMINI.md` | Gemini bootstrap that imports the canonical Skill. |
| `README.md` | Package architecture, support matrix, local installation, use, updating, and validation guidance. |

`skills/engineeringworkflow/agents/openai.yaml` remains the Codex UI metadata for the individual skill. `AGENTS.md` remains the repository-maintainer entry point, not a replacement for platform installation metadata.

## Design Decisions

### Canonical Instructions

`skills/engineeringworkflow/SKILL.md` and its `references/` directory remain the only source of engineering workflow behavior. Each platform adapter points to `./skills/`; no generated copies, symlinks, or per-platform rewrites are introduced.

### Capability Boundary

The package supports native skill discovery and explicit invocation where each platform provides it. Auto-selection is determined by that platform's skill system and the Skill description. This first version deliberately excludes runtime hooks that inject prompt text on every session or after context compaction, because those hooks are platform-specific code with a larger maintenance and security surface.

### Distribution Boundary

The repository is prepared as a local package. The README documents local installation and verification. Publishing to a remote marketplace, assigning a public repository URL, signing releases, or choosing a license is outside this change because it requires user-controlled release identity and authority.

## Installation Model

- **Codex:** install or load the package as a Codex plugin; its manifest exposes `./skills/`.
- **Claude Code:** install or load the package as a Claude Code plugin; its manifest exposes `./skills/`.
- **Gemini CLI:** install the directory as a Gemini extension; `gemini-extension.json` selects `GEMINI.md`, which imports the canonical Skill.
- **GitHub Copilot CLI:** register the repository as a local plugin marketplace and install the package entry; `.agents/plugins/marketplace.json` follows the same thin-marketplace pattern as the examined reference repository.

The README will label commands that require a repository URL or platform UI as templates and include a direct verification prompt for every platform. It will not imply that a platform was exercised if its executable is unavailable in the development environment.

## Validation

1. Parse all JSON manifests.
2. Confirm every declared path exists and resolves to the shared skill directory or expected bootstrap file.
3. Verify `GEMINI.md` imports the canonical `SKILL.md` rather than duplicating it.
4. Run the repository Skill's relevant read-only pressure scenarios as documentation validation.
5. Review `README.md` against the files above so installation instructions match the package layout.

## Non-Goals

- No platform-specific runtime hooks or background services.
- No remote publication, package installation, external download, commit, or push.
- No changes to the engineering workflow behavior itself.
