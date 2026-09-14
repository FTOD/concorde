# `langgraph.config`

Public names: `Any`, `BaseStore`, `CONF`, `CONFIG_KEY_RUNTIME`, `RunnableConfig`, `StreamWriter`, `asyncio`, `get_config`, `get_store`, `get_stream_writer`, `sys`, `var_child_runnable_config`

## class `Any(*args, **kwargs)`

Special type indicating an unconstrained type.

- Any is compatible with every type.
- Any assumed to have all methods.
- All values assumed to be instances of Any.

Note that all the above statements are true from the point of view of
static type checkers. At runtime, Any should not be used with instance
checks.

## class `BaseStore()` (bases: ABC)

Abstract base class for persistent key-value stores.

Stores enable persistence and memory that can be shared across threads,
scoped to user IDs, assistant IDs, or other arbitrary namespaces.
Some implementations may support semantic search capabilities through
an optional `index` configuration.

Note:
    Semantic search capabilities vary by implementation and are typically
    disabled by default. Stores that support this feature can be configured
    by providing an `index` configuration at creation time. Without this
    configuration, semantic search is disabled and any `index` arguments
    to storage operations will have no effect.

    Similarly, TTL (time-to-live) support is disabled by default.
    Subclasses must explicitly set `supports_ttl = True` to enable this feature.

### `BaseStore.abatch(self, ops: 'Iterable[Op]') -> 'list[Result]'`

Execute multiple operations asynchronously in a single batch.

Args:
    ops: An iterable of operations to execute.

Returns:
    A list of results, where each result corresponds to an operation in the input.
    The order of results matches the order of input operations.

### `BaseStore.adelete(self, namespace: 'tuple[str, ...]', key: 'str') -> 'None'`

Asynchronously delete an item.

Args:
    namespace: Hierarchical path for the item.
    key: Unique identifier within the namespace.

### `BaseStore.aget(self, namespace: 'tuple[str, ...]', key: 'str', *, refresh_ttl: 'bool | None' = None) -> 'Item | None'`

Asynchronously retrieve a single item.

Args:
    namespace: Hierarchical path for the item.
    key: Unique identifier within the namespace.

Returns:
    The retrieved item or `None` if not found.

### `BaseStore.alist_namespaces(self, *, prefix: 'NamespacePath | None' = None, suffix: 'NamespacePath | None' = None, max_depth: 'int | None' = None, limit: 'int' = 100, offset: 'int' = 0) -> 'list[tuple[str, ...]]'`

List and filter namespaces in the store asynchronously.

Used to explore the organization of data,
find specific collections, or navigate the namespace hierarchy.

Args:
    prefix: Filter namespaces that start with this path.
    suffix: Filter namespaces that end with this path.
    max_depth: Return namespaces up to this depth in the hierarchy.
        Namespaces deeper than this level will be truncated to this depth.
    limit: Maximum number of namespaces to return.
    offset: Number of namespaces to skip for pagination.

Returns:
    A list of namespace tuples that match the criteria. Each tuple represents a
        full namespace path up to `max_depth`.

???+ example "Examples"

    Setting `max_depth=3` with existing namespaces:
    ```python
    # Given the following namespaces:
    # ("a", "b", "c")
    # ("a", "b", "d", "e")
    # ("a", "b", "d", "i")
    # ("a", "b", "f")
    # ("a", "c", "f")

    await store.alist_namespaces(prefix=("a", "b"), max_depth=3)
    # Returns: [("a", "b", "c"), ("a", "b", "d"), ("a", "b", "f")]
    ```

### `BaseStore.aput(self, namespace: 'tuple[str, ...]', key: 'str', value: 'dict[str, Any]', index: 'Literal[False] | list[str] | None' = None, *, ttl: 'float | None | NotProvided' = NOT_GIVEN) -> 'None'`

Asynchronously store or update an item in the store.

Args:
    namespace: Hierarchical path for the item, represented as a tuple of strings.
        Example: `("documents", "user123")`
    key: Unique identifier within the namespace. Together with namespace forms
        the complete path to the item.
    value: Dictionary containing the item's data. Must contain string keys
        and JSON-serializable values.
    index: Controls how the item's fields are indexed for search:

        - None (default): Use `fields` you configured when creating the store (if any)
            If you do not initialize the store with indexing capabilities,
            the `index` parameter will be ignored
        - False: Disable indexing for this item
        - `list[str]`: List of field paths to index, supporting:
            - Nested fields: `"metadata.title"`
            - Array access: `"chapters[*].content"` (each indexed separately)
            - Specific indices: `"authors[0].name"`
    ttl: Time to live in minutes. Support for this argument depends on your store adapter.
        If specified, the item will expire after this many minutes from when it was last accessed.
        None means no expiration. Expired runs will be deleted opportunistically.
        By default, the expiration timer refreshes on both read operations (get/search)
        and write operations (put/update), whenever the item is included in the operation.

