# `langgraph.channels`

Public names: `AnyValue`, `BaseChannel`, `BinaryOperatorAggregate`, `DeltaChannel`, `EphemeralValue`, `LastValue`, `LastValueAfterFinish`, `NamedBarrierValue`, `NamedBarrierValueAfterFinish`, `Topic`, `UntrackedValue`

## class `AnyValue(typ: 'Any', key: 'str' = '') -> 'None'` (bases: BaseChannel)

Stores the last value received, assumes that if multiple values are
received, they are all equal.

### property `AnyValue.UpdateType`

The type of the update received by the channel.

### property `AnyValue.ValueType`

The type of the value stored in the channel.

### `AnyValue.__init__(self, typ: 'Any', key: 'str' = '') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `AnyValue.checkpoint(self) -> 'Value'`

Return a serializable representation of the channel's current state.

Raises `EmptyChannelError` if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `AnyValue.copy(self) -> 'Self'`

Return a copy of the channel.

### `AnyValue.from_checkpoint(self, checkpoint: 'Value') -> 'Self'`

Return a new identical channel, optionally initialized from a checkpoint.

If the checkpoint contains complex data structures, they should be copied.

### `AnyValue.get(self) -> 'Value'`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `AnyValue.is_available(self) -> 'bool'`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `AnyValue.update(self, values: 'Sequence[Value]') -> 'bool'`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.

## class `BaseChannel(typ: 'Any', key: 'str' = '') -> 'None'` (bases: Generic, ABC)

Base class for all channels.

### property `BaseChannel.UpdateType`

The type of the update received by the channel.

### property `BaseChannel.ValueType`

The type of the value stored in the channel.

### `BaseChannel.__init__(self, typ: 'Any', key: 'str' = '') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `BaseChannel.checkpoint(self) -> 'Checkpoint | Any'`

Return a serializable representation of the channel's current state.

Raises `EmptyChannelError` if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `BaseChannel.consume(self) -> 'bool'`

Notify the channel that a subscribed task ran.

By default, no-op.

A channel can use this method to modify its state, preventing the value from being consumed again.

Returns `True` if the channel was updated, `False` otherwise.

### `BaseChannel.copy(self) -> 'Self'`

Return a copy of the channel.

By default, delegates to `checkpoint()` and `from_checkpoint()`.

Subclasses can override this method with a more efficient implementation.

### `BaseChannel.finish(self) -> 'bool'`

Notify the channel that the Pregel run is finishing.

By default, no-op.

A channel can use this method to modify its state, preventing finish.

Returns `True` if the channel was updated, `False` otherwise.

### `BaseChannel.from_checkpoint(self, checkpoint: 'Checkpoint | Any') -> 'Self'`

Return a new identical channel, optionally initialized from a checkpoint.

If the checkpoint contains complex data structures, they should be copied.

### `BaseChannel.get(self) -> 'Value'`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `BaseChannel.is_available(self) -> 'bool'`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `BaseChannel.update(self, values: 'Sequence[Update]') -> 'bool'`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.

## class `BinaryOperatorAggregate(typ: type[~Value], operator: collections.abc.Callable[[~Value, ~Value], ~Value])` (bases: BaseChannel)

Stores the result of applying a binary operator to the current value and each new value.

```python
import operator

total = Channels.BinaryOperatorAggregate(int, operator.add)
```

### property `BinaryOperatorAggregate.UpdateType`

The type of the update received by the channel.

### property `BinaryOperatorAggregate.ValueType`

The type of the value stored in the channel.

### `BinaryOperatorAggregate.__init__(self, typ: type[~Value], operator: collections.abc.Callable[[~Value, ~Value], ~Value])`

Initialize self.  See help(type(self)) for accurate signature.

### `BinaryOperatorAggregate.checkpoint(self) -> ~Value`

Return a serializable representation of the channel's current state.

Raises `EmptyChannelError` if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `BinaryOperatorAggregate.copy(self) -> Self`

Return a copy of the channel.

### `BinaryOperatorAggregate.from_checkpoint(self, checkpoint: ~Value) -> Self`

Return a new identical channel, optionally initialized from a checkpoint.

If the checkpoint contains complex data structures, they should be copied.

### `BinaryOperatorAggregate.get(self) -> ~Value`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `BinaryOperatorAggregate.is_available(self) -> bool`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `BinaryOperatorAggregate.update(self, values: collections.abc.Sequence[~Value]) -> bool`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.

