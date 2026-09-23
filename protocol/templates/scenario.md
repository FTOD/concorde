# Scenario fragment

A scenario belongs to the Module owning its defining document. It may describe boundary use or an
internal verification situation. It is not a separate Spec kind, document owner or context filter.

Define it only in an `implementation` document, never in `module.md` or a `module`-role topic.
Register the reading path and write its paired metadata with `schema_version: 3`, the owner's
identity and `document.role: implementation`. The [required format](../format.md) applies.

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

Write separate scenarios for situations whose successful, failed, repeated or concurrent outcomes
differ. Put a situation's guarantees in its own steps or explanation; define a Module-wide
obligation once as a requirement and link to it.

Identities stay stable across title and path changes. A test names the scenario identity **in the
test source**; reading content never lists verifying tests. Publication exposes the identity as an
anchor.

Querying a scenario selects its owner's entire context, including both members of every owned and
selected document. It never trims to this fragment, and never selects the consumer that happened to
read it.
