# Validation Record: Concorde Core Workflow Refactoring

**Feature**: `feature.concorde.core-workflow`
**Attempt state**: active
**Evidence status**: partial

This record belongs to the current temporal implementation attempt. Feature 003 owns proof that the
same workflow is installed into a clean project from release archives.

## Automated Evidence

### Core workflow

- `uv run python -m unittest discover -s tests/concorde -p 'test_*.py' -v`: **87 tests passed**.
- The suite covers review-first initialization; one-level root/child context; deterministic nested
  feature placement proposals; atomic selection and explicit resume; complete durable/temporal phase
  paths; architecture readiness; contract example conformance; scenario crossings; bounded active
  feature context; evidence/freshness findings; three-run determinism; and source immutability.
- Codex skills and Gemini slash-command presentations expose equivalent five-command Concorde intent.
  Feature 003 separately proves those surfaces from built archives.
- `uv run python extensions/concorde/scripts/python/concorde.py --project-root . validate --format json`
  returned `success` over **35 canonical artifacts**, with zero errors, warnings, or informational
  findings. Source digest:
  `sha256:8d100c695fedb2fb64d1cbb2664914e86feb17031d1577f9b487e8d0bd7f639c`.
- The focused self-architecture and core-workflow acceptance run passed **3/3 tests** after the
  installed-surface/runtime/workspace explanation was expanded.

### Feature diagram and documentation

- `diagrams/core-workflow-components.json` passed all **9/9 Archify showcase checks** with zero
  composition errors and zero warnings.
- Delivery produced `generated/architecture/concorde-core-workflow-components.html` from source digest
  `003e4b70bfc18ec3e38fc4327404d789c1d6d2d74ee9e34789a559333a5877a2`; artifact digest is
  `4d82566c16c8afb841fe72c12b83cf7dcb12febdbdbe1332bb4766817da60414`.
- Archify visual-check was attempted but skipped because Chrome/Chromium is unavailable. The receipt
  truthfully retains `visualReview: pending`; containment, light/dark review, and perceptual polish
  are not claimed.
- `npm run check` in `docsite/` passed TypeScript, **14 test files / 29 tests**, validation of
  **31 pages** with **31 excluded sources** and zero errors, and the optimized production build.
  The canonical Feature 001 page automatically embeds the declared diagram.

## Cross-feature Distribution Handoff

- The handoff defines nine normal Spec Kit phase roots and five Concorde command intents.
- Feature 003 archive and clean-project tests compare installed adapter/runtime bytes with this
  maintained handoff and execute all fourteen registered surfaces without checkout fallback.

## Pending Human or Browser Evidence

- SC-001 provider-placement pilot: pending real participants.
- SC-007 authority mental-model pilot: pending real participants.
- SC-008 explicit maintainer approval of the acceptance architecture changes: pending.
- SC-010 browser containment/theme/perceptual portion: pending a Chrome/Chromium environment and
  human inspection; deterministic showcase validation and docsite freshness already pass.
- SC-011 installed-layer and workspace-authority comprehension pilot: pending real participants.

Automated tests must not be used to infer these outcomes.
