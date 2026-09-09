---
audience: shared
---

# Implementation Spec

An Implementation Spec binds a nonempty explicit set of implementation files to one authoritative
contract. Describe their responsibilities, callable interfaces, internal dependencies, constraints
and verification. Each file has exactly one Implementation Spec owner. Multiple Modules may reuse
this same binding, and a Module may use several bindings. File paths never establish Module parentage.

Only the code-writing phase receives this Spec in addition to the selected Module's complete
contract. The Implementation Spec explains how code realizes that contract; missing observable
behavior remains a Module Spec gap. Shared changes require independent checks of all using Module
contracts. Reverse relationships identify impact, not permission to read or change other Module Specs.
