# Engineering Workflow Skill Repository

Use `$engineering-workflow` for software-repository work. It owns the general delivery workflow and its safety, authorization, testing, debugging, verification, and handoff rules; do not duplicate those rules in this file.

This repository-specific layout is:

- Skill source: `skills/engineeringworkflow/SKILL.md`
- Supporting guidance: `skills/engineeringworkflow/references/`
- Codex integration metadata: `skills/engineeringworkflow/agents/openai.yaml`

When changing this skill, follow its `Validation` section and run the relevant read-only scenario in `skills/engineeringworkflow/references/pressure-scenarios.md`. Update the matching reference material whenever a main-skill rule changes its detailed procedure.
