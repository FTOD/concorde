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

[Optional prose that explains the scenario, names the interface entity that triggers it, or
identifies unresolved facts.]

- req.[module].[name]: [One sentence that SHALL or SHALL NOT hold in this scenario.]
````

Write one scenario per situation: the successful path, each defined failure and each repeated or
concurrent invocation whose outcome the Module promises. Keep the scenario ID stable when moving
the fragment or changing its title. Naming the scenario does not trim the Module's complete
contract context: a query for the scenario selects every registered document of its Module,
including explicitly shared and less-visible members.
