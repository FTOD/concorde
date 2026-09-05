# Profile 8 refactor: implementation and validation

The approved proposal is implemented across runtime, distributable Protocol, canonical Operation
pairs, both agent projections, initialization/migration, Concorde's own Specs and the docsite.
The branch starts from main `e48f8aaaf201ab42a7058f5e5373529b6591e5f4`, through the approved proposal commit.

## Delivered behavior

- Domain scope nesting and Service/Module composition are independent. Components may participate
  in several Domains. Concorde registers 4 Domains, 5 Services and 8 Modules in 20 explicit Markdown
  memberships; each target's complete collection is the context authority, regardless of filename.
- Versioned universal principles and kind definitions are distributed to every project and pinned
  by initialization. Service Features and Module APIs have explicit local identities.
- All 22 public entry points are paired Operations. Their public Skills include complete request
  schemas; six internal roles are invoked only by the host. Configuration and runtime input are
  separate TypedValues in invocation schema 2; null configuration is resolved by the trusted host.
- Every stage receives one digest-bound snapshot in a fresh process. Only implementation receives
  owned code. Spec-only agents use private capsules; no ancestor, peer Spec, raw log or transcript
  is added implicitly. Structured Spec gaps retain target/context provenance across Domain coordination.
- Standard/fast loops run the same typed Operations through real LangGraph. Completion evidence,
  intent, Spec revisions, code and declared check inputs are checked before delivery. Failed/stale
  attempts remain inspectable; delivery removes the attempt without merging a branch.
- Reflection investigation is a read-only implementation invocation. The host preserves original
  reports/comments, validates HEAD and findings, enforces approval settings and starts fresh Spec
  cognition for implementation. Queue disposition remains independent of implementation completion.
- Explicit migration rejects active attempts and stale proposals, applies authored target/documents
  and rolls back invalid target state. Profile 7 is not admitted to the new agent runtime. Retained
  deterministic legacy readers have separate utility tests; they are not public cognitive bypasses.
- The docsite publishes exact registered memberships, independent navigation trees and a typed,
  interactive relationship graph. Fresh projects with no components or diagrams build successfully.
  Only declared diagram outputs are staged; candidate manifests and current source hashes gate promotion.

## Validation performed

| Gate | Result |
| --- | --- |
| Complete Python suite | 388 tests; 387 passed, 1 skipped |
| Complete docsite suite | 116 tests passed across 26 files |
| TypeScript typecheck | Passed |
| Production build and candidate promotion | Passed for Concorde and a freshly initialized project |
| Final public schema/projection regeneration | 20 affected Python tests passed afterward |
| Source package and self Spec validation | Passed |
| Self-hosted concorde-context | Resolved the complete Operation-host collection |
| Self-hosted concorde-validate | Executed check.context-runtime successfully through the public host |
| Whitespace/error check | git diff --check passed |

Python command: `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/concorde -t . -v`.
Docsite commands: `node node_modules/typescript/bin/tsc --noEmit`,
`node node_modules/vitest/vitest.mjs run`, and `node --import tsx scripts/build.ts`.
The CI-equivalent tests include actual installer provisioning/ownership/rollback and a separate
fresh subprocess importing only installed framework code for complete standard loops through both
Codex and Claude completion adapters. Their native model process and client probe are explicit test
doubles. LangGraph, typed admission, host policies, file changes, behavioral subprocess checks and
delivery are real. Native permission and completion-attestation/replay unit coverage is retained.

## Limits and migration notes

No Codex or Claude CLI is installed in this environment. The single skipped test is the existing
native Codex configuration-load check; live model/CLI execution was not exercised. No provider
sandbox enforcement is claimed on the basis of a process double.

The generic skill-creator quick validator rejects the repository's pre-existing `compatibility`
frontmatter extension. Concorde's canonical/projection validators accept and verify its actual
platform-specific format; the generic check is not reported as passed.

The test-contract migration is recorded in `tests/concorde/PROFILE8_TEST_MIGRATION.md`. Removed
assertions required public leaf Skills, Feature-path CLI arguments, code-visible planning or
Module-only fixed filenames and are superseded by Profile 8 behavioral acceptance coverage.
Open reflection R-049 is retained with its original human report and attribution; this refactor
does not invent a maintainer disposition or erase its history.
