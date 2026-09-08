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
expose APIs directly. Features/APIs have local stable IDs and an explicit member document. Every Domain registers exactly one local main-visible `ontology.md`; other filenames
remain unrestricted. Domain main-document selection uses explicit membership and the exact basename,
never member order or directory scanning. The main Spec contains an Ontology section and owns one
architecture declaration with `recipe: system-overview`. Every Markdown contains exactly one `concorde-document` JSON object with
globally unique id, exact nonempty targets and boolean main_visible. A file referenced once is Target
Spec; a file referenced several times is collective Shared Specs with no unique owner. The registry
is the matching resolution index and rejects declaration mismatch, duplicate document IDs, cycles,
foreign focus IDs, overlapping code ownership and unsafe paths. A Service may expose no
document to Main when another visible routing view is sufficient to select its target worker; a
Domain always exposes its local ontology.md main Spec.
Each direct component participation edge must also have one machine-readable Domain-local
`concorde-participants` entry containing target ID, kind, responsibility, selection condition and
relied-upon promises. Registry metadata proves the relationship; the Domain entry supplies the
self-contained meaning and routing facts.

## feature.context.resolve

The context Service is host-internal: `resolve_context` produces a private ContextSnapshot behind
the executable boundary, and no Skill returns it or a redacted projection of it. Its
inputs are target_id, task, optional focus_id/constraints/phase (default ask). Other phases are
specify, plan, tasks, implementation, spec-review, code-review, validate, deliver and context-solve.
Unknown fields/versions/IDs are rejected by the host's own admission, never by an agent-facing
schema. `describe-policy` mode on any capability previews the exact grant an execution would receive —
context_id, read/write paths and a policy digest, printed to stderr — without launching an agent,
mutating project state, or exposing document content, instructions, stage inputs, implementation
locators or the reusable cognitive snapshot itself.

The private snapshots also carry declared `workspace` lifecycle metadata: current and
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
`diagram_sources` contains only the selected target's registered JSON sources as path/digest/content/declaration
records. These bytes are explicit Spec artifacts, not executable code, and participate in context
identity and freshness. Changing a diagram invalidates the target revision and its review evidence.
The context identity covers all inputs apart from its own identity field. The wire field `protocol`
contains the distributed principles bundle and matching kind definition only. This bundle includes
both Concorde Spec Protocol requirements and the Framework execution profile; the field name does
not classify all runtime rules as Spec organization rules.
Concorde Spec Protocol 1.2.0 introduces the main-Spec convention. The distributed rule bundle also
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
Before launching that assessor for a Domain, the host deterministically compares the selected
Domain's participant entries with its registry relationships. A missing direct entry returns a
Domain-owned structured Spec gap; malformed, duplicate, unknown, kind-mismatched or unrelated
entries return a conflicting outcome. Both stop planning, and no relationship inventory is injected
into the worker snapshot.

## feature.context.initialize

concorde-init request action:propose additionally requires name and configuration and optionally a
target_id (default domain.project); action:apply requires the returned typed project proposal.
A proposal records action initialize, nullable base_digest and files {path,before_digest,content}.
It creates `specs/project/ontology.md` and a System overview source at
`specs/project/diagrams/overview.architecture.json`. The stub diagrams only the known developer,
project Spec and external Framework; unknown business entities and architecture are explicit gaps.
Application validates every precondition and the complete resulting registry, then commits the file
replacements or restores original bytes. New initialization never overwrites existing files. Profile
7 is not agent-compatible and has no migration capability. The host can resolve metadata broadly;
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
Diagram records contain source,kind,title and optional recipe (only `system-overview`, for
architecture). Every Domain has exactly one such overview; its source requests showcase validation
and a generated HTML output beneath `generated/diagrams/`. Check records contain id,target_id,argv,timeout_seconds
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

All task roles use the same necessary-contract gap rule. Explanation, planning, tasks and
implementation pause only dependent judgments when a required contract is missing or ambiguous;
independent reasoning may continue. Development gaps retain target, task, phase and Spec revision
until repair and a successful fresh assessment of that step. Pure queries do not create Reflections.
The registered Shared Spec **Registry selection and value contracts** supplies this Service's local
required constructor, selection, document/type, configuration and error promises without opening
another target's remaining collection.
