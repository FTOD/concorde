---
audience: shared
---

# Module Spec

A Module defines a cohesive responsibility through its set of features and the interfaces used to
access them. Its architecture describes its internal domain: concepts, private submodules,
directed relationships, collaborations, rules and completion/failure behavior. Submodules follow
the same model, have one structural parent, and shared capabilities are independent siblings.

The registered collection, including its local module.md reading entry, must be self-contained.
Describe every relied-upon collaborator promise locally. A planner must determine contract-level
tasks without implementation files, Implementation Specs or another Module's remaining documents.
Features and usage interfaces have stable identities and include errors, effects and examples.
Architecture is Module design; file bindings belong to separately referenced Implementation Specs.
