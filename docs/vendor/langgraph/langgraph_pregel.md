# `langgraph.pregel`

Public names: `NodeBuilder`, `Pregel`

## class `NodeBuilder() -> 'None'`

### `NodeBuilder.__init__(self) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `NodeBuilder.add_cache_policy(self, policy: 'CachePolicy') -> 'Self'`

Adds cache policies to the node.

### `NodeBuilder.add_retry_policies(self, *policies: 'RetryPolicy') -> 'Self'`

Adds retry policies to the node.

### `NodeBuilder.build(self) -> 'PregelNode'`

Builds the node.

### `NodeBuilder.do(self, node: 'RunnableLike') -> 'Self'`

Adds the specified node.

### `NodeBuilder.meta(self, *tags: 'str', **metadata: 'Any') -> 'Self'`

Add tags or metadata to the node.

### `NodeBuilder.read_from(self, *channels: 'str') -> 'Self'`

Adds the specified channels to read from, without subscribing to them.

### `NodeBuilder.set_timeout(self, timeout: 'float | timedelta | TimeoutPolicy | None') -> 'Self'`

Set the per-attempt timeout policy for this node.

### `NodeBuilder.subscribe_only(self, channel: 'str') -> 'Self'`

Subscribe to a single channel.

### `NodeBuilder.subscribe_to(self, *channels: 'str', read: 'bool' = True) -> 'Self'`

Add channels to subscribe to.

Node will be invoked when any of these channels are updated, with a dict of the
channel values as input.

Args:
    channels: Channel name(s) to subscribe to
    read: If `True`, the channels will be included in the input to the node.
        Otherwise, they will trigger the node without being sent in input.

Returns:
    Self for chaining

### `NodeBuilder.write_to(self, *channels: 'str | ChannelWriteEntry', **kwargs: '_WriteValue') -> 'Self'`

Add channel writes.

Args:
    *channels: Channel names to write to.
    **kwargs: Channel name and value mappings.

Returns:
    Self for chaining

## class `Pregel(*, nodes: 'dict[str, PregelNode | NodeBuilder]', channels: 'dict[str, BaseChannel | ManagedValueSpec] | None', auto_validate: 'bool' = True, stream_mode: 'StreamMode' = 'values', stream_eager: 'bool' = False, output_channels: 'str | Sequence[str]', stream_channels: 'str | Sequence[str] | None' = None, interrupt_after_nodes: 'All | Sequence[str]' = (), interrupt_before_nodes: 'All | Sequence[str]' = (), input_channels: 'str | Sequence[str]', step_timeout: 'float | None' = None, debug: 'bool | None' = None, checkpointer: 'Checkpointer' = None, store: 'BaseStore | None' = None, cache: 'BaseCache | None' = None, retry_policy: 'RetryPolicy | Sequence[RetryPolicy]' = (), cache_policy: 'CachePolicy | None' = None, context_schema: 'type[ContextT] | None' = None, config: 'RunnableConfig | None' = None, trigger_to_nodes: 'Mapping[str, Sequence[str]] | None' = None, node_error_handler_map: 'Mapping[str, str] | None' = None, name: 'str' = 'LangGraph', stream_transformers: 'Sequence[Callable[[tuple[str, ...]], Any]] | None' = None, **deprecated_kwargs: 'Unpack[DeprecatedKwargs]') -> 'None'` (bases: PregelProtocol, Generic)

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

### property `Pregel.InputType`

Input type.

The type of input this `Runnable` accepts specified as a type annotation.

Raises:
    TypeError: If the input type cannot be inferred.

### property `Pregel.OutputType`

Output Type.

The type of output this `Runnable` produces specified as a type annotation.

Raises:
    TypeError: If the output type cannot be inferred.

