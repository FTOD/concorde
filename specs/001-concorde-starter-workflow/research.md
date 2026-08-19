# Phase 0 Research: Concorde Starter Workflow

## Decision 1: Distribute through independent components plus a native bundle

**Decision**: Publish `concorde-core` as one Spec Kit preset archive, `concorde` as one extension
archive, and `concorde-starter` as one bundle artifact that pins those exact versions. Publish matching
preset, extension, and bundle catalog entries. Development acceptance uses install-allowed catalogs
served from localhost; release catalogs use approved HTTPS artifact URLs.

**Rationale**: Spec Kit bundles are composition manifests. Their standard resolver installs component
references through the existing primitive managers, and the community bundle guide explicitly
requires authors to document any component catalogs a bundle needs. This preserves native preview,
installation, provenance, update, shared ownership, and removal behavior. It also lets each component
be versioned and tested independently.

**Alternatives considered**:

- Embed component directories in the bundle and add a Concorde installer. Rejected because the
  standard bundle installer does not treat arbitrary packaged directories as component sources, and a
  second installer would violate Spec Kit-native composition.
- Patch or fork Spec Kit to interpret local component paths. Rejected for the starter slice because
  catalogs already satisfy the requirement through a supported public mechanism.
- Require users to install the preset and extension manually before the bundle. Rejected because
  independently installed components would not be safely attributed to the bundle and the requested
  one-step lifecycle would be lost.

## Decision 2: Use append-only preset fragments

**Decision**: The preset provides append-strategy fragments for `spec-template`, `plan-template`, and
`tasks-template`. The fragments add Concorde metadata, architecture review, and architecture/evidence
task guidance without replacing the lower-priority templates.

**Rationale**: Presets are the supported mechanism for changing how core Spec Kit phases produce
artifacts. Append composition retains Spec Kit's canonical sections and remains stackable with other
presets. Using the three artifact templates maps directly to FR-005 through FR-008.

**Alternatives considered**:

- Replace core commands. Rejected because it would unnecessarily duplicate command logic and make
  compatibility fragile.
- Create a dedicated Concorde workflow. Rejected because the specification explicitly excludes
  workflows and reusable steps from the first bundle.
- Generate a second feature document beneath `architecture/`. Rejected because `spec.md` is the one
  canonical feature specification.

## Decision 3: Keep agent commands thin and runtime behavior deterministic

**Decision**: The extension owns three Markdown command definitions and a dependency-free Python 3.11
runtime. Skills inspect user intent and coordinate approval, but context projection and validation are
performed entirely by the runtime. Initialization has separate proposal and apply modes.

**Rationale**: Extension commands are rendered by Spec Kit for each active integration, including
Codex `SKILL.md` output and slash-command agents. Keeping the runtime agent-independent gives every
surface the same inputs, outputs, and failure behavior. Python 3.11 matches Spec Kit's own minimum
runtime and avoids requiring Node or a new package manager in installed projects.

**Alternatives considered**:

- Put validation rules only in the prompt. Rejected because LLM results cannot satisfy deterministic
  repeatability or cross-agent parity.
- Implement the runtime in TypeScript. Considered because it could later share types with the
  Docusaurus adapter, but rejected for this starter because Node is not a Spec Kit runtime guarantee
  and Architecture Core must stay independent of publication tooling.
- Add a global `concorde` executable. Deferred because the first user-facing surface is explicitly
  Spec Kit agent commands; the installed extension can invoke its project-local runtime directly.

## Decision 4: Use a constrained, portable architecture source profile

**Decision**: Continue using Markdown with YAML front matter for modules, features, scenarios, and
contracts, and Archify JSON for one-level views. The starter runtime implements the documented
front-matter subset it needs using the Python standard library and reports unsupported constructs
instead of guessing. `.concorde/config.json` identifies the architecture root and source-profile
version.

**Rationale**: These formats match the constitution and existing Concorde sources. A constrained
profile can be read without relying on PyYAML being importable from a separately launched system
Python, while still keeping sources readable and compatible with ordinary YAML tools. Explicit
profile versioning allows a future parser or schema library without silently changing meaning.

**Alternatives considered**:

- Depend on PyYAML from the Spec Kit installation. Rejected because `specify` may run from an isolated
  environment that is not visible to the Python interpreter launched by an agent command.
- Store all maintained intent in JSON. Rejected because prose belongs in Markdown and existing sources
  already use front matter.
- Infer structure from prose. Rejected because validation and context projection need explicit,
  machine-readable relationships.

## Decision 5: Define one stable architecture service result envelope

**Decision**: All runtime operations emit schema-versioned JSON with `operation`, `target`, `status`,
`artifacts`, `findings`, and operation-specific `result`. Findings contain stable rule ID, severity,
project-relative source location, message, and remediation. JSON keys and arrays use deterministic
ordering; timestamps are excluded.

**Rationale**: One envelope makes agent integration, fixtures, and later documentation adapters share
a contract. Stable sorting and omission of volatile fields directly support byte-equivalent repeated
validation. Project-relative paths keep output portable and prevent environment details from becoming
observable behavior.

**Alternatives considered**:

