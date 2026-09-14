# `langgraph.prebuilt`

langgraph.prebuilt exposes a higher-level API for creating and executing agents and tools.

Public names: `InjectedState`, `InjectedStore`, `ToolCallTransformer`, `ToolNode`, `ToolRuntime`, `ValidationNode`, `create_react_agent`, `tools_condition`

## class `InjectedState(field: 'str | None' = None) -> 'None'` (bases: InjectedToolArg)

Annotation for injecting graph state into tool arguments.

This annotation enables tools to access graph state without exposing state
management details to the language model. Tools annotated with `InjectedState`
receive state data automatically during execution while remaining invisible
to the model's tool-calling interface.

Args:
    field: Optional key to extract from the state dictionary. If `None`, the entire
        state is injected. If specified, only that field's value is injected.
        This allows tools to request specific state components rather than
        processing the full state structure.

Example:
    ```python
    from typing import List
    from typing_extensions import Annotated, TypedDict

    from langchain_core.messages import BaseMessage, AIMessage
    from langchain.tools import InjectedState, ToolNode, tool


    class AgentState(TypedDict):
        messages: List[BaseMessage]
        foo: str


    @tool
    def state_tool(x: int, state: Annotated[dict, InjectedState]) -> str:
        '''Do something with state.'''
        if len(state["messages"]) > 2:
            return state["foo"] + str(x)
        else:
            return "not enough messages"


    @tool
    def foo_tool(x: int, foo: Annotated[str, InjectedState("foo")]) -> str:
        '''Do something else with state.'''
        return foo + str(x + 1)


    node = ToolNode([state_tool, foo_tool])

    tool_call1 = {"name": "state_tool", "args": {"x": 1}, "id": "1", "type": "tool_call"}
    tool_call2 = {"name": "foo_tool", "args": {"x": 1}, "id": "2", "type": "tool_call"}
    state = {
        "messages": [AIMessage("", tool_calls=[tool_call1, tool_call2])],
        "foo": "bar",
    }
    node.invoke(state)
    ```

    ```python
    [
        ToolMessage(content="not enough messages", name="state_tool", tool_call_id="1"),
        ToolMessage(content="bar2", name="foo_tool", tool_call_id="2"),
    ]
    ```

!!! note
    - `InjectedState` arguments are automatically excluded from tool schemas
        presented to language models
    - `ToolNode` handles the injection process during execution
    - Tools can mix regular arguments (controlled by the model) with injected
        arguments (controlled by the system)
    - State injection occurs after the model generates tool calls but before
        tool execution

### `InjectedState.__init__(self, field: 'str | None' = None) -> 'None'`

Initialize the `InjectedState` annotation.

## class `InjectedStore()` (bases: InjectedToolArg)

Annotation for injecting persistent store into tool arguments.

This annotation enables tools to access LangGraph's persistent storage system
without exposing storage details to the language model. Tools annotated with
`InjectedStore` receive the store instance automatically during execution while
remaining invisible to the model's tool-calling interface.

The store provides persistent, cross-session data storage that tools can use
for maintaining context, user preferences, or any other data that needs to
persist beyond individual workflow executions.

!!! warning
    `InjectedStore` annotation requires `langchain-core >= 0.3.8`

Example:
    ```python
    from typing_extensions import Annotated
    from langgraph.store.memory import InMemoryStore
    from langchain.tools import InjectedStore, ToolNode, tool

    @tool
    def save_preference(
        key: str,
        value: str,
        store: Annotated[Any, InjectedStore()]
    ) -> str:
        """Save user preference to persistent storage."""
        store.put(("preferences",), key, value)
        return f"Saved {key} = {value}"

    @tool
    def get_preference(
        key: str,
        store: Annotated[Any, InjectedStore()]
    ) -> str:
        """Retrieve user preference from persistent storage."""
        result = store.get(("preferences",), key)
        return result.value if result else "Not found"
    ```

    Usage with `ToolNode` and graph compilation:

    ```python
    from langgraph.graph import StateGraph
    from langgraph.store.memory import InMemoryStore

    store = InMemoryStore()
    tool_node = ToolNode([save_preference, get_preference])

    graph = StateGraph(State)
    graph.add_node("tools", tool_node)
    compiled_graph = graph.compile(store=store)  # Store is injected automatically
    ```

    Cross-session persistence:

    ```python
    # First session
    result1 = graph.invoke({"messages": [HumanMessage("Save my favorite color as blue")]})

    # Later session - data persists
    result2 = graph.invoke({"messages": [HumanMessage("What's my favorite color?")]})
    ```

