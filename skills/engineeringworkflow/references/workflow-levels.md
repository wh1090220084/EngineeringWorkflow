# Workflow Levels

Read this file for Standard, Strict, or Explore work. Quick work follows the main skill unless a routing boundary or escalation signal appears.

## Standard

1. Read the entry point, direct callers, configuration, relevant tests/run instructions, and nearby working pattern. When changing a shared function or boundary, enumerate its callers and trace the real flow.
2. State the goal, scope, exclusions, assumptions, risks, and proving evidence. Keep the affected file set as small as the requirements and required records allow.
3. Apply the complexity checkpoint. Check plausible repository reuse, standard-library, native, and already-installed dependency options before adding code or dependencies; do not turn this into open-ended research.
4. Run a relevant baseline when cheap and useful. If unavailable, select the strongest available evidence and record the gap.
5. For deterministic behavior, write a focused test or repeatable reproduction first, observe the expected failure, make the smallest change, and rerun it. For legacy or non-deterministic work, use a controlled characterization check or explicit input/output observation.
6. Run affected regression, build, static, or integration checks proportionate to blast radius. Self-review for scope drift, compatibility, errors, generated artifacts, duplicated behavior, hand-rolled standard/native capability, and speculative flexibility.

Standard handoff: goal and scope; modified files; commands or checks and results; documentation/record decision; exceptions; residual risk; and follow-up. For a development-only dependency, include the resolved version, lockfile/build impact, source/license check, and compatibility result. “Latest minor” means the newest compatible minor/patch within the repository's declared major-version policy, not an unbounded upgrade.

## Strict

Use Strict for untrusted public boundaries; security/privacy; runtime or production dependencies; consequential data/model/training/inference changes; credentials or permissions; irreversible, production, or external writes.

1. Confirm authorization, exact target, impact, acceptance threshold, rollback owner, and proving method before mutation. If a field is unknown or ambiguous, pause at the gate.
2. Write a repository plan before implementation. Include goal, scope, exclusions, assumptions, affected interfaces/data, validation, documentation/records, risks, rollback or accepted irreversibility, approver and authorization source/time, and acceptance threshold.
3. Use test-first behavior checks where deterministic. For experiments, follow [experiments](experiments.md). For external operations, follow [safety and trust](safety-and-trust.md).
4. Verify boundary and error paths, compatibility, artifacts, rollback or deletion/revocation limits, and relevant regressions. Resolve material findings and recheck.
5. Before any external effect, record the actual target, account/audience, payload/data scope, and verification evidence. Redact secrets and unnecessary personal or proprietary data.

Strict handoff must state: authorization/approver; target and impact; acceptance threshold; rollback or accepted irreversibility; changed files/artifacts; verification evidence; external or safety actions; exceptions; residual risk; and follow-up owner.

## Explore

Use Explore to answer an unknown question without presenting a prototype as production work.

- State the question, time/resource budget, isolation boundary, data source, and exit condition before changing code.
- Use a branch, temporary directory, notebook, feature flag, or separate script when available. Do not change production defaults, shared schemas, data, weights, or external systems without Strict authorization.
- Prefer a small reproducible experiment or characterization check. Record command, input, observation, and limitations.
- If the probe accepts a limited implementation, record its ceiling and the condition that should trigger promotion through Standard or Strict.
- At the exit condition, discard it, promote it through Standard/Strict with a plan, or report the result as exploratory. Do not label a spike complete as a production feature.

Explore handoff must state the question, isolation, budget, input/command, observation, limitations, exit result, and whether the work was discarded or promoted.

## Boundary refinements

| Decision | Lower level | Escalate to Strict when |
|---|---|---|
| Interface | Internal helper or repository-local shared function | An untrusted public/API boundary, compatibility promise, or external consumer changes |
| Dependency | Development-only tool with local lockfile/build impact | Runtime/production artifact, security or supply-chain concern, public tool contract, or material lockfile drift |
| External system | Read-only lookup with no disclosure | Upload, publish, deploy, send, permission change, or any external mutation |
| Environment | Reversible sandbox or isolated probe | Production defaults, shared schemas, live data/weights, or an external system changes |

## Escalation signals

Escalate immediately when Quick or Standard work changes a public contract, reveals data loss, touches credentials or permissions, needs a runtime dependency, cannot identify affected callers, changes a model/data result, invokes an external write, or fails focused verification twice for different causes. A development-only dependency also escalates when it affects a production artifact, shared build, security posture, public contract, or materially rewrites the lockfile.

Treat lockfile drift as material when it changes a major version, changes a direct runtime dependency, updates a production-resolved graph, changes a shared workspace/CI tool used outside the local task, or produces a broad transitive rewrite that cannot be explained and reviewed from the diff.

## Review boundaries

- Keep a read-only review that corroborates a README or other documented business fact against implementation/configuration at Standard; it needs evidence but does not mutate a public or external interface.
- Keep a read-only review of an unavailable CPU/GPU benchmark at Standard when no model, dataset, production, or external result is changed. Record the missing evidence and residual risk; use Strict only when the review changes a consequential result or initiates a protected operation.
- Route any implementation or change that crosses an untrusted public API boundary through Strict, even when a native browser or platform control covers the presentation layer.

For a documented business fact, “corroborated” means at least one executable or configuration source supports the behavior, or an identified owner confirms a fact code cannot prove. If README, code, configuration, and owner evidence conflict, report the conflict and do not silently choose a winner or rewrite documentation during a read-only review. A representative command is not automatically safe to run: inspect it for writes, credentials, uploads, and external effects first.
