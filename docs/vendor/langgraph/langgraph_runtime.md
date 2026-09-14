# `langgraph.runtime`

Public names: `BaseUser`, `ExecutionInfo`, `RunControl`, `Runtime`, `ServerInfo`, `get_runtime`

## class `BaseUser(*args, **kwargs)` (bases: Protocol)

The base ASGI user protocol

### `BaseUser.__init__(self, *args, **kwargs)`

### property `BaseUser.display_name`

The display name of the user.

### property `BaseUser.identity`

The unique identifier for the user.

### property `BaseUser.is_authenticated`

Whether the user is authenticated.

### property `BaseUser.permissions`

The permissions associated with the user.

## class `ExecutionInfo(checkpoint_id: 'str', checkpoint_ns: 'str', task_id: 'str', thread_id: 'str | None' = None, run_id: 'str | None' = None, node_attempt: 'int' = 1, node_first_attempt_time: 'float | None' = None) -> None`

Read-only execution info/metadata for the execution of current thread/run/node.

### `ExecutionInfo.__init__(self, checkpoint_id: 'str', checkpoint_ns: 'str', task_id: 'str', thread_id: 'str | None' = None, run_id: 'str | None' = None, node_attempt: 'int' = 1, node_first_attempt_time: 'float | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `ExecutionInfo.patch(self, **overrides: 'Any') -> 'ExecutionInfo'`

Return a new execution info object with selected fields replaced.

## class `RunControl() -> 'None'`

Run-scoped control surface for cooperative draining.

Intended for a single graph run. Create a fresh `RunControl` per run;
reusing a control after `request_drain()` leaves it drained.

Safe to call from any thread: the drain request is represented by a
single attribute write, so no lock is needed for this signal.
If more mutable state is added here, add synchronization.

### `RunControl.__init__(self) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### property `RunControl.drain_reason`

### property `RunControl.drain_requested`

### `RunControl.request_drain(self, reason: 'str' = 'shutdown') -> 'None'`

## class `Runtime(*, context: 'ContextT' = None, store: 'BaseStore | None' = None, stream_writer: 'StreamWriter' = <function _no_op_stream_writer at 0x7d6b400ad620>, heartbeat: 'Callable[[], None]' = <function _no_op_heartbeat at 0x7d6b3fca1e40>, previous: 'Any' = None, execution_info: 'ExecutionInfo | None' = None, server_info: 'ServerInfo | None' = None, control: 'RunControl | None' = None) -> None` (bases: Generic)

Convenience class that bundles run-scoped context and other runtime utilities.

This class is injected into graph nodes and middleware. It provides access to
`context`, `store`, `stream_writer`, `previous`, and `execution_info`.

!!! note "Accessing `config`"

    `Runtime` does not include `config`. To access `RunnableConfig`, you can inject
    it directly by adding a `config: RunnableConfig` parameter to your node function
    (recommended), or use `get_config()` from `langgraph.config`.

!!! note
    `ToolRuntime` (from `langgraph.prebuilt`) is a subclass that provides similar
    functionality but is designed specifically for tools. It shares `context`, `store`,
    and `stream_writer` with `Runtime`, and adds tool-specific attributes like `config`,
    `state`, and `tool_call_id`.

!!! version-added "Added in version v0.6.0"

Example:

```python
from typing import TypedDict
from langgraph.graph import StateGraph
from dataclasses import dataclass
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore


@dataclass
class Context:  # (1)!
    user_id: str


class State(TypedDict, total=False):
    response: str


store = InMemoryStore()  # (2)!
store.put(("users",), "user_123", {"name": "Alice"})


def personalized_greeting(state: State, runtime: Runtime[Context]) -> State:
    '''Generate personalized greeting using runtime context and store.'''
    user_id = runtime.context.user_id  # (3)!
    name = "unknown_user"
    if runtime.store:
        if memory := runtime.store.get(("users",), user_id):
            name = memory.value["name"]

    response = f"Hello {name}! Nice to see you again."
    return {"response": response}


graph = (
    StateGraph(state_schema=State, context_schema=Context)
    .add_node("personalized_greeting", personalized_greeting)
    .set_entry_point("personalized_greeting")
    .set_finish_point("personalized_greeting")
    .compile(store=store)
)

result = graph.invoke({}, context=Context(user_id="user_123"))
print(result)
# > {'response': 'Hello Alice! Nice to see you again.'}
```

1. Define a schema for the runtime context.
2. Create a store to persist memories and other information.
3. Use the runtime context to access the `user_id`.

### `Runtime.__init__(self, *, context: 'ContextT' = None, store: 'BaseStore | None' = None, stream_writer: 'StreamWriter' = <function _no_op_stream_writer at 0x7d6b400ad620>, heartbeat: 'Callable[[], None]' = <function _no_op_heartbeat at 0x7d6b3fca1e40>, previous: 'Any' = None, execution_info: 'ExecutionInfo | None' = None, server_info: 'ServerInfo | None' = None, control: 'RunControl | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### property `Runtime.drain_reason`

### property `Runtime.drain_requested`

### `Runtime.merge(self, other: 'Runtime[ContextT]') -> 'Runtime[ContextT]'`

Merge two runtimes together.

If a value is not provided in the other runtime, the value from the current runtime is used.

### `Runtime.override(self, **overrides: 'Unpack[_RuntimeOverrides[ContextT]]') -> 'Runtime[ContextT]'`

Replace the runtime with a new runtime with the given overrides.

### `Runtime.patch_execution_info(self, **overrides: 'Any') -> 'Runtime[ContextT]'`

Return a new runtime with selected execution_info fields replaced.

## class `ServerInfo(assistant_id: 'str', graph_id: 'str', user: 'BaseUser | None' = None) -> None`

Metadata injected by LangGraph Server. None when running open-source LangGraph without LangSmith deployments.

### `ServerInfo.__init__(self, assistant_id: 'str', graph_id: 'str', user: 'BaseUser | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

## `get_runtime(context_schema: 'type[ContextT] | None' = None) -> 'Runtime[ContextT]'`

Get the runtime for the current graph run.

Args:
    context_schema: Optional schema used for type hinting the return type of the runtime.

Returns:
    The runtime for the current graph run.
