```concorde-document
{
  "id": "document.harness.context",
  "owner": "module.harness",
  "main_visible": true
}
```

# Context resolution

This document defines the four kinds of context a Harness freezes for one invocation and the
host-internal interface that resolves them. The Spec Protocol defines Spec context and
implementation context; this Module realizes those definitions and adds the two Framework kinds.

## Context kinds

| Kind | Content | Required for |
| --- | --- | --- |
| Spec context | The selected Module's complete resolved Markdown context, exactly the Protocol's `Context(M)`; a scenario focus changes the question, not the membership. | Every Module-bound invocation. |
| Implementation context | The Protocol's `ImplementationContext(M)`: the listing entries the selected Module's own entities declare, exact files and directory prefixes alike, and the files those entries currently bind. Every phase can see the declared entries and bound file names with their owning entity and pending status; only code-writing and code-review phases receive file contents, in their declared subsets. | Entries and file names: every phase. File contents: code-writing and code-review phases only. |
| Capability context | The contracts of the Capabilities and Tools the invocation may use, as admitted by its Harness and constraints. Descriptions given to the model and bindings accepted by the executor resolve to the same contracts. | Optional; empty for every current Agent. |
| Task context | The task and constraints, the stage artifacts admitted for this phase, such as a plan, implementation tasks, a review result or a reflection selection, and the frozen workspace lifecycle metadata. | Every invocation; stage artifacts are optional. |

A kind may be empty for a phase, but the frozen closure is never empty. Agent instructions, the
Protocol rule bundle and installed Skills are not context: instructions belong to the Agent
definition and are injected beside the context, and a Skill is the developer-facing projection of
a global or lifecycle capability. The snapshot identity covers every admitted byte of every kind.

## Context snapshot resolution

`resolve_context` freezes one Module's Spec context with its task context, and, for code phases,
its implementation context, into a private `concorde-context-snapshot@2`. `resolve_discovery_context`
freezes several explicitly selected complete Spec contexts for the global coordinator.
`recheck_context` and `recheck_discovery_context` reject reuse after any admitted input changed.
The sections below define the exact inputs, records, phases and errors.

The required Profile 12 boundary below is Module-oriented: it accepts a Module `target_id` and an
optional local scenario `focus_id`. Its project contract files implement the Protocol's Spec and
Context mapping: the one-level union of owned and explicitly referenced documents, including inline Mermaid architecture
fences and entity declarations. The independent Protocol supports only Module and scenario
queries; a scenario query resolves to its providing Module's same complete context, so this API
accepts no other `target_id` kind.

The context Module is host-internal: `resolve_context` produces a private ContextSnapshot behind
the executable boundary, and no Skill returns it or a redacted projection of it. Its
inputs are target_id, task, optional focus_id/constraints/phase (default ask). Other phases are
specify, plan, tasks, implementation, spec-review, code-review, validate, deliver and context-solve.
Unknown fields/versions/IDs are rejected by the host's own admission, never by an agent-facing
schema. `describe-policy` mode on any capability previews the exact grant an execution would receive —
context_id, read/write paths and a policy digest, printed to stderr — without launching an agent,
mutating project state, or exposing document content, instructions, stage inputs, implementation
locators or the reusable cognitive snapshot itself.

The host-internal Python call is:

```python
resolve_context(repository: SpecRepository, target_id: str, *, phase: str = "ask",
                task: str = "Understand this Spec", focus_id: str | None = None,
                constraints: tuple[str, ...] = (), instructions: str = "",
                stage_inputs: tuple[dict, ...] = (), workspace: dict | None = None,
                mode: Mode | None = None
                ) -> ContextSnapshot
```

The caller supplies a fresh, successfully admitted repository and correctly typed arguments.
An unsupported phase raises `SpecError/invalid_phase`; a blank task raises `invalid_input`;
target/focus and repository/Protocol failures use the Spec registry's declared selection errors. Unsupported
stage-input IDs raise `SpecError/incompatible_handoff`, and malformed typed stage values raise
`TypedDataError(ValueError)` with `code`, JSON-pointer `field` and message. The resolver returns no
partial snapshot on failure. `instructions` is the caller's admitted role instruction text;
`workspace=None` obtains current host lifecycle metadata. A supplied workspace is an explicit
trusted-host frozen observation, not a caller task field or replacement authority.

