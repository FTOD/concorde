```concorde-document
{
  "id": "document.distribution.runtime",
  "targets": [
    "module.distribution"
  ],
  "main_visible": true
}
```
# Managed runtime

## interface.distribution.runtime

load_runtime_spec(package_root, manifest) reads locked runtime requirements; plan_runtime describes local provisioning state; provision_runtime stages the specified Python environment and official viewer using versioned/hash-bound inputs. Verification rejects a missing/incorrect Python, dependency lock, viewer artifact or receipt. Runtime acquisition failure must not bless a partial installation. A caller supplies package/project roots and reviewed runtime plan; this Module does not select business requirements or agent context. Provisioning and rollback preserve previously valid owned runtime state.

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
`skills: tuple[str, ...]` inventory, and `viewer: ViewerSpec`. Paths are explicit relative locations;
requirements identify the locked input and runtime digests identify the accepted combination.
`ViewerSpec` has string fields `provider`, `version`, `package`, `asset_url`, `asset_sha256`, `node`,
`npm_package`, `npm_lock`, `lock_sha256`, `integrity`, `install_relative`, `entrypoint`, `launcher`,
positive integer `asset_bytes`, and ordered `graph_paths: tuple[str, ...]`. The package input binds
an immutable official asset, size/hash and npm integrity; it does not accept an arbitrary latest
release. Current accepted requirements are Python >=3.11 and Node >=18. Changing these pins is an
explicit package revision, not an automatic upgrade during a task.

`runtime_python(venv)` returns the platform's Python path inside that environment; path construction
alone does not verify an installation. `plan_runtime(target, spec, receipt)` returns string fields
`path`, `role="runtime"`, `sha256` and `action`, with optional `reason`. The action is `create` for
an absent owned destination, `unchanged` for verified matching state, `rebuild` for owned stale or
unhealthy state, or `conflict` for unsafe/unowned state. Planning may run local offline health probes
but does not replace files or acquire packages. Callers pass the returned action to provisioning;
a conflict is not an admissible provisioning action.

`provision_runtime` takes a trusted target, installed Framework root, loaded specification and
current reviewed action. Optional bootstrap_python chooses the host bootstrap interpreter; omission
uses the current interpreter. Success returns `path`, `python`, `python_version`, `requirements`,
`requirements_sha256`, `runtime_sha256`, `launcher`, `verified_skills` and a `viewer` object. That
object carries provider/version/package, asset_url/asset_sha256/asset_bytes, integrity/lock_sha256,
node/node_version/npm_version, install_relative/entrypoint/launcher and ordered graph_paths.
All are strings except asset_bytes (integer) and the two string-array fields. The result records
what was verified, not just requested. Accepted state has a schema-2, owner-concorde marker binding
its path, Concorde version, lock/runtime digests, observed tool versions, viewer version/entrypoint
and verified Skill inventory.

## Effects, failures and retries

Provisioning may create the environment, acquire the locked dependencies/viewer, run verification
processes and write the owned receipt. Even `unchanged` rechecks health and may refresh the marker;
it is not a read-only operation. A `create` destination that appears after planning is rejected.
Malformed requirements, ownership conflicts, unsupported actions, failed processes or mismatched
installed identity raise `ManagedRuntimeError(ValueError)`; filesystem/process exceptions may also
propagate. A failed call returns no successful runtime metadata.

The required replacement design preserves the previous valid runtime until the replacement is
verified and restores it after a failed rebuild. The current direct provisioning implementation
still removes an owned environment before rebuilding; fulfilling this preservation promise is an
explicit implementation gap. Callers must not infer recovery from the absence of success metadata.
A recovery failure remains failed and requires operator intervention. Replan from actual state
before retrying; package/lock changes require a new plan. This revision defines intended recovery
behavior without claiming that code migration or verification has completed.
