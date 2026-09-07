```concorde-document
{
  "id": "document.context.boundary",
  "targets": ["service.spec-context"],
  "main_visible": true
}
```

# Spec context service

## feature.concorde.define-project-ontology

A caller registers stable target identities, independent scope/component parent relationships,
overlapping participation and each target's complete ordered Markdown collection. Domain targets
hold business entities/rules; Service targets expose Features and precise exchanges; Module targets
expose APIs directly. Features/APIs have local stable IDs and an explicit member document. File names
have no semantic role. Every Markdown contains exactly one `concorde-document` JSON object with
globally unique id, exact nonempty targets and boolean main_visible. A file referenced once is Target
Spec; a file referenced several times is collective Shared Specs with no unique owner. The registry
is the matching resolution index and rejects declaration mismatch, duplicate document IDs, cycles,
foreign focus IDs, overlapping code ownership and unsafe paths. A Domain/Service may expose no
document to main when another visible routing view is sufficient to select its target worker.
Each direct component participation edge must also have one machine-readable Domain-local
`concorde-participants` entry containing target ID, kind, responsibility, selection condition and
relied-upon promises. Registry metadata proves the relationship; the Domain entry supplies the
self-contained meaning and routing facts.

## feature.context.resolve

Public concorde-context and concorde-resolve-context use the same deterministic boundary: one
concorde-operation-invocation@2 on stdin, with operation_id, mode, configuration and input TypedValue.
Configuration is concorde-operation-configuration@1 {integration: codex|claude, enforcement:
native|outer}, or null to request the host's initialized settings. Runtime input is the matching
<operation>-request@1 {target_id,task,focus_id?,constraints?,change_id?,phase?}. Strings are nonempty;
constraints is an array of strings. Default phase is ask. Other phases are specify, plan, tasks,
implementation, validate, deliver and context-solve. Unknown fields/versions/IDs are rejected.
Response <operation>-response@1 contains manifest: concorde-context-manifest@1. The manifest exposes
target/kind/focus/phase, Protocol binding, document_order and separate target_spec/shared_specs
references with document ID, path, digest, targets and main_visible; it never exposes
document content, instructions, stage inputs, implementation locators or a reusable cognitive
snapshot.

The manifest and private snapshots also carry declared `workspace` lifecycle metadata: current and
primary worktree identities/branches, current change phase/status/outcome, its reported gaps and
component progress, and basic information about live linked worktrees. This contains no target plan,
implementation body or hidden Spec document. Paths and task summaries identify candidate work, not
permission to read another worktree. A secondary context is explicitly a candidate revision.
The host rechecks the current workspace identity and lifecycle after a stage; other worktrees' frozen
summaries may advance independently. Topology proposals retain their originating workspace observation
so a committed-base handoff can recheck the same admitted Spec and design inputs in its candidate.

The snapshot data adds the content of each target_spec/shared_specs reference. Target Spec contains
documents referenced only by the selected target; Shared Specs contains each multiply referenced
document once. document_order preserves the registry order across both headings. The resolver does
not load any referencing entity's other documents and does not recurse through shared membership.
The context identity covers all inputs apart from its own identity field. Protocol contains
principles and the matching kind definition only.
Stage inputs must be versioned plan, implementation-task or reflection-selection values. Code bytes
are not embedded; only implementation phase has code references and host-issued implementation grants.
Membership, configuration, Protocol or admitted bytes changing after resolution invalidates reuse.

The private main discovery context is a different contract. It starts with the entry Domain or
Service and contains an ordered set of only main-visible Domain/Service Target Spec and Shared Specs. A main result may request
additional Domain/Service target IDs; the host appends them and produces a new digest-bound context
before starting another fresh main process. Module target expansion fails before its private
collection is read. A main-visible shared document may name a Module target without admitting that
Module's remaining documents. A main route may name a Module from visible facts; only the subsequent
fresh target worker receives its full Target Spec plus Shared Specs. Typed worker results, never raw
target snapshots, are admitted for a separate synthesis invocation.

