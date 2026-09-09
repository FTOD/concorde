```concorde-document
{
  "id": "document.context.boundary",
  "targets": [
    "module.spec-context"
  ],
  "main_visible": true
}
```

# Spec context service

## feature.concorde.define-project-ontology

A caller registers Module identities, one structural parent per Module, explicit uses relations,
features, usage interfaces and the complete ordered Markdown collection. Each Module registers
one module.md reading entry. Its collection explains its internal Architecture/domain and all
relied-upon collaborator promises. A planner determines tasks from this Module Spec alone.

Implementation Specs are registered separately by id, title, documents and explicit files.
Each file has one authoritative Implementation Spec; several Modules may reference the same
Spec. The registry derives reverse users and file ownership. An Implementation document cannot
also be Module context. Dependencies, implementation references and navigation links never add
other project Specs implicitly. The local [registry values](values.md) define the complete records.

## feature.context.resolve

The existing runtime boundary below is Module-oriented: it accepts a Module `target_id` and an
optional local Feature or Interface `focus_id`. Its project contract files implement the Protocol's
Spec and Context mapping: the whole Module document collection plus its declared diagram sources.
The independent Protocol also describes standalone Implementation Spec queries and explicit
Module/Implementation pairings; those are not additional accepted `target_id` kinds of this API.

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
                stage_inputs: tuple[dict, ...] = (), workspace: dict | None = None
                ) -> ContextSnapshot
