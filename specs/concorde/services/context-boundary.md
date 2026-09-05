# Spec context service

## feature.concorde.define-project-ontology

A caller registers stable target identities, independent scope/component parent relationships,
overlapping participation and each target's complete ordered Markdown collection. Domain targets
hold business entities/rules; Service targets expose Features and precise exchanges; Module targets
expose APIs directly. Features/APIs have local stable IDs and an explicit member document. File names
have no semantic role. The same Markdown may be explicitly registered in more than one collection.
The registry rejects cycles, foreign focus IDs, overlapping code ownership and unsafe paths.

## feature.context.resolve

Public concorde-context and concorde-resolve-context use the same deterministic boundary: one
concorde-operation-invocation@2 on stdin, with operation_id, mode, configuration and input TypedValue.
Configuration is concorde-operation-configuration@1 {integration: codex|claude, enforcement:
native|outer}, or null to request the host's initialized settings. Runtime input is the matching
<operation>-request@1 {target_id,task,focus_id?,constraints?,change_id?,phase?}. Strings are nonempty;
constraints is an array of strings. Default phase is ask. Other phases are specify, plan, tasks,
implementation, validate, deliver and context-solve. Unknown fields/versions/IDs are rejected.
Response <operation>-response@1 contains snapshot: concorde-context-snapshot@1.

The snapshot data has schema_version:1, context_id (sha256), target_id, kind, nullable focus_id,
phase, task, constraints, protocol_binding {version,digest}, protocol and documents arrays containing
{path,digest,content}, instructions, stage_inputs and implementation_artifacts {id,path,digest}.
The context identity covers all these inputs apart from its own identity field. Documents are exactly
the target's ordered members. Protocol contains principles and the matching kind definition only.
Stage inputs must be versioned plan, implementation-task or reflection-selection values. Code bytes
are not embedded; only implementation phase has code references and host-issued implementation grants.
Membership, configuration, Protocol or admitted bytes changing after resolution invalidates reuse.

Context solving is a separate fresh context-assessor stage, invoked by concorde-context-solve or
before planning. It returns sufficient, spec_incomplete, unsupported, conflicting or failed. A gap
must name question, blocked_step and needed_contract. It cannot fetch missing context. Known missing
runtime fields fail admission; semantic incompleteness is task-specific, never universally proven.

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
  "semantics": "Select the entire explicitly registered collection for target_id and assess exactly task. No relationship or link adds context.",
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
Diagram records contain source,kind,title. Check records contain id,target_id,argv,timeout_seconds
and optional inputs (exact project-relative files/directories). The host hashes check declarations,
owned implementation and declared check inputs. A changed check driver or acceptance input invalidates
prior results; check authority never becomes an agent's code grant. Timeout is 1..3600 seconds.
