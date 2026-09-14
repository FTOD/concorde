# `langgraph.checkpoint.memory`

Public names: `AbstractAsyncContextManager`, `AbstractContextManager`, `Any`, `AsyncIterator`, `BaseCheckpointSaver`, `ChannelVersions`, `Checkpoint`, `CheckpointMetadata`, `CheckpointTuple`, `DeltaChannelHistory`, `ExitStack`, `InMemorySaver`, `Iterator`, `Mapping`, `MemorySaver`, `PendingWrite`, `PersistentDict`, `RunnableConfig`, `Sequence`, `SerializerProtocol`, `TracebackType`, `WRITES_IDX_MAP`, `annotations`, `defaultdict`, `get_checkpoint_id`, `get_checkpoint_metadata`, `logger`, `logging`, `os`, `pickle`, `random`, `shutil`

## class `AbstractAsyncContextManager()` (bases: ABC)

An abstract base class for asynchronous context managers.

## class `AbstractContextManager()` (bases: ABC)

An abstract base class for context managers.

## class `Any(*args, **kwargs)`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

## class `AsyncIterator()` (bases: AsyncIterable)

## class `BaseCheckpointSaver(*, serde: 'SerializerProtocol | None' = None) -> 'None'` (bases: Generic)

Base class for creating a graph checkpointer.

Checkpointers allow LangGraph agents to persist their state
within and across multiple interactions.

When a checkpointer is configured, you should pass a `thread_id` in the config when
invoking the graph:

```python
config = {"configurable": {"thread_id": "my-thread"}}
graph.invoke(inputs, config)
```

The `thread_id` is the primary key used to store and retrieve checkpoints. Without
it, the checkpointer cannot save state, resume from interrupts, or enable
time-travel debugging.

How you choose ``thread_id`` depends on your use case:

- **Single-shot workflows**: Use a unique ID (e.g., uuid4) for each run when
    executions are independent.
- **Conversational memory**: Reuse the same `thread_id` across invocations
    to accumulate state (e.g., chat history) within a conversation.

Attributes:
    serde (SerializerProtocol): Serializer for encoding/decoding checkpoints.

Note:
    When creating a custom checkpoint saver, consider implementing async
    versions to avoid blocking the main thread.

### `BaseCheckpointSaver.__init__(self, *, serde: 'SerializerProtocol | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `BaseCheckpointSaver.acopy_thread(self, source_thread_id: 'str', target_thread_id: 'str') -> 'None'`

Asynchronously copy all checkpoints and writes from one thread to another.

Args:
    source_thread_id: The thread ID to copy from.
    target_thread_id: The thread ID to copy to.

!!! warning "DeltaChannel"

    See `copy_thread` — the copy must carry the complete parent
    chain (or at least back to a `_DeltaSnapshot` ancestor for every
    `DeltaChannel`) so the target thread can reconstruct delta
    state.

### `BaseCheckpointSaver.adelete_for_runs(self, run_ids: 'Sequence[str]') -> 'None'`

Asynchronously delete all checkpoints and writes for the given run IDs.

Args:
    run_ids: The run IDs whose checkpoints should be deleted.

!!! warning "DeltaChannel"

    See `delete_for_runs` — deleting rows a still-live thread's
    `DeltaChannel` reconstruction depends on (writes between the
    head and its nearest `_DeltaSnapshot` ancestor) will silently
    corrupt that channel's state.

### `BaseCheckpointSaver.adelete_thread(self, thread_id: 'str') -> 'None'`

Delete all checkpoints and writes associated with a specific thread ID.

Args:
    thread_id: The thread ID whose checkpoints should be deleted.

### `BaseCheckpointSaver.aget(self, config: 'RunnableConfig') -> 'Checkpoint | None'`

Asynchronously fetch a checkpoint using the given configuration.

Args:
    config: Configuration specifying which checkpoint to retrieve.

Returns:
    The requested checkpoint, or `None` if not found.

### `BaseCheckpointSaver.aget_delta_channel_history(self, *, config: 'RunnableConfig', channels: 'Sequence[str]') -> 'Mapping[str, DeltaChannelHistory]'`

Async version of `get_delta_channel_history`.

!!! warning "Beta"

    This method is part of the `DeltaChannel` support surface and is
    in beta. See `get_delta_channel_history` for caveats.

### `BaseCheckpointSaver.aget_tuple(self, config: 'RunnableConfig') -> 'CheckpointTuple | None'`

Asynchronously fetch a checkpoint tuple using the given configuration.

Args:
    config: Configuration specifying which checkpoint to retrieve.

Returns:
    The requested checkpoint tuple, or `None` if not found.

Raises:
    NotImplementedError: Implement this method in your custom checkpoint saver.