```

The caller supplies a fresh, successfully admitted repository and correctly typed arguments.
An unsupported phase raises `SpecError/invalid_phase`; a blank task raises `invalid_input`;
target/focus and repository/Protocol failures use the local companion document's declared errors. Unsupported
stage-input IDs raise `SpecError/incompatible_handoff`, and malformed typed stage values raise
`TypedDataError(ValueError)` with `code`, JSON-pointer `field` and message. The resolver returns no
partial snapshot on failure. `instructions` is the caller's admitted role instruction text;
`workspace=None` obtains current host lifecycle metadata. A supplied workspace is an explicit
trusted-host frozen observation, not a caller task field or replacement authority.

`ContextSnapshot(serialized: str)` is frozen; `.serialized` is canonical JSON, `.value` decodes a
new dictionary and `.id` returns its `context_id`. The dictionary is the data of the private
`concorde-context-snapshot@1` TypedValue; wrapping it adds the ordinary
`{type_id, schema_version: 1, data}` envelope. Its exact fields are:

- `schema_version: 1`, `context_id: sha256`, `target_id: str`, `kind: module`,
  `focus_id: str|null`, `phase: str`, `task: str`, `constraints: list[str]` and `instructions: str`.
- `protocol_binding: {version: str, digest: sha256}` and
  `protocol: list[{path, digest, content}]`, with the principles and kind documents in that order.
- `document_order: list[path]`, `target_spec` and `shared_specs`: ordered lists of
  `{document_id: str, path, digest: sha256, targets: list[str], main_visible: bool, content: str}`.
- `diagram_sources: list[{path, digest, content, declaration}]`, where the declaration is the
  legacy external-source declaration. With the inline Mermaid representation this list is empty;
  the complete containing Markdown is already in the document records.
- `implementation_specs`: empty outside code writing; in implementation, a list of `{id,title,files,modules,documents}` records with the exact Implementation Spec bodies and bindings.
- `stage_inputs: list[TypedValue]`, `implementation_artifacts: list[{id: str, path, digest: sha256}]`
  and `workspace`, the lifecycle record described below. Implementation references are empty
  outside `implementation` and `code-review`; code bytes are never embedded.

Spec and artifact paths are canonical project-relative POSIX paths; workspace locations are
absolute host identity paths. Sha256 values use the `sha256:` prefix and 64
lowercase hexadecimal digits. Arrays may be empty except the admitted nonempty document closure
and the phase-appropriate Protocol records: principles and Module kind for ordinary phases,
with the Implementation kind additionally supplied to code writing. Every listed snapshot field is required; unknown fields are rejected
at typed host admission. The digest covers the complete canonical dictionary except `context_id`.

Ordinary `stage_inputs` are version-1 TypedValues with these payloads:
`concorde-plan-artifact` has `plan: nonblank str`; `concorde-implementation-task` has that same
`plan` and `tasks: list[{id, target_id, description, acceptance, complete}]`, with nonblank strings
and a boolean `complete`; `concorde-reflection-selection` has `head: nonblank str` and
`records: list[{id: str, path, digest: sha256, content: str}]`, with nonblank string fields.
These records are closed objects. A stage input conveys only its declared content, not authority.
Only `tasks` and `implementation` additionally admit `concorde-review-result@1`, carrying a typed
review's target/focus, context/input identities, spec/code mode, status, representative tasks,
findings, gaps, answer, revision and `semantic_completeness: "not_proven"`. Findings have ID,
blocking/advisory severity, owning target/document, path and nullable line location, contract,
problem and affected task. Revisions bind Spec/implementation digests and nullable base/head commits.
The context Module enforces the declared type and phase; the workflow host independently verifies
current, target-bound code-review repair evidence and the bounded repair policy before supplying
it. This addition preserves the existing review-driven repair edge without granting raw code reads.

The private snapshots also carry declared `workspace` lifecycle metadata: current and
primary worktree identities/branches, current change phase/status/outcome, its reported gaps and
component progress, and basic information about live linked worktrees. This contains no target plan,
implementation body or hidden Spec document. Paths and task summaries identify candidate work, not
permission to read another worktree. A secondary context is explicitly a candidate revision.
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
`diagram_sources` is empty for inline Mermaid sources. Their containing registered Markdown
records include the complete fence and source declaration. Those document bytes participate in
context identity and freshness; changing a diagram invalidates the target revision and its review
evidence without adding another context file.
The context identity covers all inputs apart from its own identity field. The wire field `protocol`
contains the distributed principles bundle and Module kind definition; code writing additionally includes the Implementation kind definition. This bundle includes
both Concorde Spec Protocol requirements and the Framework execution profile; the field name does
not classify all runtime rules as Spec organization rules.
Concorde Spec Protocol 2.0.0 introduces the main-Spec convention. The distributed rule bundle also
includes the separately authored Framework execution profile, including P10 handoffs. The resolver verifies the build is
fresh, then admits Protocol assets rendered into `generated/protocol/` from the exact project-bound
manifest, without discovering root AGENTS.md/CLAUDE.md. The installed root entry serves
outer user sessions only. Package update leaves an old binding unchanged and resolution rejects
`protocol_mismatch` until the developer explicitly accepts the installed version and manifest
digest in `.concorde/config.json`. Changed bindings require new contexts.
Stage inputs must be versioned plan, implementation-task, reflection-selection or review-result
values (the last only accompanies a bounded dev-loop code-review repair round: see
`concorde-dev-loop` in the workflow-host boundary Spec). Code bytes
are not embedded in a snapshot; implementation and the dedicated read-only code-review phase have
code references and separate host-issued implementation grants. Spec review has no code references.
The review host adds a separately typed, target-scoped changes/revision input; ordinary stage_inputs
cannot smuggle patches or arbitrary artifacts into a Spec worker.
Membership, configuration, Protocol or admitted bytes changing after resolution invalidates reuse.

Main discovery admits explicitly selected complete Module collections for global reasoning,
questions and routing. A new admitted collection produces a new context identity and a fresh
coordinator invocation. Python injects deduplicated original documents and declared diagram
sources with per-Module membership. The coordinator answers directly from those complete contexts.
Implementation Specs and implementation source bodies never enter this context.
During design-topology, exact registry metadata additionally describes Module composition,
dependencies and Implementation bindings. It supplies structure, not hidden behavioral meaning.
After the design is accepted, each fresh target-local Spec author receives one proposed descriptor,
task, matching kind definition, that target's current documents and admitted registered diagram
sources. Candidate diagrams already registered elsewhere are admitted only through the accepted
target descriptor; arbitrary existing files are not read. A new target begins without invented
business documents or architecture. A document-reference change tasks every retained current/candidate reference. Shared
content changes require every candidate referencing author to return identical bytes; disagreement
is conflicting. Topology authors return complete Markdown and diagram replacements in descriptor
order. The host combines the deduplicated proposals in a registry/Spec-source overlay for
validation without exposing those bodies to the coordinator or changing project files.
Ordinary single-target authoring may update its own registered diagram bytes while preserving
their declared type/title and shared sources. It preserves the entire `concorde-document` declaration; document ID,
reference and visibility changes are topology changes even for a currently local document.

Context solving is a separate fresh context-assessor stage, run directly by the
`concorde-context-solve` stage capability or as `concorde-plan`'s preliminary sufficiency check. It returns
sufficient, spec_incomplete, unsupported, conflicting or failed. A gap
must name question, blocked_step and needed_contract. It cannot fetch missing context. Known missing
runtime fields fail admission; semantic incompleteness is task-specific, never universally proven.
Before launching that assessor for a Module, the host deterministically compares the selected
Module's dependency entries with its registry relationships. A missing direct entry returns a
Module-owned structured Spec gap; malformed, duplicate, unknown, unrelated
entries return a conflicting outcome. Both stop planning, and no relationship inventory is injected
into the worker snapshot.

## feature.context.initialize

The public input is `concorde-init-request@1`, an ordinary
`{type_id, schema_version: 1, data}` envelope. `data` is a closed object with required
`action: "propose"|"apply"` and optional `name`, `target_id`, `configuration` and `proposal`.
`name` and `target_id`, when supplied, are nonblank strings. `configuration` is
`concorde-capability-configuration@1` with exactly
`{integration: "codex"|"claude", enforcement: "native"|"outer"}` in its data.
`proposal` is `concorde-project-proposal@1` with exactly
`{action: "initialize", base_digest: sha256|null, files: list[{path, before_digest: sha256|null,
content: str}]}` in its data. File paths must be canonical project-relative paths and distinct;
content may be empty. These nested records reject unknown properties.

concorde-init request action:propose additionally requires name and configuration and optionally a
target_id (default module.project); action:apply requires the returned typed project proposal.
A proposal records action initialize, nullable base_digest and files {path,before_digest,content}.
It creates `specs/project/module.md` with an Architecture section containing an inline Mermaid
diagram, its source/kind/title declaration and accessible title/description. The registry uses
`diagrams: []`; no external diagram file is created. The stub models only known participants, the
project Spec and the external Framework; unknown business entities and architecture are explicit
gaps. The illustration does not turn a draft into a complete business contract.
Application validates every precondition and the complete resulting registry, then commits the file
replacements or restores original bytes. New initialization never overwrites existing files. Profile
7 is not agent-compatible and has no migration capability. The host can resolve metadata broadly;
no agent inherits its read authority. Local semantic authoring must make this collection sufficient.

Success returns `concorde-init-response@1` with closed data
`{status: "proposed"|"applied", proposal: TypedValue<concorde-project-proposal>|null,
files: list[path]}`. Propose returns the exact typed proposal and its ordered paths, without
changing project files; apply returns `status: "applied"`, `proposal: null` and the applied paths.
Initialization requires `base_digest` and every `before_digest` to be null. It also initializes
Reflection defaults and the topology-artifact ignore file only when absent. Missing action-specific
inputs raise `invalid_input`; an already configured project raises `already_initialized`.
Invalid proposal identity, forbidden replacement or mismatched registry/Protocol raises
`invalid_proposal`; an out-of-bound path raises `permission_denied`; changed preconditions raise
`stale_proposal`. Unsafe paths and typed-envelope errors use `TypedDataError`; filesystem or
transaction failures propagate to the host after rollback of applied file replacements.
Rollback I/O failure is itself a failure and cannot produce `applied`.

Apply admits the complete proposal by its exact `concorde-project-proposal@1` envelope and
`action: "initialize"`, not by an issuance token or lookup in a proposal store. Its files must
include `.concorde/config.json` and `.concorde/specs.json`; the proposed configuration must name
that registry and the currently installed Protocol version and exact manifest digest. The allowed
file set is those two paths, `.concorde/topology-proposals/.gitignore`, the two Reflection defaults
`.concorde/reflections/index.json` and `.concorde/reflections/config.json`, and the explicit document
and diagram-source paths in the proposed registry. Every other destination is rejected even if its
path is safe and absent. All proposed files have null before-digests and must still be absent at
application. The host validates the complete resulting registry and documents after replacement
within the rollback boundary; malformed, inconsistent or unsafe proposed structure cannot become
an applied initialization. These structural rules do not replace the developer's acceptance of
the concrete proposal or assert semantic completeness of an initialized stub.

At the executable boundary these typed values travel inside a
`concorde-capability-invocation@3` with `capability_id: "concorde-init"`, `mode: "execute"`,
nullable typed outer `configuration`, and `input` containing the request. The returned
`concorde-capability-result@3` has the same capability ID, fresh `invocation_id`, mode, nullable
workspace/output, status and `errors: list[{code, field, message}]`. Successful initialization has
`status: "succeeded"` and the typed output above; admission failures are blocked and execution
failures are failed, with no successful output. The outer configuration controls this invocation's host
settings; the propose request's configuration controls the project settings written into the
proposal. Initialization accepts different valid values for those two roles. Apply uses the
accepted proposal's configuration bytes, not a replacement from either invocation field. A null
outer configuration loads existing project settings; before initialization no such settings
exist, so callers must supply a valid outer configuration or receive `configuration_mismatch`.
There is no fallback from a null outer value to the request's project configuration. A required worktree handoff is a blocked result,
not an applied initialization. The host may not silently retry a rejected proposal against new bytes.

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
  "peer": "module.workflows",
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

## Registry and check evidence

Registry schema 2 contains schema_version, project_id, entry_target, targets, implementations
and checks. A Module descriptor has id, kind=module, title, documents, parent, uses,
implementations, features, interfaces, checks and diagrams. An Implementation Spec descriptor
has id, title, documents and explicit files. Every array is explicit; local feature/interface
records have id, title and document. The entry is a Module, and its complete collection starts routing.

Each Markdown declares id, exact targets and main_visible. Module concorde-dependencies entries
contain target_id, responsibility, selection_condition and nonempty relied_upon_promises. A diagram
is authored inline in registered Markdown, with its source path, `mermaid` kind and title stated
locally. Every Concorde Module has a principal entity diagram in `module.md`; this is a project
convention, not an extra Protocol requirement. New declarations use `diagrams: []`. Check
records declare id, target_id, argv, timeout_seconds and optional inputs. Shared implementation
checks run for every using Module, recording separate target IDs and current revisions. They never
combine the using Modules' Spec contexts or grant code to a planner.

Topology preparation stores the exact validated registry/document replacements below the ignored
`.concorde/topology-proposals/` host area. Its public ArtifactRef binds path and digest. Applying the
artifact rechecks its embedded design identity, discovery context, Protocol, registry base and every
file before-digest before one atomic transaction.

## Main routing view

Select `module.registry` for registry loading, target/focus selection, document membership and
implementation-file enumeration. Select `module.file-transactions` for proposal preconditions,
atomic replacement and rollback. Select `module.wire-contracts` for JSON/TypedValue/schema admission.
These Module responsibilities and stable IDs let the main coordinator route work without expanding
any Module target. Context resolution that orchestrates these APIs remains a `module.spec-context` task.

All task roles use the same necessary-contract gap rule. Explanation, planning, tasks and
implementation pause only dependent judgments when a required contract is missing or ambiguous;
independent reasoning may continue. Development gaps retain target, task, phase and Spec revision
until repair and a successful fresh assessment of that step. Pure queries do not create Reflections.
The local companion contract **Registry values and selection** supplies this Module's local
required constructor, selection, document/type, configuration and error promises without opening
another target's remaining collection.

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
the snapshot. Repair admission additionally belongs to the workflow host: it binds the current
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
    workspace: dict | None = None) -> DiscoveryContext
```

