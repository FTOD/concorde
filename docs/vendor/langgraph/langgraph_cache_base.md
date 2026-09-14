# `langgraph.cache.base`

Public names: `ABC`, `BaseCache`, `FullKey`, `Generic`, `JsonPlusSerializer`, `Mapping`, `Namespace`, `Sequence`, `SerializerProtocol`, `TypeVar`, `ValueT`, `abstractmethod`, `annotations`

## class `ABC()`

Helper class that provides a standard way to create an ABC using
inheritance.

## class `BaseCache(*, serde: 'SerializerProtocol | None' = None) -> 'None'` (bases: ABC, Generic)

Base class for a cache.

### `BaseCache.__init__(self, *, serde: 'SerializerProtocol | None' = None) -> 'None'`

Initialize the cache with a serializer.

### `BaseCache.aclear(self, namespaces: 'Sequence[Namespace] | None' = None) -> 'None'`

Asynchronously delete the cached values for the given namespaces.
If no namespaces are provided, clear all cached values.

### `BaseCache.aget(self, keys: 'Sequence[FullKey]') -> 'dict[FullKey, ValueT]'`

Asynchronously get the cached values for the given keys.

### `BaseCache.aset(self, pairs: 'Mapping[FullKey, tuple[ValueT, int | None]]') -> 'None'`

Asynchronously set the cached values for the given keys and TTLs.

### `BaseCache.clear(self, namespaces: 'Sequence[Namespace] | None' = None) -> 'None'`

Delete the cached values for the given namespaces.
If no namespaces are provided, clear all cached values.

### `BaseCache.get(self, keys: 'Sequence[FullKey]') -> 'dict[FullKey, ValueT]'`

Get the cached values for the given keys.

### `BaseCache.set(self, pairs: 'Mapping[FullKey, tuple[ValueT, int | None]]') -> 'None'`

Set the cached values for the given keys and TTLs.

## `FullKey(*args, **kwargs)`

Built-in immutable sequence.

If no argument is given, the constructor returns an empty tuple.
If iterable is specified the tuple is initialized from iterable's items.

If the argument is a tuple, the return value is the same object.

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

## `Namespace(*args, **kwargs)`

Built-in immutable sequence.

If no argument is given, the constructor returns an empty tuple.
If iterable is specified the tuple is initialized from iterable's items.

If the argument is a tuple, the return value is the same object.

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

## `ValueT`

Value of type `TypeVar`: `~ValueT`

## `abstractmethod(funcobj)`

A decorator indicating abstract methods.

Requires that the metaclass is ABCMeta or derived from it.  A
class that has a metaclass derived from ABCMeta cannot be
instantiated unless all of its abstract methods are overridden.
The abstract methods can be called using any of the normal
'super' call mechanisms.  abstractmethod() may be used to declare
abstract methods for properties and descriptors.

Usage:

    class C(metaclass=ABCMeta):
        @abstractmethod
        def my_abstract_method(self, arg1, arg2, argN):
            ...

## `annotations`

Value of type `_Feature`: `_Feature((3, 7, 0, 'beta', 1), None, 16777216)`
