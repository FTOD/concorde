# `langgraph.types`

Public names: `All`, `CachePolicy`, `CheckpointPayload`, `CheckpointStreamPart`, `CheckpointTask`, `Checkpointer`, `Command`, `CustomStreamPart`, `DebugPayload`, `DebugStreamPart`, `Durability`, `GraphOutput`, `Interrupt`, `MessagesStreamPart`, `Overwrite`, `PregelExecutableTask`, `PregelTask`, `RetryPolicy`, `Send`, `StateSnapshot`, `StateUpdate`, `StreamMode`, `StreamPart`, `StreamWriter`, `TaskPayload`, `TaskResultPayload`, `TasksStreamPart`, `TimeoutPolicy`, `TracePolicy`, `UpdatesStreamPart`, `ValuesStreamPart`, `ensure_valid_checkpointer`, `interrupt`, `omit_payload`

## `All(*args, **kwargs)`

## class `CachePolicy(*, key_func: 'KeyFuncT' = <function default_cache_key at 0x7d6b3ffd65c0>, ttl: 'int | None' = None) -> None` (bases: Generic)

Configuration for caching nodes.

### `CachePolicy.__init__(self, *, key_func: 'KeyFuncT' = <function default_cache_key at 0x7d6b3ffd65c0>, ttl: 'int | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

## class `CheckpointPayload` (bases: Generic, dict)

Payload for a checkpoint event.

## class `CheckpointStreamPart` (bases: Generic, dict)

Stream part emitted for `stream_mode="checkpoints"`.

## class `CheckpointTask` (bases: dict)

A task entry within a `CheckpointPayload`.

The keys present depend on the task's state:

- **Error:** `id`, `name`, `error`, `state`
- **Has result:** `id`, `name`, `result`, `interrupts`, `state`
- **Pending:** `id`, `name`, `interrupts`, `state`

## `Checkpointer`

Value of type `UnionType`: `None | bool | langgraph.checkpoint.base.BaseCheckpointSaver`

## class `Command(*, graph: 'str | None' = None, update: 'Any | None' = None, resume: 'dict[str, Any] | Any | None' = None, goto: 'Send | Sequence[Send | N] | N' = ()) -> None` (bases: Generic, ToolOutputMixin)

One or more commands to update the graph's state and send messages to nodes.

Args:
    graph: Graph to send the command to. Supported values are:

        - `None`: the current graph
        - `Command.PARENT`: closest parent graph
    update: Update to apply to the graph's state.
    resume: Value to resume execution with. To be used together with [`interrupt()`][langgraph.types.interrupt].
        Can be one of the following:

        - Mapping of interrupt ids to resume values
        - A single value with which to resume the next interrupt
    goto: Can be one of the following:

        - Name of the node to navigate to next (any node that belongs to the specified `graph`)
        - Sequence of node names to navigate to next
        - `Send` object (to execute a node with the input provided)
        - Sequence of `Send` objects

### `Command.__init__(self, *, graph: 'str | None' = None, update: 'Any | None' = None, resume: 'dict[str, Any] | Any | None' = None, goto: 'Send | Sequence[Send | N] | N' = ()) -> None`

Initialize self.  See help(type(self)) for accurate signature.

## class `CustomStreamPart` (bases: dict)

Stream part emitted for `stream_mode="custom"`.

`data` is whatever value was passed to `StreamWriter` inside a node.

## `DebugPayload()`

Create named, parameterized type aliases.

This provides a backport of the new `type` statement in Python 3.12:

    type ListOrSet[T] = list[T] | set[T]

is equivalent to:

    T = TypeVar("T")
    ListOrSet = TypeAliasType("ListOrSet", list[T] | set[T], type_params=(T,))

The name ListOrSet can then be used as an alias for the type it refers to.

The type_params argument should contain all the type parameters used
in the value of the type alias. If the alias is not generic, this
argument is omitted.

Static type checkers should only support type aliases declared using
TypeAliasType that follow these rules:

