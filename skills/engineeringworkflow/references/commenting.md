# Commenting and Documentation

Use this reference when creating or changing executable scripts, public callables, complex logic, or project business rules.

Creating a new executable script is Standard work even if it is one file and the flow is obvious: its CLI, I/O, and reusable callables form a maintenance boundary. State that the header is before imports and that comments explain why/invariants rather than restating lines. A request to skip required documentation is a scope conflict to resolve by adding the minimum contract documentation, not permission to omit it.

## Executable script header

Place a module docstring or language-standard file-header comment before imports. A required shebang, encoding declaration, or equivalent language header may come first. State:

- the core processing flow and data path;
- inputs, outputs, key parameters, and side effects;
- runtime prerequisites, dependencies, required configuration, and a useful invocation example when needed.

Keep the header accurate and concise. It should explain the contract a maintainer cannot infer safely from the first few lines of code.

## Callable documentation

Document public methods, complex methods, and methods that encode business rules. State the responsibility and, as applicable, parameters, return value, raised exceptions, side effects, and important constraints. Class, static, and asynchronous methods follow the same rule. A short, semantically obvious helper may omit a repetitive docstring, but must document non-obvious constraints or external dependencies.

Prefer explaining why a constraint or choice exists over narrating each statement. Do not use comments to hide an unsafe shortcut, replace validation, or repeat names and control flow. When behavior, parameters, return values, exceptions, side effects, or design trade-offs change, update the documentation in the same change; stale comments are defects.

## Review checklist

1. Is the script header before imports and complete for its actual I/O and side effects?
2. Are public, complex, and business-rule callables documented at the right level?
3. Are prerequisites and an example present where a user could otherwise invoke it incorrectly?
4. Does each comment explain a reason, invariant, boundary, or trade-off rather than restating code?
5. Did the change update any affected documentation and avoid line-by-line comment noise?
