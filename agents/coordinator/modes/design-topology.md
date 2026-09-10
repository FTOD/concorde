# Mode: design-topology

Read all source bodies in the discovery pool using each Module document_order and membership. Expand only explicitly identified Module targets when necessary; return a new typed expansion request, never continue a conversation.
For `design-topology`, expand every Module collection needed to understand the
requested system change. Then return `topology_proposed` with a complete candidate registry in
`topology_design`. Preserve unchanged registry fields exactly. Every added or changed target needs
a target-local `spec_task`; also include tasks for unchanged Module documents whose
routing view must change. Every added, removed or changed `uses` edge requires a
local task for the corresponding retained Module. That task states the exact participant target
ID, Module-local responsibility, selection condition and relied-upon promises so the private
Module author does not need registry access. Every added, removed or changed entry in a Module's
registry `files` needs a target-local Spec task for that Module, since its entity entry union must
equal the registry list entry for entry. An entry is an exact file or a directory prefix ending in
`/`; prefer the prefix when one Module alone owns a directory, keep a file that several Modules bind
as an exact entry in each of them, and never list a directory that contains a registered Spec
document. When several Modules bind the same file, whether exactly or through a covering directory,
task every listing Module before the change. Repair every existing invalid dependency declaration exposed by admitted Module Specs
in the same candidate. Any change to a document's target references requires a task for every
retained current or candidate reference. A changed shared document requires every candidate
referencing target author to return identical bytes. State migration constraints and observable
acceptance conditions. You may design Module identity, responsibility, relationships, document
membership and file ownership from admitted Module facts and user intent, but never invent Module
behavior or code facts. Do not include any Spec document body in the topology design. The host will
start private target authors only after explicit developer acceptance.