!!! note
    - `InjectedStore` arguments are automatically excluded from tool schemas
        presented to language models
    - The store instance is automatically injected by `ToolNode` during execution
    - Tools can access namespaced storage using the store's get/put methods
    - Store injection requires the graph to be compiled with a store instance
    - Multiple tools can share the same store instance for data consistency

## class `ToolCallTransformer(scope: 'tuple[str, ...]' = ()) -> 'None'` (bases: StreamTransformer)

Project `tools` channel events into `ToolCallStream` handles.

Each `tool-started` event spawns a `ToolCallStream`, pushed onto
`run.tool_calls`. Subsequent `tool-output-delta` events append to
that stream's deltas log; `tool-finished` and `tool-error` close it.

Native transformer — the `tool_calls` projection is exposed as a
direct attribute on the run stream.

A nameless `StreamChannel[ToolCallStream]` is used (no protocol
auto-forwarding) because the live handles are not serializable and
should not be injected into the main event log. Wire consumers
subscribe to the `tools` channel instead, where the raw protocol
events flow through untouched by this transformer (`process`
returns `True`).

Registered explicitly by users at compile time via
`builder.compile(transformers=[ToolCallTransformer])` — not a
default built-in, so the `tools` channel is user-opt-in.

### `ToolCallTransformer.__init__(self, scope: 'tuple[str, ...]' = ()) -> 'None'`

Initialize the transformer with its mux's scope.

Args:
    scope: The namespace tuple the owning mux is scoped to.
        `()` for the root. Factories receive this at
        construction time (`factory(scope)` in `StreamMux`).

### `ToolCallTransformer.fail(self, err: 'BaseException') -> 'None'`

Fail any still-active tool streams when the run errors.

### `ToolCallTransformer.finalize(self) -> 'None'`

Close any still-active tool streams left open at run end.

### `ToolCallTransformer.init(self) -> 'dict[str, Any]'`

Return the projection dict.

Keys become entries in `run.extensions`. If the transformer has
`_native = True`, keys are also set as direct attributes on the
run stream.

StreamChannel instances in the return value are automatically
wired by the StreamMux for protocol event auto-forwarding.

### `ToolCallTransformer.process(self, event: 'ProtocolEvent') -> 'bool'`

Handle an event on the sync lane.

Called for every event before it is appended to the main event
log. Subclasses must override either `process` or `aprocess`.
The default raises so a missing override fails loudly rather
than silently passing every event through.

Args:
    event: The protocol event to observe.

Returns:
    True to keep the event in the main log, False to suppress it.

## class `ToolNode(tools: 'Sequence[BaseTool | Callable]', *, name: 'str' = 'tools', tags: 'list[str] | None' = None, handle_tool_errors: 'bool | str | Callable[..., str] | type[Exception] | tuple[type[Exception], ...]' = <function _default_handle_tool_errors at 0x7d6b3faa47c0>, messages_key: 'str' = 'messages', wrap_tool_call: 'ToolCallWrapper | None' = None, awrap_tool_call: 'AsyncToolCallWrapper | None' = None) -> 'None'` (bases: RunnableCallable)

A node for executing tools in LangGraph workflows.

Handles tool execution patterns including function calls, state injection,
persistent storage, and control flow. Manages parallel execution,
error handling.

Use `ToolNode` when building custom workflows that require fine-grained control over
tool execution—for example, custom routing logic, specialized error handling, or
non-standard agent architectures.

For standard ReAct-style agents, use [`create_agent`][langchain.agents.create_agent]
instead. It uses `ToolNode` internally with sensible defaults for the agent loop,
conditional routing, and error handling.

Input Formats:
    1. **Graph state** with `messages` key that has a list of messages:
        - Common representation for agentic workflows
        - Supports custom messages key via `messages_key` parameter

    2. **Message List**: `[AIMessage(..., tool_calls=[...])]`
        - List of messages with tool calls in the last AIMessage

    3. **Direct Tool Calls**: `[{"name": "tool", "args": {...}, "id": "1", "type": "tool_call"}]`
        - Bypasses message parsing for direct tool execution
        - For programmatic tool invocation and testing

