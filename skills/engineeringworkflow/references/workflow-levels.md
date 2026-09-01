# Workflow Levels

Read this file for Standard, Strict, or Explore work. Quick work follows the main skill unless it escalates.

## Standard

1. Read the entry point, direct callers, configuration, relevant test/run instructions, and nearby working pattern. When changing a shared function or boundary, enumerate its callers and trace the real flow. State goal, scope, assumption, risk, and proving evidence.
2. Apply the complexity checkpoint from the main skill. Check plausible repository reuse, standard-library, native, and existing-dependency options before adding code or dependencies; do not turn the checkpoint into an open-ended research task. Keep the affected file set as small as the requirements and required records allow.
3. Run a relevant baseline when it is cheap and useful. If unavailable, select the strongest available evidence from the main skill and record the gap.
4. For deterministic behavior, write a focused test or repeatable reproduction first, observe the expected failure, make the smallest change, and rerun it. For legacy or non-deterministic work, use a controlled characterization check or an explicit input/output observation instead.
5. Run affected regression, build, static, or integration checks proportionate to blast radius. Review the final change for scope, compatibility, errors, generated artifacts, duplicated repository behavior, hand-rolled standard/native capability, and speculative flexibility. Simplify only when behavior, edge cases, and readability remain intact. If the implementation deliberately accepts a known ceiling, record its assumption, trigger or metric, and upgrade path.

## Strict

Use Strict when a change has public, security, data/model, training/inference, dependency, irreversible, production, or external consequences.

1. Confirm authorization, target, impact, acceptance threshold, rollback owner, and proving method before mutation.
2. Write a repository plan before implementation. Include scope, exclusions, assumptions, affected interfaces/data, validation, documentation/records, risks, rollback, approver, and approval time.
3. Use test-first behavior checks where deterministic. For experiments, follow [experiments](experiments.md). For external operations, follow [safety and trust](safety-and-trust.md).
4. Verify boundary and error paths, compatibility, artifacts, and relevant regressions. Review requirements compliance before code quality/safety; resolve material findings and recheck. Do not approve a simplification that removes trust-boundary validation, data-loss protection, security, privacy, accessibility, or required operational controls.

## Explore

Use Explore to answer an unknown question without presenting a prototype as production work.

- State the question, time/resource budget, isolation boundary, data source, and exit condition before changing code.
- Use a branch, temporary directory, notebook, feature flag, or separate script when available. Do not change production defaults, shared schemas, data, weights, or external systems without Strict authorization.
- Prefer a small reproducible experiment or characterization check. Record command, input, observation, and limitations.
- If the probe intentionally accepts a limited implementation, record its ceiling and the condition that should trigger promotion through Standard or Strict.
- At the exit condition, either discard, promote through Standard/Strict with a plan, or report the result as exploratory. Do not label a spike complete as a production feature.

## Escalation Signals

Escalate immediately when a Quick or Standard task changes a public contract, reveals data loss, touches credentials or permissions, needs new dependencies, cannot identify affected callers, changes a model/data result, invokes an external system, or fails focused verification twice for different causes.

## Review Boundaries

- Keep a read-only review that corroborates a README or other documented business fact against implementation/configuration at Standard; it needs evidence but does not mutate a public or external interface.
- Keep a read-only review of an unavailable CPU/GPU benchmark at Standard when no model, dataset, production, or external result is changed. Record the missing evidence and residual risk; use Strict only when the review itself changes a consequential result or initiates a protected operation.
- Route any implementation or change that crosses an untrusted public API boundary through Strict, even when a native browser or platform control covers the presentation layer.