- The first argument (the name) must be a string literal.
- The TypeAliasType instance must be immediately assigned to a variable
  of the same name. (For example, 'X = TypeAliasType("Y", int)' is invalid,
  as is 'X, Y = TypeAliasType("X", int), TypeAliasType("Y", int)').

## class `DebugStreamPart` (bases: Generic, dict)

Stream part emitted for `stream_mode="debug"`.

## `Durability(*args, **kwargs)`

## class `GraphOutput(value: 'OutputT', interrupts: 'tuple[Interrupt, ...]' = ()) -> None` (bases: Generic)

Typed container returned by `invoke()` / `ainvoke()` with `version="v2"`.

Attributes:
    value: The final output of the graph (dict, Pydantic model, dataclass, etc.).
    interrupts: Any interrupts that occurred during execution.

### `GraphOutput.__init__(self, value: 'OutputT', interrupts: 'tuple[Interrupt, ...]' = ()) -> None`

Initialize self.  See help(type(self)) for accurate signature.

## class `Interrupt(value: 'Any', id: 'str' = 'placeholder-id', **deprecated_kwargs: 'Unpack[DeprecatedKwargs]') -> 'None'`

Information about an interrupt that occurred in a node.

!!! version-added "Added in version 0.2.24"

!!! version-changed "Changed in version v0.4.0"
    * `interrupt_id` was introduced as a property

!!! version-changed "Changed in version v0.6.0"

    The following attributes have been removed:

    * `ns`
    * `when`
    * `resumable`
    * `interrupt_id`, deprecated in favor of `id`

### `Interrupt.__init__(self, value: 'Any', id: 'str' = 'placeholder-id', **deprecated_kwargs: 'Unpack[DeprecatedKwargs]') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `Interrupt.from_ns(cls, value: 'Any', ns: 'str') -> 'Interrupt'`

### property `Interrupt.interrupt_id`

## class `MessagesStreamPart` (bases: dict)

Stream part emitted for `stream_mode="messages"`.

`data` is a 2-tuple of `(message, metadata)` where `message` is a
`BaseMessage` (e.g. `AIMessageChunk`) and `metadata` is a dict containing
keys like `langgraph_step`, `langgraph_node`, `langgraph_triggers`, etc.

## class `Overwrite(value: 'Any', type: "Literal['__overwrite__']" = '__overwrite__') -> None`

Bypass a reducer and write the wrapped value directly to a `BinaryOperatorAggregate` channel.

Receiving multiple `Overwrite` values for the same channel in a single super-step
will raise an `InvalidUpdateError`.

!!! example

    ```python
    from typing import Annotated
    import operator
    from langgraph.graph import StateGraph
    from langgraph.types import Overwrite

    class State(TypedDict):
        messages: Annotated[list, operator.add]

    def node_a(state: TypedDict):
        # Normal update: uses the reducer (operator.add)
        return {"messages": ["a"]}

    def node_b(state: State):
        # Overwrite: bypasses the reducer and replaces the entire value
        return {"messages": Overwrite(value=["b"])}

    builder = StateGraph(State)
    builder.add_node("node_a", node_a)
    builder.add_node("node_b", node_b)
    builder.set_entry_point("node_a")
    builder.add_edge("node_a", "node_b")
    graph = builder.compile()

    # Without Overwrite in node_b, messages would be ["START", "a", "b"]
    # With Overwrite, messages is just ["b"]
    result = graph.invoke({"messages": ["START"]})
    assert result == {"messages": ["b"]}
    ```

### `Overwrite.__init__(self, value: 'Any', type: "Literal['__overwrite__']" = '__overwrite__') -> None`

Initialize self.  See help(type(self)) for accurate signature.

## class `PregelExecutableTask(name: 'str', input: 'Any', proc: 'Runnable', writes: 'deque[tuple[str, Any]]', config: 'RunnableConfig', triggers: 'Sequence[str]', retry_policy: 'Sequence[RetryPolicy]', cache_key: 'CacheKey | None', id: 'str', path: 'tuple[str | int | tuple, ...]', writers: 'Sequence[Runnable]' = (), subgraphs: 'Sequence[PregelProtocol]' = (), timeout: 'TimeoutPolicy | None' = None) -> None`

