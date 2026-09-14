# `langgraph.store.base`

Base classes and types for persistent key-value stores.

Stores provide long-term memory that persists across threads and conversations.
Supports hierarchical namespaces, key-value storage, and optional vector search.

Core types:
    - `BaseStore`: Store interface with sync/async operations
    - `Item`: Stored key-value pairs with metadata
    - `Op`: Get/Put/Search/List operations

Public names: `BaseStore`, `Embeddings`, `GetOp`, `Item`, `ListNamespacesOp`, `MatchCondition`, `NamespaceMatchType`, `NamespacePath`, `Op`, `PutOp`, `SearchOp`, `ensure_embeddings`, `get_text_at_path`, `tokenize_path`

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

## class `Embeddings()` (bases: ABC)

Interface for embedding models.

This is an interface meant for implementing text embedding models.

Text embedding models are used to map text to a vector (a point in n-dimensional
space).

Texts that are similar will usually be mapped to points that are close to each
other in this space. The exact details of what's considered "similar" and how
"distance" is measured in this space are dependent on the specific embedding model.

This abstraction contains a method for embedding a list of documents and a method
for embedding a query text. The embedding of a query text is expected to be a single
vector, while the embedding of a list of documents is expected to be a list of
vectors.

Usually the query embedding is identical to the document embedding, but the
abstraction allows treating them independently.

In addition to the synchronous methods, this interface also provides asynchronous
versions of the methods.

By default, the asynchronous methods are implemented using the synchronous methods;
however, implementations may choose to override the asynchronous methods with
an async native implementation for performance reasons.

### `Embeddings.aembed_documents(self, texts: list[str]) -> list[list[float]]`

Asynchronous Embed search docs.

Args:
    texts: List of text to embed.

Returns:
    List of embeddings.

### `Embeddings.aembed_query(self, text: str) -> list[float]`

Asynchronous Embed query text.

Args:
    text: Text to embed.

Returns:
    Embedding.

### `Embeddings.embed_documents(self, texts: list[str]) -> list[list[float]]`

Embed search docs.

Args:
    texts: List of text to embed.

Returns:
    List of embeddings.

### `Embeddings.embed_query(self, text: str) -> list[float]`

Embed query text.

Args:
    text: Text to embed.

Returns:
    Embedding.

## class `GetOp(namespace: ForwardRef('tuple[str, ...]'), key: ForwardRef('str'), refresh_ttl: ForwardRef('bool') = True)` (bases: tuple)

Operation to retrieve a specific item by its namespace and key.

This operation allows precise retrieval of stored items using their full path
(namespace) and unique identifier (key) combination.

???+ example "Examples"

    Basic item retrieval:

    ```python
    GetOp(namespace=("users", "profiles"), key="user123")
    GetOp(namespace=("cache", "embeddings"), key="doc456")
    ```

## class `Item(*, value: 'dict[str, Any]', key: 'str', namespace: 'tuple[str, ...]', created_at: 'datetime', updated_at: 'datetime')`

Represents a stored item with metadata.

Args:
    value: The stored data as a dictionary. Keys are filterable.
    key: Unique identifier within the namespace.
    namespace: Hierarchical path defining the collection in which this document resides.
        Represented as a tuple of strings, allowing for nested categorization.
        For example: `("documents", 'user123')`
    created_at: Timestamp of item creation.
    updated_at: Timestamp of last update.

### `Item.__init__(self, *, value: 'dict[str, Any]', key: 'str', namespace: 'tuple[str, ...]', created_at: 'datetime', updated_at: 'datetime')`

Initialize self.  See help(type(self)) for accurate signature.

### `Item.dict(self) -> 'dict'`

## class `ListNamespacesOp(match_conditions: ForwardRef('tuple[MatchCondition, ...] | None') = None, max_depth: ForwardRef('int | None') = None, limit: ForwardRef('int') = 100, offset: ForwardRef('int') = 0)` (bases: tuple)

Operation to list and filter namespaces in the store.

This operation allows exploring the organization of data, finding specific
collections, and navigating the namespace hierarchy.

???+ example "Examples"

    List all namespaces under the `"documents"` path:

    ```python
    ListNamespacesOp(
        match_conditions=(MatchCondition(match_type="prefix", path=("documents",)),),
        max_depth=2
    )
    ```

    List all namespaces that end with `"v1"`:

    ```python
    ListNamespacesOp(
        match_conditions=(MatchCondition(match_type="suffix", path=("v1",)),),
        limit=50
    )
    ```

## class `MatchCondition(match_type: ForwardRef('NamespaceMatchType'), path: ForwardRef('NamespacePath'))` (bases: tuple)

Represents a pattern for matching namespaces in the store.

