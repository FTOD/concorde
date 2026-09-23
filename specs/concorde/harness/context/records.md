# Task context records

The exact records, layouts and entry points of [Task context](module.md). Its obligations are in
[requirements](requirements.md).

## Context snapshot

The snapshot is the data of the private typed value `concorde-context-snapshot`, schema version 8.
It never crosses the public result boundary. All fields are required and unknown fields are
rejected.

| Field | Content |
| --- | --- |
| `schema_version` | `8` |
| `context_id` | `sha256:` digest of the canonical JSON of every other field |
| `target_id`, `kind` | the selected Module and `module` |
| `focus_id` | a scenario identity or null |
| `phase`, `task`, `constraints` | the step, as named by the Agent definition and the caller |
| `agent_binding` | the [Agent binding](#agent-binding) of the call |
| `protocol_binding` | the project's bound Protocol `{version, digest}` |
| `protocol` | `[{path, digest}]` of the Protocol files the Agent is given, today `.concorde/protocol/principles.md` and `.concorde/protocol/kinds/module.md` |
| `spec_resolution` | Spec tooling's Spec context record of the selected Module: one source record per document member (identity, owner, path, role, digest and every selecting relation) and the Module's entry; no bodies |
| `shared_bindings` | for an Agent that writes implementation, `[{module_id, files, spec_resolution}]`: each other Module binding a file of the selected Module's implementation scope, the shared files and that Module's own Spec context record; otherwise empty |
| `implementation_entries` | `[{path, entity_id, pending, directory}]`: the selected Module's realization entries in declaration order, with the realization that declares each |
| `implementation_files` | `[{path, entity_id, pending}]`: existing files the entries bind, each attributed to the most specific entry, plus exact pending entries |
| `implementation_artifacts` | `[{id, path, digest}]` of every bound file when the Agent definition reads implementation; otherwise empty |
| `external_references` | `[{path, directory, digest}]`: one tree digest per external inclusion over its readable files, excluding media and archive suffixes |
| `stage_inputs` | the admitted typed stage inputs |
| `workspace` | the [workspace facts](../worktrees/records.md#workspace-facts) of Candidate worktrees |

Paths are canonical project-relative POSIX paths; workspace paths are absolute. Digests are
`sha256:` followed by 64 lowercase hexadecimal digits.

## Phases

| Phase | Agent | Implementation contents |
| --- | --- | --- |
| `context-solve` | context assessor | no |
| `plan` | planner | no |
| `tasks` | task author | no |
| `spec-review` | spec reviewer | no |
| `issue-solve` | Issue solver | no |
| `code-review` | code reviewer | paths and digests; copies in the capsule |
| `implementation` | programmer | paths and digests; files in place, shared-file binding |

A phase is valid only when it is the bound Agent definition's phase. Implementation contents follow
the definition's `implementation` read, and shared-file binding its `implementation` write.

## Stage inputs

A stage input is a typed value `{type_id, schema_version, data}` of a type registered with Spec
tooling by its owning provider, for example `concorde-plan-artifact`,
`concorde-implementation-task`, `concorde-review-result` or `concorde-issue-selection`. A snapshot
admits a stage input only when its type is in the bound definition's admitted list, at most one per
type, and requires every type in the definition's required list. A failure is
`incompatible_handoff`. A policy preview may omit required inputs that do not exist yet.

## Capsule {#capsule}

The capsule is the `context/` subdirectory of the call's fresh private directory:

| Path in the capsule | Present when | Content |
| --- | --- | --- |
| every `protocol` path | always | byte-identical copy, verified against its digest |
| every `spec_resolution` and `shared_bindings` document member path | always | byte-identical copy, verified against its digest |
| every readable file below each `external_references` path | the definition reads `references` | byte-identical copy |
| every `implementation_artifacts` path | the definition reads but does not write `implementation` | byte-identical copy |
| `context.json` | always | the snapshot as canonical JSON; for a review phase wrapped as `{snapshot, review}` with the typed review input; for an Agent that writes implementation extended with `native_workspace` (the project worktree), `intended_write_paths` (absolute roots of the selected Module's implementation scope), `file_scope_enforcement: "prompt-level"` and `network_and_credentials: "model policy, not OS confinement"` |

A copy whose source no longer matches its recorded digest stops assembly with `stale_context`.
Assembly returns the digest of every file it wrote; verification before acceptance recomputes them
and compares every context document with the current source bytes.

## Agent binding {#agent-binding}

```text
AgentBinding(agent, spec_path, spec_digest, instructions_path, instructions_digest,
             definition_digest, build_manifest_digest, tools, effects, workspace,
             timeout_seconds, digest)
```

`spec_path` is `agents/<name>/spec.md`; `instructions_path` is
`generated/agents/<hyphenated name>.md`; `digest` is the SHA-256 digest of the canonical JSON of
every other field. Binding verifies build freshness as the build manifest contract defines it,
requires the manifest to record the instruction source with `spec_digest` and requires the rendered
instructions to exist. Names are normalized by removing a `concorde-` prefix and replacing hyphens
with underscores.

A definition is refused with `invalid_agent_binding` unless: its instruction source is
`agents/<name>/spec.md`; its workspace kind is `capsule` or `project`; its context type is
`concorde-agent-stage-context` with result `concorde-agent-stage-result`, or
`concorde-review-stage-context` with `concorde-review-stage-result`; required inputs are admitted
inputs; result fields are among `documents`, `plan`, `tasks` and `issue_decision`; effect roles are
among `spec-context`, `implementation` and `references`; every written role is also read; network
is off and credentials are `none`; implementation reads use a `project` workspace; tools are
distinct, drawn from `read`, `grep`, `find`, `ls`, `edit`, `write`, `bash` and `run_checks`,
include `read`, and include `edit` or `write` only with a write role; and the time limit is a
positive integer.

## Revision identities

`target_revision(repository, module)` digests the Module's registry record, the Protocol binding
and its resolved Spec context record. `implementation_digest(repository, module)` digests the
realization entries and the bytes of every bound file. `unconfirmed_files(repository, module)` lists
realization entries that neither exist nor are declared pending.

## Entry points

| Function | Behaviour |
| --- | --- |
| `bind_agent(package_root, name)` | the Agent binding, or `unknown_agent`, `stale_build`, `invalid_agent_binding` |
| `resolve_context(repository, target_id, *, binding, task, focus_id, constraints, stage_inputs, workspace)` | freeze a snapshot |
| `recheck_context(repository, snapshot)` | the recheck; the implementation exemption follows from the snapshot's binding |
| `assemble_capsule(repository, snapshot, directory, review=None)` | write the capsule and return the digests it wrote |
| `verify_capsule(repository, snapshot, directory, digests)` | recompute and compare before acceptance |
| `validate_agent_input(binding, value)` / `validate_agent_result(binding, value)` | the input and result checks against the definition |

## Error codes

| Code | Meaning |
| --- | --- |
| `invalid_phase` | the phase is not the bound definition's phase |
| `invalid_input` | the task is blank |
| `incompatible_handoff` | a stage input is unknown, not admitted, duplicated, or a required one is missing |
| `permission_denied` | the snapshot holds implementation contents the definition does not read, or a result fills a field the definition does not permit |
| `invalid_completion` | a result's outcome is not one the definition lists, or its shape is wrong |
| `invalid_reference` | an external inclusion is not checked out |
| `stale_context` | a recheck, capsule copy or capsule verification no longer matches the snapshot |
| `unknown_agent`, `invalid_agent_binding`, `stale_build` | binding failed |
