```concorde-document
{
  "id": "document.development.query-and-routing",
  "targets": [
    "module.development"
  ],
  "main_visible": true
}
```
# Query and routing Agent Graph

`concorde-main` accepts a question or task with optional routing hints. Main starts with the entry
Module's complete collection, then explicitly expands other Module collections
when needed. It identifies the owning target from admitted responsibilities and selection conditions.
It never reads implementation files or searches code to fill missing Module semantics.

For a query, Python resolves each explicitly selected Module's complete Spec context: every
registered document, including its inline diagrams. The coordinator receives the original
source bodies directly and may reason across all selected Modules. Shared sources are included
once, with per-Module membership retained. Non-main documents remain complete members; references
to another Module do not implicitly select its context. Additional contexts require explicit
selection and deterministic host resolution. A capability that owns a mutation or lifecycle result
has one main route and preserves the task and constraints unchanged.

A necessary missing promise returns a Spec gap with its target, context identity and blocked
question. A prohibition, contradictory requirements or execution error remains distinguishable
from a gap. Query completion returns an answer and limitations without authoring project files.
The concrete Concorde project routing tables belong to each Module's registered routing document.

The query graph runs coordinator discovery and direct answering without reading workers or a
separate synthesis stage. Discovery requests are AI control feedback: admitted target references
or an explicit target hint can select another complete context; when the sources suffice, the
coordinator returns completed with its direct answer and no worker routes. A missing fact is
reported with its owning Module and current context identity rather than causing
unbounded context expansion. The loop records its configured limits and returns an explicit limit
outcome if additional discovery cannot be admitted. Human clarification creates a revised task or
context and starts fresh invocations under the Graph and Loop contract.