### `BaseCheckpointSaver.alist(self, config: 'RunnableConfig | None', *, filter: 'dict[str, Any] | None' = None, before: 'RunnableConfig | None' = None, limit: 'int | None' = None) -> 'AsyncIterator[CheckpointTuple]'`

Asynchronously list checkpoints that match the given criteria.

Args:
    config: Base configuration for filtering checkpoints.
    filter: Additional filtering criteria for metadata.
    before: List checkpoints created before this configuration.
    limit: Maximum number of checkpoints to return.

Returns:
    Async iterator of matching checkpoint tuples.

Raises:
    NotImplementedError: Implement this method in your custom checkpoint saver.

### `BaseCheckpointSaver.aprune(self, thread_ids: 'Sequence[str]', *, strategy: 'str' = 'keep_latest') -> 'None'`

Asynchronously prune checkpoints for the given threads.

Args:
    thread_ids: The thread IDs to prune.
    strategy: The pruning strategy. `"keep_latest"` retains only the most
        recent checkpoint per namespace. `"delete"` removes all checkpoints.

!!! warning "DeltaChannel"

    See `prune` for the full `DeltaChannel` caveat. In short:
    `"keep_latest"` must not drop ancestor checkpoints / writes that
    sit between the kept checkpoint and the nearest `_DeltaSnapshot`
    ancestor, or delta channels will silently reconstruct as empty.

### `BaseCheckpointSaver.aput(self, config: 'RunnableConfig', checkpoint: 'Checkpoint', metadata: 'CheckpointMetadata', new_versions: 'ChannelVersions') -> 'RunnableConfig'`

Asynchronously store a checkpoint with its configuration and metadata.

Args:
    config: Configuration for the checkpoint.
    checkpoint: The checkpoint to store.
    metadata: Additional metadata for the checkpoint.
    new_versions: New channel versions as of this write.

Returns:
    RunnableConfig: Updated configuration after storing the checkpoint.

Raises:
    NotImplementedError: Implement this method in your custom checkpoint saver.

### `BaseCheckpointSaver.aput_writes(self, config: 'RunnableConfig', writes: 'Sequence[tuple[str, Any]]', task_id: 'str', task_path: 'str' = '') -> 'None'`

Asynchronously store intermediate writes linked to a checkpoint.

Args:
    config: Configuration of the related checkpoint.
    writes: List of writes to store.
    task_id: Identifier for the task creating the writes.
    task_path: Path of the task creating the writes.

Raises:
    NotImplementedError: Implement this method in your custom checkpoint saver.

### property `BaseCheckpointSaver.config_specs`

Define the configuration options for the checkpoint saver.

Returns:
    list: List of configuration field specs.

### `BaseCheckpointSaver.copy_thread(self, source_thread_id: 'str', target_thread_id: 'str') -> 'None'`

Copy all checkpoints and writes from one thread to another.

Args:
    source_thread_id: The thread ID to copy from.
    target_thread_id: The thread ID to copy to.

!!! warning "DeltaChannel"

    Implementations must copy the **complete** parent chain (all
    ancestor checkpoints and their `checkpoint_writes`) — copying
    only the head checkpoint will leave the target thread with
    `DeltaChannel` state that cannot be reconstructed (no path back
    to a `_DeltaSnapshot` ancestor). Equivalently, the copy must
    include enough ancestors that every `DeltaChannel`-backed key
    has either a `_DeltaSnapshot` in `channel_values` somewhere in
    the chain, or a complete write history back to the chain root.

### `BaseCheckpointSaver.delete_for_runs(self, run_ids: 'Sequence[str]') -> 'None'`

Delete all checkpoints and writes associated with the given run IDs.

Args:
    run_ids: The run IDs whose checkpoints should be deleted.

!!! warning "DeltaChannel"

    Deleting a run that produced ancestor `checkpoint_writes` — or
    the only `_DeltaSnapshot` blob — for a still-live thread will
    break reconstruction of any `DeltaChannel` whose history
    depended on those rows. See the `DeltaChannel` note on `prune`
    for safe-recovery strategies.

### `BaseCheckpointSaver.delete_thread(self, thread_id: 'str') -> 'None'`

Delete all checkpoints and writes associated with a specific thread ID.

Args:
    thread_id: The thread ID whose checkpoints should be deleted.

### `BaseCheckpointSaver.get(self, config: 'RunnableConfig') -> 'Checkpoint | None'`

Fetch a checkpoint using the given configuration.

Args:
    config: Configuration specifying which checkpoint to retrieve.

Returns:
    The requested checkpoint, or `None` if not found.

### `BaseCheckpointSaver.get_delta_channel_history(self, *, config: 'RunnableConfig', channels: 'Sequence[str]') -> 'Mapping[str, DeltaChannelHistory]'`

Walk the parent chain returning per-channel writes + seed.