`ContextSnapshot(serialized: str)` is frozen; `.serialized` is canonical JSON, `.value` decodes a
new dictionary and `.id` returns its `context_id`. The dictionary is the data of the private
`concorde-context-snapshot@2` TypedValue; wrapping it adds the ordinary
`{type_id, schema_version: 2, data}` envelope. Its exact fields are:

- `schema_version: 2`, `context_id: sha256`, `target_id: str`, `kind: module`,
  `focus_id: str|null` (a scenario ID when present), `phase: str`, `task: str`,
  `constraints: list[str]` and `instructions: str`.
- `protocol_binding: {version: str, digest: sha256}` and
  `protocol: list[{path, digest, content}]`, with the principles and Module kind documents in that order.
- `spec_resolution: SpecResolution`, the canonical record defined by
  [Spec resolution](../spec/registry.md#stable-id-spec-context-queries). Its sources include full
  content, sole owners, byte digests and all inclusion reasons. There are no target/shared partitions.
  Inline diagrams already occur in those source bytes and add no separate field.

- `implementation_entries: list[{path: str, entity_id: str, pending: bool, directory: bool}]`,
  present for every phase: the listing entries the selected Module's own entities declare, in
  registered order, with the owning entity, whether the entry is still declared pending, and whether
  it is a directory prefix. A directory entry keeps its trailing `/` in `path`.
- `implementation_files: list[{path: str, entity_id: str, pending: bool}]`, present for every
  phase: the existing regular files those entries currently bind, with each directory entry expanded
  and each file attributed to the entity whose most specific entry covers it, plus any exact file
  still declared pending. Non-code phases see only these names, never file contents. Because the
  entries and not the expanded names are the declaration, a code writer may create a file below a
  listed directory; a recheck that verifies implementation inputs still rejects a changed file set
  for every other phase.
- `stage_inputs: list[TypedValue]`, `implementation_artifacts: list[{id: str, path, digest: sha256}]`
  and `workspace`, the lifecycle record described below. `implementation_artifacts` is populated
  only for the `implementation` and `code-review` phases, with the current content digest of each
  entity-bound file; code bytes are never embedded in the snapshot.

Spec and artifact paths are canonical project-relative POSIX paths; workspace locations are
absolute host identity paths. Sha256 values use the `sha256:` prefix and 64
lowercase hexadecimal digits. Arrays may be empty except the admitted nonempty document closure
and the phase-appropriate Protocol records, which supply the principles and Module kind documents
to every phase alike. Every listed snapshot field is required; unknown fields are rejected
at typed host admission. The digest covers the complete canonical dictionary except `context_id`.

Ordinary `stage_inputs` are version-1 TypedValues with these payloads:
`concorde-plan-artifact` has `plan: nonblank str`; `concorde-implementation-task` has that same
`plan` and `tasks: list[{id, target_id, description, acceptance, complete}]`, with nonblank strings
and a boolean `complete`; `concorde-reflection-selection` has `head: nonblank str` and
`records: list[{id: str, path, digest: sha256, content: str}]`, with nonblank string fields.
`concorde-task-scope-feedback` has `tasks_digest: sha256` and `reason: "implementation_boundary"`; only task authoring admits it with prior tasks and the plan. It carries no implementation contents or raw check logs.
`concorde-task-identity-constraints` has `reserved_task_ids: list[nonblank str]`, unique and possibly
empty. Only task authoring admits it and requires it alongside the plan. Development supplies all
retained historical IDs and the current list for repair; the IDs reserve identity without adding
software obligations or code contents. The snapshot digest covers this input like every stage artifact.
These records are closed objects. A stage input conveys only its declared content, not authority.
Only `tasks` and `implementation` additionally admit `concorde-review-result@1`, carrying a typed
review's target/focus, context/input identities, spec/code mode, status, representative tasks,
findings, gaps, answer, revision and `semantic_completeness: "not_proven"`. Findings have ID,
blocking/advisory severity, owning target/document, path and nullable line location, contract,
problem and affected task. Revisions bind Spec/implementation digests and nullable base/head commits.
This service enforces the declared type and phase; the Development host independently verifies
current, target-bound code-review repair evidence and the bounded repair policy before supplying
it. This addition preserves the existing review-driven repair edge without granting raw code reads.

The private snapshots also carry declared `workspace` lifecycle metadata: current and
primary worktree identities/branches, current change phase/status/outcome, its reported gaps and
component progress, and basic information about live linked worktrees. This contains no target plan,
implementation body or hidden Spec document. Paths and task summaries identify candidate work, not
permission to read another worktree. A secondary context is explicitly a candidate revision.
The record is computed from the invocation's own project root, the worktree at the entry process's
working directory, and each linked worktree's summary comes from its `.concorde/worktree.json` alone.
The host rechecks the current workspace identity and lifecycle after a stage; other worktrees' frozen
summaries may advance independently. Topology proposals retain their originating workspace observation
so a committed-base handoff can recheck the same admitted Spec and design inputs in its candidate.

That closed record has `kind: primary|change|unversioned`, `current_worktree: str`, nullable string
`current_branch`, `primary_worktree`, `primary_branch`, `change_id`, `phase`, `status` and `outcome`,
plus arrays `gaps`, `components` and `active_worktrees`. A gap has nonblank `question`, `blocked_step`
and `needed_contract`, and optional `target_id` and sha256 `context_id`. A component has nonblank
`target_id`, `spec_status`, `implementation_status` and nullable `outcome`. Each active-worktree
summary has `path: str`, nullable `branch`, `head`, `change_id`, `target_id`, `phase` and `outcome`,
booleans `managed` and `locked`, `task: str` (possibly empty) and nonblank `status`.

The `spec_resolution` record freezes owned and directly referenced documents once per physical
file, sorted by path. A referenced Module contributes its owned documents only, never its own
references. Ownership and source provenance remain distinct from inclusion. Changing either the
selected references, included ownership, or document bytes invalidates context and review evidence,
even if the set of paths remains unchanged. Only the selected Module's own entity bindings supply
implementation entries, file names and any phase-authorized contents.

The context identity covers all inputs apart from its own identity field. The wire field `protocol`
contains the distributed principles bundle and Module kind definition. This bundle includes
both Concorde Spec Protocol requirements and the Framework execution profile; the field name does
not classify all runtime rules as Spec organization rules.
Concorde Spec Protocol 5.0.0 defines the Spec context and implementation context this service
resolves. The distributed rule bundle also includes the separately authored Framework execution
profile, including P10 handoffs. The resolver verifies the build is
fresh, then admits Protocol assets rendered into `generated/protocol/` from the exact project-bound
manifest, without discovering root AGENTS.md/CLAUDE.md. The installed root entry serves
outer user sessions only. Package update leaves an old binding unchanged and resolution rejects
`protocol_mismatch` until the developer explicitly accepts the installed version and manifest
digest in `.concorde/config.json`. Changed bindings require new contexts.
Stage inputs must be versioned plan, implementation-task, task-identity-constraints,
task-scope-feedback, reflection-selection or review-result
values (the last only accompanies a bounded dev-loop code-review repair round: see
`concorde-dev-loop` in the Development Module's host boundary). Code bytes
are not embedded in a snapshot; implementation and the dedicated read-only code-review phase have
code references and separate host-issued implementation grants. Spec review has no code references.
The review host adds a separately typed, target-scoped changes/revision input; ordinary stage_inputs
cannot smuggle patches or arbitrary artifacts into a Spec worker.
Membership, configuration, Protocol or admitted bytes changing after resolution invalidates reuse.

Main discovery admits explicitly selected complete Module collections for global reasoning,
questions and routing. A new admitted collection produces a new context identity and a fresh
coordinator invocation. Python injects deduplicated original documents, already carrying their
inline Mermaid fences, with per-Module resolution provenance and original owners. The coordinator answers directly from those
complete contexts. Implementation source bodies never enter this context.
During design-topology, exact registry metadata additionally describes Module composition,
dependencies and entity listing entries. It supplies structure, not hidden behavioral meaning.
After the design is accepted, each fresh Module author receives the proposed descriptor and its
complete resolved context. Candidate sources enter through explicit ownership/references only.
An author may replace only that Module's owned documents; referenced definitions remain read-only.
The owner authors a shared-interface change once. Every old or candidate context consumer receives
a separate compatibility review, retaining local obligations and pointing to the same canonical
definition. A transfer assigns exactly one candidate owner and preserves stable IDs and links.
The host validates all replacements and declarations atomically before exposing an application.
Ownership/reference changes invalidate affected snapshots even when source paths stay equal.
Ordinary owner authoring can update content and diagram fences while preserving metadata;
document ID, owner, visibility or registered references change through topology reconciliation.

Context solving is a separate fresh spec-engineer context-solve mode, run directly by the
`concorde-context-solve` stage capability or as `concorde-plan`'s preliminary sufficiency check. It returns
sufficient, spec_incomplete, unsupported, conflicting or failed. A gap
must name question, blocked_step and needed_contract. It cannot fetch missing context. Known missing
runtime fields fail admission; semantic incompleteness is task-specific, never universally proven.
Before launching that assessor for a Module, the host deterministically compares the selected
Module's dependency entries with its registry relationships. A missing direct entry returns a
Module-owned structured Spec gap; malformed, duplicate, unknown, unrelated
entries return a conflicting outcome. Both stop planning, and no relationship inventory is injected
into the worker snapshot.

## Context selection agreement

This is the sole canonical definition of the selection agreement. Development references this
owned document and declares its local binding. Version 2 changes context semantics; version 1
membership-based snapshots are incompatible and must be resolved again.

This agreement uses the offline object-schema subset: `type`, `properties`, `required`,
`additionalProperties` and `minLength` have their ordinary JSON Schema meanings. All properties
listed as required must occur, unknown properties are rejected, and string lengths are measured
in characters. The example’s target ID illustrates a separately registered consumer project.

```concorde-contract
{
  "id": "contract.context.selection",
  "version": 2,
  "schema": {
    "type": "object",
    "properties": {
      "target_id": {
        "type": "string",
        "minLength": 1
      },
      "task": {
        "type": "string",
        "minLength": 1
      }
    },
    "required": [
      "target_id",
      "task"
    ],
    "additionalProperties": false
  },
  "semantics": "Resolve target_id as a Module; include its owned documents and its explicit Module/document references exactly once without recursion, retain original owners and all provenance, and assess exactly task. Missing necessary definitions produce an attributed gap; inclusion grants no provider code or write authority.",
  "example": {
    "target_id": "service.transfer",
    "task": "Explain transfer admission"
  }
}
```

## Gap rule for bounded tasks

All task roles use the same necessary-contract gap rule. Explanation, planning, tasks and
implementation pause only dependent judgments when a required contract is missing or ambiguous;
independent reasoning may continue. Development gaps retain target, task, phase and Spec revision
until repair and a successful fresh assessment of that step. Pure queries do not create Reflections.

## Review-result stage-input value

The canonical [review-result record](../development/review-result.md)
is owned by Development and included by Harness's explicit document reference. Harness validates
and freezes it only in admitted tasks/implementation repair contexts; Development checks current
review intent and evidence before providing it. Neither party copies or widens its definition.

## Global Spec context assembly

The host-internal Python API resolves several explicitly selected Module contexts for a
coordinator with a global view:

```python
resolve_discovery_context(repository: SpecRepository, target_ids: tuple[str, ...], *,
    capability: str, phase: str, task: str, action: str = "route",
    target_hint: str | None = None, focus_hint: str | None = None,
    constraints: tuple[str, ...] = (), instructions: str = "",
    workspace: dict | None = None, mode: Mode | None = None) -> DiscoveryContext
```

Here each selected Spec's context means its complete resolved Markdown context, including its
inline architecture diagrams. The Python resolver determines membership without model judgment. It
includes non-main documents in full, never follows dependencies or hyperlinks implicitly, and never
substitutes an answer or summary for an original source.

Inputs require a nonempty, duplicate-free ordered tuple of Module IDs, a nonblank task,
capability concorde-main or concorde-dev-loop, phase route, and action route, ask or
design-topology. A focus hint requires a target hint and must belong to that Module. Unsupported
phases/actions, invalid selections, unavailable required files and inconsistent membership reject
resolution; no partial context is returned. Hints do not themselves add a Module's documents.

DiscoveryContext has serialized, value and id accessors like ContextSnapshot. Its canonical
concorde-discovery-context@2 payload contains context_id, schema_version, capability, phase,
action, task, constraints, target_hint, focus_hint, protocol_binding, protocol, topology,
targets, documents, instructions and workspace. Topology is the exact registry
only for design-topology; otherwise it is null.

Each target has `target_id`, `kind: module` and `spec_resolution`. This resolution uses the
[Spec record](../spec/registry.md#stable-id-spec-context-queries) with source metadata/reasons but
without `content`. The top-level `documents` pool contains each complete source record once,
without per-selection reasons, sorted by path; per-target reasons remain in the target resolutions.
Every pooled document has exactly one owner. Overlapping selections preserve all attribution and
include its bytes once. No provider references are recursively followed and no diagram pool exists.

The coordinator reads these original pools directly, combines facts across selected contexts,
and returns an answer or an attributed Spec gap. No separate reading Agent, recursive reading
factory or worker-result synthesis is provided. Mutating workers retain their single-Module
context and separately bound permissions.

recheck_discovery_context(repository, snapshot) reconstructs the same selection from current
repository inputs. Ownership, references, provenance, document order, original bytes, Protocol, instructions and
lifecycle metadata bind context identity; changes reject reuse with SpecError/stale_context.
Context assembly and rechecking launch no model and grant no write or network authority.

The Protocol schema asset is produced by the wire provider from its registered schemas: stable
IDs, exact closed versioned payloads and self-contained local definitions. This Module verifies
manifest/asset byte binding through the repository constructor rather than reconstructing schema
export. Missing assets prevent construction; digest mismatches report protocol_mismatch.

Mode admission precedes launch: the instruction digest identifies common responsibilities plus one
selected task mode. Stage artifact types are restricted by that mode; Spec and code reviews admit
no author stage_inputs. Programmer investigation receives code read-only and only the selected
reflection artifact, while implementation receives the implementation task and optional review
feedback. Neither mode inherits conversation or private reasoning.

The optional host-only Mode argument to resolve_context rejects incompatible phases and artifact
types before resolving implementation digests. It permits missing prerequisites only for policy
preview; actual launch admission requires every mode-required input.

```concorde-contract-binding
{
  "id": "contract.context.selection",
  "version": 2,
  "role": "provided",
  "peer": "module.development",
  "selection_condition": "When Development asks the host to freeze a bounded Module context.",
  "relied_upon_guarantees": [
    "[Selection](#contract.context.selection) supplies the admitted context for task assessment."
  ],
  "obligations": [
    "Resolve and recheck the exact owner/reference/byte provenance; reject stale inputs and return attributed gaps without undeclared reads."
  ]
}
```

## Implementation status

Snapshot/discovery serializers and the agent-stage, main-stage, review-stage and topology-author
wrappers use version 2. They freeze spec_resolution and original source pools, preserve owner and
inclusion provenance, and reject version-1 membership partitions. Native capsules and grants keep
referenced sources read-only; only owned entity listings grant implementation access. Rechecks
compare declarations and exact bytes, including reference changes with unchanged path sets.
