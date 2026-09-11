```concorde-document
{
  "id": "document.harness.context",
  "targets": [
    "module.harness"
  ],
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
| Spec context | The selected Module's complete registered Markdown collection, exactly the Protocol's `Context(M)`; a scenario focus changes the question, not the membership. | Every Module-bound invocation. |
| Implementation context | The Protocol's `ImplementationContext(M)`: the listing entries the selected Module's own entities declare, exact files and directory prefixes alike, and the files those entries currently bind. Every phase can see the declared entries and bound file names with their owning entity and pending status; only code-writing and code-review phases receive file contents, in their declared subsets. | Entries and file names: every phase. File contents: code-writing and code-review phases only. |
| Capability context | The contracts of the Capabilities and Tools the invocation may use, as admitted by its Harness and constraints. Descriptions given to the model and bindings accepted by the executor resolve to the same contracts. | Optional; empty for every current Agent. |
| Task context | The task and constraints, the stage artifacts admitted for this phase, such as a plan, implementation tasks, a review result or a reflection selection, and the frozen workspace lifecycle metadata. | Every invocation; stage artifacts are optional. |

A kind may be empty for a phase, but the frozen closure is never empty. Agent instructions, the
Protocol rule bundle and installed Skills are not context: instructions belong to the Agent
definition and are injected beside the context, and a Skill is the developer-facing projection of
a global or lifecycle capability. The snapshot identity covers every admitted byte of every kind.

## Context snapshot resolution

`resolve_context` freezes one Module's Spec context with its task context, and, for code phases,
its implementation context, into a private `concorde-context-snapshot@1`. `resolve_discovery_context`
freezes several explicitly selected complete Spec contexts for the global coordinator.
`recheck_context` and `recheck_discovery_context` reject reuse after any admitted input changed.
The sections below define the exact inputs, records, phases and errors.

The existing runtime boundary below is Module-oriented: it accepts a Module `target_id` and an
optional local scenario `focus_id`. Its project contract files implement the Protocol's Spec and
Context mapping: the whole Module document collection, including its inline Mermaid architecture
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
`concorde-context-snapshot@1` TypedValue; wrapping it adds the ordinary
`{type_id, schema_version: 3, data}` envelope. Its exact fields are:

- `schema_version: 3`, `context_id: sha256`, `target_id: str`, `kind: module`,
  `focus_id: str|null` (a scenario ID when present), `phase: str`, `task: str`,
  `constraints: list[str]` and `instructions: str`.
- `protocol_binding: {version: str, digest: sha256}` and
  `protocol: list[{path, digest, content}]`, with the principles and Module kind documents in that order.
- `document_order: list[path]`, `target_spec` and `shared_specs`: ordered lists of
  `{document_id: str, path, digest: sha256, targets: list[str], main_visible: bool, content: str}`.
  Every inline Mermaid architecture fence already occurs in this content; there is no separate
  diagram source list.
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

The snapshot data adds the content of each target_spec/shared_specs reference. Target Spec contains
documents referenced only by the selected target; Shared Specs contains each multiply referenced
document once. document_order preserves the registry order across both headings. The resolver does
not load any referencing entity's other documents and does not recurse through shared membership.
Every inline Mermaid architecture fence is already part of its containing registered Markdown
record's content; there is no separate diagram source field. Those document bytes participate in
context identity and freshness; changing a diagram invalidates the target revision and its review
evidence without adding another context file.
The context identity covers all inputs apart from its own identity field. The wire field `protocol`
contains the distributed principles bundle and Module kind definition. This bundle includes
both Concorde Spec Protocol requirements and the Framework execution profile; the field name does
not classify all runtime rules as Spec organization rules.
Concorde Spec Protocol 4.0.0 defines the Spec context and implementation context this service
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
inline Mermaid fences, with per-Module membership. The coordinator answers directly from those
complete contexts. Implementation source bodies never enter this context.
During design-topology, exact registry metadata additionally describes Module composition,
dependencies and entity listing entries. It supplies structure, not hidden behavioral meaning.
After the design is accepted, each fresh target-local Spec author receives one proposed descriptor,
task, matching kind definition and that target's current documents, which already contain their
inline diagram fences. Candidate document content is admitted only through the accepted target
descriptor; arbitrary existing files are not read. A new target begins without invented business
documents or architecture. A document-reference change tasks every retained current/candidate
reference. Shared content changes require every candidate referencing author to return identical
bytes; disagreement is conflicting. Topology authors return complete Markdown replacements,
including any changed inline diagram fences, in descriptor order. The host combines the
deduplicated proposals in a registry/Spec-source overlay for validation without exposing those
bodies to the coordinator or changing project files.
Ordinary single-target authoring may update its own Architecture fences and other Markdown content
directly, as long as the fence's node labels keep naming the Module's declared entity titles. It
preserves the entire `concorde-document` declaration; document ID, reference and visibility
changes are topology changes even for a currently local document.

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

The following local provider contract repeats the common selection obligation independently of its
consumer's Spec. Schema equality is checked deterministically; prose semantics still need review.

This agreement uses the offline object-schema subset: `type`, `properties`, `required`,
`additionalProperties` and `minLength` have their ordinary JSON Schema meanings. All properties
listed as required must occur, unknown properties are rejected, and string lengths are measured
in characters. The example’s target ID illustrates a separately registered consumer project.

```concorde-contract
{
  "id": "contract.context.selection",
  "version": 1,
  "role": "provided",
  "peer": "module.development",
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
  "semantics": "Select target_id's exact Target Spec plus Shared Specs and assess exactly task. Shared membership adds only that document; no relationship or link expands another entity context.",
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

`concorde-review-result@1` has exactly the typed envelope fields `type_id`, integer
`schema_version: 1` (not boolean), and `data`. Its closed payload has all these required fields.
Here `S` is a nonblank string, `N` is `S|null`, and `D` is `sha256:` plus exactly 64 lowercase
hexadecimal digits:

| Field | Type or allowed values |
| --- | --- |
| `context_id` | `D|null` |
| `input_digest` | `D` |
| `review_mode` | `"spec"|"code"` |
| `status` | `"no_findings"|"findings"|"incomplete"|"skipped"|"not_run"` |
| `representative_tasks` | unique `S[]` |
| `findings` | `Finding[]` |
| `gaps` | `ReviewGap[]` |
| `answer`, `target_id` | `S` |
| `focus_id` | `N` |
| `revision` | closed object with `spec_digest: D`, `implementation_digest: D|null`, `baseline: N`, `head: N`, all required |
| `semantic_completeness` | exactly `"not_proven"` |

A closed `Finding` requires `id: S`, `severity: "blocking"|"advisory"`, `target_id: S`,
`document: S`, `contract: S`, `location`, `problem: S`, and `affected_task: S`. The closed
`location` requires `path` (a safe project-relative path) and `line` (positive integer or null).
A closed `ReviewGap` requires `question: S`, `blocked_step: S`, and `needed_contract: S`, with
optional `target_id: S` and `context_id: D`. These optional wire fields do not weaken the review
host's requirement to bind blocking gaps to the reviewed target and context. Arrays may be empty
unless the review host's status/coverage rules require contents. Unknown fields, invalid versions,
unsafe paths and shape mismatches raise `TypedDataError` during typed validation. String baseline
and head fields identify revisions; the wire shape itself does not prove their freshness.

The context service validates allowed typed stage-input values and freezes their exact bytes into
the snapshot. Repair admission additionally belongs to the Development host: it binds the current
code review and revision, admits that declared result only to `tasks`/`implementation` repair
contexts, and removes write authority during review. A structurally valid review result alone
neither authorizes a repair nor proves review completion, currentness or semantic completeness.

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

Here each selected Spec's context means its complete registered Markdown collection, including its
inline architecture diagrams. The Python resolver determines membership without model judgment. It
includes non-main documents in full, never follows dependencies or hyperlinks implicitly, and never
substitutes an answer or summary for an original source.

Inputs require a nonempty, duplicate-free ordered tuple of Module IDs, a nonblank task,
capability concorde-main or concorde-dev-loop, phase route, and action route, ask or
design-topology. A focus hint requires a target hint and must belong to that Module. Unsupported
phases/actions, invalid selections, unavailable required files and inconsistent membership reject
resolution; no partial context is returned. Hints do not themselves add a Module's documents.

DiscoveryContext has serialized, value and id accessors like ContextSnapshot. Its canonical
concorde-discovery-context@1 payload contains context_id, schema_version, capability, phase,
action, task, constraints, target_hint, focus_hint, protocol_binding, protocol, topology,
targets, documents, instructions and workspace. Topology is the exact registry
only for design-topology; otherwise it is null.

Each target has target_id, kind (module), document_order, target_spec and shared_specs. Target
Spec and Shared Specs contain document metadata references {document_id, path, digest, targets,
main_visible}; they contain no duplicate source bodies.

The top-level documents pool contains complete {document_id, path, digest, targets, main_visible,
content} records, once per physical Markdown path, sorted by path; per-target registration order
and attribution remain in the target records. A shared document's other owners remain metadata and
do not select those owners' remaining contexts. An inline diagram is already part of its Markdown
body; there is no separate diagram pool.

The coordinator reads these original pools directly, combines facts across selected contexts,
and returns an answer or an attributed Spec gap. No separate reading Agent, recursive reading
factory or worker-result synthesis is provided. Mutating workers retain their single-Module
context and separately bound permissions.

recheck_discovery_context(repository, snapshot) reconstructs the same selection from current
repository inputs. Membership, document order, original bytes, Protocol, instructions and
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