Output Formats:
    Output format depends on input type and tool behavior:

    **For Regular tools**:

    - Dict input → `{"messages": [ToolMessage(...)]}`
    - List input → `[ToolMessage(...)]`

    **For Command tools**:

    - Returns `[Command(...)]` or mixed list with regular tool outputs
    - `Command` can update state, trigger navigation, or send messages

Args:
    tools: A sequence of tools that can be invoked by this node.

        Supports:

        - **BaseTool instances**: Tools with schemas and metadata
        - **Plain functions**: Automatically converted to tools with inferred schemas

    name: The name identifier for this node in the graph. Used for debugging
        and visualization.
    tags: Optional metadata tags to associate with the node for filtering
        and organization.
    handle_tool_errors: Configuration for error handling during tool execution.
        Supports multiple strategies:

        - `True`: Catch all errors and return a `ToolMessage` with the default
            error template containing the exception details.
        - `str`: Catch all errors and return a `ToolMessage` with this custom
            error message string.
        - `type[Exception]`: Only catch exceptions with the specified type and
            return the default error message for it.
        - `tuple[type[Exception], ...]`: Only catch exceptions with the specified
            types and return default error messages for them.
        - `Callable[..., str]`: Catch exceptions matching the callable's signature
            and return the string result of calling it with the exception.
        - `False`: Disable error handling entirely, allowing exceptions to
            propagate.

        Defaults to a callable that:

        - Catches tool invocation errors (due to invalid arguments provided by the
            model) and returns a descriptive error message
        - Ignores tool execution errors (they will be re-raised)

    messages_key: The key in the state dictionary that contains the message list.
        This same key will be used for the output `ToolMessage` objects.

        Allows custom state schemas with different message field names.

Examples:
    Basic usage:

    ```python
    from langchain.tools import ToolNode
    from langchain_core.tools import tool

    @tool
    def calculator(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    tool_node = ToolNode([calculator])
    ```

    State injection:

    ```python
    from typing_extensions import Annotated
    from langchain.tools import InjectedState

    @tool
    def context_tool(query: str, state: Annotated[dict, InjectedState]) -> str:
        """Some tool that uses state."""
        return f"Query: {query}, Messages: {len(state['messages'])}"

    tool_node = ToolNode([context_tool])
    ```

    Error handling:

    ```python
    def handle_errors(e: ValueError) -> str:
        return "Invalid input provided"


    tool_node = ToolNode([my_tool], handle_tool_errors=handle_errors)
    ```

### `ToolNode.__init__(self, tools: 'Sequence[BaseTool | Callable]', *, name: 'str' = 'tools', tags: 'list[str] | None' = None, handle_tool_errors: 'bool | str | Callable[..., str] | type[Exception] | tuple[type[Exception], ...]' = <function _default_handle_tool_errors at 0x7d6b3faa47c0>, messages_key: 'str' = 'messages', wrap_tool_call: 'ToolCallWrapper | None' = None, awrap_tool_call: 'AsyncToolCallWrapper | None' = None) -> 'None'`

Initialize `ToolNode` with tools and configuration.

Args:
    tools: Sequence of tools to make available for execution.
    name: Node name for graph identification.
    tags: Optional metadata tags.
    handle_tool_errors: Error handling configuration.
    messages_key: State key containing messages.
    wrap_tool_call: Sync wrapper function to intercept tool execution. Receives
        ToolCallRequest and execute callable, returns ToolMessage or Command.
        Enables retries, caching, request modification, and control flow.
    awrap_tool_call: Async wrapper function to intercept tool execution.
        If not provided, falls back to wrap_tool_call for async execution.

### property `ToolNode.tools_by_name`

Mapping from tool name to BaseTool instance.

## class `ToolRuntime(state: 'StateT', context: 'ContextT', config: 'RunnableConfig', stream_writer: 'StreamWriter', tool_call_id: 'str | None', store: 'BaseStore | None', tools: 'list[BaseTool]' = <factory>, execution_info: 'ExecutionInfo | None' = None, server_info: 'ServerInfo | None' = None) -> None` (bases: _DirectlyInjectedToolArg, Generic)

Runtime context automatically injected into tools.

