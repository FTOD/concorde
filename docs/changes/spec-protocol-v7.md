# Spec Protocol 7 migration: completed

The requested content/reading refactor is active throughout this checkout. This is a maintenance
record, not another specification authority. The canonical standard is under `protocol/` and its
accepted installed copy is bound by `.concorde/config.json`.

## Accepted design

The Protocol defines complete content and its human-readable subset. Reading is not a summary or a
renderer-selected approximation. Purpose, Usage, Design and Relationships lead the reading entry;
precise requirements, scenarios and interface agreements remain readable and normative. A publisher
chooses its pages, navigation, folding and interactions without changing that subset or agent scope.

Every registered Markdown reading file has a `.md.json` companion. The pair has one document ID and
one owner. Metadata records identity, mappings and implementation bindings and points to local
readable meaning rather than copying responsibilities or obligations. Several related entities can
share a coherent explanation through adjacent anchors on one line. Reading has no separate entity
inventory chapter. Scoped relationship diagrams may omit irrelevant inventory nodes but cannot
invent entities or unlabeled relationships.

Old-format runtime admission was removed, not retained as a compatibility branch. The explicit
read-only `concorde.spec.content_migration` planner remains available for inspecting Protocol-6
sources. It neither applies changes nor turns a mechanical conversion into semantic completeness.
Normal source and capability admission accepts only the current format.

## Active versions

| Agreement | Version |
| --- | --- |
| Spec Protocol | 7.0.0 |
| Framework project profile | 14 |
| Module registry | 5 |
| Document metadata / SpecResolution | 1 |
| Bound context snapshot | 5 |
| Discovery context | 4 |
| Agent, main, review and topology-author context wrappers | 3 |
| Canonical context-selection agreement | 3 |
| Docsite publication/build manifest | 20 |

The public capability invocation/result envelopes remain version 3. Unchanged request/response,
review-result and task-artifact contracts retain their own existing versions. Merely moving prose
or metadata did not arbitrarily increment interface behavior versions.

## Implementation

- `repository_base.py` contains shared grammar, values and deterministic structural/file operations,
  not an old inline-declaration backend. `DocumentUnitRepository` implements document-unit sources;
  the public `SpecRepository` adds installed, explicitly accepted Protocol admission.
- Every resolved unit contributes reading and metadata records with separate exact-byte digests,
  one owner and identical inclusion provenance. The selecting registration is bound to resolution
  identity. Module/document references still expand only once; scenario selection uses its owner.
- Host snapshots, discovery pools, capsules, source grants, topology author contexts and review
  changes carry both members. A metadata-only overlay selects the complete candidate unit, avoiding
  stale owner/metadata selection through an unchanged Markdown path.
- Author replacements are checked as one overlay and applied through digest-bound transactions.
  Referenced source members remain read-only. Topology authors return complete candidate-owned pairs;
  ordinary authoring cannot transfer document identity or ownership.
- Implementation entries must match the entity metadata union before they can supply an
  implementation grant. Neither document member can be implementation or external-reference
  material. Pending confirmation edits metadata only and keeps missing intentions explicit.
- Initialization, installer admission, Protocol binding, worker wire schemas, authoring prompts,
  Skills, package inventory checks, test fixtures and build expectations all use the new model.
- Framework-specific capability and Agent inventories moved into named metadata extensions.
  Behavioral descriptions and canonical interface schemas remain reading content.

## Specs and reading experience

All 17 Modules and 56 document units were migrated, yielding 112 source members. The pre-existing
Spec whitespace edits were used as part of the migration input, not discarded. The audit against
commit `99196255` preserves all 567 document/requirement/scenario/entity/contract identities and
their owners, and separately checks preservation of the 17 Module identities.

The resulting collection has 141 requirements, 182 scenarios, 185 entities, three canonical
structured contracts and four participant bindings. Format-specific scenarios were updated for the
new representation while retaining stable IDs. Existing valid behavioral obligations were retained;
pre-existing unrelated realization gaps remain honestly documented rather than silently waived.

Design and collaboration prose was reorganized instead of merely displaying the old entity JSON
as another inventory. Framework overview and Views diagrams are split into scoped views. The
primary-page table of contents shows major sections instead of every formal definition ID; those
definitions remain present, searchable and directly linked. No duplicate Files inventory is appended.
Metadata stays in a collapsed provenance disclosure with its own source path and digest.

The docsite validates metadata, identities, reading structure, precise definition syntax, scoped
relationship nodes/labels and canonical examples through a bounded offline schema vocabulary.
Missing partners, duplicate JSON keys, invalid examples, remote schema references and unsafe
external-reference overlap reject publication. Browser checks found a Mermaid reserved-word node
that structural admission previously missed; it was fixed and a regression now rejects that form
before publication. Dark-theme link colors were adjusted for readable contrast.

The README, workflow guide, Protocol chapters/templates and docsite documentation describe the
active model. The README screenshot was refreshed from the local production build; the obsolete
standalone-graph screenshot is labeled historical rather than presented as an active feature.

## Verification

- Full Python suite: **827 tests**, zero failures/errors; **10 Studio-server tests skipped** under
  their existing environment conditions.
- Docsite suite: **188 tests across 15 files**, all passed, including a freshly initialized consumer
  receiving and building the packaged adapter.
- Maintained TypeScript typecheck: passed.
- Changed Python files: fresh Pyright CLI reported zero errors/warnings; active LSP probes of the
  changed/new Python and core TypeScript sources also reported zero diagnostics.
- Framework build and `build --check`: passed.
- `python3 scripts/concorde.py validate`: success, zero errors. **72 existing coverage/test-listing
  warnings remain**; these are not hidden or counted as passes.
- Flow Spec check: zero findings.
- Offline source/identity audit against `99196255`: passed, including 434 local reading links and
  complete paired context identities.
- Production docsite build and internal route/anchor validation: passed.
- Chromium: Framework, Views and Harness reading checked in light and dark themes; all scoped
  diagrams were scrolled into view and rendered (2, 3 and 1 respectively), without runtime errors,
  obsolete sections or document overflow. Views also passed 390px mobile checks in both themes.

These results verify this refactor and its regression boundaries. They do not claim universal
semantic completeness, fulfillment of unrelated pre-existing design gaps, deployment to the public
website, a live model review or lifecycle delivery. No public-site deployment or primary-delivery
operation was performed; this was developer-authorized maintenance in the original worktree.