### `Pregel.__init__(self, *, nodes: 'dict[str, PregelNode | NodeBuilder]', channels: 'dict[str, BaseChannel | ManagedValueSpec] | None', auto_validate: 'bool' = True, stream_mode: 'StreamMode' = 'values', stream_eager: 'bool' = False, output_channels: 'str | Sequence[str]', stream_channels: 'str | Sequence[str] | None' = None, interrupt_after_nodes: 'All | Sequence[str]' = (), interrupt_before_nodes: 'All | Sequence[str]' = (), input_channels: 'str | Sequence[str]', step_timeout: 'float | None' = None, debug: 'bool | None' = None, checkpointer: 'Checkpointer' = None, store: 'BaseStore | None' = None, cache: 'BaseCache | None' = None, retry_policy: 'RetryPolicy | Sequence[RetryPolicy]' = (), cache_policy: 'CachePolicy | None' = None, context_schema: 'type[ContextT] | None' = None, config: 'RunnableConfig | None' = None, trigger_to_nodes: 'Mapping[str, Sequence[str]] | None' = None, node_error_handler_map: 'Mapping[str, str] | None' = None, name: 'str' = 'LangGraph', stream_transformers: 'Sequence[Callable[[tuple[str, ...]], Any]] | None' = None, **deprecated_kwargs: 'Unpack[DeprecatedKwargs]') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `Pregel.abulk_update_state(self, config: 'RunnableConfig', supersteps: 'Sequence[Sequence[StateUpdate]]') -> 'RunnableConfig'`

Asynchronously apply updates to the graph state in bulk. Requires a checkpointer to be set.

Args:
    config: The config to apply the updates to.
    supersteps: A list of supersteps, each including a list of updates to apply sequentially to a graph state.

        Each update is a tuple of the form `(values, as_node, task_id)` where `task_id` is optional.

Raises:
    ValueError: If no checkpointer is set or no updates are provided.
    InvalidUpdateError: If an invalid update is provided.

Returns:
    RunnableConfig: The updated config.

### `Pregel.aclear_cache(self, nodes: 'Sequence[str] | None' = None) -> 'None'`

Asynchronously clear the cache for the given nodes.

### `Pregel.aget_graph(self, config: 'RunnableConfig | None' = None, *, xray: 'int | bool' = False) -> 'Graph'`

Return a drawable representation of the computation graph.

### `Pregel.aget_state(self, config: 'RunnableConfig', *, subgraphs: 'bool' = False) -> 'StateSnapshot'`

Get the current state of the graph.

### `Pregel.aget_state_history(self, config: 'RunnableConfig', *, filter: 'dict[str, Any] | None' = None, before: 'RunnableConfig | None' = None, limit: 'int | None' = None) -> 'AsyncIterator[StateSnapshot]'`

Asynchronously get the history of the state of the graph.

### `Pregel.aget_subgraphs(self, *, namespace: 'str | None' = None, recurse: 'bool' = False) -> 'AsyncIterator[tuple[str, PregelProtocol]]'`

Get the subgraphs of the graph.

Args:
    namespace: The namespace to filter the subgraphs by.
    recurse: Whether to recurse into the subgraphs.
        If `False`, only the immediate subgraphs will be returned.

Returns:
    An iterator of the `(namespace, subgraph)` pairs.

### `Pregel.ainvoke(self, input: 'InputT | Command | None', config: 'RunnableConfig | None' = None, *, context: 'ContextT | None' = None, stream_mode: 'StreamMode' = 'values', print_mode: 'StreamMode | Sequence[StreamMode]' = (), output_keys: 'str | Sequence[str] | None' = None, interrupt_before: 'All | Sequence[str] | None' = None, interrupt_after: 'All | Sequence[str] | None' = None, durability: 'Durability | None' = None, control: 'RunControl | None' = None, version: "Literal['v1', 'v2']" = 'v1', **kwargs: 'Any') -> 'dict[str, Any] | Any'`

Asynchronously run the graph with a single input and config.

Args:
    input: The input data for the graph. It can be a dictionary or any other type.
    config: The configuration for the graph run.
    context: The static context to use for the run.
        !!! version-added "Added in version 0.6.0"
    stream_mode: The stream mode for the graph run.
    print_mode: Accepts the same values as `stream_mode`, but only prints the output to the console, for debugging purposes.

        Does not affect the output of the graph in any way.
    output_keys: The output keys to retrieve from the graph run.
    interrupt_before: The nodes to interrupt the graph run before.
    interrupt_after: The nodes to interrupt the graph run after.
    durability: The durability mode for the graph execution, defaults to `"async"`.

        Options are:

        - `"sync"`: Changes are persisted synchronously before the next step starts.
        - `"async"`: Changes are persisted asynchronously while the next step executes.
        - `"exit"`: Changes are persisted only when the graph exits.
    control: Optional run control used to request cooperative drain.
    version: The streaming format version. `"v1"` (default) returns the
        traditional format, `"v2"` returns `StreamPart` typed dicts when
        `stream_mode` is not `"values"`.
    **kwargs: Additional keyword arguments to pass to the graph run.