PregelExecutableTask(name: 'str', input: 'Any', proc: 'Runnable', writes: 'deque[tuple[str, Any]]', config: 'RunnableConfig', triggers: 'Sequence[str]', retry_policy: 'Sequence[RetryPolicy]', cache_key: 'CacheKey | None', id: 'str', path: 'tuple[str | int | tuple, ...]', writers: 'Sequence[Runnable]' = (), subgraphs: 'Sequence[PregelProtocol]' = (), timeout: 'TimeoutPolicy | None' = None)

### `PregelExecutableTask.__init__(self, name: 'str', input: 'Any', proc: 'Runnable', writes: 'deque[tuple[str, Any]]', config: 'RunnableConfig', triggers: 'Sequence[str]', retry_policy: 'Sequence[RetryPolicy]', cache_key: 'CacheKey | None', id: 'str', path: 'tuple[str | int | tuple, ...]', writers: 'Sequence[Runnable]' = (), subgraphs: 'Sequence[PregelProtocol]' = (), timeout: 'TimeoutPolicy | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

## class `PregelTask(id: ForwardRef('str'), name: ForwardRef('str'), path: ForwardRef('tuple[str | int | tuple, ...]'), error: ForwardRef('Exception | None') = None, interrupts: ForwardRef('tuple[Interrupt, ...]') = (), state: ForwardRef('None | RunnableConfig | StateSnapshot') = None, result: ForwardRef('Any | None') = None)` (bases: tuple)

A Pregel task.

## class `RetryPolicy(initial_interval: ForwardRef('float') = 0.5, backoff_factor: ForwardRef('float') = 2.0, max_interval: ForwardRef('float') = 128.0, max_attempts: ForwardRef('int') = 3, jitter: ForwardRef('bool') = True, retry_on: ForwardRef('type[Exception] | Sequence[type[Exception]] | Callable[[Exception], bool]') = <function default_retry_on at 0x7d6b3ffd6700>)` (bases: tuple)

Configuration for retrying nodes.

!!! version-added "Added in version 0.2.24"

## class `Send(node: 'str', arg: 'Any', *, timeout: 'float | timedelta | TimeoutPolicy | None' = None) -> 'None'`

A message or packet to send to a specific node in the graph.

The `Send` class is used within a `StateGraph`'s conditional edges to
dynamically invoke a node with a custom state at the next step.

Importantly, the sent state can differ from the core graph's state,
allowing for flexible and dynamic workflow management.

One such example is a "map-reduce" workflow where your graph invokes
the same node multiple times in parallel with different states,
before aggregating the results back into the main graph's state.

Attributes:
    node (str): The name of the target node to send the message to.
    arg (Any): The state or message to send to the target node.
    timeout (TimeoutPolicy | None): Optional timeout policy for this specific
        pushed task. If omitted, the target node's timeout policy is used.

!!! example

    ```python
    from typing import Annotated
    from langgraph.types import Send
    from langgraph.graph import END, START
    from langgraph.graph import StateGraph
    import operator

    class OverallState(TypedDict):
        subjects: list[str]
        jokes: Annotated[list[str], operator.add]

    def continue_to_jokes(state: OverallState):
        return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]

    builder = StateGraph(OverallState)
    builder.add_node("generate_joke", lambda state: {"jokes": [f"Joke about {state['subject']}"]})
    builder.add_conditional_edges(START, continue_to_jokes)
    builder.add_edge("generate_joke", END)
    graph = builder.compile()

    # Invoking with two subjects results in a generated joke for each
    graph.invoke({"subjects": ["cats", "dogs"]})
    # {'subjects': ['cats', 'dogs'], 'jokes': ['Joke about cats', 'Joke about dogs']}
    ```

