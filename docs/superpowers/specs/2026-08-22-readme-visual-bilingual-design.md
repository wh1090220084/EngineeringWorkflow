# README Visual and Bilingual Documentation Design

## Goal

Make the project documentation easier to scan by adding five locally maintained diagrams, keep the primary `README.md` in English, and add an equivalent Chinese `README_CN.md`.

## Design

The diagrams are code-native SVG assets under `docs/images/`, so they render in common repository viewers without external URLs, binary dependencies, or image-generation services. Both README files use the same relative image paths and captions.

The five diagrams cover distinct relationships:

1. `architecture.svg`: platform adapters converge on the canonical Skill source.
2. `workflow.svg`: task classification through evidence-backed handoff.
3. `risk-levels.svg`: Quick, Standard, Strict, and Explore routing.
4. `evidence-ladder.svg`: increasing strength of verification evidence.
5. `platform-installation.svg`: install and smoke-test paths for four supported platforms.

The existing package validator will verify that both README files exist, are language-specific, reference all five images, and that every referenced image exists. It will continue to validate manifests and canonical Skill integrity.

## Scope

- Rewrite `README.md` in English while preserving the current package architecture and installation guidance.
- Add `README_CN.md` with equivalent Chinese content.
- Add five SVG diagrams and no external images.
- Extend `scripts/validate_package.py` with documentation and image-link checks.

No workflow behavior, platform manifest, installation command, or external service is changed by this documentation update.
