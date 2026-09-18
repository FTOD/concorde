# Harness interface contracts

These precise specifications belong directly to the [Harness Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Context](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Snapshot](../module.md#terminology) | Defined in Concorde Framework. |
| [Capsule](module.md#terminology) | Defined in Harness. |
| [Spec context](context.md#terminology) | Defined in What information a worker receives. |
| [Implementation context](context.md#terminology) | Defined in What information a worker receives. |
| [Resource context](context.md#terminology) | Defined in What information a worker receives. |
| [Task context](context.md#terminology) | Defined in What information a worker receives. |
| [Document unit](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Source-member role](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Protocol binding](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Issue](../module.md#terminology) | Defined in Concorde Framework. |
| [Blocker](../module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |

## Context resolution

### Context snapshot resolution {#context-context-snapshot-resolution}

`resolve_context` freezes one Module's Spec context with its task context, its external
references, and, for code phases, its implementation context, into a private
`concorde-context-snapshot@6`. `resolve_discovery_context`
freezes several explicitly selected complete Spec contexts for the global coordinator.
`recheck_context` and `recheck_discovery_context` reject reuse after any admitted input changed.
The sections below define the exact inputs, records, phases and errors.

The required Profile 15 boundary below is Module-oriented: it accepts a Module `target_id` and an
optional local scenario `focus_id`. Its project contract files implement the Protocol's Spec and
Context mapping: the one-level union of owned and explicitly referenced documents, including readable design/relationship explanations and associated metadata declarations. The independent Protocol supports only Module and scenario
queries; a scenario query resolves to its providing Module's same complete context, so this API
accepts no other `target_id` kind.

The context Module is host-internal: `resolve_context` produces a private ContextSnapshot behind
the executable boundary, and no Skill returns it or a redacted projection of it. Its
inputs are target_id, task, optional focus_id/constraints/phase (default ask). Other phases are
specify, plan, tasks, implementation, spec-review, code-review, validate, deliver and context-solve.
Unknown fields/versions/IDs are rejected by the host's own admission, never by an agent-facing
schema. `describe-policy` mode on any operation previews the exact grant an execution would receive —
context_id, read/write paths and a policy digest, printed to stderr — without launching an agent,
mutating project state, or exposing document content, instructions, stage inputs, implementation
locators or the reusable cognitive snapshot itself.

The host-internal Python call is:

```python
resolve_context(repository: SpecRepository, target_id: str, *, phase: str = "ask",
                task: str = "Understand this Spec", focus_id: str | None = None,
                constraints: tuple[str, ...] = (), instructions: str = "",
                stage_inputs: tuple[dict, ...] = (), workspace: dict | None = None,
                agent: Agent | None = None
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
`concorde-context-snapshot@6` TypedValue; wrapping it adds the ordinary
`{type_id, schema_version: 6, data}` envelope. Its exact fields are:

- `schema_version: 6`, `context_id: sha256`, `target_id: str`, `kind: module`,
  `focus_id: str|null` (a scenario ID when present), `phase: str`, `task: str`,
  `constraints: list[str]` and `instructions: str`.
- `protocol_binding: {version: str, digest: sha256}` and
  `protocol: list[{path, digest}]`, with the principles and Module kind documents in that order;
  the rendered files are granted read-only at those paths beside the Spec documents.
- `spec_resolution: SpecResolution`, the canonical record defined by
  [Spec resolution](../spec/contracts.md#registry-stable-id-spec-context-queries). Its sources are index
  records: document identity, path, sole owner, byte digest, source role and all inclusion
  reasons, with the Module's `reading_entry` named; no source body is embedded. The listed
  documents are granted read-only at their paths (see the Spec context grant below). There are no
  target/shared partitions. Inline diagrams occur in the granted bytes and add no separate field.

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
- `external_references: list[{path: str, directory: bool, digest: sha256}]`, present for every
  phase: the selected Module's `references` of kind `external` in declaration order, each with one
  digest over the paths and bytes of its readable files (the ordinary directory exclusions plus
  media and archive suffixes). Reference bytes are never embedded and never listed per file. A
  missing entry fails resolution with `invalid_reference`. A mode that declares the `references`
  effect is granted exactly those entries' base paths read-only: in a project workspace at their
  paths, in a capsule as byte-identical copies of the same readable files at the same
  project-relative paths. A recheck rejects any change to the entries or their digests. An installed
  dependency's sources and the network remain outside every grant.
- `stage_inputs: list[TypedValue]`, `implementation_artifacts: list[{id: str, path, digest: sha256}]`
  and `workspace`, the lifecycle record described below. `implementation_artifacts` is populated
  only for the `implementation` and `code-review` phases, with the current content digest of each
  entity-bound file; code bytes are never embedded in the snapshot.

Spec and artifact paths are canonical project-relative POSIX paths; workspace locations are
absolute host identity paths. Sha256 values use the `sha256:` prefix and 64
lowercase hexadecimal digits. Arrays may be empty except the admitted nonempty document closure
and the phase-appropriate Protocol records, which name the principles and Module kind documents
granted to every phase alike. Every listed snapshot field is required; unknown fields are rejected
at typed host admission. The digest covers the complete canonical dictionary except `context_id`.

### Spec context grant {#context-spec-context-grant}

The Spec Protocol defines which files a Module-bound reader may see and leaves their delivery to the
tool. The Framework chooses a context index and grant, so an invocation pays only for the documents
its task opens, and every launch delivers the Spec context this way. The snapshot is
the index, written to `context.json`; the `spec-context` role path list names that file together
with every path in `spec_resolution.sources` and `protocol`, and the compiled policy grants
exactly those paths read-only. Every grant is a project-relative path: Spec documents where they
live and the installed Protocol copy under `.concorde/protocol/`. In a capsule the host copies every
granted file to that path, byte-identical to the digest the index records, before launch; in a
project workspace the files are granted in place after the host verifies that their current bytes
still match the index. No document or Protocol body is embedded in the invocation input or
prompt: the
agent opens the granted files with its own tools, starting from `spec_resolution.reading_entry`,
and reads what its task needs. `context_grants` derives that path set from any of the three
context kinds, `context_documents` produces the verified bytes and raises `stale_context` when a
listed file changed, and `validate_mode_policy` rejects a launch whose `spec-context` role paths
are not exactly the index plus its grants. After the process exits the host rereads the index file
and re-resolves the repository, so a change to a granted project document is rejected as
`stale_context`. The discovery and topology author contexts are delivered the same way.

Task context is embedded rather than granted. The stage inputs and, for a review, the
`concorde-review-input` with its `changes` travel inline in the invocation input beside the index.
Those changes are the unified diffs, since the baseline revision, of the reviewed Module's own Spec
documents in a Spec review or of its bound implementation files in a code review. They are derived
from files inside the phase's visible scope, add no path to the grant and replace no granted file: a
reviewer still reads the complete documents and files, not only the changed lines.

Ordinary `stage_inputs` are version-1 TypedValues with these payloads:
`concorde-plan-artifact` has `plan: nonblank str`; `concorde-implementation-task` has that same
`plan` and `tasks: list[{id, target_id, description, acceptance, complete}]`, with nonblank strings
and a boolean `complete`. `concorde-issue-selection` binds a selected problem, revision and bounded
progress for the Issue solver. `concorde-issue-intent` supplies only intended behavior to ordinary stages.
`concorde-task-scope-feedback` has `tasks_digest: sha256` and `reason: "implementation_boundary"`; only task authoring admits it with prior tasks and the plan. It carries no implementation contents or raw check logs.
`concorde-task-identity-constraints` has `reserved_task_ids: list[nonblank str]`, unique and possibly
empty. Only task authoring admits it and requires it alongside the plan. The common host supplies all
retained historical IDs and the current list for repair; the IDs reserve identity without adding
software obligations or code contents. The snapshot digest covers this input like every stage artifact.
These records are closed objects. A stage input conveys only its declared content, not authority.
Only `tasks` and `implementation` additionally admit `concorde-review-result@2`, carrying a typed
review's target/focus, context/input identities, spec/code mode, status, representative tasks,
Issue judgments, answer, revision and `semantic_completeness: "not_proven"`. A judgment carries
immutable receipt fields, blocking/advisory severity and affected_task. The host admits only the
selected observation descriptions through concorde-issue-context, not the whole Issue history. Revisions bind Spec/implementation digests and nullable base/head commits.
This service enforces the declared type and phase; the common host enforces [Development Graph](../dev-loop/module.md) policy and independently verifies
current, target-bound code-review repair evidence and the bounded repair policy before supplying
it. This addition preserves the existing review-driven repair edge without granting raw code reads.

The private snapshots also carry declared `workspace` lifecycle metadata: current and
primary worktree identities/branches, current change phase/status/outcome, its task-scoped Issue blocker references and
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
plus arrays `blockers`, `components` and `active_worktrees`. A blocker has receipt fields
issue_id/report_id/path and blocked_step. Bound contexts select their accepted Module work scope;
unrelated task scopes and other Modules are not injected. A component has nonblank
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
Concorde Spec Protocol 10.0.0 defines the Spec context, implementation context and external
references this service resolves. The distributed rule bundle also includes the separately authored Framework execution
profile, including P10 handoffs. The resolver verifies the build is
fresh, then admits the Protocol copy the installer placed under `.concorde/protocol/`, the manifest
the configuration binds and its rendered assets, cross-checked against the installed package's
manifest, without discovering root AGENTS.md/CLAUDE.md. The installed root entry serves
outer user sessions only. An installation update refreshes the copy but leaves the binding
unchanged, and resolution rejects `protocol_mismatch` until the developer explicitly accepts the
installed version through `concorde-configure` with `accept_protocol`. Changed bindings require new contexts.
Stage inputs must be versioned plan, implementation-task, task-identity-constraints,
task-scope-feedback, issue-selection, issue-intent, issue-context or review-result
values (the last only accompanies a bounded dev-loop code-review repair round: see
`concorde-dev-loop` in the Development Graph contract). Code bytes
are not embedded in a snapshot; implementation and the dedicated read-only code-review phase have
code references and separate host-issued implementation grants. Spec review has no code references.
The review host adds a separately typed, target-scoped changes/revision input; ordinary stage_inputs
cannot smuggle patches or arbitrary artifacts into a Spec worker.
Membership, configuration, Protocol or admitted bytes changing after resolution invalidates reuse.

Main discovery admits explicitly selected complete Module collections for global reasoning,
questions and routing. A new admitted collection produces a new context identity and a fresh
coordinator invocation. Python indexes the deduplicated original documents once, with per-Module
resolution provenance and original owners, and grants them read-only in the coordinator's capsule
together with the Protocol files. The coordinator opens them on demand and answers directly from
those complete contexts. Implementation source bodies never enter this context.
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
document ID, owner or registered references change through topology reconciliation.

Context solving invokes the context-assessor Operation in a separate fresh worker, selected by the
`concorde-context-solve` operation or as `concorde-plan`'s preliminary sufficiency check. It returns
sufficient, spec_incomplete, unsupported, conflicting or failed. A gap
is reported once as an Issue; a dependent step references its receipt and names blocked_step. It cannot fetch missing context. Known missing
runtime fields fail admission; semantic incompleteness is task-specific, never universally proven.
Before launching that assessor for a Module, the host deterministically compares the selected
Module's dependency entries with its registry relationships. A missing direct entry returns a
Module-owned structured Spec gap; malformed, duplicate, unknown, unrelated
entries return a conflicting outcome. Both stop planning, and no relationship inventory is injected
into the worker snapshot.

### Context selection agreement {#context-context-selection-agreement}

This is the sole canonical definition of the selection agreement. Development references this
owned document and declares its local binding. Version 3 selects complete reading/metadata units;
older reading-only or membership-based snapshots are incompatible and must be resolved again.

This agreement uses the offline object-schema subset: `type`, `properties`, `required`,
`additionalProperties` and `minLength` have their ordinary JSON Schema meanings. All properties
listed as required must occur, unknown properties are rejected, and string lengths are measured
in characters. The example’s target ID illustrates a separately registered consumer project.

```concorde-contract
{
  "id": "contract.context.selection",
  "version": 3,
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
  "semantics": "Resolve target_id as a Module; include both reading and metadata members of its owned and explicitly referenced document units exactly once without recursion, retain original owners, source roles and all provenance, and assess exactly task. Missing necessary definitions produce an attributed gap; inclusion grants no provider code or write authority.",
  "example": {
    "target_id": "service.transfer",
    "task": "Explain transfer admission"
  }
}
```

### Review-result stage-input value {#context-review-result-stage-input-value}

The canonical [review-result record](../review/review-result.md)
is owned by Review and included by Harness's explicit document reference. Harness validates
and freezes it only in admitted tasks/implementation repair contexts; [Development Module](../development/module.md) checks current
review intent and evidence before providing it. Neither party copies or widens its definition.

### Global Spec context assembly {#context-global-spec-context-assembly}

The host-internal Python API resolves several explicitly selected Module contexts for a
coordinator with a global view:

```python
resolve_discovery_context(repository: SpecRepository, target_ids: tuple[str, ...], *,
    operation: str, phase: str, task: str, action: str = "route",
    target_hint: str | None = None, focus_hint: str | None = None,
    constraints: tuple[str, ...] = (), instructions: str = "",
    workspace: dict | None = None, agent: Agent | None = None) -> DiscoveryContext
```

Here each selected Spec's context means its complete resolved document-unit context (reading plus metadata), including its
inline architecture diagrams. The Python resolver determines membership without model judgment. It
includes non-main documents in full, never follows dependencies or hyperlinks implicitly, and never
substitutes an answer or summary for an original source.

Inputs require a nonempty, duplicate-free ordered tuple of Module IDs, a nonblank task,
operation concorde-main, concorde-dev-loop, concorde-specify-loop or concorde-review, phase route, and action route, ask or
design-topology. A focus hint requires a target hint and must belong to that Module. Unsupported
phases/actions, invalid selections, unavailable required files and inconsistent membership reject
resolution; no partial context is returned. Hints do not themselves add a Module's documents.

DiscoveryContext has serialized, value and id accessors like ContextSnapshot. Its canonical
concorde-discovery-context@6 payload contains context_id, schema_version, operation, phase,
action, task, constraints, target_hint, focus_hint, protocol_binding, protocol, topology,
targets, documents, instructions and workspace. Topology is the exact registry
only for design-topology; otherwise it is null.

Each target has `target_id`, `kind: module` and `spec_resolution`, the
[Spec record](../spec/contracts.md#registry-stable-id-spec-context-queries) with its source index records and
reasons. The top-level `documents` pool contains each document's index record once, without
per-selection reasons, sorted by path; per-target reasons remain in the target resolutions. Every
pooled document has exactly one owner. Overlapping selections preserve all attribution and grant
the file once: the coordinator launch copies every pooled document and Protocol file into its
capsule and grants exactly those paths read-only, as the Spec context grant above describes. No
provider references are recursively followed and no diagram pool exists.

The coordinator opens these granted originals directly, combines facts across selected contexts,
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
no author stage_inputs. The Issue solver receives a selected problem and bounded host feedback with Spec-only authority.
[Implementation Module](../implementation/module.md) receives its tasks and optional admitted review/Issue context. No phase inherits
conversation, private reasoning or another Module's implementation.

The optional host-only Mode argument to resolve_context rejects incompatible phases and artifact
types before resolving implementation digests. It permits missing prerequisites only for policy
preview; actual launch admission requires every mode-required input.

<a id="participation.document.harness.context.1"></a>

**Interface participation.** This Module has the provided role for `contract.context.selection` version 3 with `module.development`.

**When this applies.** When Development asks the host to freeze a bounded Module context.

**Relied-upon guarantee.** [Selection](#contract.context.selection) supplies the admitted context for task assessment.

**Local obligation.** Resolve and recheck the exact owner/reference/byte provenance; reject stale inputs and return attributed gaps without undeclared reads.

## Permissions

### Interface signatures {#permissions-interface-signatures}

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of permissions:

```text
compile_policy(effects: EffectDeclaration, binding: PolicyBinding, role_paths: Mapping[str, tuple[str, ...]], *, deny_paths: tuple[str, ...]=(), outer_sandbox_required: bool=False) -> NormalizedPolicy
verify_effective_subset(declared: NormalizedPolicy, effective: NormalizedPolicy) -> None
```

Public functions of worktree:

```text
inspect_worktree(project_root: str | Path) -> WorktreeBoundary
require_isolated_worktree(project_root: str | Path, *, allow_primary_worktree: bool=False) -> WorktreeBoundary
```

`WorktreeBoundary` is a frozen record with string fields `project_root`, `repository_root`, `head`,
`git_dir` and `common_dir`, and boolean `isolated`; `to_dict() -> dict[str, Any]` returns those exact
fields. Successful Git inspection uses resolved absolute paths and a verified commit ID for `head`.
`isolated` means that the worktree's Git directory differs from its shared common directory.
`inspect_worktree` observes this identity without changing files or checking for local dirt; it
does not require isolation and may inspect a directory within a worktree. A symlink root, missing
directory, unavailable/failing Git command, empty Git identity or absent committed HEAD raises
`WorktreeBoundaryError(ValueError)`.

`require_isolated_worktree` returns the inspected record for a committed linked worktree. With
`allow_primary_worktree=False`, it rejects a primary worktree or non-worktree directory with the
same exception. The trusted host's explicit `True` exception also accepts a committed primary
worktree. If the initial Git probe cannot establish any worktree (including an unavailable Git
executable), this exception returns the resolved `project_root`, empty other string fields and
`isolated=False`. It never accepts a symlink or missing directory, and a subsequent inspection
failure inside an identified Git worktree still raises. The exception is not a task-input
permission and does not alter delivery's separate preservation requirements.

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.

## Typed values

### Interface signatures {#typed-values-interface-signatures}

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of typed_data:

```text
canonical(value: Any) -> str
decode(text: str) -> Any
obj(properties: dict, optional: tuple[str, ...]=()) -> dict
array(items: dict, *, unique: bool=False) -> dict
typed_schema(type_id: str) -> dict
check_schema(value: Any, schema: dict, field: str='') -> None
safe_path(value: str, field: str='') -> str
checked_path(project: Path, relative: str, field: str='') -> Path
typed(type_id: str, data: dict) -> dict
validate_typed(value: Any, expected: str | None=None, field: str='') -> dict
artifact(project: Path, identifier: str, relative: str) -> dict
verify_artifacts(project: Path, value: Any, field: str='') -> None
json_schema(type_id: str) -> dict
```

Public functions of contracts:

```text
dependencies(operation: str) -> tuple[str, ...]
contracts() -> dict[str, tuple[str, str]]
schemas() -> dict
exported_types() -> tuple[str, ...]
```

Public functions of wire_shapes:

```text
obj(properties: dict, optional: tuple[str, ...]=()) -> dict
array(items: dict, *, unique: bool=False) -> dict
typed_schema(type_id: str) -> dict
```

Public functions of schema:

```text
pointer(base: str, key: Any) -> str
admit(schema: Any, root: dict | None=None) -> None
validate(value: Any, schema: Any, field: str='', *, root: dict | None=None, depth: int=0) -> None
```

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.

## Context kinds

| Kind | Content | Required for |
| --- | --- | --- |
| Spec context | The selected Module's complete resolved document-unit context (reading plus metadata), exactly the Protocol's `Context(M)`; a scenario focus changes the question, not the membership. The Protocol fixes only this visible set; the Framework delivers it as a context index and grant: the snapshot lists every document with identity, owner, digest, inclusion reasons and the reading entry, and the documents are granted read-only at their project-relative paths, byte-identical copies in a capsule. No document body is embedded. | Every Module-bound invocation. |
| Implementation context | The Protocol's `ImplementationContext(M)`: the listing entries the selected Module's own entities declare, exact files and directory prefixes alike, and the files those entries currently bind. Every phase can see the declared entries and bound file names with their owning entity and pending status; only code-writing and code-review phases receive file contents, in their declared subsets. | Entries and file names: every phase. File contents: code-writing and code-review phases only. |
| Resource context | The contracts of the Operations and Tools the invocation may use, as admitted by its Harness and constraints, together with the Module's Protocol-defined external references: the vendored documentation and source it declares with `references` of kind `external`, one tree digest per entry. Descriptions given to the model and bindings accepted by the executor resolve to the same contracts. | Reference entries and digests: every phase. Reference contents, read-only: the modes that declare the `references` effect (plan, tasks, implementation, code-review). Operation and Tool contracts: none admitted by any current Agent. |
| Task context | The task and constraints, the stage artifacts admitted for this phase, such as a plan, implementation tasks, a review result or an Issue selection, and the frozen workspace lifecycle metadata. Task context travels inline in the invocation input, including the review host's typed changes. | Every invocation; stage artifacts are optional. |

A kind may be empty for a phase, but the frozen closure is never empty. Agent instructions, the
Protocol rule bundle and installed Skills are not context: instructions belong to the Agent
definition and are injected beside the context, and a Skill is the developer-facing projection of
a public Operation. The snapshot identity covers every admitted byte of every kind.
