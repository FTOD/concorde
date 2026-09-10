```concorde-document
{
  "id": "document.spec.initialize",
  "targets": [
    "module.spec"
  ],
  "main_visible": true
}
```

# Project initialization

This document defines `concorde-init`'s propose/apply behavior. [module](module.md) introduces the Module; [registry](registry.md) and [values](values.md) define the general query and value records this capability builds on.

## Request and proposal shapes

The public input is `concorde-init-request@1`, an ordinary
`{type_id, schema_version: 1, data}` envelope. `data` is a closed object with required
`action: "propose"|"apply"` and optional `name`, `target_id`, `configuration` and `proposal`.
`name` and `target_id`, when supplied, are nonblank strings. `configuration` is
`concorde-capability-configuration@1` with exactly
`{integration: "codex"|"claude", enforcement: "native"|"outer"}` in its data.
`proposal` is `concorde-project-proposal@1` with exactly `{action: "initialize", base_digest: sha256|null,
files: list[{path, before_digest: sha256|null, content: str}]}` in its data. File paths must be
canonical project-relative paths and distinct; content may be empty. These nested records reject
unknown properties.

`action: "propose"` additionally requires `name` and `configuration` and optionally a `target_id`
(default `module.project`); `action: "apply"` requires the returned typed project proposal. A
proposal records `action: "initialize"`, a nullable `base_digest` and `files: {path, before_digest,
content}`. It creates `specs/project/module.md` with the four mandatory Purpose, Requirements,
Scenarios and Ontology sections, the latter's Entities and Relationships subsections included, and
an inline Mermaid diagram in Relationships with accessible title and description text; no external
diagram file is created. The stub models only known participants, the project Spec and the external
Framework; unknown business requirements, scenarios and architecture are explicit gaps recorded in
the stub's own Unresolved information. The illustration does not turn a draft into a complete
business contract.

Success returns `concorde-init-response@1` with closed data
`{status: "proposed"|"applied", proposal: TypedValue<concorde-project-proposal>|null,
files: list[path]}`. Propose returns the exact typed proposal and its ordered paths, without
changing project files; apply returns `status: "applied"`, `proposal: null` and the applied paths.

## Scenarios

### scenario.spec.propose-initialization — Proposing an initial project structure

- GIVEN an uninitialized project, a name and a supported capability configuration
- WHEN the developer requests action propose
- THEN the capability returns a typed concorde-project-proposal with a null base_digest, every file's before_digest null, and an honest Module stub
- AND no project file changes yet

### scenario.spec.apply-initialization — Applying an accepted proposal

- GIVEN a previously returned proposal whose destinations are still absent and whose Protocol binding is current
- WHEN the developer requests action apply with that exact proposal
- THEN the capability validates the complete resulting registry and documents and commits every file in one transaction
- AND it also creates the Reflection defaults and the topology-artifact ignore file when they are absent
- AND the response reports status applied with the applied paths

### scenario.spec.reject-already-initialized — Rejecting an already-configured project

- GIVEN a project whose configuration already exists
- WHEN initialization is requested
- THEN the capability fails with already_initialized
- AND no existing file is overwritten

### scenario.spec.reject-stale-or-invalid-proposal — Rejecting a stale, invalid or out-of-bound proposal

- GIVEN a proposal whose identity, registry/Protocol binding or destination set is invalid, out of bound, or whose preconditions changed since it was proposed
- WHEN the developer requests action apply
- THEN the capability fails with invalid_proposal, permission_denied or stale_proposal as appropriate
- AND it does not apply a partial file set

### scenario.spec.rollback-on-failure — Restoring original bytes on failure

- GIVEN an accepted proposal is being applied
- WHEN a filesystem or transaction failure occurs after some files were staged
- THEN the capability restores the original bytes and cannot report applied
- BUT a failure during that recovery itself is reported as a failure, never as a successful rollback

## Requirements

### req.spec.init-allowed-files — Initialization touches only its allowed files

Application SHALL touch only .concorde/config.json, .concorde/specs.json,
.concorde/topology-proposals/.gitignore, .concorde/reflections/index.json,
.concorde/reflections/config.json and the explicit document paths named in the proposed registry.

### req.spec.init-null-digests — Every proposed file has a null before_digest

Every proposed file SHALL have a null before_digest.

### req.spec.init-destination-absent — Application requires each destination to still be absent

Application SHALL require each proposed destination to still be absent.

### req.spec.init-no-overwrite — New initialization never overwrites an existing file

A new initialization SHALL NOT overwrite an existing file.

### req.spec.init-no-profile-migration — Older profile configurations are not migratable

An existing configuration declaring an older profile SHALL NOT be treated as migratable.

### req.spec.init-explicit-envelope — Apply admits only the exact proposal envelope

Apply SHALL admit the proposal by its exact concorde-project-proposal@1 envelope.

### req.spec.init-no-token-substitute — Apply rejects issuance tokens and store lookups

Apply SHALL NOT accept an issuance token or a store lookup in place of that exact proposal
envelope.

### req.spec.init-configuration-roles — Outer configuration controls host settings only

The invocation's outer configuration SHALL control host settings for the call itself.

### req.spec.init-propose-configuration-role — Propose controls the proposal's settings

The propose request's configuration SHALL control the project settings written into the proposal.

### req.spec.init-apply-uses-proposal-configuration — Apply uses the proposal's configuration bytes

Apply SHALL use the accepted proposal's configuration bytes rather than a replacement from either
invocation field.

### req.spec.init-configuration-required — Null outer configuration loads existing settings

A null outer configuration SHALL load existing project settings.

### req.spec.init-requires-outer-configuration — Uninitialized projects require outer configuration

Before a project is initialized no such settings exist, so the caller SHALL supply a valid outer
configuration or receive configuration_mismatch.

### req.spec.init-worktree-handoff — Worktree handoffs are reported, not applied

A required worktree handoff SHALL be reported as a blocked result, never as an applied
initialization.

### req.spec.init-no-blind-retry — No blind retries of a rejected proposal

The host SHALL NOT silently retry a rejected proposal against different bytes.

## Executable boundary

At the executable boundary these typed values travel inside a
`concorde-capability-invocation@3` with `capability_id: "concorde-init"`, `mode: "execute"`,
nullable typed outer `configuration`, and `input` containing the request. The returned
`concorde-capability-result@3` has the same capability ID, fresh `invocation_id`, mode, nullable
workspace/output, status and `errors: list[{code, field, message}]`. Successful initialization has
`status: "succeeded"` and the typed output above; admission failures are blocked and execution
failures are failed, with no successful output.
