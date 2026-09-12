```concorde-document
{
  "id": "document.distribution.runtime",
  "owner": "module.distribution",
  "main_visible": true
}
```
# Managed runtime

A caller supplies package/project roots and a reviewed runtime plan; this Module does not select
business requirements or agent context.

## Planning and provisioning

### scenario.distribution.runtime-plan — Planning compares existing state without changing it

- GIVEN a target directory, the loaded runtime specification and its current receipt
- WHEN plan_runtime runs
- THEN it returns one action of create, unchanged, rebuild or conflict with the compared path, role and digest
- AND planning performs no file replacement or package acquisition, though it may run local offline health probes

### scenario.distribution.runtime-provision — Provisioning stages and verifies the reviewed action

- GIVEN a current reviewed plan_runtime action that is not conflict
- WHEN provision_runtime runs
- THEN it stages the locked Python interpreter and official viewer, verifies their identity, and records the resulting receipt
- AND an unchanged verified runtime may be reused, though even `unchanged` rechecks health and may refresh the marker

### scenario.distribution.runtime-provision-failure — Failed acquisition or verification does not replace a valid runtime

- GIVEN a provisioning attempt that fails acquisition or verification
- WHEN provision_runtime returns that failure
- THEN it must not replace a previously valid runtime or mark partial state usable
- AND a create destination that appears after planning is rejected rather than adopted
- AND the returned result carries no successful runtime metadata, so a caller cannot infer recovery from its absence

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of managed_runtime:

```text
load_runtime_spec(package_root: Path, manifest: Mapping[str, Any]) -> ManagedRuntimeSpec
runtime_python(venv: Path) -> Path
plan_runtime(target: Path, spec: ManagedRuntimeSpec, receipt: Mapping[str, Any]) -> dict[str, str]
provision_runtime(target: Path, framework: Path, spec: ManagedRuntimeSpec, action: Mapping[str, str], *, bootstrap_python: str | None=None) -> dict[str, Any]
```

## Values and completion

`ManagedRuntimeSpec` is a frozen record with string fields `venv`, `requirements`, `launcher`,
`python`, `requirements_sha256`, `runtime_sha256`, `langgraph_version` and `concorde_version`, a
`skills: tuple[str, ...]` inventory, and `viewer: ViewerSpec`. Paths are explicit relative
locations; requirements identify the locked input and runtime digests identify the accepted
combination. `ViewerSpec` has string fields `provider`, `version`, `package`, `asset_url`,
`asset_sha256`, `node`, `npm_package`, `npm_lock`, `lock_sha256`, `integrity`, `install_relative`,
`entrypoint`, `launcher`, positive integer `asset_bytes`, and ordered `graph_paths: tuple[str, ...]`.
The package input binds an immutable official asset, size/hash and npm integrity; it does not
accept an arbitrary latest release. Current accepted requirements are Python >=3.11 and Node >=18.
Changing these pins is an explicit package revision, not an automatic upgrade during a task.

`runtime_python(venv)` returns the platform's Python path inside that environment; path
construction alone does not verify an installation. `plan_runtime(target, spec, receipt)` returns
string fields `path`, `role="runtime"`, `sha256` and `action`, with optional `reason`. Callers pass
the returned action to provisioning; a conflict is not an admissible provisioning action.

`provision_runtime` takes a trusted target, installed Framework root, loaded specification and
current reviewed action. Optional `bootstrap_python` chooses the host bootstrap interpreter;
omission uses the current interpreter. Success returns `path`, `python`, `python_version`,
`requirements`, `requirements_sha256`, `runtime_sha256`, `launcher`, `verified_skills` and a
`viewer` object. That object carries provider/version/package, asset_url/asset_sha256/asset_bytes,
integrity/lock_sha256, node/node_version/npm_version, install_relative/entrypoint/launcher and
ordered graph_paths. All are strings except asset_bytes (integer) and the two string-array fields.
The result records what was verified, not just requested. Accepted state has a schema-2,
owner-concorde marker binding its path, Concorde version, lock/runtime digests, observed tool
versions, viewer version/entrypoint and verified Skill inventory.

## Effects, failures and retries

Provisioning may create the environment, acquire the locked dependencies/viewer, run verification
processes and write the owned receipt. Malformed requirements, ownership conflicts, unsupported
actions, failed processes or mismatched installed identity raise `ManagedRuntimeError(ValueError)`;
filesystem/process exceptions may also propagate.

The required replacement design preserves the previous valid runtime until the replacement is
verified and restores it after a failed rebuild; this Module's Unresolved information names the gap
between that design and the current provisioning implementation. Replan from actual state before
retrying; package/lock changes require a new plan.