### `Send.__init__(self, /, node: 'str', arg: 'Any', *, timeout: 'float | timedelta | TimeoutPolicy | None' = None) -> 'None'`

Initialize a new instance of the `Send` class.

Args:
    node: The name of the target node to send the message to.
    arg: The state or message to send to the target node.
    timeout: Optional timeout policy for this specific pushed task. A
        number or `timedelta` is treated as a hard `run_timeout`.

## class `StateSnapshot(values: ForwardRef('dict[str, Any] | Any'), next: ForwardRef('tuple[str, ...]'), config: ForwardRef('RunnableConfig'), metadata: ForwardRef('CheckpointMetadata | None'), created_at: ForwardRef('str | None'), parent_config: ForwardRef('RunnableConfig | None'), tasks: ForwardRef('tuple[PregelTask, ...]'), interrupts: ForwardRef('tuple[Interrupt, ...]'))` (bases: tuple)

Snapshot of the state of the graph at the beginning of a step.

## class `StateUpdate(values: ForwardRef('dict[str, Any] | None'), as_node: ForwardRef('str | None') = None, task_id: ForwardRef('str | None') = None)` (bases: tuple)

StateUpdate(values, as_node, task_id)

## `StreamMode(*args, **kwargs)`

## `StreamPart()`

Create named, parameterized type aliases.

This provides a backport of the new `type` statement in Python 3.12:

    type ListOrSet[T] = list[T] | set[T]

is equivalent to:

    T = TypeVar("T")
    ListOrSet = TypeAliasType("ListOrSet", list[T] | set[T], type_params=(T,))

The name ListOrSet can then be used as an alias for the type it refers to.

The type_params argument should contain all the type parameters used
in the value of the type alias. If the alias is not generic, this
argument is omitted.

Static type checkers should only support type aliases declared using
TypeAliasType that follow these rules:

- The first argument (the name) must be a string literal.
- The TypeAliasType instance must be immediately assigned to a variable
  of the same name. (For example, 'X = TypeAliasType("Y", int)' is invalid,
  as is 'X, Y = TypeAliasType("X", int), TypeAliasType("Y", int)').

## `StreamWriter(*args, **kwargs)`

## class `TaskPayload` (bases: dict)

Payload for a task start event.

## class `TaskResultPayload` (bases: dict)

Payload for a task result event.

## class `TasksStreamPart` (bases: dict)

Stream part emitted for `stream_mode="tasks"`.

For task start events, `data` is a `TaskPayload` with `id`, `name`,
`input`, and `triggers` keys.

For task result events, `data` is a `TaskResultPayload` with `id`,
`name`, `error`, `interrupts`, and `result` keys.

## class `TimeoutPolicy(*, run_timeout: 'float | timedelta | None' = None, idle_timeout: 'float | timedelta | None' = None, refresh_on: "Literal['auto', 'heartbeat']" = 'auto') -> None`

Configuration for timing out node attempts.

!!! note "Cooperative cancellation"

    Timeouts rely on asyncio cancellation. If your node uses synchronous
    time.sleep() or other CPU-bound work that blocks the GIL, the timeout will not
    be fired until after the event loop has been released.

!!! note "Inline callback dispatch"

    Under `refresh_on="auto"`, an internal handler refreshes the timeout on any
    callback event that occurs in the execution of the node or its nested descendants.

### `TimeoutPolicy.__init__(self, *, run_timeout: 'float | timedelta | None' = None, idle_timeout: 'float | timedelta | None' = None, refresh_on: "Literal['auto', 'heartbeat']" = 'auto') -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `TimeoutPolicy.coerce(cls, value: 'float | timedelta | TimeoutPolicy | None') -> 'TimeoutPolicy | None'`

Normalize a timeout value to positive-second policy fields.

## class `TracePolicy(*, process_inputs: 'Callable[[Any], Any] | None' = None, process_outputs: 'Callable[[Any], Any] | None' = None) -> None`