- Human-readable output only. Rejected because tests and downstream tools need a normative result.
- Separate incompatible response formats for each command. Rejected because shared status and
  diagnostic semantics would drift.
- Include execution timestamps. Rejected because they break reproducibility without helping the
  starter workflow.

## Decision 6: Make initialization review-first and non-destructive

**Decision**: `init --propose` reads project context and returns a proposed root package without
writing. `init --apply <proposal-file>` validates the accepted proposal, refuses conflicting existing
sources by default, and writes through a stage-then-promote operation. Re-running against a complete
package reports it unchanged.

**Rationale**: The feature and constitution require human review of AI-proposed architecture and
explicit approval before maintained intent changes. Separating proposal from apply makes that boundary
testable. Refusing conflicts avoids treating an agent's suggestion as higher authority than existing
sources.

**Alternatives considered**:

- Prompt interactively inside the runtime. Rejected because prompts are agent-specific and difficult
  to test deterministically.
- Merge existing documents automatically. Rejected because semantic merges could silently rewrite
  maintained intent.
- Overwrite with a `--force` default. Rejected as unsafe; any future force path must present exact
  changes and require explicit approval.

## Decision 7: Resolve bounded context from stable IDs, never path depth alone

**Decision**: Build an index of declared IDs and relationships, resolve a requested module directly or
resolve a feature to its providing module, then return only that module's features/contracts, its
immediate child summaries/contracts, permitted external actors, corresponding view scenarios, and
adjacent refinement links. Deeper items appear only as stable navigation references.

**Rationale**: Filesystem nesting can mirror the hierarchy but stable IDs are the contract. Explicit
relationship traversal enforces the one-level rule for both regular and adapted source layouts and
avoids exposing grandchildren merely because their files are easy to find.

**Alternatives considered**:

- Return every descendant document. Rejected because it defeats bounded reasoning.
- Use directory depth as the sole hierarchy. Rejected because the constitution permits an explicit
  deterministic path mapping and requires references to remain authoritative.
- Let the agent summarize selected files. Rejected because inclusion boundaries would vary by agent.

## Decision 8: Validate rule groups in a stable order

**Decision**: Validation runs in this order: source/profile parsing, identity uniqueness, reference
resolution, containment and cycles, feature ownership/refinement, contract completeness and usage,
scenario participants/interactions, one-level view visibility, and evidence status. Each group emits
sorted findings and never modifies sources.

**Rationale**: Later rules depend on a valid index, so a fixed dependency order prevents cascades from
becoming nondeterministic. The groups cover FR-014 and the highest-value rules in the prototype
reference. Unknown evidence remains a valid explicit state, not a passing implementation claim.

**Alternatives considered**:

- Stop at the first error. Rejected because maintainers need a complete actionable report.
- Auto-correct broken references. Rejected because validation must not silently change intent.
- Treat missing evidence as failure or success. Rejected because both conflate architecture intent
  with implementation evidence.

## Decision 9: Verify actual agent artifacts and command behavior

**Decision**: Acceptance initializes one temporary project with Codex skills mode and one with a
slash-command integration, installs the released component archives via the bundle, checks the native
registered artifacts, and invokes or simulates the command contract against the same runtime fixtures.

**Rationale**: Inspecting extension source alone does not prove Spec Kit registration or syntax
translation. Clean installed fixtures cover the active integration, command discovery, project-local
paths, and removal behavior required by FR-010 and FR-017.

**Alternatives considered**:

- Test only Codex because this repository uses Codex. Rejected because the specification requires one
  slash-command portability target.
- Snapshot only generated command files. Rejected because discovery without successful primary
  behavior is insufficient.
- Hard-code `/speckit.concorde.*` inside command bodies. Rejected because skills agents use different
  invocation syntax.

## Decision 10: Treat release and lifecycle evidence as first-class outputs

**Decision**: Release verification produces component archives, a reproducible bundle artifact,
catalogs with matching hashes/versions, and a validation record mapping requirements to tests. Clean
fixtures compare the expanded info plan with installed records, run three idempotent installations,
exercise a compatible update and an injected failure, and verify safe removal.

**Rationale**: The product is the installable workflow, so source-unit tests alone cannot demonstrate
completion. Matching manifest pins, catalogs, artifacts, registries, and lifecycle outcomes catches
the integration failures most likely to make the bundle unusable.

**Alternatives considered**:

- Hand-build archives for each test. Rejected because release and acceptance could exercise different
  bytes.
- Use mocks for the entire bundle lifecycle. Rejected because that would not prove native Spec Kit
  behavior.
- Commit installation timestamps into reproducibility checks. Rejected; archive bytes must be stable,
  while project-local lifecycle timestamps are provenance rather than build content.

## Unknowns Resolved

No `NEEDS CLARIFICATION` items remain. The initial implementation uses Python 3.11, standard Spec Kit
catalog distribution, append-only preset fragments, a strict architecture-source profile, and the
schema in `contracts/architecture-service.schema.json`. Broader Spec Kit versions, additional agent
integrations, generic JSON Schema evaluation, rendering, and publication remain explicitly deferred.
