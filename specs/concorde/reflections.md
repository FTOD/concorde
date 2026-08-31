# Reflections: Concorde

The project's remaining open reflection log: unresolved difficulties or problems coding agents met
while planning or implementing a feature, attributed to that feature and naming the source the
problem concerns. Closed entries are removed by explicit maintainer direction. Grammar:
[reflection-log contract](features/005-record-workflow-reflections/contracts/reflection-log.md).
Ordinary recording appends entries/occurrences; explicit rename or documentation reconciliation may
rewrite existing content while preserving stable valid `R-NNN` identifiers and contract shape.

### R-048 · Bare Python is unavailable during mirror verification

- **Phase**: fast-loop
- **Date**: 2026-08-31
- **Feature**: feature.concorde.install-with-spec-kit
- **Kind**: environment
- **Concerns**: pyproject.toml
- **Expected**: Repository verification uses the project-declared Python 3.11 environment and can
  compile both canonical and installed acceptance runtime sources.
- **Observed**: A combined mirror check invoked bare `python`, but this checkout exposes Python only
  through the project virtual environment.
- **Effect**: worked-around
- **Action**: Re-ran the exact compile and byte-equality checks with `.venv/bin/python`; both runtime
  sources compiled and the canonical/installed mirrors matched.
- **Improvement**: Keep repository verification commands aligned with the explicit interpreter in
  `[tool.concorde]` or use `.venv/bin/python` consistently.
- **Status**: open