!!! note

    This is distinct from `Runtime` (from `langgraph.runtime`), which is injected
    into graph nodes and middleware. `ToolRuntime` includes additional tool-specific
    attributes like `config`, `state`, and `tool_call_id` that `Runtime` does not
    have.

When a tool function has a parameter named `runtime` with type hint
`ToolRuntime`, the tool execution system will automatically inject an instance
containing:

- `state`: The current graph state
- `tool_call_id`: The ID of the current tool call
- `config`: `RunnableConfig` for the current execution
- `context`: Runtime context (shared with `Runtime`)
- `store`: `BaseStore` instance for persistent storage (shared with `Runtime`)
- `stream_writer`: `StreamWriter` for streaming output (shared with `Runtime`)
- `tools`: List of all available `BaseTool` instances

No `Annotated` wrapper is needed - just use `runtime: ToolRuntime`
as a parameter.

Example:
    ```python
    from langchain_core.tools import tool
    from langchain.tools import ToolRuntime

    @tool
    def my_tool(x: int, runtime: ToolRuntime) -> str:
        """Tool that accesses runtime context."""
        # Access state
        messages = tool_runtime.state["messages"]

        # Access tool_call_id
        print(f"Tool call ID: {tool_runtime.tool_call_id}")

        # Access config
        print(f"Run ID: {tool_runtime.config.get('run_id')}")

        # Access runtime context
        user_id = tool_runtime.context.get("user_id")

        # Access store
        tool_runtime.store.put(("metrics",), "count", 1)

        # Stream output
        tool_runtime.stream_writer.write("Processing...")

        return f"Processed {x}"
    ```

!!! note
    This is a marker class used for type checking and detection.
    The actual runtime object will be constructed during tool execution.

### `ToolRuntime.__init__(self, state: 'StateT', context: 'ContextT', config: 'RunnableConfig', stream_writer: 'StreamWriter', tool_call_id: 'str | None', store: 'BaseStore | None', tools: 'list[BaseTool]' = <factory>, execution_info: 'ExecutionInfo | None' = None, server_info: 'ServerInfo | None' = None) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `ToolRuntime.emit_output_delta(self, delta: 'Any') -> 'None'`

Stream a partial output chunk on the `tools` stream channel.

Reads the per-tool-call writer that `StreamToolCallHandler`
installs on a ContextVar at `on_tool_start` and forwards `delta`
through it. Silent no-op when the graph was not run with
`"tools"` in `stream_mode` (no writer is set), so tool authors
can leave `emit_output_delta` calls in place without gating
them on stream mode.

Args:
    delta: Partial output chunk. Any JSON-serializable value;
        surfaced as-is on the `tools` channel's
        `tool-output-delta` payload under `"delta"`.

## class `ValidationNode(*args, **kwargs)` (bases: RunnableCallable)

A node that validates all tools requests from the last `AIMessage`.

It can be used either in `StateGraph` with a `'messages'` key.

!!! note

    This node does not actually **run** the tools, it only validates the tool calls,
    which is useful for extraction and other use cases where you need to generate
    structured output that conforms to a complex schema without losing the original
    messages and tool IDs (for use in multi-turn conversations).

Returns:
    (Union[Dict[str, List[ToolMessage]], Sequence[ToolMessage]]): A list of
        `ToolMessage` objects with the validated content or error messages.

Example:
    ```python title="Example usage for re-prompting the model to generate a valid response:"
    from typing import Literal, Annotated
    from typing_extensions import TypedDict

    from langchain_anthropic import ChatAnthropic
    from pydantic import BaseModel, field_validator

    from langgraph.graph import END, START, StateGraph
    from langgraph.prebuilt import ValidationNode
    from langgraph.graph.message import add_messages

    class SelectNumber(BaseModel):
        a: int

        @field_validator("a")
        def a_must_be_meaningful(cls, v):
            if v != 37:
                raise ValueError("Only 37 is allowed")
            return v

    builder = StateGraph(Annotated[list, add_messages])
    llm = ChatAnthropic(model="claude-3-5-haiku-latest").bind_tools([SelectNumber])
    builder.add_node("model", llm)
    builder.add_node("validation", ValidationNode([SelectNumber]))
    builder.add_edge(START, "model")

    def should_validate(state: list) -> Literal["validation", "__end__"]:
        if state[-1].tool_calls:
            return "validation"
        return END

    builder.add_conditional_edges("model", should_validate)

    def should_reprompt(state: list) -> Literal["model", "__end__"]:
        for msg in state[::-1]:
            # None of the tool calls were errors
            if msg.type == "ai":
                return END
            if msg.additional_kwargs.get("is_error"):
                return "model"
        return END

    builder.add_conditional_edges("validation", should_reprompt)

    graph = builder.compile()
    res = graph.invoke(("user", "Select a number, any number"))
    # Show the retry logic
    for msg in res:
        msg.pretty_print()
    ```

