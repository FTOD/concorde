# `langgraph.errors`

Public names: `EmptyChannelError`, `EmptyInputError`, `ErrorCode`, `GraphBubbleUp`, `GraphDrained`, `GraphInterrupt`, `GraphRecursionError`, `InvalidUpdateError`, `NodeCancelledError`, `NodeError`, `NodeInterrupt`, `NodeTimeoutError`, `ParentCommand`, `TaskNotFound`

## class `EmptyChannelError` (bases: Exception)

Raised when attempting to get the value of a channel that hasn't been updated
for the first time yet.

## class `EmptyInputError` (bases: Exception)

Raised when graph receives an empty input.

## class `ErrorCode(value, names=None, *, module=None, qualname=None, type=None, start=1, boundary=None)` (bases: Enum)

Create a collection of name/value pairs.

Example enumeration:

>>> class Color(Enum):
...     RED = 1
...     BLUE = 2
...     GREEN = 3

Access them by:

- attribute access::

>>> Color.RED
<Color.RED: 1>

- value lookup:

>>> Color(1)
<Color.RED: 1>

- name lookup:

>>> Color['RED']
<Color.RED: 1>

Enumerations can be iterated over, and know how many members they have:

>>> len(Color)
3

>>> list(Color)
[<Color.RED: 1>, <Color.BLUE: 2>, <Color.GREEN: 3>]

Methods can be added to enumerations, and members can have their own
attributes -- see the documentation for details.

## class `GraphBubbleUp` (bases: Exception)

Common base class for all non-exit exceptions.

## class `GraphDrained(reason: 'str' = 'shutdown') -> 'None'` (bases: GraphBubbleUp)

Raised when a graph run exits early due to a drain request.

This indicates the graph stopped cooperatively at a superstep boundary
because `RunControl.request_drain()` was called (e.g., in response to
SIGTERM). The checkpoint is saved and the run can be resumed later.

### `GraphDrained.__init__(self, reason: 'str' = 'shutdown') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

## class `GraphInterrupt(interrupts: 'Sequence[Interrupt]' = ()) -> 'None'` (bases: GraphBubbleUp)

Raised when a subgraph is interrupted, suppressed by the root graph.
Never raised directly, or surfaced to the user.

### `GraphInterrupt.__init__(self, interrupts: 'Sequence[Interrupt]' = ()) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

## class `GraphRecursionError` (bases: RecursionError)

Raised when the graph has exhausted the maximum number of steps.

This prevents infinite loops. To increase the maximum number of steps,
run your graph with a config specifying a higher `recursion_limit`.

Troubleshooting guides:

- [`GRAPH_RECURSION_LIMIT`](https://docs.langchain.com/oss/python/langgraph/GRAPH_RECURSION_LIMIT)

Examples:

    graph = builder.compile()
    graph.invoke(
        {"messages": [("user", "Hello, world!")]},
        # The config is the second positional argument
        {"recursion_limit": 1000},
    )

## class `InvalidUpdateError` (bases: Exception)

Raised when attempting to update a channel with an invalid set of updates.

Troubleshooting guides:

- [`INVALID_CONCURRENT_GRAPH_UPDATE`](https://docs.langchain.com/oss/python/langgraph/INVALID_CONCURRENT_GRAPH_UPDATE)
- [`INVALID_GRAPH_NODE_RETURN_VALUE`](https://docs.langchain.com/oss/python/langgraph/INVALID_GRAPH_NODE_RETURN_VALUE)

## class `NodeCancelledError(node: 'str', message: 'str | None' = None) -> 'None'` (bases: Exception)

Raised when a node body raises ``asyncio.CancelledError`` itself.

``asyncio.CancelledError`` is a ``BaseException`` and the pregel runner
treats cancelled task futures as silent tear-down (e.g. when it stops
sibling tasks after a peer fails). That is the correct behaviour for
*framework-initiated* cancellation, but a user node that raises
``asyncio.CancelledError`` from its own body should surface as a node
failure, the same way any other exception would.

The retry layer converts user-raised ``asyncio.CancelledError`` into this
type so it flows through the normal error path and the run reports as
``error`` instead of silently succeeding.

### `NodeCancelledError.__init__(self, node: 'str', message: 'str | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

## class `NodeError(node: 'str', error: 'BaseException') -> None`

Failure context passed to a node-level error handler.

Inject by adding a parameter typed `NodeError` to a handler registered via
`StateGraph.add_node(..., error_handler=...)`:

```python
def handler(state: State, error: NodeError) -> Command:
    return Command(update={"status": f"recovered from {error.node}: {error.error}"})
```

### `NodeError.__init__(self, node: 'str', error: 'BaseException') -> None`

Initialize self.  See help(type(self)) for accurate signature.

## class `NodeInterrupt(value: 'Any', id: 'str | None' = None) -> 'None'` (bases: GraphInterrupt)

Raised by a node to interrupt execution.

### `NodeInterrupt.__init__(self, value: 'Any', id: 'str | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

## class `NodeTimeoutError(node: 'str', elapsed: 'float', *, kind: "Literal['idle', 'run']", idle_timeout: 'float | None' = None, run_timeout: 'float | None' = None) -> 'None'` (bases: Exception)

Raised when a node invocation exceeds one of its configured timeouts.

Does **not** inherit from the built-in `TimeoutError` (a subclass of
`OSError`) so that the default `RetryPolicy` treats it as retryable.

Both `idle_timeout` and `run_timeout` reflect the configured policy at the
time of the failure (each is `None` if not configured). `kind` and
`timeout` identify which one fired.

### `NodeTimeoutError.__init__(self, node: 'str', elapsed: 'float', *, kind: "Literal['idle', 'run']", idle_timeout: 'float | None' = None, run_timeout: 'float | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

## class `ParentCommand(command: 'Command') -> 'None'` (bases: GraphBubbleUp)

Common base class for all non-exit exceptions.

### `ParentCommand.__init__(self, command: 'Command') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

## class `TaskNotFound` (bases: Exception)

Raised when the executor is unable to find a task (for distributed mode).
