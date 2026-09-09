```concorde-document
{
  "id": "document.specs.modules.concorde.protocol.module-model",
  "targets": [
    "module.protocol"
  ],
  "main_visible": true
}
```

# Module model

A Module provides a set of features through explicit usage interfaces: functions, APIs, commands,
files, protocols, events or other described exchanges. Its architecture is its internal domain:
relevant concepts, private submodules, responsibilities, relationships and operating behavior.
The same definition applies recursively. Each Module has at most one structural parent, without
composition cycles. When A and B share C, all three are siblings; uses does not duplicate ownership.

The complete Module Spec must explain the behavior and tasks without another Module's Spec,
implementation files or Implementation Specs. Planners and task authors use this collection alone.
A missing required promise is a gap in this Module contract, not permission to infer it from code.
Public signatures and usage examples are interface contracts and belong in the Module Spec.