During `design-topology`, the discovery snapshot additionally includes exact registry metadata and
all global kind definitions. It still directly expands no Module target and contains no implementation source.
After the design is accepted, each fresh target-local Spec author receives one proposed descriptor,
task, matching kind definition and only that target's current documents. A new target begins with no
documents. A document-reference change tasks every retained current/candidate reference. Shared
content changes require every candidate referencing author to return identical bytes; disagreement
is conflicting. The host combines the deduplicated proposals in a registry/document overlay for
validation without exposing those bodies to the coordinator or changing project files.
Ordinary single-target authoring preserves the entire `concorde-document` declaration; document ID,
reference and visibility changes are topology changes even for a currently local document.

Context solving is a separate fresh context-assessor stage, invoked by concorde-context-solve or
before planning. It returns sufficient, spec_incomplete, unsupported, conflicting or failed. A gap
must name question, blocked_step and needed_contract. It cannot fetch missing context. Known missing
runtime fields fail admission; semantic incompleteness is task-specific, never universally proven.
Before launching that assessor for a Domain, the host deterministically compares the selected
Domain's participant entries with its registry relationships. A missing direct entry returns a
Domain-owned structured Spec gap; malformed, duplicate, unknown, kind-mismatched or unrelated
entries return a conflicting outcome. Both stop planning, and no relationship inventory is injected
into the worker snapshot.

## feature.context.initialize

concorde-init request action:propose additionally requires name and configuration and optionally a
target_id (default domain.project); action:apply requires the returned typed project proposal.
A proposal records action initialize|migrate, nullable base_digest and files {path,before_digest,content}.
Application validates every precondition and the complete resulting registry, then commits the file
replacements or restores original bytes. New initialization never overwrites existing files.
Migration requires Profile 7, an authored registry_json and documents {path,content}, optional replacement
configuration and no active attempts. It preserves implementation/reflection history. A mismatched
configuration digest or invalid target state blocks migration. The host can resolve metadata broadly;
no agent inherits its read authority. Local semantic authoring must make this collection sufficient.

The following local provider contract repeats the common selection obligation independently of its
consumer's Spec. Schema equality is checked deterministically; prose semantics still need review.

```concorde-contract
{
  "id": "contract.context.selection",
  "version": 1,
  "role": "provided",
  "peer": "service.workflow-host",
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

The registry object is {schema_version:1,project_id,entry_target,targets,checks}. Each target has
id,kind,title,documents,nullable scope_parent/component_parent, participates_in,implementation,
features,apis,checks,diagrams. Every array is explicit. Focus records contain id,title,document.
The entry target is a Domain or Service so main discovery never begins by reading a Module Spec.
Each physical Markdown declares `{id,targets,main_visible}` in one `concorde-document` block.
Declaration targets equal the reverse registry membership; document IDs are globally unique.
Domain Markdown carries `concorde-participants` JSON arrays; each entry has target_id, kind,
responsibility, selection_condition and a nonempty unique relied_upon_promises array.
Diagram records contain source,kind,title. Check records contain id,target_id,argv,timeout_seconds
and optional inputs (exact project-relative files/directories). The host hashes check declarations,
owned implementation and declared check inputs. A changed check driver or acceptance input invalidates
prior results; check authority never becomes an agent's code grant. Timeout is 1..3600 seconds.

Topology preparation stores the exact validated registry/document replacements below the ignored
`.concorde/topology-proposals/` host area. Its public ArtifactRef binds path and digest. Applying the
artifact rechecks its embedded design identity, discovery context, Protocol, registry base and every
file before-digest before one atomic transaction.

## Main routing view

Select `module.registry` for registry loading, target/focus selection, document membership and
implementation-file enumeration. Select `module.file-transactions` for proposal preconditions,
atomic replacement and rollback. Select `module.wire-contracts` for JSON/TypedValue/schema admission.
These Module responsibilities and stable IDs let the main coordinator route work without expanding
any Module target. Context resolution that orchestrates these APIs remains a `service.spec-context` task.