Note:
    Indexing support depends on your store implementation.
    If you do not initialize the store with indexing capabilities,
    the `index` parameter will be ignored.

    Similarly, TTL support depends on the specific store implementation.
    Some implementations may not support expiration of items.

???+ example "Examples"

    Store item. Indexing depends on how you configure the store:

    ```python
    await store.aput(("docs",), "report", {"memory": "Will likes ai"})
    ```

    Do not index item for semantic search. Still accessible through `get()`
    and `search()` operations but won't have a vector representation.

    ```python
    await store.aput(("docs",), "report", {"memory": "Will likes ai"}, index=False)
    ```

    Index specific fields for search (if store configured to index items):

    ```python
    await store.aput(
        ("docs",),
        "report",
        {
            "memory": "Will likes ai",
            "context": [{"content": "..."}, {"content": "..."}]
        },
        index=["memory", "context[*].content"]
    )
    ```

### `BaseStore.asearch(self, namespace_prefix: 'tuple[str, ...]', /, *, query: 'str | None' = None, filter: 'dict[str, Any] | None' = None, limit: 'int' = 10, offset: 'int' = 0, refresh_ttl: 'bool | None' = None) -> 'list[SearchItem]'`

Asynchronously search for items within a namespace prefix.

Args:
    namespace_prefix: Hierarchical path prefix to search within.
    query: Optional query for natural language search.
    filter: Key-value pairs to filter results.
    limit: Maximum number of items to return.
    offset: Number of items to skip before returning results.
    refresh_ttl: Whether to refresh TTLs for the returned items.
        If `None`, uses the store's `TTLConfig.refresh_default` setting.
        If `TTLConfig` is not provided or no TTL is specified, this argument is ignored.

Returns:
    List of items matching the search criteria.

???+ example "Examples"

    Basic filtering:

    ```python
    # Search for documents with specific metadata
    results = await store.asearch(
        ("docs",),
        filter={"type": "article", "status": "published"}
    )
    ```

    Natural language search (requires vector store implementation):

    ```python
    # Initialize store with embedding configuration
    store = YourStore( # e.g., InMemoryStore, AsyncPostgresStore
        index={
            "dims": 1536,  # embedding dimensions
            "embed": your_embedding_function,  # function to create embeddings
            "fields": ["text"]  # fields to embed
        }
    )

    # Search for semantically similar documents

    results = await store.asearch(
        ("docs",),
        query="machine learning applications in healthcare",
        filter={"type": "research_paper"},
        limit=5
    )
    ```

    !!! note

        Natural language search support depends on your store implementation
        and requires proper embedding configuration.

### `BaseStore.batch(self, ops: 'Iterable[Op]') -> 'list[Result]'`

Execute multiple operations synchronously in a single batch.

Args:
    ops: An iterable of operations to execute.

Returns:
    A list of results, where each result corresponds to an operation in the input.
    The order of results matches the order of input operations.

### `BaseStore.delete(self, namespace: 'tuple[str, ...]', key: 'str') -> 'None'`

Delete an item.

Args:
    namespace: Hierarchical path for the item.
    key: Unique identifier within the namespace.

### `BaseStore.get(self, namespace: 'tuple[str, ...]', key: 'str', *, refresh_ttl: 'bool | None' = None) -> 'Item | None'`

Retrieve a single item.

Args:
    namespace: Hierarchical path for the item.
    key: Unique identifier within the namespace.
    refresh_ttl: Whether to refresh TTLs for the returned item.
        If `None`, uses the store's default `refresh_ttl` setting.
        If no TTL is specified, this argument is ignored.

Returns:
    The retrieved item or `None` if not found.

### `BaseStore.list_namespaces(self, *, prefix: 'NamespacePath | None' = None, suffix: 'NamespacePath | None' = None, max_depth: 'int | None' = None, limit: 'int' = 100, offset: 'int' = 0) -> 'list[tuple[str, ...]]'`

List and filter namespaces in the store.

Used to explore the organization of data,
find specific collections, or navigate the namespace hierarchy.

