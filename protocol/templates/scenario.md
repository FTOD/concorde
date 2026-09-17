# Scenario fragment

A scenario belongs to the Module owning its defining document unit. It can describe boundary use or
an internal verification situation. It is not another Spec kind, document owner or context filter.
Define it only in an implementation-role companion, never in `module.md` or a module-role topic.
Register its Markdown reading path and author schema-2 metadata with the owner's identity,
`document.role: implementation` and explicit declaration arrays. No enclosing usage/architecture parts
are required. The [required format](../format.md) applies.

````markdown
### scenario.example.situation — [Scenario title]

- GIVEN [the precondition or state]
- AND [another precondition]
- WHEN [the trigger]
- THEN [the promised outcome]
- AND [another outcome]
- BUT [an outcome that explicitly must not occur]

[Explain relevant limits, the triggering interface or unresolved facts in ordinary prose.]
````

Write separate scenarios for situations with distinct successful, failed, repeated or concurrent
outcomes. Put a situation's guarantees in its steps or explanation; define Module-wide obligations
once as requirements and link to them. Keep identities stable across title or path changes. Tests
name the scenario identity, and publication exposes it as an anchor. Querying the scenario selects
its owner's entire complete context, including both source members of every explicitly included
unit, not just this fragment or the human-readable subset.
