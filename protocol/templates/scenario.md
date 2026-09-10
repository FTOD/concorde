# Scenario fragment

Use this fragment within a Module's registered collection to describe one usage scenario. A
scenario belongs to the Module that solely owns its defining document; it is not an independent
Spec kind. If the fragment occupies a separate physical document, add the required
`concorde-document` block with that single Module as its target and register the document in the
Module's collection. The [required format](../format.md) still applies.

````markdown
### scenario.[module].[name] — [Scenario title]

- GIVEN [the precondition or state of the world]
- AND [a further precondition]
- WHEN [the trigger: what an actor or collaborator does]
- THEN [the observable outcome this Module promises]
- AND [a further outcome]
- BUT [an outcome that explicitly does not happen]

[Optional prose that explains the scenario, names the interface entity that triggers it, states a
limit or invariant that must hold in this situation, or identifies unresolved facts.]
````

Write one scenario per situation: the successful path, each defined failure and each repeated or
concurrent invocation whose outcome the Module promises. Everything the situation guarantees goes
into its steps or its prose; a promise that holds across situations is a Module requirement and
is defined in the Requirements part instead. Keep the scenario ID stable when moving the fragment
or changing its title; the ID is also the anchor by which links and tests refer to the scenario.
Naming the scenario does not trim the Module's complete contract context: a query for the scenario
selects every registered document of its Module, including explicitly shared and less-visible
members.