!!! warning "Beta"

    This method is part of the `DeltaChannel` support surface and is
    in beta. The signature, return shape (`DeltaChannelHistory`), and
    interaction with `_DeltaSnapshot` blobs may change. Override at
    your own risk; the default implementation will continue to work
    against the public `BaseCheckpointSaver` contract.

For each requested channel, walks ancestors of the checkpoint
identified by `config` (following `parent_config`) and accumulates
`pending_writes` for that channel. The walk terminates per-channel
at the nearest ancestor whose `channel_values[ch]` is populated;
that value is returned as `seed`. If the walk reaches the root
without finding a stored value, `seed` is omitted from that
channel's entry — the consumer treats the absence as "start
empty."

Walks the **parent chain** (not `list(before=...)`): for forked
threads, only on-path ancestors contribute.

The default implementation walks `get_tuple` + `parent_config`
once for all channels — each ancestor visited once, not once per
channel. Savers with direct storage access (`InMemorySaver`,
`PostgresSaver`) override for performance; the return contract is
fixed here.

Args:
    config: Configuration identifying the target checkpoint.
    channels: Channel names to walk for. Empty → empty mapping.

Returns:
    Per-channel `DeltaChannelHistory` for every name in `channels`.

### `BaseCheckpointSaver.get_next_version(self, current: 'V | None', channel: 'None') -> 'V'`

Generate the next version ID for a channel.

Default is to use integer versions, incrementing by `1`.

If you override, you can use `str`/`int`/`float` versions, as long as they are monotonically increasing.

Args:
    current: The current version identifier (`int`, `float`, or `str`).
    channel: Deprecated argument, kept for backwards compatibility.

Returns:
    V: The next version identifier, which must be increasing.

### `BaseCheckpointSaver.get_tuple(self, config: 'RunnableConfig') -> 'CheckpointTuple | None'`

Fetch a checkpoint tuple using the given configuration.

Args:
    config: Configuration specifying which checkpoint to retrieve.

Returns:
    The requested checkpoint tuple, or `None` if not found.

Raises:
    NotImplementedError: Implement this method in your custom checkpoint saver.

### `BaseCheckpointSaver.list(self, config: 'RunnableConfig | None', *, filter: 'dict[str, Any] | None' = None, before: 'RunnableConfig | None' = None, limit: 'int | None' = None) -> 'Iterator[CheckpointTuple]'`

List checkpoints that match the given criteria.

Args:
    config: Base configuration for filtering checkpoints.
    filter: Additional filtering criteria.
    before: List checkpoints created before this configuration.
    limit: Maximum number of checkpoints to return.

Returns:
    Iterator of matching checkpoint tuples.

Raises:
    NotImplementedError: Implement this method in your custom checkpoint saver.

### `BaseCheckpointSaver.prune(self, thread_ids: 'Sequence[str]', *, strategy: 'str' = 'keep_latest') -> 'None'`

Prune checkpoints for the given threads.

Args:
    thread_ids: The thread IDs to prune.
    strategy: The pruning strategy. `"keep_latest"` retains only the most
        recent checkpoint per namespace. `"delete"` removes all checkpoints.

!!! warning "DeltaChannel"

    Custom implementations must be `DeltaChannel`-aware. `DeltaChannel`
    stores only a sentinel in `channel_values` for non-snapshot steps;
    reconstruction walks the parent chain via
    `get_delta_channel_history`, accumulating rows from
    `checkpoint_writes` until it reaches an ancestor whose
    `channel_values` contains a `_DeltaSnapshot` blob (written every
    `snapshot_frequency` updates).

    A naive `"keep_latest"` that drops intermediate checkpoints and
    their writes can sever that chain: the surviving "latest"
    checkpoint is rarely a snapshot point itself, so its delta
    channels would silently reconstruct as empty (no error raised —
    `get_delta_channel_history` simply returns no `seed`). Safe
    options when the graph uses `DeltaChannel`:

    * Walk back from each kept checkpoint and preserve every
      ancestor (plus its `checkpoint_writes`) up to the nearest one
      whose `channel_values` already contains a `_DeltaSnapshot` for
      every `DeltaChannel`-backed key.
    * Force a fresh snapshot on the kept checkpoint before deleting
      ancestors — rewrite `channel_values[k] = _DeltaSnapshot(value)`
      for each delta channel `k` (resolving `value` via the existing
      ancestor walk first), then prune.
    * Skip pruning threads whose graph uses `DeltaChannel` until one
      of the above is implemented.

### `BaseCheckpointSaver.put(self, config: 'RunnableConfig', checkpoint: 'Checkpoint', metadata: 'CheckpointMetadata', new_versions: 'ChannelVersions') -> 'RunnableConfig'`

Store a checkpoint with its configuration and metadata.

Args:
    config: Configuration for the checkpoint.
    checkpoint: The checkpoint to store.
    metadata: Additional metadata for the checkpoint.
    new_versions: New channel versions as of this write.