### `ValidationNode.__init__(self, schemas: collections.abc.Sequence[langchain_core.tools.base.BaseTool | type[pydantic.main.BaseModel] | collections.abc.Callable], *, format_error: collections.abc.Callable[[BaseException, langchain_core.messages.tool.ToolCall, type[pydantic.main.BaseModel]], str] | None = None, name: str = 'validation', tags: list[str] | None = None) -> None`

Initialize the ValidationNode.

Args:
    schemas: A list of schemas to validate the tool calls with. These can be
        any of the following:
        - A pydantic BaseModel class
        - A BaseTool instance (the args_schema will be used)
        - A function (a schema will be created from the function signature)
    format_error: A function that takes an exception, a ToolCall, and a schema
        and returns a formatted error string. By default, it returns the
        exception repr and a message to respond after fixing validation errors.
    name: The name of the node.
    tags: A list of tags to add to the node.

## `create_react_agent(model: Union[str, langchain_core.runnables.base.Runnable[langchain_core.prompt_values.PromptValue | str | collections.abc.Sequence[langchain_core.messages.base.BaseMessage | list[str] | tuple[str, str | list[str | dict[str, Any]]] | str | dict[str, Any]], langchain_core.messages.base.BaseMessage | str], collections.abc.Callable[[~StateSchema, langgraph.runtime.Runtime[~ContextT]], langchain_core.language_models.chat_models.BaseChatModel], collections.abc.Callable[[~StateSchema, langgraph.runtime.Runtime[~ContextT]], collections.abc.Awaitable[langchain_core.language_models.chat_models.BaseChatModel]], collections.abc.Callable[[~StateSchema, langgraph.runtime.Runtime[~ContextT]], langchain_core.runnables.base.Runnable[langchain_core.prompt_values.PromptValue | str | collections.abc.Sequence[langchain_core.messages.base.BaseMessage | list[str] | tuple[str, str | list[str | dict[str, Any]]] | str | dict[str, Any]], langchain_core.messages.base.BaseMessage]], collections.abc.Callable[[~StateSchema, langgraph.runtime.Runtime[~ContextT]], collections.abc.Awaitable[langchain_core.runnables.base.Runnable[langchain_core.prompt_values.PromptValue | str | collections.abc.Sequence[langchain_core.messages.base.BaseMessage | list[str] | tuple[str, str | list[str | dict[str, Any]]] | str | dict[str, Any]], langchain_core.messages.base.BaseMessage]]]], tools: collections.abc.Sequence[langchain_core.tools.base.BaseTool | collections.abc.Callable | dict[str, typing.Any]] | langgraph.prebuilt.tool_node.ToolNode, *, prompt: Union[langchain_core.messages.system.SystemMessage, str, collections.abc.Callable[[~StateSchema], langchain_core.prompt_values.PromptValue | str | collections.abc.Sequence[langchain_core.messages.base.BaseMessage | list[str] | tuple[str, str | list[str | dict[str, Any]]] | str | dict[str, Any]]], langchain_core.runnables.base.Runnable[~StateSchema, langchain_core.prompt_values.PromptValue | str | collections.abc.Sequence[langchain_core.messages.base.BaseMessage | list[str] | tuple[str, str | list[str | dict[str, Any]]] | str | dict[str, Any]]], NoneType] = None, response_format: dict | type[pydantic.main.BaseModel] | tuple[str, dict | type[pydantic.main.BaseModel]] | None = None, pre_model_hook: Union[langchain_core.runnables.base.Runnable[-Input, +Output], collections.abc.Callable[[-Input], +Output], collections.abc.Callable[[-Input], collections.abc.Awaitable[+Output]], collections.abc.Callable[[collections.abc.Iterator[-Input]], collections.abc.Iterator[+Output]], collections.abc.Callable[[collections.abc.AsyncIterator[-Input]], collections.abc.AsyncIterator[+Output]], langchain_core.runnables.base._RunnableCallableSync[-Input, +Output], langchain_core.runnables.base._RunnableCallableAsync[-Input, +Output], langchain_core.runnables.base._RunnableCallableIterator[-Input, +Output], langchain_core.runnables.base._RunnableCallableAsyncIterator[-Input, +Output], collections.abc.Mapping[str, Any], langgraph._internal._runnable._RunnableWithWriter[-Input, +Output], langgraph._internal._runnable._RunnableWithStore[-Input, +Output], langgraph._internal._runnable._RunnableWithWriterStore[-Input, +Output], langgraph._internal._runnable._RunnableWithConfigWriter[-Input, +Output], langgraph._internal._runnable._RunnableWithConfigStore[-Input, +Output], langgraph._internal._runnable._RunnableWithConfigWriterStore[-Input, +Output], NoneType] = None, post_model_hook: Union[langchain_core.runnables.base.Runnable[-Input, +Output], collections.abc.Callable[[-Input], +Output], collections.abc.Callable[[-Input], collections.abc.Awaitable[+Output]], collections.abc.Callable[[collections.abc.Iterator[-Input]], collections.abc.Iterator[+Output]], collections.abc.Callable[[collections.abc.AsyncIterator[-Input]], collections.abc.AsyncIterator[+Output]], langchain_core.runnables.base._RunnableCallableSync[-Input, +Output], langchain_core.runnables.base._RunnableCallableAsync[-Input, +Output], langchain_core.runnables.base._RunnableCallableIterator[-Input, +Output], langchain_core.runnables.base._RunnableCallableAsyncIterator[-Input, +Output], collections.abc.Mapping[str, Any], langgraph._internal._runnable._RunnableWithWriter[-Input, +Output], langgraph._internal._runnable._RunnableWithStore[-Input, +Output], langgraph._internal._runnable._RunnableWithWriterStore[-Input, +Output], langgraph._internal._runnable._RunnableWithConfigWriter[-Input, +Output], langgraph._internal._runnable._RunnableWithConfigStore[-Input, +Output], langgraph._internal._runnable._RunnableWithConfigWriterStore[-Input, +Output], NoneType] = None, state_schema: type[~StateSchema] | None = None, context_schema: type[typing.Any] | None = None, checkpointer: None | bool | langgraph.checkpoint.base.BaseCheckpointSaver = None, store: langgraph.store.base.BaseStore | None = None, interrupt_before: list[str] | None = None, interrupt_after: list[str] | None = None, debug: bool = False, version: Literal['v1', 'v2'] = 'v2', name: str | None = None, **deprecated_kwargs: Any) -> langgraph.graph.state.CompiledStateGraph`