Args:
    prefix: Filter namespaces that start with this path.
    suffix: Filter namespaces that end with this path.
    max_depth: Return namespaces up to this depth in the hierarchy.
        Namespaces deeper than this level will be truncated.
    limit: Maximum number of namespaces to return.
    offset: Number of namespaces to skip for pagination.

Returns:
    A list of namespace tuples that match the criteria. Each tuple represents a
        full namespace path up to `max_depth`.

???+ example "Examples":

    Setting `max_depth=3`. Given the namespaces:

    ```python
    # Example if you have the following namespaces:
    # ("a", "b", "c")
    # ("a", "b", "d", "e")
    # ("a", "b", "d", "i")
    # ("a", "b", "f")
    # ("a", "c", "f")
    store.list_namespaces(prefix=("a", "b"), max_depth=3)
    # [("a", "b", "c"), ("a", "b", "d"), ("a", "b", "f")]
    ```

### `BaseStore.put(self, namespace: 'tuple[str, ...]', key: 'str', value: 'dict[str, Any]', index: 'Literal[False] | list[str] | None' = None, *, ttl: 'float | None | NotProvided' = NOT_GIVEN) -> 'None'`

Store or update an item in the store.

Args:
    namespace: Hierarchical path for the item, represented as a tuple of strings.
        Example: `("documents", "user123")`
    key: Unique identifier within the namespace. Together with namespace forms
        the complete path to the item.
    value: Dictionary containing the item's data. Must contain string keys
        and JSON-serializable values.
    index: Controls how the item's fields are indexed for search:

        - None (default): Use `fields` you configured when creating the store (if any)
            If you do not initialize the store with indexing capabilities,
            the `index` parameter will be ignored
        - False: Disable indexing for this item
        - `list[str]`: List of field paths to index, supporting:
            - Nested fields: `"metadata.title"`
            - Array access: `"chapters[*].content"` (each indexed separately)
            - Specific indices: `"authors[0].name"`
    ttl: Time to live in minutes. Support for this argument depends on your store adapter.
        If specified, the item will expire after this many minutes from when it was last accessed.
        None means no expiration. Expired runs will be deleted opportunistically.
        By default, the expiration timer refreshes on both read operations (get/search)
        and write operations (put/update), whenever the item is included in the operation.

Note:
    Indexing support depends on your store implementation.
    If you do not initialize the store with indexing capabilities,
    the `index` parameter will be ignored.

    Similarly, TTL support depends on the specific store implementation.
    Some implementations may not support expiration of items.

???+ example "Examples"

    Store item. Indexing depends on how you configure the store:

    ```python
    store.put(("docs",), "report", {"memory": "Will likes ai"})
    ```

    Do not index item for semantic search. Still accessible through `get()`
    and `search()` operations but won't have a vector representation.

    ```python
    store.put(("docs",), "report", {"memory": "Will likes ai"}, index=False)
    ```

    Index specific fields for search:

    ```python
    store.put(("docs",), "report", {"memory": "Will likes ai"}, index=["memory"])
    ```

### `BaseStore.search(self, namespace_prefix: 'tuple[str, ...]', /, *, query: 'str | None' = None, filter: 'dict[str, Any] | None' = None, limit: 'int' = 10, offset: 'int' = 0, refresh_ttl: 'bool | None' = None) -> 'list[SearchItem]'`

Search for items within a namespace prefix.

Args:
    namespace_prefix: Hierarchical path prefix to search within.
    query: Optional query for natural language search.
    filter: Key-value pairs to filter results.
    limit: Maximum number of items to return.
    offset: Number of items to skip before returning results.
    refresh_ttl: Whether to refresh TTLs for the returned items.
        If no TTL is specified, this argument is ignored.

Returns:
    List of items matching the search criteria.

???+ example "Examples"

    Basic filtering:

    ```python
    # Search for documents with specific metadata
    results = store.search(
        ("docs",),
        filter={"type": "article", "status": "published"}
    )
    ```

    Natural language search (requires vector store implementation):

    ```python
    # Initialize store with embedding configuration
    store = YourStore( # e.g., InMemoryStore, AsyncPostgresStore
        index={
            "dims": 1536,  # embedding dimensions
            "embed": your_embedding_function,  # function to create embeddings
            "fields": ["text"]  # fields to embed. Defaults to ["$"]
        }
    )

    # Search for semantically similar documents

    results = store.search(
        ("docs",),
        query="machine learning applications in healthcare",
        filter={"type": "research_paper"},
        limit=5
    )
    ```

    !!! note

        Natural language search support depends on your store implementation
        and requires proper embedding configuration.

