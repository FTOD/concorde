---
name: concorde-main
description: "Global entry: answer questions, route work, and design or apply system topology from main-visible Domain and Service Specs."
capability: main
---

# concorde-main

This is Concorde's public main entry. It replaces the former ask capability. The internal coordinator
starts from the project's entry Domain or Service and may expand only registered Domain and Service
main-visible Target Spec and Shared Specs. Shared membership never expands another entity's remaining
documents. It understands every global kind definition but cannot directly expand a Module target or read
implementation code.

Action `ask` (the default when action is omitted) routes one or more fresh target readers and then
synthesizes only their typed results. Action `design-topology` returns a digest-bound architecture
proposal without changing files. Action `accept-topology` explicitly accepts that design, launches
private target-local Spec authors and stores the resulting exact application as a host artifact;
only its path and digest return to ambient cognition. After the developer reviews that artifact,
action `apply-topology` accepts it and atomically applies or rolls back the registry/document set.

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-main
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-main
Ask and design-topology requests require task and accept optional target_id/focus_id routing hints
and constraints. Accept-topology requires the exact topology_proposal returned by design. Apply-
topology requires only the exact application ArtifactRef returned by accept.
The hint never grants Spec access to the coordinator. The global development loop
(`concorde-dev-loop`) accepts the same task, with optional target_id, focus_id, constraints, and
change_id, and routes through main exactly like this capability's own ask action; its internal
stages are bound to one target by the loop and are never invoked directly.
@include prompts/workflow-host/init-request-and-no-flags.md

The coordinator expands main-visible Domain/Service documents only as needed and records the exact
Target Spec/Shared Specs membership and digests in every discovery identity. A Module may be selected
from visible responsibilities, but its remaining Spec is visible only to the fresh target reader.
Topology design receives exact registry metadata but does not expand Module targets. Target authors' complete output
is never returned through this capability; it stays in the ignored host application artifact. Report
Spec gaps or blocked execution as returned and do not work around the boundary. Non-implementation
agents never receive implementation code or raw test logs.

A topology proposal that adds, removes or changes a component's `participates_in` relationship must
also task every retained affected Domain to reconcile its local `concorde-participants` declaration.
The Domain task carries the exact ID, kind, local responsibility, selection condition and relied-upon
promises. Candidate overlay validation rejects a registry edge without that self-contained Domain
routing view.

Every physical Spec document declares stable ID, exact target references and main visibility.
Changing document references tasks every retained current/candidate target. Shared truth has no
unique owner: ordinary single-target authoring cannot change it, and topology preparation accepts a
replacement only when every candidate referencing target author returns identical exact bytes.


Every main invocation receives host-supplied workspace metadata. In the primary worktree it lists
all live linked worktrees and their basic change status, so ongoing work is visible without loading
other worktrees' Spec or implementation bodies. In a secondary worktree it identifies the current
candidate, its phase/status, and the primary worktree. The primary inventory is
`.concorde/worktrees.json`; secondary lifecycle state is `.concorde/worktree.json`.
A worktree is a mutable candidate until its exact version is verified and delivered. Do not treat
partial drafts as the accepted primary revision. Read-only awareness does not authorize cross-worktree
reads or a continuation of the same agent session in another checkout.

`concorde-deliver` may be requested from either the selected source or destination worktree.
Report the selected change_id and both participants; a third worktree cannot deliver that change.
The source is retained when it owns the active session or keep_worktree:true is requested.