Configuration for how a node's run is traced.

Scope: this only transforms what the node's *own* run records. Child runs created
by a traced `bound` runnable and the root graph run are not affected. Plain
function nodes are traced with `trace=False`, so they have no such child runs.

Not intended to redact secrets. To redact inputs/outputs across all runs
(children included), use the LangSmith client's
`hide_inputs`/`hide_outputs`/`anonymizer` instead.

Each processor receives the node's raw input/output value (not a normalized
kwargs dict) and returns the value to record.

### `TracePolicy.__init__(self, *, process_inputs: 'Callable[[Any], Any] | None' = None, process_outputs: 'Callable[[Any], Any] | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

## class `UpdatesStreamPart` (bases: dict)

Stream part emitted for `stream_mode="updates"`.

`data` maps node names to their outputs. May also contain
`__interrupt__` (tuple of `Interrupt` dicts) and `__metadata__` keys.

## class `ValuesStreamPart` (bases: Generic, dict)

Stream part emitted for `stream_mode="values"`.

`data` contains the full state after each step, as returned by `read_channels()`.

## `ensure_valid_checkpointer(checkpointer: 'Checkpointer') -> 'Checkpointer'`

## `interrupt(value: 'Any') -> 'Any'`

Interrupt the graph with a resumable exception from within a node.

The `interrupt` function enables human-in-the-loop workflows by pausing graph
execution and surfacing a value to the client. This value can communicate context
or request input required to resume execution.

In a given node, the first invocation of this function raises a `GraphInterrupt`
exception, halting execution. The provided `value` is included with the exception
and sent to the client executing the graph.

A client resuming the graph must use the [`Command`][langgraph.types.Command]
primitive to specify a value for the interrupt and continue execution.
The graph resumes from the start of the node, **re-executing** all logic.

If a node contains multiple `interrupt` calls, LangGraph matches resume values
to interrupts based on their order in the node. This list of resume values
is scoped to the specific task executing the node and is not shared across tasks.

To use an `interrupt`, you must enable a checkpointer, as the feature relies
on persisting the graph state.

!!! example

    ```python
    import uuid
    from typing import Optional
    from typing_extensions import TypedDict

    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.constants import START
    from langgraph.graph import StateGraph
    from langgraph.types import interrupt, Command


    class State(TypedDict):
        """The graph state."""

        foo: str
        human_value: Optional[str]
        """Human value will be updated using an interrupt."""


    def node(state: State):
        answer = interrupt(
            # This value will be sent to the client
            # as part of the interrupt information.
            "what is your age?"
        )
        print(f"> Received an input from the interrupt: {answer}")
        return {"human_value": answer}


    builder = StateGraph(State)
    builder.add_node("node", node)
    builder.add_edge(START, "node")

    # A checkpointer must be enabled for interrupts to work!
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    config = {
        "configurable": {
            "thread_id": uuid.uuid4(),
        }
    }

    for chunk in graph.stream({"foo": "abc"}, config):
        print(chunk)

    # > {'__interrupt__': (Interrupt(value='what is your age?', id='45fda8478b2ef754419799e10992af06'),)}

    command = Command(resume="some input from a human!!!")

    for chunk in graph.stream(Command(resume="some input from a human!!!"), config):
        print(chunk)

    # > Received an input from the interrupt: some input from a human!!!
    # > {'node': {'human_value': 'some input from a human!!!'}}
    ```

Args:
    value: The value to surface to the client when the graph is interrupted.

Returns:
    Any: On subsequent invocations within the same node (same task to be precise), returns the value provided during the first invocation

Raises:
    GraphInterrupt: On the first invocation within the node, halts execution and surfaces the provided value to the client.

## `omit_payload(_value: 'Any') -> 'dict[str, Any]'`

`TracePolicy` helper that records an empty payload, dropping the value entirely.

Use as `process_inputs` and/or `process_outputs` on a `TracePolicy` to keep a node's
span and its timing while omitting its inputs/outputs from the trace.
