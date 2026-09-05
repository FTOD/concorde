# Managed runtime

## api.runtime.provision

load_runtime_spec(package_root) reads locked runtime requirements; plan_runtime describes local provisioning state; provision_runtime stages the specified Python environment and official viewer using versioned/hash-bound inputs. Verification rejects a missing/incorrect Python, dependency lock, viewer artifact or receipt. Runtime acquisition failure must not bless a partial installation. A caller supplies package/project roots and reviewed runtime plan; this Module does not select business requirements or agent context. Provisioning and rollback preserve previously valid owned runtime state.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of managed_runtime:

```text
load_runtime_spec(package_root: Path, manifest: Mapping[str, Any]) -> ManagedRuntimeSpec
runtime_python(venv: Path) -> Path
plan_runtime(target: Path, spec: ManagedRuntimeSpec, receipt: Mapping[str, Any]) -> dict[str, str]
provision_runtime(target: Path, framework: Path, spec: ManagedRuntimeSpec, action: Mapping[str, str], *, bootstrap_python: str | None=None) -> dict[str, Any]
```

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