This class combines a match type (prefix or suffix) with a namespace path
pattern that can include wildcards to flexibly match different namespace
hierarchies.

???+ example "Examples"

    Prefix matching:

    ```python
    MatchCondition(match_type="prefix", path=("users", "profiles"))
    ```

    Suffix matching with wildcard:

    ```python
    MatchCondition(match_type="suffix", path=("cache", "*"))
    ```

    Simple suffix matching:

    ```python
    MatchCondition(match_type="suffix", path=("v1",))
    ```

## `NamespaceMatchType(*args, **kwargs)`

## `NamespacePath(*args, **kwargs)`

Built-in immutable sequence.

If no argument is given, the constructor returns an empty tuple.
If iterable is specified the tuple is initialized from iterable's items.

If the argument is a tuple, the return value is the same object.

## `Op`

Value of type `UnionType`: `langgraph.store.base.GetOp | langgraph.store.base.SearchOp | langgraph.store.base.PutOp | langgraph.store.base.ListNamespacesOp`

## class `PutOp(namespace: ForwardRef('tuple[str, ...]'), key: ForwardRef('str'), value: ForwardRef('dict[str, Any] | None'), index: ForwardRef('Literal[False] | list[str] | None') = None, ttl: ForwardRef('float | None') = None)` (bases: tuple)

Operation to store, update, or delete an item in the store.

This class represents a single operation to modify the store's contents,
whether adding new items, updating existing ones, or removing them.

## class `SearchOp(namespace_prefix: ForwardRef('tuple[str, ...]'), filter: ForwardRef('dict[str, Any] | None') = None, limit: ForwardRef('int') = 10, offset: ForwardRef('int') = 0, query: ForwardRef('str | None') = None, refresh_ttl: ForwardRef('bool') = True)` (bases: tuple)

Operation to search for items within a specified namespace hierarchy.

This operation supports both structured filtering and natural language search
within a given namespace prefix. It provides pagination through limit and offset
parameters.

!!! note

    Natural language search support depends on your store implementation.

???+ example "Examples"

    Search with filters and pagination:

    ```python
    SearchOp(
        namespace_prefix=("documents",),
        filter={"type": "report", "status": "active"},
        limit=5,
        offset=10
    )
    ```

    Natural language search:

    ```python
    SearchOp(
        namespace_prefix=("users", "content"),
        query="technical documentation about APIs",
        limit=20
    )
    ```

## `ensure_embeddings(embed: 'Embeddings | EmbeddingsFunc | AEmbeddingsFunc | str | None') -> 'Embeddings'`

Ensure that an embedding function conforms to LangChain's Embeddings interface.

This function wraps arbitrary embedding functions to make them compatible with
LangChain's Embeddings interface. It handles both synchronous and asynchronous
functions.

Args:
    embed: Either an existing Embeddings instance, or a function that converts
        text to embeddings. If the function is async, it will be used for both
        sync and async operations.

Returns:
    An Embeddings instance that wraps the provided function(s).

??? example "Examples"

    Wrap a synchronous embedding function:

    ```python
    def my_embed_fn(texts):
        return [[0.1, 0.2] for _ in texts]

    embeddings = ensure_embeddings(my_embed_fn)
    result = embeddings.embed_query("hello")  # Returns [0.1, 0.2]
    ```

    Wrap an asynchronous embedding function:

    ```python
    async def my_async_fn(texts):
        return [[0.1, 0.2] for _ in texts]

    embeddings = ensure_embeddings(my_async_fn)
    result = await embeddings.aembed_query("hello")  # Returns [0.1, 0.2]
    ```

    Initialize embeddings using a provider string:

    ```python
    # Requires langchain>=0.3.9 and langgraph-checkpoint>=2.0.11
    embeddings = ensure_embeddings("openai:text-embedding-3-small")
    result = embeddings.embed_query("hello")
    ```

## `get_text_at_path(obj: 'Any', path: 'str | list[str]') -> 'list[str]'`

Extract text from an object using a path expression or pre-tokenized path.

Args:
    obj: The object to extract text from
    path: Either a path string or pre-tokenized path list.

!!! info "Path types handled"
    - Simple paths: "field1.field2"
    - Array indexing: "[0]", "[*]", "[-1]"
    - Wildcards: "*"
    - Multi-field selection: "{field1,field2}"
    - Nested paths in multi-field: "{field1,nested.field2}"

## `tokenize_path(path: 'str') -> 'list[str]'`

Tokenize a path into components.

!!! info "Types handled"
    - Simple paths: "field1.field2"
    - Array indexing: "[0]", "[*]", "[-1]"
    - Wildcards: "*"
    - Multi-field selection: "{field1,field2}"