## `CONF`

Value of type `str`: `'configurable'`

## `CONFIG_KEY_RUNTIME`

Value of type `str`: `'__pregel_runtime'`

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

## `StreamWriter(*args, **kwargs)`

## `get_config() -> langchain_core.runnables.config.RunnableConfig`

## `get_store() -> langgraph.store.base.BaseStore`

Access LangGraph store from inside a graph node or entrypoint task at runtime.

Can be called from inside any [`StateGraph`][langgraph.graph.StateGraph] node or
functional API [`task`][langgraph.func.task], as long as the `StateGraph` or the [`entrypoint`][langgraph.func.entrypoint]
was initialized with a store, e.g.:

```python
# with StateGraph
graph = (
    StateGraph(...)
    ...
    .compile(store=store)
)

# or with entrypoint
@entrypoint(store=store)
def workflow(inputs):
    ...
```

!!! warning "Async with Python < 3.11"

    If you are using Python < 3.11 and are running LangGraph asynchronously,
    `get_store()` won't work since it uses [`contextvar`](https://docs.python.org/3/library/contextvars.html) propagation (only available in [Python >= 3.11](https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task)).


Example: Using with `StateGraph`
    ```python
    from typing_extensions import TypedDict
    from langgraph.graph import StateGraph, START
    from langgraph.store.memory import InMemoryStore
    from langgraph.config import get_store

    store = InMemoryStore()
    store.put(("values",), "foo", {"bar": 2})


    class State(TypedDict):
        foo: int


    def my_node(state: State):
        my_store = get_store()
        stored_value = my_store.get(("values",), "foo").value["bar"]
        return {"foo": stored_value + 1}


    graph = (
        StateGraph(State)
        .add_node(my_node)
        .add_edge(START, "my_node")
        .compile(store=store)
    )

    graph.invoke({"foo": 1})
    ```

    ```pycon
    {"foo": 3}
    ```

Example: Using with functional API
    ```python
    from langgraph.func import entrypoint, task
    from langgraph.store.memory import InMemoryStore
    from langgraph.config import get_store

    store = InMemoryStore()
    store.put(("values",), "foo", {"bar": 2})


    @task
    def my_task(value: int):
        my_store = get_store()
        stored_value = my_store.get(("values",), "foo").value["bar"]
        return stored_value + 1


    @entrypoint(store=store)
    def workflow(value: int):
        return my_task(value).result()


    workflow.invoke(1)
    ```

    ```pycon
    3
    ```

## `get_stream_writer() -> collections.abc.Callable[[typing.Any], None]`

Access LangGraph [`StreamWriter`][langgraph.types.StreamWriter] from inside a graph node or entrypoint task at runtime.

Can be called from inside any [`StateGraph`][langgraph.graph.StateGraph] node or
functional API [`task`][langgraph.func.task].

!!! warning "Async with Python < 3.11"

    If you are using Python < 3.11 and are running LangGraph asynchronously,
    `get_stream_writer()` won't work since it uses [`contextvar`](https://docs.python.org/3/library/contextvars.html) propagation (only available in [Python >= 3.11](https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task)).

Example: Using with `StateGraph`
    ```python
    from typing_extensions import TypedDict
    from langgraph.graph import StateGraph, START
    from langgraph.config import get_stream_writer


    class State(TypedDict):
        foo: int


    def my_node(state: State):
        my_stream_writer = get_stream_writer()
        my_stream_writer({"custom_data": "Hello!"})
        return {"foo": state["foo"] + 1}


    graph = (
        StateGraph(State)
        .add_node(my_node)
        .add_edge(START, "my_node")
        .compile(store=store)
    )

    for chunk in graph.stream({"foo": 1}, stream_mode="custom"):
        print(chunk)
    ```

    ```pycon
    {"custom_data": "Hello!"}
    ```

Example: Using with functional API
    ```python
    from langgraph.func import entrypoint, task
    from langgraph.config import get_stream_writer


    @task
    def my_task(value: int):
        my_stream_writer = get_stream_writer()
        my_stream_writer({"custom_data": "Hello!"})
        return value + 1


    @entrypoint(store=store)
    def workflow(value: int):
        return my_task(value).result()


    for chunk in workflow.stream(1, stream_mode="custom"):
        print(chunk)
    ```

    ```pycon
    {"custom_data": "Hello!"}
    ```

## `var_child_runnable_config`

Value of type `ContextVar`: `<ContextVar name='child_runnable_config' default=None at 0x7d6b40b4de90>`
