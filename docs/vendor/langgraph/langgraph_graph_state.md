# `langgraph.graph.state`

Public names: `CompiledStateGraph`, `StateGraph`

## class `CompiledStateGraph(*, builder: 'StateGraph[StateT, ContextT, InputT, OutputT]', schema_to_mapper: 'dict[type[Any], Callable[[Any], Any] | None]', **kwargs: 'Any') -> 'None'` (bases: Pregel, Generic)

Pregel manages the runtime behavior for LangGraph applications.

## Overview

Pregel combines [**actors**](https://en.wikipedia.org/wiki/Actor_model)
and **channels** into a single application.
**Actors** read data from channels and write data to channels.
Pregel organizes the execution of the application into multiple steps,
following the **Pregel Algorithm**/**Bulk Synchronous Parallel** model.

Each step consists of three phases:

- **Plan**: Determine which **actors** to execute in this step. For example,
    in the first step, select the **actors** that subscribe to the special
    **input** channels; in subsequent steps,
    select the **actors** that subscribe to channels updated in the previous step.
- **Execution**: Execute all selected **actors** in parallel,
    until all complete, or one fails, or a timeout is reached. During this
    phase, channel updates are invisible to actors until the next step.
- **Update**: Update the channels with the values written by the **actors**
    in this step.

Repeat until no **actors** are selected for execution, or a maximum number of
steps is reached.

## Actors

An **actor** is a `PregelNode`.
It subscribes to channels, reads data from them, and writes data to them.
It can be thought of as an **actor** in the Pregel algorithm.
`PregelNodes` implement LangChain's
Runnable interface.

## Channels

Channels are used to communicate between actors (`PregelNodes`).
Each channel has a value type, an update type, and an update function – which
takes a sequence of updates and
modifies the stored value. Channels can be used to send data from one chain to
another, or to send data from a chain to itself in a future step. LangGraph
provides a number of built-in channels:

### Basic channels: LastValue and Topic

- `LastValue`: The default channel, stores the last value sent to the channel,
   useful for input and output values, or for sending data from one step to the next
- `Topic`: A configurable PubSub Topic, useful for sending multiple values
   between *actors*, or for accumulating output. Can be configured to deduplicate
   values, and/or to accumulate values over the course of multiple steps.

### Advanced channels: Context and BinaryOperatorAggregate

- `Context`: exposes the value of a context manager, managing its lifecycle.
    Useful for accessing external resources that require setup and/or teardown. e.g.
    `client = Context(httpx.Client)`
- `BinaryOperatorAggregate`: stores a persistent value, updated by applying
    a binary operator to the current value and each update
    sent to the channel, useful for computing aggregates over multiple steps. e.g.
    `total = BinaryOperatorAggregate(int, operator.add)`

## Examples

Most users will interact with Pregel via a
[StateGraph (Graph API)][langgraph.graph.StateGraph] or via an
[entrypoint (Functional API)][langgraph.func.entrypoint].

However, for **advanced** use cases, Pregel can be used directly. If you're
not sure whether you need to use Pregel directly, then the answer is probably no
- you should use the Graph API or Functional API instead. These are higher-level
interfaces that will compile down to Pregel under the hood.

Here are some examples to give you a sense of how it works:

Example: Single node application
    ```python
    from langgraph.channels import EphemeralValue
    from langgraph.pregel import Pregel, NodeBuilder

    node1 = (
        NodeBuilder().subscribe_only("a")
        .do(lambda x: x + x)
        .write_to("b")
    )

    app = Pregel(
        nodes={"node1": node1},
        channels={
            "a": EphemeralValue(str),
            "b": EphemeralValue(str),
        },
        input_channels=["a"],
        output_channels=["b"],
    )

    app.invoke({"a": "foo"})
    ```

    ```con
    {'b': 'foofoo'}
    ```

Example: Using multiple nodes and multiple output channels
    ```python
    from langgraph.channels import LastValue, EphemeralValue
    from langgraph.pregel import Pregel, NodeBuilder

    node1 = (
        NodeBuilder().subscribe_only("a")
        .do(lambda x: x + x)
        .write_to("b")
    )

    node2 = (
        NodeBuilder().subscribe_to("b")
        .do(lambda x: x["b"] + x["b"])
        .write_to("c")
    )


    app = Pregel(
        nodes={"node1": node1, "node2": node2},
        channels={
            "a": EphemeralValue(str),
            "b": LastValue(str),
            "c": EphemeralValue(str),
        },
        input_channels=["a"],
        output_channels=["b", "c"],
    )

    app.invoke({"a": "foo"})
    ```

    ```con
    {'b': 'foofoo', 'c': 'foofoofoofoo'}
    ```

Example: Using a Topic channel
    ```python
    from langgraph.channels import LastValue, EphemeralValue, Topic
    from langgraph.pregel import Pregel, NodeBuilder

    node1 = (
        NodeBuilder().subscribe_only("a")
        .do(lambda x: x + x)
        .write_to("b", "c")
    )

    node2 = (
        NodeBuilder().subscribe_only("b")
        .do(lambda x: x + x)
        .write_to("c")
    )


    app = Pregel(
        nodes={"node1": node1, "node2": node2},
        channels={
            "a": EphemeralValue(str),
            "b": EphemeralValue(str),
            "c": Topic(str, accumulate=True),
        },
        input_channels=["a"],
        output_channels=["c"],
    )

    app.invoke({"a": "foo"})
    ```

    ```pycon
    {"c": ["foofoo", "foofoofoofoo"]}
    ```

Example: Using a `BinaryOperatorAggregate` channel
    ```python
    from langgraph.channels import EphemeralValue, BinaryOperatorAggregate
    from langgraph.pregel import Pregel, NodeBuilder


    node1 = (
        NodeBuilder().subscribe_only("a")
        .do(lambda x: x + x)
        .write_to("b", "c")
    )

    node2 = (
        NodeBuilder().subscribe_only("b")
        .do(lambda x: x + x)
        .write_to("c")
    )


    def reducer(current, update):
        if current:
            return current + " | " + update
        else:
            return update


    app = Pregel(
        nodes={"node1": node1, "node2": node2},
        channels={
            "a": EphemeralValue(str),
            "b": EphemeralValue(str),
            "c": BinaryOperatorAggregate(str, operator=reducer),
        },
        input_channels=["a"],
        output_channels=["c"],
    )

    app.invoke({"a": "foo"})
    ```

    ```con
    {'c': 'foofoo | foofoofoofoo'}
    ```

Example: Introducing a cycle
    This example demonstrates how to introduce a cycle in the graph, by having
    a chain write to a channel it subscribes to.

    Execution will continue until a `None` value is written to the channel.

    ```python
    from langgraph.channels import EphemeralValue
    from langgraph.pregel import Pregel, NodeBuilder, ChannelWriteEntry

    example_node = (
        NodeBuilder()
        .subscribe_only("value")
        .do(lambda x: x + x if len(x) < 10 else None)
        .write_to(ChannelWriteEntry(channel="value", skip_none=True))
    )

    app = Pregel(
        nodes={"example_node": example_node},
        channels={
            "value": EphemeralValue(str),
        },
        input_channels=["value"],
        output_channels=["value"],
    )

    app.invoke({"value": "a"})
    ```

    ```con
    {'value': 'aaaaaaaaaaaaaaaa'}
    ```

### `CompiledStateGraph.__init__(self, *, builder: 'StateGraph[StateT, ContextT, InputT, OutputT]', schema_to_mapper: 'dict[type[Any], Callable[[Any], Any] | None]', **kwargs: 'Any') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `CompiledStateGraph.attach_branch(self, start: 'str', name: 'str', branch: 'BranchSpec', *, with_reader: 'bool' = True) -> 'None'`

### `CompiledStateGraph.attach_edge(self, starts: 'str | Sequence[str]', end: 'str') -> 'None'`

### `CompiledStateGraph.attach_node(self, key: 'str', node: 'StateNodeSpec[Any, ContextT] | None') -> 'None'`

### `CompiledStateGraph.get_input_jsonschema(self, config: 'RunnableConfig | None' = None) -> 'dict[str, Any]'`

Get a JSON schema that represents the input to the `Runnable`.

Args:
    config: A config to use when generating the schema.

Returns:
    A JSON schema that represents the input to the `Runnable`.

Example:
    ```python
    from langchain_core.runnables import RunnableLambda


    def add_one(x: int) -> int:
        return x + 1


    runnable = RunnableLambda(add_one)

    print(runnable.get_input_jsonschema())
    ```

!!! version-added "Added in `langchain-core` 0.3.0"

### `CompiledStateGraph.get_output_jsonschema(self, config: 'RunnableConfig | None' = None) -> 'dict[str, Any]'`

Get a JSON schema that represents the output of the `Runnable`.

Args:
    config: A config to use when generating the schema.

Returns:
    A JSON schema that represents the output of the `Runnable`.

Example:
    ```python
    from langchain_core.runnables import RunnableLambda


    def add_one(x: int) -> int:
        return x + 1


    runnable = RunnableLambda(add_one)

    print(runnable.get_output_jsonschema())
    ```

!!! version-added "Added in `langchain-core` 0.3.0"

## class `StateGraph(state_schema: 'type[StateT]', context_schema: 'type[ContextT] | None' = None, *, input_schema: 'type[InputT] | None' = None, output_schema: 'type[OutputT] | None' = None, **kwargs: 'Unpack[DeprecatedKwargs]') -> 'None'` (bases: Generic)

A graph whose nodes communicate by reading and writing to a shared state.

The signature of each node is `State -> Partial<State>`.

Each state key can optionally be annotated with a reducer function that
will be used to aggregate the values of that key received from multiple nodes.
The signature of a reducer function is `(Value, Value) -> Value`.

!!! warning

    `StateGraph` is a builder class and cannot be used directly for execution.
    You must first call `.compile()` to create an executable graph that supports
    methods like `invoke()`, `stream()`, `astream()`, and `ainvoke()`. See the
    `CompiledStateGraph` documentation for more details.

Args:
    state_schema: The schema class that defines the state.
    context_schema: The schema class that defines the runtime context.

        Use this to expose immutable context data to your nodes, like `user_id`, `db_conn`, etc.
    input_schema: The schema class that defines the input to the graph.
    output_schema: The schema class that defines the output from the graph.

!!! warning "`config_schema` Deprecated"
    The `config_schema` parameter is deprecated in v0.6.0 and support will be removed in v2.0.0.
    Please use `context_schema` instead to specify the schema for run-scoped context.

Example:
    ```python
    from langchain_core.runnables import RunnableConfig
    from typing_extensions import Annotated, TypedDict
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import StateGraph
    from langgraph.runtime import Runtime


    def reducer(a: list, b: int | None) -> list:
        if b is not None:
            return a + [b]
        return a


    class State(TypedDict):
        x: Annotated[list, reducer]


    class Context(TypedDict):
        r: float


    graph = StateGraph(state_schema=State, context_schema=Context)


    def node(state: State, runtime: Runtime[Context]) -> dict:
        r = runtime.context.get("r", 1.0)
        x = state["x"][-1]
        next_value = x * r * (1 - x)
        return {"x": next_value}


    graph.add_node("A", node)
    graph.set_entry_point("A")
    graph.set_finish_point("A")
    compiled = graph.compile()

    step1 = compiled.invoke({"x": 0.5}, context={"r": 3.0})
    # {'x': [0.5, 0.75]}
    ```

### `StateGraph.__init__(self, state_schema: 'type[StateT]', context_schema: 'type[ContextT] | None' = None, *, input_schema: 'type[InputT] | None' = None, output_schema: 'type[OutputT] | None' = None, **kwargs: 'Unpack[DeprecatedKwargs]') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `StateGraph.add_conditional_edges(self, source: 'str', path: 'Callable[..., Hashable | Sequence[Hashable]] | Callable[..., Awaitable[Hashable | Sequence[Hashable]]] | Runnable[Any, Hashable | Sequence[Hashable]]', path_map: 'dict[Hashable, str] | list[str] | None' = None) -> 'Self'`

Add a conditional edge from the starting node to any number of destination nodes.

Args:
    source: The starting node. This conditional edge will run when
        exiting this node.
    path: The callable that determines the next node or nodes.

        If not specifying `path_map` it should return one or more nodes.

        If it returns `'END'`, the graph will stop execution.
    path_map: Optional mapping of paths to node names.

        If omitted the paths returned by `path` should be node names.

Returns:
    Self: The instance of the graph, allowing for method chaining.

!!! warning
    Without type hints on the `path` function's return value (e.g., `-> Literal["foo", "__end__"]:`)
    or a path_map, the graph visualization assumes the edge could transition to any node in the graph.

### `StateGraph.add_edge(self, start_key: 'str | list[str]', end_key: 'str') -> 'Self'`

Add a directed edge from the start node (or list of start nodes) to the end node.

When a single start node is provided, the graph will wait for that node to complete
before executing the end node. When multiple start nodes are provided,
the graph will wait for ALL of the start nodes to complete before executing the end node.

Args:
    start_key: The key(s) of the start node(s) of the edge.
    end_key: The key of the end node of the edge.

Raises:
    ValueError: If the start key is `'END'` or if the start key or end key is not present in the graph.

Returns:
    Self: The instance of the `StateGraph`, allowing for method chaining.

### `StateGraph.add_node(self, node: 'str | StateNode[NodeInputT, ContextT]', action: 'StateNode[NodeInputT, ContextT] | None' = None, *, defer: 'bool' = False, metadata: 'dict[str, Any] | None' = None, input_schema: 'type[NodeInputT] | None' = None, retry_policy: 'RetryPolicy | Sequence[RetryPolicy] | None' = None, cache_policy: 'CachePolicy | None' = None, error_handler: 'StateNode[Any, ContextT] | None' = None, destinations: 'dict[str, str] | tuple[str, ...] | None' = None, timeout: 'float | timedelta | TimeoutPolicy | None' = None, trace_policy: 'TracePolicy | None' = None, **kwargs: 'Unpack[DeprecatedKwargs]') -> 'Self'`

Add a new node to the `StateGraph`.

Args:
    node: The function or runnable this node will run.

        If a string is provided, it will be used as the node name, and action will be used as the function or runnable.
    action: The action associated with the node.

        Will be used as the node function or runnable if `node` is a string (node name).
    defer: Whether to defer the execution of the node until the run is about to end.
    metadata: The metadata associated with the node.
    input_schema: The input schema for the node. (Default: the graph's state schema)
    retry_policy: The retry policy for the node.

        If a sequence is provided, the first matching policy will be applied.
    cache_policy: The cache policy for the node.
    error_handler: Optional node-level error handler callable for this node.
    trace_policy: Optional policy controlling how this node's run is traced. Its
        `process_inputs` callable transforms the node's input before it is
        recorded (e.g. to omit or summarize large message history) without
        changing the value passed to the node. Does not affect execution.
    destinations: Destinations that indicate where a node can route to.

        Useful for edgeless graphs with nodes that return `Command` objects.

        If a `dict` is provided, the keys will be used as the target node names and the values will be used as the labels for the edges.

        If a `tuple` is provided, the values will be used as the target node names.

        !!! warning

            This is only used for graph rendering and doesn't have any effect on the graph execution.
    timeout: Timeout for each node attempt. A number or `timedelta` is
        a hard wall-clock cap and is not refreshed. Use `TimeoutPolicy`
        to configure both a wall-clock `run_timeout` and an
        `idle_timeout` refreshed by progress signals. When exceeded, a
        [`NodeTimeoutError`][langgraph.errors.NodeTimeoutError] is raised
        and the retry policy (if any) decides whether to retry. Timeouts
        are supported only for async nodes; sync nodes cannot be safely
        cancelled in-process.

Example:
    ```python
    from typing_extensions import TypedDict

    from langchain_core.runnables import RunnableConfig
    from langgraph.graph import START, StateGraph


    class State(TypedDict):
        x: int


    def my_node(state: State, config: RunnableConfig) -> State:
        return {"x": state["x"] + 1}


    builder = StateGraph(State)
    builder.add_node(my_node)  # node name will be 'my_node'
    builder.add_edge(START, "my_node")
    graph = builder.compile()
    graph.invoke({"x": 1})
    # {'x': 2}
    ```

Example: Customize the name:
    ```python
    builder = StateGraph(State)
    builder.add_node("my_fair_node", my_node)
    builder.add_edge(START, "my_fair_node")
    graph = builder.compile()
    graph.invoke({"x": 1})
    # {'x': 2}
    ```

Returns:
    Self: The instance of the `StateGraph`, allowing for method chaining.

### `StateGraph.add_sequence(self, nodes: 'Sequence[StateNode[NodeInputT, ContextT] | tuple[str, StateNode[NodeInputT, ContextT]]]') -> 'Self'`

Add a sequence of nodes that will be executed in the provided order.

Args:
    nodes: A sequence of `StateNode` (callables that accept a `state` arg) or `(name, StateNode)` tuples.

        If no names are provided, the name will be inferred from the node object (e.g. a `Runnable` or a `Callable` name).

        Each node will be executed in the order provided.

Raises:
    ValueError: If the sequence is empty.
    ValueError: If the sequence contains duplicate node names.

Returns:
    Self: The instance of the `StateGraph`, allowing for method chaining.

### `StateGraph.compile(self, checkpointer: 'Checkpointer' = None, *, cache: 'BaseCache | None' = None, store: 'BaseStore | None' = None, interrupt_before: 'All | list[str] | None' = None, interrupt_after: 'All | list[str] | None' = None, debug: 'bool' = False, name: 'str | None' = None, transformers: 'Sequence[Callable[[tuple[str, ...]], Any]] | None' = None) -> 'CompiledStateGraph[StateT, ContextT, InputT, OutputT]'`

Compiles the `StateGraph` into a `CompiledStateGraph` object.

The compiled graph implements the `Runnable` interface and can be invoked,
streamed, batched, and run asynchronously.

Args:
    checkpointer: A checkpoint saver object or flag.

        If provided, this `Checkpointer` serves as a fully versioned "short-term memory" for the graph,
        allowing it to be paused, resumed, and replayed from any point.

        If `None`, it may inherit the parent graph's checkpointer when used as a subgraph.

        If `False`, it will not use or inherit any checkpointer.

        **Important**: When a checkpointer is enabled, you should pass a `thread_id`
        in the config when invoking the graph:

        ```python
        config = {"configurable": {"thread_id": "my-thread"}}
        graph.invoke(inputs, config)
        ```

        The `thread_id` is the key used to store and retrieve checkpoints. Use a
        unique ID for independent runs, or reuse the same ID to accumulate state
        across invocations (e.g., for conversation memory).

    interrupt_before: An optional list of node names to interrupt before.
    interrupt_after: An optional list of node names to interrupt after.
    debug: A flag indicating whether to enable debug mode.
    name: The name to use for the compiled graph.
    transformers: Optional sequence of `StreamTransformer` classes or
        configured factories. Classes and factories are instantiated
        per run whenever `stream_events(version="v3")` / `astream_events(version="v3")` is called and are
        propagated to subgraph scopes. Custom factories should follow
        the standard `StreamTransformer` constructor shape by
        accepting `scope` as their first argument. Appended after the
        built-in stream transformers.

Returns:
    CompiledStateGraph: The compiled `StateGraph`.

### `StateGraph.set_conditional_entry_point(self, path: 'Callable[..., Hashable | Sequence[Hashable]] | Callable[..., Awaitable[Hashable | Sequence[Hashable]]] | Runnable[Any, Hashable | Sequence[Hashable]]', path_map: 'dict[Hashable, str] | list[str] | None' = None) -> 'Self'`

Sets a conditional entry point in the graph.

Args:
    path: The callable that determines the next node or nodes.

        If not specifying `path_map` it should return one or more nodes.

        If it returns END, the graph will stop execution.
    path_map: Optional mapping of paths to node names.

        If omitted the paths returned by `path` should be node names.

Returns:
    Self: The instance of the graph, allowing for method chaining.

### `StateGraph.set_entry_point(self, key: 'str') -> 'Self'`

Specifies the first node to be called in the graph.

Equivalent to calling `add_edge(START, key)`.

Parameters:
    key (str): The key of the node to set as the entry point.

Returns:
    Self: The instance of the graph, allowing for method chaining.

### `StateGraph.set_finish_point(self, key: 'str') -> 'Self'`

Marks a node as a finish point of the graph.

If the graph reaches this node, it will cease execution.

Parameters:
    key (str): The key of the node to set as the finish point.

Returns:
    Self: The instance of the graph, allowing for method chaining.

### `StateGraph.set_node_defaults(self, *, retry_policy: 'RetryPolicy | Sequence[RetryPolicy] | None' = None, cache_policy: 'CachePolicy | None' = None, error_handler: 'StateNode[Any, ContextT] | None' = None, timeout: 'float | timedelta | TimeoutPolicy | None' = None) -> 'Self'`

Set default node policies that apply to every node in this graph.

Per-node values passed to `add_node` always take precedence over these
defaults. Defaults are applied at `compile()` time. Policies set here
are **not** inherited by subgraphs.

`retry_policy` and `timeout` defaults apply to **all** nodes,
including error-handler nodes. `cache_policy` and `error_handler`
defaults only apply to regular nodes -- caching error-handler results
is unsafe, and handlers must never catch themselves.

Args:
    retry_policy: Default retry policy for nodes that don't specify
        their own via `add_node(..., retry_policy=...)`. Also applies
        to error-handler nodes.
    cache_policy: Default cache policy for nodes that don't specify
        their own via `add_node(..., cache_policy=...)`. Does **not**
        apply to error-handler nodes.
    error_handler: Default error handler invoked when any regular node
        raises and does not have its own `error_handler` set via
        `add_node`. The handler is **not** invoked when an
        error-handler node itself raises -- handler failures fail the
        run.
    timeout: Default timeout policy for nodes that don't specify their
        own via `add_node(..., timeout=...)`. Also applies to
        error-handler nodes. Accepts a `TimeoutPolicy`, a number of
        seconds (`float`), or a `timedelta`.

Returns:
    Self: The builder instance, for chaining.

Example:
    ```python
    graph = (
        StateGraph(State)
        .set_node_defaults(
            retry_policy=RetryPolicy(max_attempts=3),
            error_handler=my_fallback_handler,
        )
        .add_node("a", node_a)
        .add_node("b", node_b, retry_policy=custom_retry)  # overrides default
        .add_edge(START, "a")
        .compile()
    )
    ```

### `StateGraph.validate(self, interrupt: 'Sequence[str] | None' = None) -> 'Self'`