## class `DeltaChannel(reducer: 'Callable[[Any, Sequence[Any]], Any]', typ: 'type[Value] | None' = None, *, snapshot_frequency: 'int' = 1000) -> 'None'` (bases: BaseChannel)

Reducer channel that stores only a sentinel in checkpoint blobs and
reconstructs state by replaying ancestor writes through the reducer.

!!! warning "Beta"

    `DeltaChannel` is in beta. The API and on-disk representation may
    change in future releases. Threads written with `DeltaChannel` today
    are expected to remain readable, but the surrounding contract
    (`BaseCheckpointSaver.get_delta_channel_history`, the
    `_DeltaSnapshot` blob shape, the `counters_since_delta_snapshot`
    metadata field) is not yet stable.

The reducer receives the current accumulated value and a batch of writes
in one call: `reducer(state, [write1, write2, ...]) -> new_state`.

Reducers must be deterministic and batching-invariant (associative across
folds): applying two consecutive write batches separately must produce the
same state as applying their concatenation once:

    reducer(reducer(state, xs), ys) == reducer(state, xs + ys)

This lets LangGraph replay checkpointed writes in larger batches than they
were originally produced without changing reconstructed state.

Snapshot cadence is driven by two counters: per-channel update count and
total supersteps since last snapshot. `create_checkpoint` writes a full
`_DeltaSnapshot` blob when EITHER the update count reaches
`snapshot_frequency` OR the supersteps count reaches the system-wide
`DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` bound (default 5000), bounding
replay depth even for channels that stop receiving writes.

Parameters:
    reducer: `(state, list[writes]) -> new_state`. Must be deterministic
        and batching-invariant as described above.
    typ: The value type (e.g. `list`, `dict`). Inferred automatically
        from the outer type when used inside `Annotated[T, DeltaChannel(...)]`.
    snapshot_frequency: Every Nth update to this channel writes a snapshot
        blob (default `1000`). Must be a positive int.

### property `DeltaChannel.UpdateType`

The type of the update received by the channel.

### property `DeltaChannel.ValueType`

The type of the value stored in the channel.

### `DeltaChannel.__init__(self, reducer: 'Callable[[Any, Sequence[Any]], Any]', typ: 'type[Value] | None' = None, *, snapshot_frequency: 'int' = 1000) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `DeltaChannel.checkpoint(self) -> 'Any'`

Return stored representation: always `MISSING`.

Snapshot decisions live in `create_checkpoint` (which has the channel
version) and write `_DeltaSnapshot(ch.get())` directly into
`channel_values`. For non-snapshot steps the channel does not appear
in `channel_values`; reconstruction walks ancestor writes via the
saver's `get_delta_channel_history`.

### `DeltaChannel.copy(self) -> 'Self'`

Return a copy of the channel.

By default, delegates to `checkpoint()` and `from_checkpoint()`.

Subclasses can override this method with a more efficient implementation.

### `DeltaChannel.from_checkpoint(self, checkpoint: 'Any') -> 'Self'`

Initialize from a stored blob.

Blob types:
  * `MISSING`: start empty; caller replays writes.
  * `_DeltaSnapshot(value)`: restore value directly from snapshot.
  * plain value (migration from old `BinaryOperatorAggregate` blobs):
    use directly.

### `DeltaChannel.get(self) -> 'Any'`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `DeltaChannel.is_available(self) -> 'bool'`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `DeltaChannel.replay_writes(self, writes: 'Sequence[PendingWrite]') -> 'None'`

Apply ancestor writes oldest-to-newest via a single reducer call.

If any write is an Overwrite, the last one in the sequence acts as
the reset point: its value becomes the new base and only writes
after it are passed to the reducer.

### `DeltaChannel.update(self, values: 'Sequence[Any]') -> 'bool'`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.

## class `EphemeralValue(typ: 'Any', guard: 'bool' = True) -> 'None'` (bases: BaseChannel)

Stores the value received in the step immediately preceding, clears after.

### property `EphemeralValue.UpdateType`

The type of the update received by the channel.

### property `EphemeralValue.ValueType`

The type of the value stored in the channel.

### `EphemeralValue.__init__(self, typ: 'Any', guard: 'bool' = True) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `EphemeralValue.checkpoint(self) -> 'Value'`

Return a serializable representation of the channel's current state.

Raises `EmptyChannelError` if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `EphemeralValue.copy(self) -> 'Self'`

Return a copy of the channel.

### `EphemeralValue.from_checkpoint(self, checkpoint: 'Value') -> 'Self'`

Return a new identical channel, optionally initialized from a checkpoint.

If the checkpoint contains complex data structures, they should be copied.