Returns:
    The output of the graph run. If `stream_mode` is `"values"`, it returns the latest output.
    If `stream_mode` is not `"values"`, it returns a list of output chunks.

### `Pregel.astream(self, input: 'InputT | Command | None', config: 'RunnableConfig | None' = None, *, context: 'ContextT | None' = None, stream_mode: 'StreamMode | Sequence[StreamMode] | None' = None, print_mode: 'StreamMode | Sequence[StreamMode]' = (), output_keys: 'str | Sequence[str] | None' = None, interrupt_before: 'All | Sequence[str] | None' = None, interrupt_after: 'All | Sequence[str] | None' = None, durability: 'Durability | None' = None, control: 'RunControl | None' = None, subgraphs: 'bool' = False, debug: 'bool | None' = None, version: "Literal['v1', 'v2']" = 'v1', **kwargs: 'Unpack[DeprecatedKwargs]') -> 'AsyncIterator[dict[str, Any] | Any]'`

Asynchronously stream graph steps for a single input.

Args:
    input: The input to the graph.
    config: The configuration to use for the run.
    context: The static context to use for the run.
        !!! version-added "Added in version 0.6.0"
    stream_mode: The mode to stream output, defaults to `self.stream_mode`.

        Options are:

        - `"values"`: Emit all values in the state after each step, including interrupts.
            When used with functional API, values are emitted once at the end of the workflow.
        - `"updates"`: Emit only the node or task names and updates returned by the nodes or tasks after each step.
            If multiple updates are made in the same step (e.g. multiple nodes are run) then those updates are emitted separately.
        - `"custom"`: Emit custom data from inside nodes or tasks using `StreamWriter`.
        - `"messages"`: Emit LLM messages token-by-token together with metadata for any LLM invocations inside nodes or tasks.
            - Will be emitted as 2-tuples `(LLM token, metadata)`.
        - `"checkpoints"`: Emit an event when a checkpoint is created, in the same format as returned by `get_state()`.
        - `"tasks"`: Emit events when tasks start and finish, including their results and errors.
        - `"debug"`: Emit debug events with as much information as possible for each step.

        You can pass a list as the `stream_mode` parameter to stream multiple modes at once.
        The streamed outputs will be tuples of `(mode, data)`.

        See [LangGraph streaming guide](https://docs.langchain.com/oss/python/langgraph/streaming) for more details.
    print_mode: Accepts the same values as `stream_mode`, but only prints the output to the console, for debugging purposes.

        Does not affect the output of the graph in any way.
    output_keys: The keys to stream, defaults to all non-context channels.
    interrupt_before: Nodes to interrupt before, defaults to all nodes in the graph.
    interrupt_after: Nodes to interrupt after, defaults to all nodes in the graph.
    durability: The durability mode for the graph execution, defaults to `"async"`.

        Options are:

        - `"sync"`: Changes are persisted synchronously before the next step starts.
        - `"async"`: Changes are persisted asynchronously while the next step executes.
        - `"exit"`: Changes are persisted only when the graph exits.
    control: Optional run control used to request cooperative drain.
    subgraphs: Whether to stream events from inside subgraphs, defaults to `False`.

        If `True`, the events will be emitted as tuples `(namespace, data)`,
        or `(namespace, mode, data)` if `stream_mode` is a list,
        where `namespace` is a tuple with the path to the node where a subgraph is invoked,
        e.g. `("parent_node:<task_id>", "child_node:<task_id>")`.

        See [LangGraph streaming guide](https://docs.langchain.com/oss/python/langgraph/streaming) for more details.

Yields:
    The output of each step in the graph. The output shape depends on the `stream_mode`.

### `Pregel.astream_events(self, input: 'InputT | Command | None', config: 'RunnableConfig | None' = None, *, version: "Literal['v1', 'v2', 'v3']" = 'v2', interrupt_before: 'All | Sequence[str] | None' = None, interrupt_after: 'All | Sequence[str] | None' = None, control: 'RunControl | None' = None, transformers: 'Sequence[Callable[[tuple[str, ...]], Any]] | None' = None, **kwargs: 'Any') -> 'AsyncIterator[StreamEvent] | Awaitable[Any]'`

Async variant of `stream_events`.

For `version="v3"`, returns an `AsyncGraphRunStream` whose
projections can be awaited concurrently; each subscribed cursor
drives the pump when its buffer is empty. The same nesting
limitation as the sync path applies — see `stream_events` for
details.

!!! warning

    The `version="v3"` API is experimental and may change.

See `stream_events` for full argument and return documentation.

### `Pregel.aupdate_state(self, config: 'RunnableConfig', values: 'dict[str, Any] | Any', as_node: 'str | None' = None, task_id: 'str | None' = None) -> 'RunnableConfig'`

Asynchronously update the state of the graph with the given values, as if they came from
node `as_node`. If `as_node` is not provided, it will be set to the last node
that updated the state, if not ambiguous.

### `Pregel.bulk_update_state(self, config: 'RunnableConfig', supersteps: 'Sequence[Sequence[StateUpdate]]') -> 'RunnableConfig'`

Apply updates to the graph state in bulk. Requires a checkpointer to be set.

Args:
    config: The config to apply the updates to.
    supersteps: A list of supersteps, each including a list of updates to apply sequentially to a graph state.

        Each update is a tuple of the form `(values, as_node, task_id)` where `task_id` is optional.

Raises:
    ValueError: If no checkpointer is set or no updates are provided.
    InvalidUpdateError: If an invalid update is provided.

Returns:
    RunnableConfig: The updated config.

### `Pregel.clear_cache(self, nodes: 'Sequence[str] | None' = None) -> 'None'`

Clear the cache for the given nodes.

### `Pregel.config_schema(self, *, include: 'Sequence[str] | None' = None) -> 'type[BaseModel]'`

The type of config this `Runnable` accepts specified as a Pydantic model.

To mark a field as configurable, see the `configurable_fields`
and `configurable_alternatives` methods.

Args:
    include: A list of fields to include in the config schema.

Returns:
    A Pydantic model that can be used to validate config.

### `Pregel.copy(self, update: 'dict[str, Any] | None' = None) -> 'Self'`

### `Pregel.get_config_jsonschema(self, *, include: 'Sequence[str] | None' = None) -> 'dict[str, Any]'`

Get a JSON schema that represents the config of the `Runnable`.

Args:
    include: A list of fields to include in the config schema.

Returns:
    A JSON schema that represents the config of the `Runnable`.

!!! version-added "Added in `langchain-core` 0.3.0"

### `Pregel.get_context_jsonschema(self) -> 'dict[str, Any] | None'`

### `Pregel.get_graph(self, config: 'RunnableConfig | None' = None, *, xray: 'int | bool' = False) -> 'Graph'`

Return a drawable representation of the computation graph.

### `Pregel.get_input_jsonschema(self, config: 'RunnableConfig | None' = None) -> 'dict[str, Any]'`

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

### `Pregel.get_input_schema(self, config: 'RunnableConfig | None' = None) -> 'type[BaseModel]'`

Get a Pydantic model that can be used to validate input to the `Runnable`.

`Runnable` objects that leverage the `configurable_fields` and
`configurable_alternatives` methods will have a dynamic input schema that
depends on which configuration the `Runnable` is invoked with.

This method allows to get an input schema for a specific configuration.

Args:
    config: A config to use when generating the schema.

Returns:
    A Pydantic model that can be used to validate input.

### `Pregel.get_output_jsonschema(self, config: 'RunnableConfig | None' = None) -> 'dict[str, Any]'`

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

### `Pregel.get_output_schema(self, config: 'RunnableConfig | None' = None) -> 'type[BaseModel]'`

Get a Pydantic model that can be used to validate output to the `Runnable`.

`Runnable` objects that leverage the `configurable_fields` and
`configurable_alternatives` methods will have a dynamic output schema that
depends on which configuration the `Runnable` is invoked with.

This method allows to get an output schema for a specific configuration.

Args:
    config: A config to use when generating the schema.

Returns:
    A Pydantic model that can be used to validate output.

### `Pregel.get_state(self, config: 'RunnableConfig', *, subgraphs: 'bool' = False) -> 'StateSnapshot'`

Get the current state of the graph.

### `Pregel.get_state_history(self, config: 'RunnableConfig', *, filter: 'dict[str, Any] | None' = None, before: 'RunnableConfig | None' = None, limit: 'int | None' = None) -> 'Iterator[StateSnapshot]'`

Get the history of the state of the graph.

### `Pregel.get_subgraphs(self, *, namespace: 'str | None' = None, recurse: 'bool' = False) -> 'Iterator[tuple[str, PregelProtocol]]'`

Get the subgraphs of the graph.

Args:
    namespace: The namespace to filter the subgraphs by.
    recurse: Whether to recurse into the subgraphs.
        If `False`, only the immediate subgraphs will be returned.

Returns:
    An iterator of the `(namespace, subgraph)` pairs.

### `Pregel.invoke(self, input: 'InputT | Command | None', config: 'RunnableConfig | None' = None, *, context: 'ContextT | None' = None, stream_mode: 'StreamMode' = 'values', print_mode: 'StreamMode | Sequence[StreamMode]' = (), output_keys: 'str | Sequence[str] | None' = None, interrupt_before: 'All | Sequence[str] | None' = None, interrupt_after: 'All | Sequence[str] | None' = None, durability: 'Durability | None' = None, control: 'RunControl | None' = None, version: "Literal['v1', 'v2']" = 'v1', **kwargs: 'Any') -> 'dict[str, Any] | Any'`

Run the graph with a single input and config.

Args:
    input: The input data for the graph. It can be a dictionary or any other type.
    config: The configuration for the graph run.
    context: The static context to use for the run.
        !!! version-added "Added in version 0.6.0"
    stream_mode: The stream mode for the graph run.
    print_mode: Accepts the same values as `stream_mode`, but only prints the output to the console, for debugging purposes.

        Does not affect the output of the graph in any way.
    output_keys: The output keys to retrieve from the graph run.
    interrupt_before: The nodes to interrupt the graph run before.
    interrupt_after: The nodes to interrupt the graph run after.
    durability: The durability mode for the graph execution, defaults to `"async"`.

        Options are:

        - `"sync"`: Changes are persisted synchronously before the next step starts.
        - `"async"`: Changes are persisted asynchronously while the next step executes.
        - `"exit"`: Changes are persisted only when the graph exits.
    control: Optional run control used to request cooperative drain.
    version: The streaming format version. `"v1"` (default) returns the
        traditional format, `"v2"` returns `StreamPart` typed dicts when
        `stream_mode` is not `"values"`.
    **kwargs: Additional keyword arguments to pass to the graph run.

Returns:
    The output of the graph run. If `stream_mode` is `"values"`, it returns the latest output.
    If `stream_mode` is not `"values"`, it returns a list of output chunks.

### `Pregel.stream(self, input: 'InputT | Command | None', config: 'RunnableConfig | None' = None, *, context: 'ContextT | None' = None, stream_mode: 'StreamMode | Sequence[StreamMode] | None' = None, print_mode: 'StreamMode | Sequence[StreamMode]' = (), output_keys: 'str | Sequence[str] | None' = None, interrupt_before: 'All | Sequence[str] | None' = None, interrupt_after: 'All | Sequence[str] | None' = None, durability: 'Durability | None' = None, control: 'RunControl | None' = None, subgraphs: 'bool' = False, debug: 'bool | None' = None, version: "Literal['v1', 'v2']" = 'v1', **kwargs: 'Unpack[DeprecatedKwargs]') -> 'Iterator[dict[str, Any] | Any]'`

Stream graph steps for a single input.

Args:
    input: The input to the graph.
    config: The configuration to use for the run.
    context: The static context to use for the run.
        !!! version-added "Added in version 0.6.0"
    stream_mode: The mode to stream output, defaults to `self.stream_mode`.

        Options are:

        - `"values"`: Emit all values in the state after each step, including interrupts.
            When used with functional API, values are emitted once at the end of the workflow.
        - `"updates"`: Emit only the node or task names and updates returned by the nodes or tasks after each step.
            If multiple updates are made in the same step (e.g. multiple nodes are run) then those updates are emitted separately.
        - `"custom"`: Emit custom data from inside nodes or tasks using `StreamWriter`.
        - `"messages"`: Emit LLM messages token-by-token together with metadata for any LLM invocations inside nodes or tasks.
            - Will be emitted as 2-tuples `(LLM token, metadata)`.
        - `"checkpoints"`: Emit an event when a checkpoint is created, in the same format as returned by `get_state()`.
        - `"tasks"`: Emit events when tasks start and finish, including their results and errors.
        - `"debug"`: Emit debug events with as much information as possible for each step.

        You can pass a list as the `stream_mode` parameter to stream multiple modes at once.
        The streamed outputs will be tuples of `(mode, data)`.

        See [LangGraph streaming guide](https://docs.langchain.com/oss/python/langgraph/streaming) for more details.
    print_mode: Accepts the same values as `stream_mode`, but only prints the output to the console, for debugging purposes.

        Does not affect the output of the graph in any way.
    output_keys: The keys to stream, defaults to all non-context channels.
    interrupt_before: Nodes to interrupt before, defaults to all nodes in the graph.
    interrupt_after: Nodes to interrupt after, defaults to all nodes in the graph.
    durability: The durability mode for the graph execution, defaults to `"async"`.

        Options are:

        - `"sync"`: Changes are persisted synchronously before the next step starts.
        - `"async"`: Changes are persisted asynchronously while the next step executes.
        - `"exit"`: Changes are persisted only when the graph exits.
    control: Optional run control used to request cooperative drain.
    subgraphs: Whether to stream events from inside subgraphs, defaults to `False`.

        If `True`, the events will be emitted as tuples `(namespace, data)`,
        or `(namespace, mode, data)` if `stream_mode` is a list,
        where `namespace` is a tuple with the path to the node where a subgraph is invoked,
        e.g. `("parent_node:<task_id>", "child_node:<task_id>")`.

        See [LangGraph streaming guide](https://docs.langchain.com/oss/python/langgraph/streaming) for more details.

Yields:
    The output of each step in the graph. The output shape depends on the `stream_mode`.

### property `Pregel.stream_channels_asis`

### property `Pregel.stream_channels_list`

### `Pregel.stream_events(self, input: 'InputT | Command | None', config: 'RunnableConfig | None' = None, *, version: "Literal['v1', 'v2', 'v3']" = 'v2', interrupt_before: 'All | Sequence[str] | None' = None, interrupt_after: 'All | Sequence[str] | None' = None, control: 'RunControl | None' = None, transformers: 'Sequence[Callable[[tuple[str, ...]], Any]] | None' = None, **kwargs: 'Any') -> 'Any'`

Stream events from this graph.

For `version="v1"` / `"v2"`, yields `StreamEvent` dicts (see
`Runnable.stream_events`). For `version="v3"`, returns a
`GraphRunStream` whose typed projections the caller drives by
iterating — no background thread.

!!! warning

    The `version="v3"` API is experimental and may change.

Builds a `StreamMux` from the built-in transformers, this
graph's compile-time `stream_transformers`, and any additional
`transformers=` supplied at the call site. `run.output`,
`run.interrupted`, and `run.interrupts` work regardless of
which transformers are registered.

Note:
    Nesting v1 `stream(stream_mode="messages")` inside a node
    of a `stream_events(version="v3")` run is not fully
    supported. The outer v3 messages handler reroutes
    `BaseChatModel.invoke` through the v2 event protocol, so
    the inner v1 handler does not see `on_llm_new_token`
    chunks. The inner stream still yields a finalized message
    via `on_llm_end`. Use `stream_events(version="v3")` for the
    inner graph as well, or call `chat_model.stream(...)`
    explicitly, to get token-level streaming.

Args:
    input: Graph input.
    config: Optional runnable config.
    version: Streaming-event schema version. `"v3"` selects the
        content-block-centric streaming protocol.
    interrupt_before: Nodes to interrupt before, if any. Only
        used for `version="v3"`.
    interrupt_after: Nodes to interrupt after, if any. Only
        used for `version="v3"`.
    control: Optional run control used to request cooperative
        drain. Only used for `version="v3"`.
    transformers: Extra transformer classes or configured
        factories appended after compile-time
        `stream_transformers`. Factories are called as
        `factory(scope)` so they can propagate to subgraph
        scopes. Only used for `version="v3"`.
    **kwargs: For `version="v1"`/`"v2"`, forwarded to
        `Runnable.stream_events`. For `version="v3"`, forwarded
        to the underlying `stream(...)` call (e.g. `context`,
        `durability`, `output_keys`, `print_mode`, `debug`).
        `stream_mode` and `subgraphs` are not accepted under
        `version="v3"` and raise `TypeError` if supplied; v3
        owns them.

Returns:
    For `version="v3"`, a `GraphRunStream` the caller iterates
    to drive the run. Otherwise an `Iterator[StreamEvent]`.

### `Pregel.update_state(self, config: 'RunnableConfig', values: 'dict[str, Any] | Any | None', as_node: 'str | None' = None, task_id: 'str | None' = None) -> 'RunnableConfig'`

Update the state of the graph with the given values, as if they came from
node `as_node`. If `as_node` is not provided, it will be set to the last node
that updated the state, if not ambiguous.

### `Pregel.validate(self) -> 'Self'`

### `Pregel.with_config(self, config: 'RunnableConfig | None' = None, **kwargs: 'Any') -> 'Self'`

Create a copy of the Pregel object with an updated config.
