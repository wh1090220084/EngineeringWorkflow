# Evidence and Debugging

Read this file for bugs, unexpected behavior, blocked verification, or completion claims.

## Root-Cause Loop

1. Read the complete error, warning, trace, relevant logs, and recent changes.
2. Reproduce with recorded input, command, and environment. If not reproducible, gather observations instead of guessing.
3. Trace the bad value, state, or artifact backward. At each component boundary check input, output, configuration, and state; locate the first unexpected transition. Before changing a shared function or boundary, enumerate its callers. Prefer one root-cause fix at the common boundary only when those callers share the same invariant; otherwise preserve caller-specific behavior.
4. Compare a working example and state one falsifiable hypothesis.
5. Test the hypothesis with the smallest diagnostic. After confirmation, make one root-cause fix and rerun focused evidence.

Do not stack speculative patches. If distinct root-cause attempts fail repeatedly, reassess the design or ask for context.

## Evidence Ladder

Use the strongest available item, then disclose the gap:

1. Existing targeted automated test.
2. New focused test or repeatable reproduction.
3. Build, type, lint, static, or parser check.
4. Controlled input/output or artifact inspection.
5. Documented manual check with exact steps and observed result.

An unavailable test framework, GPU, dataset, or baseline does not make lower evidence worthless. It does prevent claims about behavior that only the unavailable check could prove.

For non-trivial logic without a usable test framework, leave the smallest runnable check that would fail if the logic regresses: an assertion, self-check, minimal reproduction, or controlled input/output check. This supplements the evidence ladder; it does not replace required regression coverage.

## Completion Gate

For each completion claim, run fresh evidence after the final edit. Read the exit status and relevant output. Check error paths, boundaries, logs, artifacts, compatibility, and performance when they are in scope. For a deliberately limited implementation, include relevant edge or adversarial inputs; when a ceiling is recorded, confirm the current case remains within it and the revisit trigger is observable. Inspect the final change set for scope drift, secrets, data, weights, caches, logs, and accidental generated files.

When evidence is incomplete, report: executed evidence; skipped evidence and reason; what remains unknown; residual risk; owner and follow-up. Do not replace these with “should work”, “probably”, or an unqualified completion claim.
