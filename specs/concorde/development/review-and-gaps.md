# Attributed Issue blockers and host history

A problem is recorded once as an Issue, through the host reporting service. Its reporter classifies
it as bug, gap or limitation and supplies evidence within its admitted context. A missing necessary
contract is gap/missing-contract; conflicting contracts and implementation/Spec mismatches have
their respective gap subtypes. Classification alone does not stop a worker or start a repair.

Stage results carry `blockers`: an immutable Issue receipt and a task-local blocked_step. A worker
can report several nonblocking problems and still complete its work; completed/sufficient results
cannot simultaneously claim blockers. Necessary missing contracts use spec_incomplete, other
blocking contradictions can use conflicting, and execution failures remain failed. Review owns
[its independent judgments](../review/review.md), which reference Issues with severity and
affected_task rather than repeating problem text in findings and gaps.

The host retains candidate `issue_blockers` keyed by change, accepted work scope, Module, phase and Issue identity.
Task text is an observation label, never the problem identity or join key. Root and registered
component/review intents select stable candidate scopes; unrelated standalone work gets its own
scope and cannot block or clear the accepted candidate task. Each relation keeps its exact
report reference, phase input revision, observed contexts and source-ownership/inclusion evidence.
Coordinators forward those references rather than creating another problem or copying it under a
new owner. Replanning cannot strand a dependency solely because its task wording changed.

An unchanged necessary-contract dependency waits for repair. Fresh successful phase assessment
can release the phase's earlier relations after the relevant inputs change; review evidence uses
its independently bound review input identity. Missing original review identity is never inferred
from a later mutable review record. Ordinary code-review defect feedback follows the bounded
repair/review loop rather than the unchanged-contract wait rule. A completed fresh code review can
release such a dependency even when it corrects an earlier judgment without further code changes.
Failed, incomplete and unrelated assessments cannot erase unresolved dependencies. Successful Spec
authoring can release its own phase's dependencies; other affected phases still need reassessment.

Releasing a relation means the current work no longer depends on that problem. It does not close
its Issue, imply delivery or erase history. A workaround can therefore permit work to continue
while the original problem remains open. Issue disposition belongs to an explicitly authorized
solving decision with evidence. Neither an open Issue elsewhere in the project nor an advisory
report is a blanket gate on readiness.

Target-bound snapshots expose only their Module's blocker references, never another Module's
problem text. Discovery may observe aggregate bookkeeping identities but receives no implicit Issue
file grant. A reporter's known provider owner remains distinct from the consumer task and context
that encountered the problem. Fixing that provider requires its own authoring or implementation
boundary. No problem record permits reading outside the admitted context.

Reports are acknowledged during execution and survive cancellation, timeout or invalid final
output. These observations do not establish review coverage or stage success. Description-only
previews launch no reporter. Query workers may explicitly report an Issue, but have no code/Spec
write authority. The former two-step gap-history-to-Reflection capture path is removed.

Review inputs remain bound to Spec, code, task/focus/constraints, configuration, worker instructions,
Protocol/build binding, candidate identity and scoped patches. Changed relevant inputs invalidate
required evidence. A report received after preliminary checks changes deliverable metadata; the
ready node refreshes deterministic validation when the Issue collection changed, then rechecks all
ordinary completion gates. It never rewrites a review as passed because an Issue was closed.