Returns:
    RunnableConfig: Updated configuration after storing the checkpoint.

Raises:
    NotImplementedError: Implement this method in your custom checkpoint saver.

### `BaseCheckpointSaver.put_writes(self, config: 'RunnableConfig', writes: 'Sequence[tuple[str, Any]]', task_id: 'str', task_path: 'str' = '') -> 'None'`

Store intermediate writes linked to a checkpoint.

Args:
    config: Configuration of the related checkpoint.
    writes: List of writes to store.
    task_id: Identifier for the task creating the writes.
    task_path: Path of the task creating the writes.

Raises:
    NotImplementedError: Implement this method in your custom checkpoint saver.

### `BaseCheckpointSaver.with_allowlist(self, extra_allowlist: 'Collection[tuple[str, ...]]') -> 'BaseCheckpointSaver[V]'`

Return a shallow clone with a derived msgpack allowlist.

## `ChannelVersions(*args, **kwargs)`

dict() -> new empty dictionary
dict(mapping) -> new dictionary initialized from a mapping object's
    (key, value) pairs
dict(iterable) -> new dictionary initialized as if via:
    d = {}
    for k, v in iterable:
        d[k] = v
dict(**kwargs) -> new dictionary initialized with the name=value pairs
    in the keyword argument list.  For example:  dict(one=1, two=2)

## class `Checkpoint` (bases: dict)

State snapshot at a given point in time.

## class `CheckpointMetadata` (bases: dict)

Metadata associated with a checkpoint.

## class `CheckpointTuple(config: ForwardRef('RunnableConfig'), checkpoint: ForwardRef('Checkpoint'), metadata: ForwardRef('CheckpointMetadata'), parent_config: ForwardRef('RunnableConfig | None') = None, pending_writes: ForwardRef('list[PendingWrite] | None') = None)` (bases: tuple)

A tuple containing a checkpoint and its associated data.

## class `DeltaChannelHistory` (bases: dict)

Per-channel result entry from `BaseCheckpointSaver.get_delta_channel_history`.

!!! warning "Beta"

    Part of the `DeltaChannel` support surface; in beta. Field names and
    semantics may change.

Storage-level view of what one channel contributed across the ancestor
chain of a target checkpoint:

* `writes` — on-path deltas oldest→newest as `PendingWrite` tuples.
  Always present; possibly empty. Already filtered to one channel.
  Writes stored at the target checkpoint itself are pending for the
  next super-step and are excluded.
* `seed` — the stored value at the nearest ancestor whose
  `channel_values[ch]` is populated. Omitted if the walk reached the
  root without finding any stored value (consumer treats absence as
  "start empty"). Typically a `_DeltaSnapshot` for delta channels with
  finite snapshot frequency, or a plain value for threads migrated
  from a pre-delta channel type.

## class `ExitStack()` (bases: _BaseExitStack, AbstractContextManager)

Context manager for dynamic management of a stack of exit callbacks.

For example:
    with ExitStack() as stack:
        files = [stack.enter_context(open(fname)) for fname in filenames]
        # All opened files will automatically be closed at the end of
        # the with statement, even if attempts to open files later
        # in the list raise an exception.

### `ExitStack.close(self)`

Immediately unwind the context stack.

## class `InMemorySaver(*, serde: 'SerializerProtocol | None' = None, factory: 'type[defaultdict]' = <class 'collections.defaultdict'>) -> 'None'` (bases: BaseCheckpointSaver, AbstractContextManager, AbstractAsyncContextManager)

An in-memory checkpoint saver.

This checkpoint saver stores checkpoints in memory using a `defaultdict`.

