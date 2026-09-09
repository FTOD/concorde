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
target/focus and repository/Protocol failures use the Shared Spec's declared errors. Unsupported
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
  selected target's registered `{source, kind, title, recipe?}` diagram record.
- `implementation_specs`: empty outside code writing; in implementation, a list of `{id,title,files,modules,documents}` records with the exact Implementation Spec bodies and bindings.
- `stage_inputs: list[TypedValue]`, `implementation_artifacts: list[{id: str, path, digest: sha256}]`
  and `workspace`, the lifecycle record described below. Implementation references are empty
  outside `implementation` and `code-review`; code bytes are never embedded.

Spec and artifact paths are canonical project-relative POSIX paths; workspace locations are
absolute host identity paths. Sha256 values use the `sha256:` prefix and 64
lowercase hexadecimal digits. Arrays may be empty except the admitted nonempty document closure
and two Protocol records. Every listed snapshot field is required; unknown fields are rejected
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
`diagram_sources` contains only the selected target's registered JSON sources as path/digest/content/declaration
records. These bytes are explicit Spec artifacts, not executable code, and participate in context
identity and freshness. Changing a diagram invalidates the target revision and its review evidence.
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

Main discovery admits explicitly selected complete Module collections for global routing.
A new admitted collection produces a new context identity and a fresh coordinator invocation.
Implementation Specs and source bodies never enter this context. Selected target readers each
receive only their own complete Module Spec; synthesis receives their typed results.
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
It creates `specs/project/module.md` and a System overview source at
`specs/project/diagrams/overview.architecture.json`. The stub diagrams only the known developer,
project Spec and external Framework; unknown business entities and architecture are explicit gaps.
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
is optional; declared sources have source/kind/title and an optional system-overview recipe. Check
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
The local companion contract **Registry selection and value contracts** supplies this Module's local
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

## Reader Agent and recursive factory

This Module owns `agents/reader/AGENT` in the Python package `agents.reader` and its single authored
`agents/reader/spec.md`. The same canonical Agent supports an ordinary one-decision stage and an
explicitly assembled recursive invocation. Legacy stage input receives only its stage result and
no child interface. `concorde-agent-loop-context@1` admits one typed loop action, advertised child
contracts and typed feedback. Neither path enables provider-native delegation. The registered
reader declares `allow_delegation=True`; effective child edges and target access still come from
the host's graph binding and invocation grant.

```python
agents.reader.runtime(project_root, package_root, target_id, *, integration="codex", executor=None,
                      executor_reference=None, limits=None, cancelled=lambda: False) -> AgentRuntime
```

The factory requires a nonblank target ID and codex/claude integration. It loads the reader through
`module.package-assets.load_agent(package_root, "reader")`, whose result supplies `.body: str`
and an immutable, current `.binding: AgentBinding` (the admitted runtime Shared Spec defines that
record). It creates a fixed-target, explicit self-edge graph node named `reader`, with eight local
steps. It accepts typed `concorde-agent-task@1` data `{task: nonblank str, target_id: nonblank str}`
and returns `concorde-agent-answer@1` data `{answer: nonblank str}`. A mismatched task target is
rejected before target context resolution. The resolver passes the loaded instruction body and
actual task to the existing complete-context service and rechecks build freshness on every call.
No authority or execution is created by constructing this factory result.

The required execution collaborator supplies
`RuntimeAgent(agent: Agent, decide, package_root: Path, targets: frozenset[str],
delegates: frozenset[str], decision_reference: str, input_type="concorde-agent-task",
result_type="concorde-agent-answer", max_steps=8, binding: AgentBinding|None=None)` and
`AgentRuntime(nodes, resolver, *, limits=AgentLimits(), cancelled=callback)`. The node is a graph
binding of the canonical Agent, not a new definition model; the callback reference identifies the
native integration and executor configuration. The native adapter consumes one private frame and
returns a typed loop decision. It uses the supplied canonical binding and rendered prompt in the
existing process executor, verifies native receipts, and restricts execution to a private
read-only context capsule. The callback interface for an injected executor is
`executor(launch: LaunchSpecification, *, deadline: float) -> CapabilityExecutionResult`; deadline
is absolute on `time.monotonic()` and must bound its preflight and execution. Injection requires a
nonblank versioned `executor_reference`; omission or invalid configuration raises `ValueError`.
The default executor uses deadline-bound runner/probe callbacks, never a permissive retry.

`AgentLimits(max_calls=16, max_depth=4, max_decisions=64, timeout_seconds=300)` has positive integer
counts except depth may be zero, and a positive finite timeout; `limits=None` uses these defaults.
An enclosing host invokes the returned runtime with `AgentGrant(targets: frozenset[str],
agents: frozenset[str])`; its `invoke(agent_id, typed_input, grant)` returns `AgentRun(result, events)`.
The frozen result has invocation/parent/Agent identities, outcome, nullable serialized typed
`value_json`, stable nullable `error` and nullable serialized typed interruption `details_json`.
Outcomes distinguish completed, spec_incomplete, waiting, cancelled, failed, limit_exhausted and
rejected. Only completed has a value. Gaps/waiting use `concorde-agent-interruption@1`
`{gaps, decision}`; each gap has question/blocked_step/needed_contract/target_id/context_id matching
its snapshot, and waiting has only a nonblank decision. Events are host-only admission/decision/
return evidence. The execution collaborator enforces explicit edges, inherited target/Agent
allowlists, immutable contexts, and shared and per-Agent deadlines. Failed/rejected children are
bounded feedback; cancellation or exhaustion terminates ancestors. Native cancellation and timeout
classifications are retained. No persistent resume or parallel scheduling is implied.

