# `langgraph.checkpoint.base`

Public names: `Any`, `AsyncIterator`, `BaseCheckpointSaver`, `ChannelProtocol`, `ChannelVersions`, `Checkpoint`, `CheckpointMetadata`, `CheckpointTuple`, `Collection`, `DeltaChannelHistory`, `ERROR`, `EXCLUDED_METADATA_KEYS`, `EmptyChannelError`, `EncryptedSerializer`, `Generic`, `INTERRUPT`, `Iterator`, `JsonPlusSerializer`, `LATEST_VERSION`, `Literal`, `Mapping`, `NamedTuple`, `NotRequired`, `PendingWrite`, `RESUME`, `RunnableConfig`, `SCHEDULED`, `Sequence`, `SerializerProtocol`, `TypeVar`, `TypedDict`, `V`, `WRITES_IDX_MAP`, `annotations`, `copy`, `copy_checkpoint`, `create_checkpoint`, `empty_checkpoint`, `get_checkpoint_id`, `get_checkpoint_metadata`, `get_serializable_checkpoint_metadata`, `id`, `logger`, `logging`, `maybe_add_typed_methods`, `uuid6`

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

## class `ChannelProtocol(*args, **kwargs)` (bases: Protocol)

Base class for protocol classes.

Protocol classes are defined as::

    class Proto(Protocol):
        def meth(self) -> int:
            ...

Such classes are primarily used with static type checkers that recognize
structural subtyping (static duck-typing).

For example::

    class C:
        def meth(self) -> int:
            return 0

    def func(x: Proto) -> int:
        return x.meth()

    func(C())  # Passes static type check

See PEP 544 for details. Protocol classes decorated with
@typing.runtime_checkable act as simple-minded runtime protocols that check
only the presence of given attributes, ignoring their type signatures.
Protocol classes can be generic, they are defined as::

    class GenProto(Protocol[T]):
        def meth(self) -> T:
            ...

### property `ChannelProtocol.UpdateType`

### property `ChannelProtocol.ValueType`

### `ChannelProtocol.__init__(self, *args, **kwargs)`

### `ChannelProtocol.checkpoint(self) -> Optional[~C]`

### `ChannelProtocol.consume(self) -> bool`

### `ChannelProtocol.from_checkpoint(self, checkpoint: Optional[~C]) -> Self`

### `ChannelProtocol.get(self) -> +Value`

### `ChannelProtocol.update(self, values: collections.abc.Sequence[-Update]) -> bool`

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

## class `Collection()` (bases: Sized, Iterable, Container)

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

## `ERROR`

Value of type `str`: `'__error__'`

## `EXCLUDED_METADATA_KEYS`

Value of type `set`: `{'checkpoint_id', 'langgraph_node', 'langgraph_step', 'langgraph_path', 'checkpoint_ns', 'langgraph_triggers', 'checkpoint_map', 'thread_id', 'langgraph_checkpoint_ns'}`

## class `EmptyChannelError` (bases: Exception)

Raised when attempting to get the value of a channel that hasn't been updated
for the first time yet.

## class `EncryptedSerializer(cipher: langgraph.checkpoint.serde.base.CipherProtocol, serde: langgraph.checkpoint.serde.base.SerializerProtocol = <langgraph.checkpoint.serde.jsonplus.JsonPlusSerializer object at 0x7d6b4018d450>) -> None` (bases: SerializerProtocol)

Serializer that encrypts and decrypts data using an encryption protocol.

### `EncryptedSerializer.__init__(self, cipher: langgraph.checkpoint.serde.base.CipherProtocol, serde: langgraph.checkpoint.serde.base.SerializerProtocol = <langgraph.checkpoint.serde.jsonplus.JsonPlusSerializer object at 0x7d6b4018d450>) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `EncryptedSerializer.dumps_typed(self, obj: Any) -> tuple[str, bytes]`

Serialize an object to a tuple `(type, bytes)` and encrypt the bytes.

### `EncryptedSerializer.from_pycryptodome_aes(cls, serde: langgraph.checkpoint.serde.base.SerializerProtocol = <langgraph.checkpoint.serde.jsonplus.JsonPlusSerializer object at 0x7d6b4018d550>, **kwargs: Any) -> 'EncryptedSerializer'`

Create an `EncryptedSerializer` using AES encryption.

### `EncryptedSerializer.loads_typed(self, data: tuple[str, bytes]) -> Any`

## class `Generic()`

Abstract base class for generic types.

A generic type is typically declared by inheriting from
this class parameterized with one or more type variables.
For example, a generic mapping type might be defined as::

  class Mapping(Generic[KT, VT]):
      def __getitem__(self, key: KT) -> VT:
          ...
      # Etc.

