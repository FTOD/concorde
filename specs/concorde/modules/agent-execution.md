# Agent execution

## api.execution.execute

AgentProcessExecutor receives a host-built OperationLaunchSpecification and returns OperationExecutionResult with native receipt and typed completion. It probes the selected native integration, builds a fresh process command, supplies the immutable admitted task/context and exact result schema, then validates status, role, invocation, launch/workspace/policy identities and result contracts. Missing binary, unsupported enforcement or malformed/replayed completion fails closed. A process returning success is insufficient without matching evidence. Raw stdout is parsed host-side and cannot become arbitrary predecessor context.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Public functions of operation_executor:

```text
resolve_runtime_bootstrap(integration: str, executable: str, project_root: str, environment: Mapping[str, str]) -> tuple[RuntimeBootstrapFile, ...]
verify_runtime_bootstrap(files: tuple[RuntimeBootstrapFile, ...]) -> None
```

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
