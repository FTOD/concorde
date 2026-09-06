# Profile 8 refactor: implementation and validation

The approved proposal is implemented across runtime, distributable Protocol, canonical Operation
pairs, both agent projections, initialization/migration, Concorde's own Specs and the docsite.
The branch starts from main `e48f8aaaf201ab42a7058f5e5373529b6591e5f4`, through the approved proposal commit.

## Delivered behavior

- Domain scope nesting and Service/Module composition are independent. Components may participate
  in several Domains. Concorde registers 4 Domains, 5 Services and 8 Modules in 20 explicit Markdown
  memberships; each target's complete collection is the context authority, regardless of filename.
- Every direct `participates_in` edge has one machine-readable Domain-local declaration with stable
  target ID, kind, responsibility, selection condition and relied-upon promises. Concorde's three
  directly participating Domains contain all 19 views. Deterministic validation aligns them with the
  registry; missing entries stop context solving with Spec gaps and inconsistent entries conflict.
- Versioned universal principles and kind definitions are distributed to every project and pinned
  by initialization. Service Features and Module APIs have explicit local identities.
- All 22 public entry points are paired Operations. Their public Skills include complete request
  schemas; seven internal roles are invoked only by the host. Configuration and runtime input are
  separate TypedValues in invocation schema 2; null configuration is resolved by the trusted host.
- New agent-backed tasks first use a separate main coordinator. It starts at the entry Domain or
  Service and may append only referenced Domain/Service Specs; Module Specs and code are rejected.
  Each selected target worker starts fresh with one digest-bound snapshot. The public
  `concorde-main` Operation replaces standalone ask: its default `ask` action may route several
  readers and synthesize typed results; other Operations route one owner, using a Domain for
  cross-target mutation. Public context inspection returns membership/digests without bodies.
- `concorde-main` also owns steady-state topology evolution. Its coordinator designs a complete
  registry from exact topology metadata, all kind definitions and admitted Domain/Service bodies,
  but no Module body or code. Explicit maintainer acceptance precedes private target-local Spec
  authoring; an in-memory overlay must validate before the host stores exact proposed bytes. A
  second acceptance applies that digest/before-digest-bound artifact atomically.
- Only implementation receives owned code. Spec-only agents use private capsules; no ancestor,
  peer Spec, raw log or transcript is added implicitly. Structured Spec gaps retain target/context
  provenance across main discovery and Domain coordination.
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
| Complete Python suite | 406 tests passed |
| Complete docsite suite | 116 tests passed across 26 files |
| TypeScript typecheck | Passed |
| Production build and candidate promotion | Passed for Concorde and a freshly initialized project |
| Final public schema/projection regeneration | Package validation and complete Python suite passed afterward |
| Source package and self Spec validation | Passed |
| Self-hosted concorde-context | Returned the exact Operation-host membership/digests without document bodies |
| Self-hosted concorde-validate | Executed check.context-runtime successfully through the public host |
| Whitespace/error check | git diff --check passed |

Python command: `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests/concorde -t . -v`.
Docsite commands: `node node_modules/typescript/bin/tsc --noEmit`,
`node node_modules/vitest/vitest.mjs run`, and `node --import tsx scripts/build.ts`.
The CI-equivalent tests include actual installer provisioning/ownership/rollback and a separate
fresh subprocess importing only installed framework code for complete standard loops and main
discovery/reader/synthesis through both Codex and Claude completion adapters. They also exercise
topology design, both acceptance gates, private Module authoring, stale/tampered proposal rejection,
read-only policy description, participant-aware topology tasks, participant alignment, pre-planning
gaps, Domain author rollback, overlay validation and atomic application. Their native model process
is an explicit test double. LangGraph, typed admission, host policies, file changes, behavioral
subprocess checks and delivery are real. Native permission and completion-attestation/replay unit
coverage is retained.

## Limits and migration notes

Codex CLI 0.153.4 and Claude Code 2.1.260 are present, but live model execution was not exercised.
The tests use process doubles for model completions, so no provider sandbox-enforcement claim rests
on those doubles; native configuration parsing and host-side policy/evidence checks remain covered.

The generic skill-creator quick validator rejects the repository's pre-existing `compatibility`
frontmatter extension. Concorde's canonical/projection validators accept and verify its actual
platform-specific format; the generic check is not reported as passed.

The test-contract migration is recorded in `tests/concorde/PROFILE8_TEST_MIGRATION.md`. Removed
assertions required public leaf Skills, Feature-path CLI arguments, code-visible planning or
Module-only fixed filenames and are superseded by Profile 8 behavioral acceptance coverage.
Open reflection R-049 is retained with its original human report and attribution; this refactor
does not invent a maintainer disposition or erase its history.
