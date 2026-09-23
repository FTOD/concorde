# Task context contracts

The exact agreements and records of [Task context](module.md). Its obligations are in
[requirements](requirements.md).

## Context selection

### Selection agreement {#selection-agreement}

A caller that binds a Module-bound step asks Task context for exactly one Module and one task. The
agreement fixes the question a snapshot answers; the snapshot record below fixes the answer.

The schema uses the offline object-schema subset: `type`, `properties`, `required`,
`additionalProperties` and `minLength` have their ordinary JSON Schema meanings, unknown properties
are rejected and string lengths are measured in characters.

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
  "semantics": "Resolve target_id as a Module, or a scenario as its owning Module; include both members of every document in that Module's SpecContext exactly once, one level deep, retaining each document's owner and the declarations that selected it; and assess exactly task. Missing necessary definitions produce an attributed gap. Selection grants no provider code and no write authority.",
  "example": {
    "target_id": "module.transfer",
    "task": "Explain transfer admission"
  }
}
```

The providers under [Operations](../../operations/module.md) supply the explicit Module and task
before any assessment, planning, authoring or review step. Task context resolves and rechecks the
exact owners, selecting declarations and bytes, rejects stale inputs, and reports gaps instead of
reading outside the selection.

## Context snapshot

The snapshot is the data of the private typed value `concorde-context-snapshot`, schema version 7.
It never crosses the public result boundary. All fields are required and unknown fields are
rejected.

| Field | Content |
| --- | --- |
| `schema_version` | `7` |
| `context_id` | `sha256:` digest of the canonical JSON of every other field |
| `target_id`, `kind` | the selected Module and `module` |
| `focus_id` | a scenario ID or null |
| `phase`, `task`, `constraints` | the step |
| `instructions` | the Agent's rendered instructions, supplied by the caller |
| `protocol_binding` | the project's bound Protocol `{version, digest}` |
| `protocol` | `[{path, digest}]` of the Protocol files the worker is given, today `.concorde/protocol/principles.md` and `.concorde/protocol/kinds/module.md` |
| `spec_resolution` | the Spec Module's [Spec context record](../../spec/contracts.md#spec-context-records) of the Module's `SpecContext`: one source record per document member (identity, owner, path, role, digest, and every selecting relation) and the Module's entry; no bodies. In phase `implementation` it is requested with `shares`, so it also holds the documents of every other Module binding a file of the Module's implementation scope, each with a `shares` reason |
| `implementation_entries` | `[{path, entity_id, pending, directory}]`: the Module's realization entries in declaration order, with the realization that declares each |
| `implementation_files` | `[{path, entity_id, pending}]`: existing files the entries bind, each attributed to the most specific entry, plus exact pending entries |
| `implementation_artifacts` | `[{id, path, digest}]` of every bound file, only for phases `implementation` and `code-review`; otherwise empty |
| `external_references` | `[{path, directory, digest}]`: one tree digest per external inclusion over its readable files, excluding media and archive suffixes |
| `stage_inputs` | admitted typed stage inputs |
| `workspace` | the workspace facts of [Candidate worktrees](../worktrees/records.md#workspace-facts) |

Paths are canonical project-relative POSIX paths; workspace paths are absolute. Digests are
`sha256:` followed by 64 lowercase hexadecimal digits. The Python entry points are
`resolve_context(repository, target_id, *, phase, task, focus_id, constraints, instructions,
stage_inputs, workspace, agent)` and `recheck_context(repository, snapshot,
check_implementation=True)`.

## Phases

| Phase | Implementation contents in the snapshot |
| --- | --- |
| `context-solve`, `plan`, `tasks`, `spec-review`, `validate`, `deliver`, `issue-solve` | no |
| `implementation`, `code-review` | yes |

The admitted stage input types are `concorde-plan-artifact`, `concorde-task-identity-constraints`,
`concorde-implementation-task`, `concorde-task-scope-feedback`, `concorde-issue-selection`,
`concorde-issue-context`, `concorde-issue-intent` and `concorde-review-result`. Each is a closed,
versioned typed value. The worker profile decides which of them a step admits and requires; only phase
`tasks` admits `concorde-task-identity-constraints` and `concorde-task-scope-feedback`. Every profile also admits `concorde-issue-intent`, and a profile that admits
`concorde-review-result` also admits `concorde-issue-context`. An input a profile does not admit, a
duplicate type, or a missing required input fails with `incompatible_handoff`; a policy preview may
omit required inputs that do not exist yet.

## Delivery to a native Agent

The capsule is a fresh private directory whose `context/` subdirectory holds:

- a byte-identical copy of every `protocol` and `spec_resolution` path, verified against its digest
  before copying (a mismatch is `stale_context`);
- the readable files of every external inclusion, when the profile reads the `references` role;
- a copy of every `implementation_artifacts` file, in phase `code-review`;
- `context.json`: the snapshot; in phase `spec-review` or `code-review` wrapped with the typed review
  input; in phase `implementation` extended with `native_workspace` (the project worktree),
  `intended_write_paths`, and the declarations `file_scope_enforcement: "prompt-level"` and
  `network_and_credentials: "model policy, not OS confinement"`.

## Worker profile

```text
EffectDeclaration(reads: tuple[str, ...], writes: tuple[str, ...], network: bool, credentials: "none" | "declared")
Contract(phase, context, result, effects, stage_inputs, required_inputs, output_fields, outcomes)
WorkerProfile(name, spec, workspace: "capsule" | "project", contract, tools, timeout_seconds = 1800)
WorkerBinding(agent, spec_path, spec_digest, instructions_path, instructions_digest,
              profile_digest, build_manifest_digest, timeout_seconds, digest)