### `EphemeralValue.get(self) -> 'Value'`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `EphemeralValue.is_available(self) -> 'bool'`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `EphemeralValue.update(self, values: 'Sequence[Value]') -> 'bool'`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.

## class `LastValue(typ: 'Any', key: 'str' = '') -> 'None'` (bases: BaseChannel)

Stores the last value received, can receive at most one value per step.

### property `LastValue.UpdateType`

The type of the update received by the channel.

### property `LastValue.ValueType`

The type of the value stored in the channel.

### `LastValue.__init__(self, typ: 'Any', key: 'str' = '') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `LastValue.checkpoint(self) -> 'Value'`

Return a serializable representation of the channel's current state.

Raises `EmptyChannelError` if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `LastValue.copy(self) -> 'Self'`

Return a copy of the channel.

### `LastValue.from_checkpoint(self, checkpoint: 'Value') -> 'Self'`

Return a new identical channel, optionally initialized from a checkpoint.

If the checkpoint contains complex data structures, they should be copied.

### `LastValue.get(self) -> 'Value'`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `LastValue.is_available(self) -> 'bool'`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `LastValue.update(self, values: 'Sequence[Value]') -> 'bool'`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.

## class `LastValueAfterFinish(typ: 'Any', key: 'str' = '') -> 'None'` (bases: BaseChannel)

Stores the last value received, but only made available after finish().
Once made available, clears the value.

### property `LastValueAfterFinish.UpdateType`

The type of the update received by the channel.

### property `LastValueAfterFinish.ValueType`

The type of the value stored in the channel.

### `LastValueAfterFinish.__init__(self, typ: 'Any', key: 'str' = '') -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `LastValueAfterFinish.checkpoint(self) -> 'tuple[Value | Any, bool] | Any'`

Return a serializable representation of the channel's current state.

Raises `EmptyChannelError` if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `LastValueAfterFinish.consume(self) -> 'bool'`

Notify the channel that a subscribed task ran.

By default, no-op.

A channel can use this method to modify its state, preventing the value from being consumed again.

Returns `True` if the channel was updated, `False` otherwise.

### `LastValueAfterFinish.finish(self) -> 'bool'`

Notify the channel that the Pregel run is finishing.

By default, no-op.

A channel can use this method to modify its state, preventing finish.

Returns `True` if the channel was updated, `False` otherwise.

### `LastValueAfterFinish.from_checkpoint(self, checkpoint: 'tuple[Value | Any, bool] | Any') -> 'Self'`

Return a new identical channel, optionally initialized from a checkpoint.

If the checkpoint contains complex data structures, they should be copied.

### `LastValueAfterFinish.get(self) -> 'Value'`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `LastValueAfterFinish.is_available(self) -> 'bool'`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `LastValueAfterFinish.update(self, values: 'Sequence[Value | Any]') -> 'bool'`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.

## class `NamedBarrierValue(typ: type[~Value], names: set[~Value]) -> None` (bases: BaseChannel)

A channel that waits until all named values are received before making the value available.

### property `NamedBarrierValue.UpdateType`

The type of the update received by the channel.

### property `NamedBarrierValue.ValueType`

The type of the value stored in the channel.

### `NamedBarrierValue.__init__(self, typ: type[~Value], names: set[~Value]) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `NamedBarrierValue.checkpoint(self) -> set[~Value]`

Return a serializable representation of the channel's current state.

Raises `EmptyChannelError` if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `NamedBarrierValue.consume(self) -> bool`

Notify the channel that a subscribed task ran.

By default, no-op.

A channel can use this method to modify its state, preventing the value from being consumed again.

Returns `True` if the channel was updated, `False` otherwise.

### `NamedBarrierValue.copy(self) -> Self`

Return a copy of the channel.

### `NamedBarrierValue.from_checkpoint(self, checkpoint: set[~Value]) -> Self`

Return a new identical channel, optionally initialized from a checkpoint.

If the checkpoint contains complex data structures, they should be copied.

### `NamedBarrierValue.get(self) -> ~Value`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `NamedBarrierValue.is_available(self) -> bool`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `NamedBarrierValue.update(self, values: collections.abc.Sequence[~Value]) -> bool`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.

## class `NamedBarrierValueAfterFinish(typ: type[~Value], names: set[~Value]) -> None` (bases: BaseChannel)

A channel that waits until all named values are received before making the value ready to be made available. It is only made available after finish() is called.

### property `NamedBarrierValueAfterFinish.UpdateType`

The type of the update received by the channel.

### property `NamedBarrierValueAfterFinish.ValueType`