This class can then be used as follows::

  def lookup_name(mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
      try:
          return mapping[key]
      except KeyError:
          return default

## `INTERRUPT`

Value of type `str`: `'__interrupt__'`

## class `Iterator()` (bases: Iterable)

## class `JsonPlusSerializer(*, pickle_fallback: 'bool' = False, allowed_json_modules: 'Iterable[tuple[str, ...]] | Literal[True] | None' = None, allowed_msgpack_modules: 'AllowedMsgpackModules | Literal[True] | None' = <object object at 0x7d6b429862e0>, __unpack_ext_hook__: 'Callable[[int, bytes], Any] | None' = None) -> 'None'` (bases: SerializerProtocol)

Serializer that uses ormsgpack, with optional fallbacks.

!!! warning

    Security note: This serializer is intended for use within the `BaseCheckpointSaver`
    class and called within the Pregel loop. It should not be used on untrusted
    python objects. If an attacker can write directly to your checkpoint database,
    they may be able to trigger code execution when data is deserialized.

    Set the environment variable ``LANGGRAPH_STRICT_MSGPACK=true`` to restrict
    deserialization to a built-in allowlist of safe types.  You can also pass
    an explicit ``allowed_msgpack_modules`` to the constructor.

### `JsonPlusSerializer.__init__(self, *, pickle_fallback: 'bool' = False, allowed_json_modules: 'Iterable[tuple[str, ...]] | Literal[True] | None' = None, allowed_msgpack_modules: 'AllowedMsgpackModules | Literal[True] | None' = <object object at 0x7d6b429862e0>, __unpack_ext_hook__: 'Callable[[int, bytes], Any] | None' = None) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `JsonPlusSerializer.dumps_typed(self, obj: 'Any') -> 'tuple[str, bytes]'`

### `JsonPlusSerializer.loads_typed(self, data: 'tuple[str, bytes]') -> 'Any'`

### `JsonPlusSerializer.with_msgpack_allowlist(self, extra_allowlist: 'Iterable[tuple[str, ...] | type]') -> 'JsonPlusSerializer'`

Return a new serializer with a merged msgpack allowlist.

## `LATEST_VERSION`

Value of type `int`: `2`

## `Literal(*args, **kwds)`

Special typing form to define literal types (a.k.a. value types).

This form can be used to indicate to type checkers that the corresponding
variable or function parameter has a value equivalent to the provided
literal (or one of several literals)::

    def validate_simple(data: Any) -> Literal[True]:  # always returns True
        ...

    MODE = Literal['r', 'rb', 'w', 'wb']
    def open_helper(file: str, mode: MODE) -> str:
        ...

    open_helper('/some/path', 'r')  # Passes type check
    open_helper('/other/path', 'typo')  # Error in type checker

Literal[...] cannot be subclassed. At runtime, an arbitrary value
is allowed as type argument to Literal[...], but type checkers may
impose restrictions.

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

## `NamedTuple(typename, fields=None, /, **kwargs)`

Typed version of namedtuple.

Usage::

    class Employee(NamedTuple):
        name: str
        id: int

This is equivalent to::

    Employee = collections.namedtuple('Employee', ['name', 'id'])

The resulting class has an extra __annotations__ attribute, giving a
dict that maps field names to types.  (The field names are also in
the _fields attribute, which is part of the namedtuple API.)
An alternative equivalent functional syntax is also accepted::

    Employee = NamedTuple('Employee', [('name', str), ('id', int)])

## `NotRequired(*args, **kwds)`

Special typing construct to mark a TypedDict key as potentially missing.

For example::

    class Movie(TypedDict):
        title: str
        year: NotRequired[int]

    m = Movie(
        title='The Matrix',  # typechecker error if key is omitted
        year=1999,
    )

## `PendingWrite(*args, **kwargs)`

Built-in immutable sequence.

If no argument is given, the constructor returns an empty tuple.
If iterable is specified the tuple is initialized from iterable's items.

If the argument is a tuple, the return value is the same object.

## `RESUME`

Value of type `str`: `'__resume__'`

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

## `SCHEDULED`

Value of type `str`: `'__scheduled__'`

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

## class `TypeVar(name, *constraints, bound=None, covariant=False, contravariant=False)` (bases: _Final, _Immutable, _BoundVarianceMixin, _PickleUsingNameMixin)

Type variable.

Usage::

  T = TypeVar('T')  # Can be anything
  A = TypeVar('A', str, bytes)  # Must be str or bytes

Type variables exist primarily for the benefit of static type
checkers.  They serve as the parameters for generic types as well
as for generic function definitions.  See class Generic for more
information on generic types.  Generic functions work as follows:

  def repeat(x: T, n: int) -> List[T]:
      '''Return a list containing n references to x.'''
      return [x]*n

  def longest(x: A, y: A) -> A:
      '''Return the longest of two strings.'''
      return x if len(x) >= len(y) else y

The latter example's signature is essentially the overloading
of (str, str) -> str and (bytes, bytes) -> bytes.  Also note
that if the arguments are instances of some subclass of str,
the return type is still plain str.

At runtime, isinstance(x, T) and issubclass(C, T) will raise TypeError.

Type variables defined with covariant=True or contravariant=True
can be used to declare covariant or contravariant generic types.
See PEP 484 for more details. By default generic types are invariant
in all type variables.

Type variables can be introspected. e.g.:

  T.__name__ == 'T'
  T.__constraints__ == ()
  T.__covariant__ == False
  T.__contravariant__ = False
  A.__constraints__ == (str, bytes)

Note that only type variables defined in global scope can be pickled.

### `TypeVar.__init__(self, name, *constraints, bound=None, covariant=False, contravariant=False)`

Initialize self.  See help(type(self)) for accurate signature.

## `TypedDict(typename, fields=None, /, *, total=True, **kwargs)`

A simple typed namespace. At runtime it is equivalent to a plain dict.

TypedDict creates a dictionary type such that a type checker will expect all
instances to have a certain set of keys, where each key is
associated with a value of a consistent type. This expectation
is not checked at runtime.

Usage::

    >>> class Point2D(TypedDict):
    ...     x: int
    ...     y: int
    ...     label: str
    ...
    >>> a: Point2D = {'x': 1, 'y': 2, 'label': 'good'}  # OK
    >>> b: Point2D = {'z': 3, 'label': 'bad'}           # Fails type check
    >>> Point2D(x=1, y=2, label='first') == dict(x=1, y=2, label='first')
    True

The type info can be accessed via the Point2D.__annotations__ dict, and
the Point2D.__required_keys__ and Point2D.__optional_keys__ frozensets.
TypedDict supports an additional equivalent form::

    Point2D = TypedDict('Point2D', {'x': int, 'y': int, 'label': str})

By default, all keys must be present in a TypedDict. It is possible
to override this by specifying totality::

    class Point2D(TypedDict, total=False):
        x: int
        y: int

This means that a Point2D TypedDict can have any of the keys omitted. A type
checker is only expected to support a literal False or True as the value of
the total argument. True is the default, and makes all items defined in the
class body be required.

The Required and NotRequired special forms can also be used to mark
individual keys as being required or not required::

    class Point2D(TypedDict):
        x: int               # the "x" key must always be present (Required is the default)
        y: NotRequired[int]  # the "y" key can be omitted

See PEP 655 for more details on Required and NotRequired.

## `V`

Value of type `TypeVar`: `~V`

## `WRITES_IDX_MAP`

Value of type `dict`: `{'__error__': -1, '__scheduled__': -2, '__interrupt__': -3, '__resume__': -4}`

## `annotations`

Value of type `_Feature`: `_Feature((3, 7, 0, 'beta', 1), None, 16777216)`

## `copy_checkpoint(checkpoint: 'Checkpoint') -> 'Checkpoint'`

## `create_checkpoint(checkpoint: 'Checkpoint', channels: 'Mapping[str, ChannelProtocol] | None', step: 'int', *, id: 'str | None' = None) -> 'Checkpoint'`

Create a checkpoint for the given channels.

## `empty_checkpoint() -> 'Checkpoint'`

## `get_checkpoint_id(config: 'RunnableConfig') -> 'str | None'`

Get checkpoint ID.

## `get_checkpoint_metadata(config: 'RunnableConfig', metadata: 'CheckpointMetadata') -> 'CheckpointMetadata'`

Get checkpoint metadata in a backwards-compatible manner.

## `get_serializable_checkpoint_metadata(config: 'RunnableConfig', metadata: 'CheckpointMetadata') -> 'CheckpointMetadata'`

Get checkpoint metadata in a backwards-compatible manner.

## `logger`

Value of type `Logger`: `<Logger langgraph.checkpoint.base (WARNING)>`

## `maybe_add_typed_methods(serde: 'SerializerProtocol | UntypedSerializerProtocol') -> 'SerializerProtocol'`

Wrap serde old serde implementations in a class with loads_typed and dumps_typed for backwards compatibility.

## `uuid6(node: 'int | None' = None, clock_seq: 'int | None' = None) -> 'UUID'`

UUID version 6 is a field-compatible version of UUIDv1, reordered for
improved DB locality. It is expected that UUIDv6 will primarily be
used in contexts where there are existing v1 UUIDs. Systems that do
not involve legacy UUIDv1 SHOULD consider using UUIDv7 instead.

If 'node' is not given, a random 48-bit number is chosen.

If 'clock_seq' is given, it is used as the sequence number;
otherwise a random 14-bit sequence number is chosen.