Here each selected Spec's context means its complete registered Markdown collection plus its
declared authored diagram sources. The Python resolver determines membership without model
judgment. It includes non-main documents in full, never follows dependencies or hyperlinks
implicitly, and never substitutes an answer or summary for an original source.

Inputs require a nonempty, duplicate-free ordered tuple of Module IDs, a nonblank task,
capability concorde-main or concorde-dev-loop, phase route, and action route, ask or
design-topology. A focus hint requires a target hint and must belong to that Module. Unsupported
phases/actions, invalid selections, unavailable required files and inconsistent membership reject
resolution; no partial context is returned. Hints do not themselves add a Module's documents.

DiscoveryContext has serialized, value and id accessors like ContextSnapshot. Its canonical
concorde-discovery-context@1 payload contains context_id, schema_version, capability, phase,
action, task, constraints, target_hint, focus_hint, protocol_binding, protocol, topology,
targets, documents, diagram_sources, instructions and workspace. Topology is the exact registry
only for design-topology; otherwise it is null.

Each target has target_id, kind (module), document_order, target_spec, shared_specs and
diagram_sources. Target Spec and Shared Specs contain document metadata references
{document_id, path, digest, targets, main_visible}; they contain no duplicate source bodies.
The target's diagram_sources are its exact declarations {source, kind, title, recipe?}.

The top-level documents pool contains complete {document_id, path, digest, targets, main_visible,
content} records, once per physical Markdown path. The top-level diagram_sources pool contains
{path, digest, content} records, once per declared source path. Both pools are sorted by path;
per-target registration order and attribution remain in the target records. A shared document's
other owners remain metadata and do not select those owners' remaining contexts. An inline
diagram is already part of its Markdown body.

The coordinator reads these original pools directly, combines facts across selected contexts,
and returns an answer or an attributed Spec gap. No separate reading Agent, recursive reading
factory or worker-result synthesis is provided. Mutating workers retain their single-Module
context and separately bound permissions.

recheck_discovery_context(repository, snapshot) reconstructs the same selection from current
repository inputs. Membership, document order, original bytes, diagram declarations or sources,
Protocol, instructions and lifecycle metadata bind context identity; changes reject reuse with
SpecError/stale_context. Context assembly and rechecking launch no model and grant no write or
network authority.

The Protocol schema asset is produced by the wire provider from its registered schemas: stable
IDs, exact closed versioned payloads and self-contained local definitions. This Module verifies
manifest/asset byte binding through the repository constructor rather than reconstructing schema
export. Missing assets prevent construction; digest mismatches report protocol_mismatch.