The type of the value stored in the channel.

### `NamedBarrierValueAfterFinish.__init__(self, typ: type[~Value], names: set[~Value]) -> None`

Initialize self.  See help(type(self)) for accurate signature.

### `NamedBarrierValueAfterFinish.checkpoint(self) -> tuple[set[~Value], bool]`

Return a serializable representation of the channel's current state.

Raises `EmptyChannelError` if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `NamedBarrierValueAfterFinish.consume(self) -> bool`

Notify the channel that a subscribed task ran.

By default, no-op.

A channel can use this method to modify its state, preventing the value from being consumed again.

Returns `True` if the channel was updated, `False` otherwise.

### `NamedBarrierValueAfterFinish.copy(self) -> Self`

Return a copy of the channel.

### `NamedBarrierValueAfterFinish.finish(self) -> bool`

Notify the channel that the Pregel run is finishing.

By default, no-op.

A channel can use this method to modify its state, preventing finish.

Returns `True` if the channel was updated, `False` otherwise.

### `NamedBarrierValueAfterFinish.from_checkpoint(self, checkpoint: tuple[set[~Value], bool]) -> Self`

Return a new identical channel, optionally initialized from a checkpoint.

If the checkpoint contains complex data structures, they should be copied.

### `NamedBarrierValueAfterFinish.get(self) -> ~Value`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `NamedBarrierValueAfterFinish.is_available(self) -> bool`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `NamedBarrierValueAfterFinish.update(self, values: collections.abc.Sequence[~Value]) -> bool`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.

## class `Topic(typ: 'type[Value]', accumulate: 'bool' = False) -> 'None'` (bases: BaseChannel)

A configurable PubSub Topic.

Args:
    typ: The type of the value stored in the channel.
    accumulate: Whether to accumulate values across steps. If `False`, the channel will be emptied after each step.

### property `Topic.UpdateType`

The type of the update received by the channel.

### property `Topic.ValueType`

The type of the value stored in the channel.

### `Topic.__init__(self, typ: 'type[Value]', accumulate: 'bool' = False) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `Topic.checkpoint(self) -> 'list[Value]'`

Return a serializable representation of the channel's current state.

Raises `EmptyChannelError` if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `Topic.copy(self) -> 'Self'`

Return a copy of the channel.

### `Topic.from_checkpoint(self, checkpoint: 'list[Value]') -> 'Self'`

Return a new identical channel, optionally initialized from a checkpoint.

If the checkpoint contains complex data structures, they should be copied.

### `Topic.get(self) -> 'Sequence[Value]'`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `Topic.is_available(self) -> 'bool'`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `Topic.update(self, values: 'Sequence[Value | list[Value]]') -> 'bool'`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.

## class `UntrackedValue(typ: 'type[Value]', guard: 'bool' = True) -> 'None'` (bases: BaseChannel)

Stores the last value received, never checkpointed.

### property `UntrackedValue.UpdateType`

The type of the update received by the channel.

### property `UntrackedValue.ValueType`

The type of the value stored in the channel.

### `UntrackedValue.__init__(self, typ: 'type[Value]', guard: 'bool' = True) -> 'None'`

Initialize self.  See help(type(self)) for accurate signature.

### `UntrackedValue.checkpoint(self) -> 'Value | Any'`

Return a serializable representation of the channel's current state.

Raises `EmptyChannelError` if the channel is empty (never updated yet),
or doesn't support checkpoints.

### `UntrackedValue.copy(self) -> 'Self'`

Return a copy of the channel.

### `UntrackedValue.from_checkpoint(self, checkpoint: 'Value') -> 'Self'`

Return a new identical channel, optionally initialized from a checkpoint.

If the checkpoint contains complex data structures, they should be copied.

### `UntrackedValue.get(self) -> 'Value'`

Return the current value of the channel.

Raises `EmptyChannelError` if the channel is empty (never updated yet).

### `UntrackedValue.is_available(self) -> 'bool'`

Return `True` if the channel is available (not empty), `False` otherwise.

Subclasses should override this method to provide a more efficient
implementation than calling `get()` and catching `EmptyChannelError`.

### `UntrackedValue.update(self, values: 'Sequence[Value]') -> 'bool'`

Update the channel's value with the given sequence of updates.
The order of the updates in the sequence is arbitrary.
This method is called by Pregel for all channels at the end of each step.

If there are no updates, it is called with an empty sequence.

Raises `InvalidUpdateError` if the sequence of updates is invalid.

Returns `True` if the channel was updated, `False` otherwise.