Creates an agent graph that calls tools in a loop until a stopping condition is met.

!!! warning

    This function is deprecated in favor of
    [`create_agent`][langchain.agents.create_agent] from the `langchain`
    package, which provides an equivalent agent factory with a flexible
    middleware system. For migration guidance, see
    [Migrating from LangGraph v0](https://docs.langchain.com/oss/python/migrate/langgraph-v1).

Args:
    model: The language model for the agent. Supports static and dynamic
        model selection.

        - **Static model**: A chat model instance (e.g.,
            [`ChatOpenAI`][langchain_openai.ChatOpenAI]) or string identifier (e.g.,
            `"openai:gpt-4"`)
        - **Dynamic model**: A callable with signature
            `(state, runtime) -> BaseChatModel` that returns different models
            based on runtime context

            If the model has tools bound via `bind_tools` or other configurations,
            the return type should be a `Runnable[LanguageModelInput, BaseMessage]`
            Coroutines are also supported, allowing for asynchronous model selection.

        Dynamic functions receive graph state and runtime, enabling
        context-dependent model selection. Must return a `BaseChatModel`
        instance. For tool calling, bind tools using `.bind_tools()`.
        Bound tools must be a subset of the `tools` parameter.

        !!! example "Dynamic model"

            ```python
            from dataclasses import dataclass

            @dataclass
            class ModelContext:
                model_name: str = "gpt-3.5-turbo"

            # Instantiate models globally
            gpt4_model = ChatOpenAI(model="gpt-4")
            gpt35_model = ChatOpenAI(model="gpt-3.5-turbo")

            def select_model(state: AgentState, runtime: Runtime[ModelContext]) -> ChatOpenAI:
                model_name = runtime.context.model_name
                model = gpt4_model if model_name == "gpt-4" else gpt35_model
                return model.bind_tools(tools)
            ```

        !!! note "Dynamic Model Requirements"

            Ensure returned models have appropriate tools bound via
            `.bind_tools()` and support required functionality. Bound tools
            must be a subset of those specified in the `tools` parameter.

    tools: A list of tools or a `ToolNode` instance.
        If an empty list is provided, the agent will consist of a single LLM node without tool calling.
    prompt: An optional prompt for the LLM. Can take a few different forms:

        - `str`: This is converted to a `SystemMessage` and added to the beginning of the list of messages in `state["messages"]`.
        - `SystemMessage`: this is added to the beginning of the list of messages in `state["messages"]`.
        - `Callable`: This function should take in full graph state and the output is then passed to the language model.
        - `Runnable`: This runnable should take in full graph state and the output is then passed to the language model.

    response_format: An optional schema for the final agent output.

        If provided, output will be formatted to match the given schema and returned in the 'structured_response' state key.

        If not provided, `structured_response` will not be present in the output state.

        Can be passed in as:

        - An OpenAI function/tool schema,
        - A JSON Schema,
        - A TypedDict class,
        - A Pydantic class.
        - A tuple `(prompt, schema)`, where schema is one of the above.
            The prompt will be used together with the model that is being used to
            generate the structured response.

        !!! Important
            `response_format` requires the model to support `.with_structured_output`

        !!! Note
            The graph will make a separate call to the LLM to generate the structured response after the agent loop is finished.
            This is not the only strategy to get structured responses, see more options in [this guide](https://langchain-ai.github.io/langgraph/how-tos/react-agent-structured-output/).

    pre_model_hook: An optional node to add before the `agent` node (i.e., the node that calls the LLM).
        Useful for managing long message histories (e.g., message trimming, summarization, etc.).
        Pre-model hook must be a callable or a runnable that takes in current graph state and returns a state update in the form of
            ```python
            # At least one of `messages` or `llm_input_messages` MUST be provided
            {
                # If provided, will UPDATE the `messages` in the state
                "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), ...],
                # If provided, will be used as the input to the LLM,
                # and will NOT UPDATE `messages` in the state
                "llm_input_messages": [...],
                # Any other state keys that need to be propagated
                ...
            }
            ```

        !!! Important
            At least one of `messages` or `llm_input_messages` MUST be provided and will be used as an input to the `agent` node.
            The rest of the keys will be added to the graph state.

        !!! Warning
            If you are returning `messages` in the pre-model hook, you should OVERWRITE the `messages` key by doing the following:

            ```python
            {
                "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages]
                ...
            }
            ```
    post_model_hook: An optional node to add after the `agent` node (i.e., the node that calls the LLM).
        Useful for implementing human-in-the-loop, guardrails, validation, or other post-processing.
        Post-model hook must be a callable or a runnable that takes in current graph state and returns a state update.

        !!! Note
            Only available with `version="v2"`.
    state_schema: An optional state schema that defines graph state.
        Must have `messages` and `remaining_steps` keys.
        Defaults to `AgentState` that defines those two keys.
        !!! Note
            `remaining_steps` is used to limit the number of steps the react agent can take.
            Calculated roughly as `recursion_limit` - `total_steps_taken`.
            If `remaining_steps` is less than 2 and tool calls are present in the response,
            the react agent will return a final AI Message with
            the content "Sorry, need more steps to process this request.".
            No `GraphRecusionError` will be raised in this case.

    context_schema: An optional schema for runtime context.
    checkpointer: An optional checkpoint saver object. This is used for persisting
        the state of the graph (e.g., as chat memory) for a single thread (e.g., a single conversation).
    store: An optional store object. This is used for persisting data
        across multiple threads (e.g., multiple conversations / users).
    interrupt_before: An optional list of node names to interrupt before.
        Should be one of the following: `"agent"`, `"tools"`.

        This is useful if you want to add a user confirmation or other interrupt before taking an action.
    interrupt_after: An optional list of node names to interrupt after.
        Should be one of the following: `"agent"`, `"tools"`.

        This is useful if you want to return directly or run additional processing on an output.
    debug: A flag indicating whether to enable debug mode.
    version: Determines the version of the graph to create.

        Can be one of:

        - `"v1"`: The tool node processes a single message. All tool
            calls in the message are executed in parallel within the tool node.
        - `"v2"`: The tool node processes a tool call.
            Tool calls are distributed across multiple instances of the tool
            node using the [Send](https://langchain-ai.github.io/langgraph/concepts/low_level/#send)
            API.
    name: An optional name for the `CompiledStateGraph`.
        This name will be automatically used when adding ReAct agent graph to another graph as a subgraph node -
        particularly useful for building multi-agent systems.

!!! warning "`config_schema` Deprecated"
    The `config_schema` parameter is deprecated in v0.6.0 and support will be removed in v2.0.0.
    Please use `context_schema` instead to specify the schema for run-scoped context.


Returns:
    A compiled LangChain `Runnable` that can be used for chat interactions.

The "agent" node calls the language model with the messages list (after applying the prompt).
If the resulting AIMessage contains `tool_calls`, the graph will then call the ["tools"][langgraph.prebuilt.tool_node.ToolNode].
The "tools" node executes the tools (1 tool per `tool_call`) and adds the responses to the messages list
as `ToolMessage` objects. The agent node then calls the language model again.
The process repeats until no more `tool_calls` are present in the response.
The agent then returns the full list of messages as a dictionary containing the key `'messages'`.

``` mermaid
    sequenceDiagram
        participant U as User
        participant A as LLM
        participant T as Tools
        U->>A: Initial input
        Note over A: Prompt + LLM
        loop while tool_calls present
            A->>T: Execute tools
            T-->>A: ToolMessage for each tool_calls
        end
        A->>U: Return final state
```

Example:
    ```python
    from langgraph.prebuilt import create_react_agent

    def check_weather(location: str) -> str:
        '''Return the weather forecast for the specified location.'''
        return f"It's always sunny in {location}"

    graph = create_react_agent(
        "anthropic:claude-3-7-sonnet-latest",
        tools=[check_weather],
        prompt="You are a helpful assistant",
    )
    inputs = {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
    for chunk in graph.stream(inputs, stream_mode="updates"):
        print(chunk)
    ```

## `tools_condition(state: 'list[AnyMessage] | dict[str, Any] | BaseModel', messages_key: 'str' = 'messages') -> "Literal['tools', '__end__']"`

Conditional routing function for tool-calling workflows.

This utility function implements the standard conditional logic for ReAct-style
agents: if the last `AIMessage` contains tool calls, route to the tool execution
node; otherwise, end the workflow. This pattern is fundamental to most tool-calling
agent architectures.

The function handles multiple state formats commonly used in LangGraph applications,
making it flexible for different graph designs while maintaining consistent behavior.

Args:
    state: The current graph state to examine for tool calls. Supported formats:
        - Dictionary containing a messages key (for `StateGraph`)
        - `BaseModel` instance with a messages attribute
    messages_key: The key or attribute name containing the message list in the state.
        This allows customization for graphs using different state schemas.

Returns:
    Either `'tools'` if tool calls are present in the last `AIMessage`, or `'__end__'`
        to terminate the workflow. These are the standard routing destinations for
        tool-calling conditional edges.

Raises:
    ValueError: If no messages can be found in the provided state format.

Example:
    Basic usage in a ReAct agent:

    ```python
    from langgraph.graph import StateGraph
    from langchain.tools import ToolNode
    from langchain.tools.tool_node import tools_condition
    from typing_extensions import TypedDict


    class State(TypedDict):
        messages: list


    graph = StateGraph(State)
    graph.add_node("llm", call_model)
    graph.add_node("tools", ToolNode([my_tool]))
    graph.add_conditional_edges(
        "llm",
        tools_condition,  # Routes to "tools" or "__end__"
        {"tools": "tools", "__end__": "__end__"},
    )
    ```

    Custom messages key:

    ```python
    def custom_condition(state):
        return tools_condition(state, messages_key="chat_history")
    ```

!!! note
    This function is designed to work seamlessly with `ToolNode` and standard
    LangGraph patterns. It expects the last message to be an `AIMessage` when
    tool calls are present, which is the standard output format for tool-calling
    language models.