Note:
    Only use `InMemorySaver` for debugging or testing purposes.
    For production use cases we recommend installing [langgraph-checkpoint-postgres](https://pypi.org/project/langgraph-checkpoint-postgres/) and using `PostgresSaver` / `AsyncPostgresSaver`.

    If you are using LangSmith Deployment, no checkpointer needs to be specified. The correct managed checkpointer will be used automatically.

Args:
    serde: The serializer to use for serializing and deserializing checkpoints.

Example:
    ```python
    import asyncio

    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import StateGraph

    builder = StateGraph(int)
    builder.add_node("add_one", lambda x: x + 1)
    builder.set_entry_point("add_one")
    builder.set_finish_point("add_one")

    memory = InMemorySaver()
    graph = builder.compile(checkpointer=memory)
    coro = graph.ainvoke(1, {"configurable": {"thread_id": "thread-1"}})
    asyncio.run(coro)  # Output: 2
    ```

### `InMemorySaver.__init__(self, *, serde: 'SerializerProtocol | None' = None, factory: 'type[defaultdict]' = <class 'collections.defaultdict'>) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `InMemorySaver.adelete_thread(self, thread_id: 'str') -> 'None'`

Delete all checkpoints and writes associated with a thread ID.

Args:
    thread_id: The thread ID to delete.

Returns:
    None

### `InMemorySaver.aget_delta_channel_history(self, *, config: 'RunnableConfig', channels: 'Sequence[str]') -> 'Mapping[str, DeltaChannelHistory]'`

Async version of `get_delta_channel_history`.

!!! warning "Beta"

    This method is part of the `DeltaChannel` support surface and is
    in beta. See `get_delta_channel_history` for caveats.

### `InMemorySaver.aget_tuple(self, config: 'RunnableConfig') -> 'CheckpointTuple | None'`

Asynchronous version of `get_tuple`.

This method is an asynchronous wrapper around `get_tuple` that runs the synchronous
method in a separate thread using asyncio.

Args:
    config: The config to use for retrieving the checkpoint.

Returns:
    The retrieved checkpoint tuple, or None if no matching checkpoint was found.

### `InMemorySaver.alist(self, config: 'RunnableConfig | None', *, filter: 'dict[str, Any] | None' = None, before: 'RunnableConfig | None' = None, limit: 'int | None' = None) -> 'AsyncIterator[CheckpointTuple]'`

Asynchronous version of `list`.

This method is an asynchronous wrapper around `list` that runs the synchronous
method in a separate thread using asyncio.

Args:
    config: The config to use for listing the checkpoints.

Yields:
    An asynchronous iterator of checkpoint tuples.

### `InMemorySaver.aput(self, config: 'RunnableConfig', checkpoint: 'Checkpoint', metadata: 'CheckpointMetadata', new_versions: 'ChannelVersions') -> 'RunnableConfig'`

Asynchronous version of `put`.

Args:
    config: The config to associate with the checkpoint.
    checkpoint: The checkpoint to save.
    metadata: Additional metadata to save with the checkpoint.
    new_versions: New versions as of this write

Returns:
    RunnableConfig: The updated config containing the saved checkpoint's timestamp.

### `InMemorySaver.aput_writes(self, config: 'RunnableConfig', writes: 'Sequence[tuple[str, Any]]', task_id: 'str', task_path: 'str' = '') -> 'None'`

Asynchronous version of `put_writes`.

This method is an asynchronous wrapper around `put_writes` that runs the synchronous
method in a separate thread using asyncio.

Args:
    config: The config to associate with the writes.
    writes: The writes to save, each as a (channel, value) pair.
    task_id: Identifier for the task creating the writes.
    task_path: Path of the task creating the writes.

Returns:
    None

### `InMemorySaver.delete_thread(self, thread_id: 'str') -> 'None'`

Delete all checkpoints and writes associated with a thread ID.

Args:
    thread_id: The thread ID to delete.

Returns:
    None

### `InMemorySaver.get_delta_channel_history(self, *, config: 'RunnableConfig', channels: 'Sequence[str]') -> 'Mapping[str, DeltaChannelHistory]'`

Override: walk the parent chain ONCE for all requested channels.

Each channel terminates independently at the nearest ancestor
whose stored blob is non-empty. Other channels keep walking until
they find their own terminator or hit the root.

A blob is the value AT its ancestor, prior to the writes stored
under that same ancestor (those writes produce its child, which
is on the path to the target). This holds for `_DeltaSnapshot`
blobs and for pre-delta plain values alike, so the seed
ancestor's own writes are always collected. Writes at ancestors
older than the seed are subsumed by the seed value and are never
reached — the walk terminates there.

### `InMemorySaver.get_next_version(self, current: 'str | None', channel: 'None') -> 'str'`

Generate the next version ID for a channel.

Default is to use integer versions, incrementing by `1`.

If you override, you can use `str`/`int`/`float` versions, as long as they are monotonically increasing.

Args:
    current: The current version identifier (`int`, `float`, or `str`).
    channel: Deprecated argument, kept for backwards compatibility.

Returns:
    V: The next version identifier, which must be increasing.

### `InMemorySaver.get_tuple(self, config: 'RunnableConfig') -> 'CheckpointTuple | None'`

Get a checkpoint tuple from the in-memory storage.

This method retrieves a checkpoint tuple from the in-memory storage based on the
provided config. If the config contains a `checkpoint_id` key, the checkpoint with
the matching thread ID and timestamp is retrieved. Otherwise, the latest checkpoint
for the given thread ID is retrieved.

Args:
    config: The config to use for retrieving the checkpoint.

Returns:
    The retrieved checkpoint tuple, or None if no matching checkpoint was found.

### `InMemorySaver.list(self, config: 'RunnableConfig | None', *, filter: 'dict[str, Any] | None' = None, before: 'RunnableConfig | None' = None, limit: 'int | None' = None) -> 'Iterator[CheckpointTuple]'`

List checkpoints from the in-memory storage.

This method retrieves a list of checkpoint tuples from the in-memory storage based
on the provided criteria.

Args:
    config: Base configuration for filtering checkpoints.
    filter: Additional filtering criteria for metadata.
    before: List checkpoints created before this configuration.
    limit: Maximum number of checkpoints to return.

Yields:
    An iterator of matching checkpoint tuples.

### `InMemorySaver.put(self, config: 'RunnableConfig', checkpoint: 'Checkpoint', metadata: 'CheckpointMetadata', new_versions: 'ChannelVersions') -> 'RunnableConfig'`

Save a checkpoint to the in-memory storage.

This method saves a checkpoint to the in-memory storage. The checkpoint is associated
with the provided config.

Args:
    config: The config to associate with the checkpoint.
    checkpoint: The checkpoint to save.
    metadata: Additional metadata to save with the checkpoint.
    new_versions: New versions as of this write

Returns:
    RunnableConfig: The updated config containing the saved checkpoint's timestamp.

### `InMemorySaver.put_writes(self, config: 'RunnableConfig', writes: 'Sequence[tuple[str, Any]]', task_id: 'str', task_path: 'str' = '') -> 'None'`

Save a list of writes to the in-memory storage.

This method saves a list of writes to the in-memory storage. The writes are associated
with the provided config.

Args:
    config: The config to associate with the writes.
    writes: The writes to save.
    task_id: Identifier for the task creating the writes.
    task_path: Path of the task creating the writes.

Returns:
    RunnableConfig: The updated config containing the saved writes' timestamp.

## class `Iterator()` (bases: Iterable)

## class `Mapping()` (bases: Collection)

A Mapping is a generic container for associating key/value
pairs.

This class provides concrete generic implementations of all
methods except for __getitem__, __iter__, and __len__.

### `Mapping.get(self, key, default=None)`

D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.

### `Mapping.items(self)`

D.items() -> a set-like object providing a view on D's items

### `Mapping.keys(self)`

D.keys() -> a set-like object providing a view on D's keys

### `Mapping.values(self)`

D.values() -> an object providing a view on D's values

## class `MemorySaver(*, serde: 'SerializerProtocol | None' = None, factory: 'type[defaultdict]' = <class 'collections.defaultdict'>) -> 'None'` (bases: BaseCheckpointSaver, AbstractContextManager, AbstractAsyncContextManager)

An in-memory checkpoint saver.

This checkpoint saver stores checkpoints in memory using a `defaultdict`.

Note:
    Only use `InMemorySaver` for debugging or testing purposes.
    For production use cases we recommend installing [langgraph-checkpoint-postgres](https://pypi.org/project/langgraph-checkpoint-postgres/) and using `PostgresSaver` / `AsyncPostgresSaver`.

    If you are using LangSmith Deployment, no checkpointer needs to be specified. The correct managed checkpointer will be used automatically.

Args:
    serde: The serializer to use for serializing and deserializing checkpoints.

Example:
    ```python
    import asyncio

    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import StateGraph

    builder = StateGraph(int)
    builder.add_node("add_one", lambda x: x + 1)
    builder.set_entry_point("add_one")
    builder.set_finish_point("add_one")

    memory = InMemorySaver()
    graph = builder.compile(checkpointer=memory)
    coro = graph.ainvoke(1, {"configurable": {"thread_id": "thread-1"}})
    asyncio.run(coro)  # Output: 2
    ```

### `MemorySaver.__init__(self, *, serde: 'SerializerProtocol | None' = None, factory: 'type[defaultdict]' = <class 'collections.defaultdict'>) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `MemorySaver.adelete_thread(self, thread_id: 'str') -> 'None'`

Delete all checkpoints and writes associated with a thread ID.

Args:
    thread_id: The thread ID to delete.

Returns:
    None

### `MemorySaver.aget_delta_channel_history(self, *, config: 'RunnableConfig', channels: 'Sequence[str]') -> 'Mapping[str, DeltaChannelHistory]'`

Async version of `get_delta_channel_history`.

!!! warning "Beta"

    This method is part of the `DeltaChannel` support surface and is
    in beta. See `get_delta_channel_history` for caveats.

### `MemorySaver.aget_tuple(self, config: 'RunnableConfig') -> 'CheckpointTuple | None'`

Asynchronous version of `get_tuple`.

This method is an asynchronous wrapper around `get_tuple` that runs the synchronous
method in a separate thread using asyncio.

Args:
    config: The config to use for retrieving the checkpoint.

Returns:
    The retrieved checkpoint tuple, or None if no matching checkpoint was found.

### `MemorySaver.alist(self, config: 'RunnableConfig | None', *, filter: 'dict[str, Any] | None' = None, before: 'RunnableConfig | None' = None, limit: 'int | None' = None) -> 'AsyncIterator[CheckpointTuple]'`

Asynchronous version of `list`.

This method is an asynchronous wrapper around `list` that runs the synchronous
method in a separate thread using asyncio.

Args:
    config: The config to use for listing the checkpoints.

Yields:
    An asynchronous iterator of checkpoint tuples.

### `MemorySaver.aput(self, config: 'RunnableConfig', checkpoint: 'Checkpoint', metadata: 'CheckpointMetadata', new_versions: 'ChannelVersions') -> 'RunnableConfig'`

Asynchronous version of `put`.

Args:
    config: The config to associate with the checkpoint.
    checkpoint: The checkpoint to save.
    metadata: Additional metadata to save with the checkpoint.
    new_versions: New versions as of this write

Returns:
    RunnableConfig: The updated config containing the saved checkpoint's timestamp.

### `MemorySaver.aput_writes(self, config: 'RunnableConfig', writes: 'Sequence[tuple[str, Any]]', task_id: 'str', task_path: 'str' = '') -> 'None'`

Asynchronous version of `put_writes`.

This method is an asynchronous wrapper around `put_writes` that runs the synchronous
method in a separate thread using asyncio.

Args:
    config: The config to associate with the writes.
    writes: The writes to save, each as a (channel, value) pair.
    task_id: Identifier for the task creating the writes.
    task_path: Path of the task creating the writes.

Returns:
    None

### `MemorySaver.delete_thread(self, thread_id: 'str') -> 'None'`

Delete all checkpoints and writes associated with a thread ID.

Args:
    thread_id: The thread ID to delete.

Returns:
    None

### `MemorySaver.get_delta_channel_history(self, *, config: 'RunnableConfig', channels: 'Sequence[str]') -> 'Mapping[str, DeltaChannelHistory]'`

Override: walk the parent chain ONCE for all requested channels.

Each channel terminates independently at the nearest ancestor
whose stored blob is non-empty. Other channels keep walking until
they find their own terminator or hit the root.

A blob is the value AT its ancestor, prior to the writes stored
under that same ancestor (those writes produce its child, which
is on the path to the target). This holds for `_DeltaSnapshot`
blobs and for pre-delta plain values alike, so the seed
ancestor's own writes are always collected. Writes at ancestors
older than the seed are subsumed by the seed value and are never
reached — the walk terminates there.

### `MemorySaver.get_next_version(self, current: 'str | None', channel: 'None') -> 'str'`

Generate the next version ID for a channel.

Default is to use integer versions, incrementing by `1`.

If you override, you can use `str`/`int`/`float` versions, as long as they are monotonically increasing.

Args:
    current: The current version identifier (`int`, `float`, or `str`).
    channel: Deprecated argument, kept for backwards compatibility.

Returns:
    V: The next version identifier, which must be increasing.

### `MemorySaver.get_tuple(self, config: 'RunnableConfig') -> 'CheckpointTuple | None'`

Get a checkpoint tuple from the in-memory storage.

This method retrieves a checkpoint tuple from the in-memory storage based on the
provided config. If the config contains a `checkpoint_id` key, the checkpoint with
the matching thread ID and timestamp is retrieved. Otherwise, the latest checkpoint
for the given thread ID is retrieved.

Args:
    config: The config to use for retrieving the checkpoint.

Returns:
    The retrieved checkpoint tuple, or None if no matching checkpoint was found.

### `MemorySaver.list(self, config: 'RunnableConfig | None', *, filter: 'dict[str, Any] | None' = None, before: 'RunnableConfig | None' = None, limit: 'int | None' = None) -> 'Iterator[CheckpointTuple]'`

List checkpoints from the in-memory storage.

This method retrieves a list of checkpoint tuples from the in-memory storage based
on the provided criteria.

Args:
    config: Base configuration for filtering checkpoints.
    filter: Additional filtering criteria for metadata.
    before: List checkpoints created before this configuration.
    limit: Maximum number of checkpoints to return.

Yields:
    An iterator of matching checkpoint tuples.

### `MemorySaver.put(self, config: 'RunnableConfig', checkpoint: 'Checkpoint', metadata: 'CheckpointMetadata', new_versions: 'ChannelVersions') -> 'RunnableConfig'`

Save a checkpoint to the in-memory storage.

This method saves a checkpoint to the in-memory storage. The checkpoint is associated
with the provided config.

Args:
    config: The config to associate with the checkpoint.
    checkpoint: The checkpoint to save.
    metadata: Additional metadata to save with the checkpoint.
    new_versions: New versions as of this write

Returns:
    RunnableConfig: The updated config containing the saved checkpoint's timestamp.

### `MemorySaver.put_writes(self, config: 'RunnableConfig', writes: 'Sequence[tuple[str, Any]]', task_id: 'str', task_path: 'str' = '') -> 'None'`

Save a list of writes to the in-memory storage.

This method saves a list of writes to the in-memory storage. The writes are associated
with the provided config.

Args:
    config: The config to associate with the writes.
    writes: The writes to save.
    task_id: Identifier for the task creating the writes.
    task_path: Path of the task creating the writes.

Returns:
    RunnableConfig: The updated config containing the saved writes' timestamp.

## `PendingWrite(*args, **kwargs)`

Built-in immutable sequence.

If no argument is given, the constructor returns an empty tuple.
If iterable is specified the tuple is initialized from iterable's items.

If the argument is a tuple, the return value is the same object.

## class `PersistentDict(*args: 'Any', filename: 'str', **kwds: 'Any') -> 'None'` (bases: defaultdict)

Persistent dictionary with an API compatible with shelve and anydbm.

The dict is kept in memory, so the dictionary operations run as fast as
a regular dictionary.

Write to disk is delayed until close or sync (similar to gdbm's fast mode).

Input file format is automatically discovered.
Output file format is selectable between pickle, json, and csv.
All three serialization formats are backed by fast C implementations.

Adapted from https://code.activestate.com/recipes/576642-persistent-dict-with-multiple-standard-file-format/

### `PersistentDict.__init__(self, *args: 'Any', filename: 'str', **kwds: 'Any') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `PersistentDict.close(self) -> 'None'`

### `PersistentDict.dump(self, fileobj: 'Any') -> 'None'`

### `PersistentDict.load(self) -> 'None'`

### `PersistentDict.sync(self) -> 'None'`

Write dict to disk

## class `RunnableConfig` (bases: dict)

Configuration for a `Runnable`.

!!! note Custom values

    The `TypedDict` has `total=False` set intentionally to:

    - Allow partial configs to be created and merged together via `merge_configs`
    - Support config propagation from parent to child runnables via
        `var_child_runnable_config` (a `ContextVar` that automatically passes
        config down the call stack without explicit parameter passing), where
        configs are merged rather than replaced

    !!! example

        ```python
        # Parent sets tags
        chain.invoke(input, config={"tags": ["parent"]})
        # Child automatically inherits and can add:
        # ensure_config({"tags": ["child"]}) -> {"tags": ["parent", "child"]}
        ```

## class `Sequence()` (bases: Reversible, Collection)

All the operations on a read-only sequence.

Concrete subclasses must override __new__ or __init__,
__getitem__, and __len__.

### `Sequence.count(self, value)`

S.count(value) -> integer -- return number of occurrences of value

### `Sequence.index(self, value, start=0, stop=None)`

S.index(value, [start, [stop]]) -> integer -- return first index of value.
Raises ValueError if the value is not present.

Supporting start and stop arguments is optional, but
recommended.

## class `SerializerProtocol(*args, **kwargs)` (bases: Protocol)

Protocol for serialization and deserialization of objects.

- `dumps_typed`: Serialize an object to a tuple `(type, bytes)`.
- `loads_typed`: Deserialize an object from a tuple `(type, bytes)`.

Valid implementations include the `pickle`, `json` and `orjson` modules.

### `SerializerProtocol.__init__(self, *args, **kwargs)`

### `SerializerProtocol.dumps_typed(self, obj: 'Any') -> 'tuple[str, bytes]'`

### `SerializerProtocol.loads_typed(self, data: 'tuple[str, bytes]') -> 'Any'`

## class `TracebackType`

TracebackType(tb_next, tb_frame, tb_lasti, tb_lineno)
--

Create a new traceback object.

## `WRITES_IDX_MAP`

Value of type `dict`: `{'__error__': -1, '__scheduled__': -2, '__interrupt__': -3, '__resume__': -4}`

## `annotations`

Value of type `_Feature`: `_Feature((3, 7, 0, 'beta', 1), None, 16777216)`

## class `defaultdict` (bases: dict)

defaultdict(default_factory=None, /, [...]) --> dict with default factory

The default factory is called without arguments to produce
a new value when a key is not present, in __getitem__ only.
A defaultdict compares equal to a dict with the same items.
All remaining arguments are treated the same as if they were
passed to the dict constructor, including keyword arguments.

### `defaultdict.__init__(self, /, *args, **kwargs)`

Initialize self.  See help(type(self)) for accurate signature.

### `defaultdict.copy`

D.copy() -> a shallow copy of D.

## `get_checkpoint_id(config: 'RunnableConfig') -> 'str | None'`

Get checkpoint ID.

## `get_checkpoint_metadata(config: 'RunnableConfig', metadata: 'CheckpointMetadata') -> 'CheckpointMetadata'`

Get checkpoint metadata in a backwards-compatible manner.

## `logger`

Value of type `Logger`: `<Logger langgraph.checkpoint.memory (WARNING)>`
