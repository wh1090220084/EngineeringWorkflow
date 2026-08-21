# README Visual and Bilingual Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add five maintainable diagrams, convert `README.md` to English, add `README_CN.md`, and validate all documentation assets offline.

**Architecture:** SVG diagrams live in `docs/images/` and are referenced by relative paths from both README files. The English README remains the canonical package guide; the Chinese README mirrors its structure and operational facts. The existing Python validator checks both language files and all five asset paths.

**Tech Stack:** Markdown, SVG, Python 3 standard library.

---

### Task 1: Add the Five Diagram Assets

**Files:**
- Create: `docs/images/architecture.svg`
- Create: `docs/images/workflow.svg`
- Create: `docs/images/risk-levels.svg`
- Create: `docs/images/evidence-ladder.svg`
- Create: `docs/images/platform-installation.svg`

- [ ] **Step 1: Create architecture and workflow diagrams**

Use self-contained SVG files with a white background, accessible text labels, viewBox dimensions, and no external image or font references. Architecture must show Codex, Claude Code, Gemini CLI, and GitHub Copilot CLI flowing into `skills/engineeringworkflow/`; workflow must show classify, route, inspect, verify, and hand off.

- [ ] **Step 2: Create routing and evidence diagrams**

Create `risk-levels.svg` with four visibly distinct levels and their concise decision cues. Create `evidence-ladder.svg` with five ordered evidence levels from targeted automated test to documented manual check.

- [ ] **Step 3: Create the platform installation diagram**

Create `platform-installation.svg` with four platform lanes, each ending in a smoke-test/explicit-invocation checkpoint and all pointing to the same canonical Skill.

### Task 2: Rewrite README Files

**Files:**
- Modify: `README.md`
- Create: `README_CN.md`

- [ ] **Step 1: Rewrite `README.md` in English**

Preserve the package architecture, platform installation, validation, maintenance, and runtime-boundary content in English. Add an image near the introduction and one image in each relevant section, using these exact links:

```markdown
![Architecture](docs/images/architecture.svg)
![Workflow](docs/images/workflow.svg)
![Risk levels](docs/images/risk-levels.svg)
![Evidence ladder](docs/images/evidence-ladder.svg)
![Platform installation](docs/images/platform-installation.svg)
```

Include a link to `README_CN.md` near the title.

- [ ] **Step 2: Create `README_CN.md`**

Translate the same sections and commands into Simplified Chinese. Use the same five image links and link back to `README.md` near the title. Keep file names, package identifiers, commands, and code blocks unchanged.

### Task 3: Extend Offline Validation

**Files:**
- Modify: `scripts/validate_package.py`

- [ ] **Step 1: Add documentation and image requirements before asset creation is considered complete**

Add `README_CN` and an `IMAGE_FILES` tuple. Require both README files, require each image file, require all five image paths in both README texts, require `README.md` to contain `# Engineering Workflow`, and require `README_CN.md` to contain `# Engineering Workflow（中文）`.

- [ ] **Step 2: Run the validator and inspect the expected failure**

Run `python scripts/validate_package.py`. It must fail with a missing `README_CN.md` or missing image path until Tasks 1 and 2 are complete.

- [ ] **Step 3: Run the validator after all assets and docs exist**

Run `python scripts/validate_package.py`. Expected output: `Package validation passed.` with exit code 0.

### Task 4: Review Scope and Rendering References

**Files:**
- Inspect: `README.md`
- Inspect: `README_CN.md`
- Inspect: `docs/images/*.svg`
- Inspect: `scripts/validate_package.py`

- [ ] **Step 1: Check all five image links and SVG files**

Confirm every Markdown image target resolves from the repository root and every SVG is self-contained ASCII/UTF-8 text with no remote URL.

- [ ] **Step 2: Check language parity**

Confirm both READMEs document the same four platforms, validation limits, maintenance path, and canonical-source rule.

- [ ] **Step 3: Report runtime limits**

Report that validation covers files and links only; no browser or platform runtime smoke test is claimed unless it was actually run.
