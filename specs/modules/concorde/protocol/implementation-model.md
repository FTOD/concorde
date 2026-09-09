```concorde-document
{
  "id": "document.specs.modules.concorde.protocol.implementation-model",
  "targets": [
    "module.protocol"
  ],
  "main_visible": true
}
```

# Implementation model

An Implementation Spec describes a concrete realization and directly binds its implementation
files. One authoritative Spec may cover several files; several Modules may reuse that same Spec.
A file has one Implementation Spec owner. Reuse neither merges Module identities nor changes their
structural parents. A Module can have its own coordination code as well as private submodules.

Only code-writing agents receive Implementation Specs, in addition to the selected Module's full
contract. They may maintain bound implementation documents and files without changing Module
contracts or registry identity. Non-code agents, including planners, determine work from Module
Specs alone. Code review checks authorized code against the Module contract in a separate invocation.

The Framework derives Implementation-to-Module usage and file-to-Implementation ownership indexes.
After shared code, Spec or binding changes, each affected Module's contract is checked separately.
Checks and reviews identify their Module and input revision. A later shared change invalidates
all affected evidence; a caller's completion does not establish compatibility for another user.
