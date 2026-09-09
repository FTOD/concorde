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

## feature.spec.initialize

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