The resolver callback is `resolver(node: RuntimeAgent, input: dict, grant: AgentGrant) -> dict`.
The host passes the selected node, validated typed input envelope and effective grant (inherited
Agent allowlist and intersection of inherited/node target sets). It must return the full typed
`concorde-context-snapshot@1` envelope, not a ContextSnapshot object or serialized string. The
reader factory wraps `resolve_context(...).value` in that envelope using phase `ask`, the task's
text and loaded instructions. The runtime validates the envelope and recomputes its context ID,
requires no implementation artifacts, requires phase `ask` and a target in the effective grant,
and for `concorde-agent-task` requires the task and context targets to match. Initial resolver
exceptions or invalid returns reject admission with `admission_failed`, unless cancellation or
exhaustion has already taken precedence. Before every decision it calls the resolver again with
the same node, decoded typed input and effective grant; a changed valid envelope is rejected as
`stale_context`. Exceptions or malformed returns during this subsequent check are execution
failures (`failed`/`execution_failed`), again subject to cancellation/deadline precedence. Resolver
calls do not broaden the grant and do not themselves start native processes.

### Recursive decision and feedback interface

The graph callback is `decide(frame: AgentFrame) -> AgentStep`. `AgentFrame` is frozen and has
`invocation_id: str`, `parent_id: str|None`, `agent_id: str`, `input_json: str`,
`context_json: str`, `spec: str`, `feedback: tuple[AgentResult, ...]`, `children_json: str`,
`result_schema_json: str`, `remaining_seconds: float`, `deadline: float`, and
`agent_binding_json: str|None = None`. The input and complete bound context are serialized typed
values; `spec` contains the admitted instructions. The child list and result schema are serialized
JSON; time values describe the shared absolute monotonic deadline and its remaining duration.
The native adapter requires the serialized canonical binding. A frame and its context are private
to this invocation; children receive their own host-resolved contexts.

`AgentStep(source: str, action: str, agent_id: str|None=None, value: dict|None=None,
outcome: str="completed", details: dict|None=None)` is frozen. The native adapter's public call
shape is `NativeAgentAdapter(integration="codex", executor=None)(frame) -> AgentStep`. It launches
one fresh model decision and converts its validated wire result into this record, decoding
`value_json` to `value`. Native decisions require `source="model-driven"`; graph callbacks can
also identify `code-driven` decisions. Invalid typed decisions or malformed JSON raise
`InvalidAgentStep(ValueError)` and the runtime rejects them with `invalid_step`. Invalid native
evidence raises `ValueError` and is classified as execution failure; enforced cancellation and
deadline exhaustion retain their distinct outcomes.

The native input/output use exact envelopes `{type_id, schema_version: 1, data}` with no other
properties. All following payload fields are required and closed. `S` means nonblank string,
`N` means `S|null`, and `Outcome` is the outcome enumeration above:

| Type ID | Data |
| --- | --- |
| `concorde-agent-loop-context` | `invocation_id: S`, `parent_id: N`, `agent_id: S`, `input_json: S`, `context_json: S`, `feedback: Feedback[]`, `children: Child[]`, `result_schema_json: S` |
| `concorde-agent-loop-step` | `source: "code-driven"|"model-driven"`, `action: "delegate"|"complete"`, `agent_id: N`, `value_json: N`, `outcome: Outcome`, `details: TypedValue<concorde-agent-interruption>|null` |

`Feedback` contains `invocation_id: S`, `parent_id: N`, `agent_id: S`, `outcome: Outcome`,
`value_json: N`, `error: N`, and nullable typed interruption `details`. `Child` contains
`agent_id`, `input_type`, `result_type`, `input_schema_json` and `result_schema_json`, all `S`.
These nested objects are also closed. Schemas describe the complete typed input/result envelopes;
`_json` values are JSON strings, never additional authority. Interruption payloads have exactly
`gaps: Gap[]` and `decision: N`; Gap's five fields listed above are nonblank strings and its
context ID is `sha256:` plus 64 lowercase hexadecimal digits.

Delegation sets `agent_id` to the advertised recipient, `value_json` to its serialized typed
input, `outcome="completed"`, and `details=null`; it requests a child and does not claim that
child has completed. The host checks the edge, effective grants and input type, allocates a fresh
child invocation ID, and sets its `parent_id` to the current invocation. Direct-child results are
appended in call order to cumulative feedback for the parent's next fresh decision; descendants'
private results are not automatically propagated. Denied delegation returns a correlated rejected
feedback item with `error="delegation_denied"`. Failed and rejected children permit another bounded
parent decision; cancelled or exhausted children terminate their ancestors immediately.

Completion requires `agent_id=null`. Successful completion supplies a serialized value matching
the advertised result type and `details=null`. Other outcomes require `value_json=null`;
`spec_incomplete` requires nonempty gaps matching the bound target/context and no decision,
`waiting` requires only a nonblank decision, and the remaining outcomes require `details=null`.
The runtime rejects inconsistent combinations with `invalid_step`. `AgentResult.wire()` produces
the Feedback shape, decoding `details_json` into `details`. No untyped transcript, arbitrary child
file, or provider-native delegation becomes an implicit input to the next decision.

The Protocol schema asset is produced by the wire provider from its registered schemas: stable
IDs, exact closed versioned payloads and self-contained local definitions. This Module verifies
manifest/asset byte binding through the repository constructor rather than reconstructing schema
export. Missing assets prevent construction; digest mismatches report `protocol_mismatch`.
