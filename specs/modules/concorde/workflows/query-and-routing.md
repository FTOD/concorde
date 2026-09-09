```concorde-document
{
  "id": "document.workflow.query-and-routing",
  "targets": [
    "module.workflows"
  ],
  "main_visible": true
}
```

# Query and routing Agent Graph

`concorde-main` accepts a question or task with optional routing hints. Main starts with the entry
Module's complete collection, then explicitly expands other Module collections
when needed. It identifies the owning target from admitted responsibilities and selection conditions.
It never reads Implementation Specs or searches code to fill missing Module semantics.

For a query, the host resolves complete target contexts and starts fresh target readers. Main may
combine their typed results into an answer; private snapshots do not return through the coordinator.
A query may have several target readers. A capability that owns a mutation or lifecycle result has
one main route and preserves the task and constraints unchanged.

A necessary missing promise returns a Spec gap with its target, context identity and blocked
question. A prohibition, contradictory requirements or execution error remains distinguishable
from a gap. Query completion returns an answer and limitations without authoring project files.
The concrete Concorde project routing tables belong to each Module's registered routing document.

The Graph binds coordinator, reader and synthesis invocations separately. Discovery requests are AI
control feedback: admitted target references can select another discovery step; a complete routing
result advances to readers or synthesis. A missing fact waits for clarification rather than causing
unbounded context expansion. The loop records its configured limits and returns an explicit limit
outcome if additional discovery cannot be admitted. Human clarification creates a revised task or
context and starts fresh invocations under the Graph and Loop contract.
