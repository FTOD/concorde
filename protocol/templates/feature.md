# Feature fragment

Use this fragment within a Module's registered collection to describe one capability. A feature
belongs to its providing Module; it is not an independent Spec kind. If the fragment occupies a
separate physical document, add the required `concorde-document` block and register that document
in the Module's collection. The [required format](../format.md) still applies.

````markdown
### [feature-id] — [Feature title]

[Identify the observable capability and the conditions in which it applies.]

**Promises:** [State the guaranteed outcome and relevant constraints.]

**Failures:** [State defined failure and partial-outcome behavior.]

**Usage interfaces:** [Name the providing Module's interface IDs and where their complete
contracts are defined in this collection.]

**Local reliance:** [Explain any collaborator promises relevant to this capability; keep them
consistent with the Module's concorde-dependencies declarations.]

**Unresolved facts:** [Name any behavior that remains unspecified.]
````

Keep the feature ID stable when moving the fragment or changing its title. Update its defining
local document reference when its location changes. Naming the feature does not trim the Module's
complete contract context.

That context includes all of the Module's registered documents and declared authored diagram
sources, including explicitly shared and less-visible members. The fragment's defining document
locates the feature; it does not select a smaller file set.