```

A profile is refused with `invalid_agent_binding` unless: `spec` is `agents/<name>/spec.md`; the
workspace kind is known; the context type is `concorde-agent-stage-context` with result
`concorde-agent-stage-result`, or `concorde-review-stage-context` with
`concorde-review-stage-result`; required inputs are admitted inputs; output fields are among
`documents`, `plan`, `tasks` and `issue_decision`; every written role is also read; network is off
and credentials are `none`; implementation reads use a `project` workspace; tools are distinct,
drawn from `read`, `grep`, `find`, `ls`, `edit`, `write`, `bash` and `run_checks`, include `read`,
and include `edit` or `write` only with a write role; and the timeout is a positive integer.

Binding (`resolve_worker(package_root, name)`) verifies build freshness, validates the profile,
requires the instruction source's digest to be recorded in `generated/build-manifest.json` and the
rendered instructions `generated/agents/<hyphenated name>.md` to exist. The binding digest covers every other
field of the binding.

## Grant

`compile_policy(effects, binding, role_paths, *, deny_paths=())` returns a frozen
`NormalizedPolicy` with the bound operation, stage, occurrence, role and Agent, sorted
`read_paths`, `write_paths` and `deny_paths`, `default_deny: true`, `network_enabled`,
`credentials`, and a digest. The path roles that carry paths today are:

| Role | Paths |
| --- | --- |
| `spec-context` | `context.json` and every `protocol` and `spec_resolution` path of the snapshot |
| `implementation` | the Module's bound files, or its realization entries for a writer |
| `references` | the external inclusion roots; may be absent when the Module declares none |

A launch check additionally requires exactly one `context.json` and exactly the snapshot's listed
files in `spec-context`, implementation grants inside the selected Module (and, for a read-only
profile, inside the frozen files), and reference grants inside the snapshot's external inclusions.
`.env`, `.aws`, `.config/gcloud`, `.npmrc`, `.pypirc` and `.ssh` are always denied.

## Revision identities

`target_revision(repository, module)` digests the Module's registry record, the Protocol binding
and its resolved `SpecContext` record. `implementation_digest(repository, module)` digests the
realization entries and the bytes of every bound file. Planning, Review, Validation, Implementation
and Issues bind their evidence to these digests, so a changed Spec or implementation makes the
evidence stale.

## Error codes

| Code | Meaning |
| --- | --- |
| `invalid_phase` | the phase is not one of the phases above |
| `invalid_input` | the task is blank |
| `incompatible_handoff` | a stage input is unknown, not admitted for the phase or profile, or a required one is missing |
| `permission_denied` | the phase or implementation reads exceed the worker profile's contract |
| `invalid_reference` | an external inclusion is not checked out |
| `stale_context` | a recheck or a granted file no longer matches the snapshot |
| `unknown_agent`, `invalid_agent_binding`, `stale_build` | profile lookup, validation or binding failed |
| `PermissionPolicyError` | a grant would widen the profile or the binding, or names an unsafe path |
