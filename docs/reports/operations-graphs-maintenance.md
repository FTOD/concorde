# Operations and graphs maintenance verification

## Scope and revision

- Worktree: `/home/zhenyu/concorde.worktrees/concorde1`.
- Initial branch: `spec-restructuring`; retained branch: `refactor/operations-graphs`.
- Baseline: `7af5a831220091693695fa92b71079d9f10c5bd7`.
- Verified implementation commit: `206517fe59005d3f8cd62f5cd4fd057b5872d814`.
- This session completed an inherited, uncommitted migration as direct maintenance. It did not
  switch worktrees, invoke a Concorde business graph, delegate model work, load project-local Skills
  as session instructions, merge, push, run delivery or remove the worktree.

## Result

The root Spec, concepts and homepage now introduce Operation as the sole executable entity,
with complete State/effect/policy contracts and trusted Host/Harness enforcement. The Operations
hierarchy includes composed development and specification providers while preserving the distinction
between Module ownership, executable composition and context references.

Current authoring sources, Python APIs, metadata, launcher, graph inspection, tests and build inputs
use Operations and LangGraph graph/node vocabulary. The cutover uses Framework 8.0.0, Protocol 10,
Profile 15 and Workspace Protocol 16. The stale constitution index now points to current authorities.

[Migration policy](../changes/operations-graphs.md) records the interface/storage gates, the 14
explicit identity replacements, the 620 retained identity strings and the ten retained provider
entity identities whose ownership moved to Operations. Every baseline identity has a current
counterpart. Old worktree progress is refused; immutable Issue observations remain historical
read-only records; usage diagnostics have explicit current/historical/unsupported format reporting.

## Deterministic verification

| Check | Result |
| --- | --- |
| `python3 scripts/concorde.py build` | Passed; projections generated from authoring sources. |
| `python3 scripts/development/init-references.py` | All four pinned reference checkouts prepared; no vendored source changes staged. |
| `python3 scripts/concorde.py protocol-manifest --write --bind-project` | Accepted and refreshed the exact current Protocol assets and project binding. |
| `python3 scripts/concorde.py build --check` | Passed, including after the implementation commit. |
| `python3 scripts/concorde.py validate` | Success, 0 errors, 0 warnings. |
| `.venv/bin/python scripts/development/check-graph-specs.py` | 0 findings. |
| `.venv/bin/python scripts/development/check-spec-v5.py` | Passed the current Protocol-10 audit. |
| `python3 scripts/development/run-tests.py --jobs 4` | 860 tests in 67 modules; 0 failures, 0 errors, 11 skipped. |
| `npm --prefix docsite run check` | Typecheck, all 224 tests in 17 files, validation and production build passed. |
| Post-commit fresh-clone bootstrap tests | All 3 passed against the committed Operations implementation. |
| Direct executable launcher `concorde-main --runtime-check` | Passed with Python 3.11.15 and LangGraph 1.2.11; no model invocation. |
| Targeted active LSP probes | No errors on the probed migration-critical runtime paths, including State adapters, Host, Studio, Issue store, wire admission and usage accounting. |

The 11 skipped Python checks were ten opt-in live Studio-server tests and one native Pi-worker
integration test. These results do not establish live model effectiveness or those unexecuted
integration behaviors. Targeted LSP results are not a claim of repository-wide lint/type cleanliness;
existing test-fixture style findings were triaged separately from runtime failures.

Changed Python and web source files were formatted with the selected Ruff/Biome formatters before
verification. A second formatting pass was a no-op; both final passes preserved the already-tested
bytes. The staged diff and whitespace checks were inspected before committing, the launcher's
executable mode was preserved, and the post-commit worktree was clean.

No files under `reference/`, `generated/`, `.claude/skills/` or `.agents/skills/` were staged.
Installed Protocol copies were refreshed through the binding command, not edited directly. The
third-party API and historical-material exceptions are named in the migration policy rather than
hidden behind a global search-and-replace claim.

## Evidence limits

This was direct maintenance with deterministic tests and source/spec inspection, not a Concorde
lifecycle run or an independent model review. Structural success does not prove semantic
completeness, and no lifecycle readiness, delivery or primary-merge evidence is claimed. The branch
and worktree remain available for subsequent human review.
