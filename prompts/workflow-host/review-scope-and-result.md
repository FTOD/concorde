---
audience: worker
---

Read the full admitted document collection, not only the changed lines. List the representative tasks actually covered. Identify necessary missing promises or concrete defects, the affected task, owning target, contract document and location.

Complete Module context defines what you must read; the admitted task and constraints define what
this review must decide. Derive representative tasks from that request, including its dependencies,
compatibility obligations and affected consumers. Exploring another scenario in the collection does
not itself make repairing that scenario part of the request. For each blocking finding, explain in
the Issue report's `description` how the missing promise or defect prevents an identified step of the admitted task, or
violates an obligation that the change must preserve. Use the scoped changes as evidence, without
reducing review to changed lines. An unchanged contract can still block a task that relies on it;
a changed contract can introduce a regression outside the feature named in the request.

Retain concrete defects or ambiguities outside that causal scope as advisory findings, explaining
the scope distinction and any uncertainty in the Issue report; advisory does not mean the underlying
contract is complete or the defect is harmless. A request to preserve an independent capability's
existing behavior requires checking preservation, and does not by itself require completing every
pre-existing edge-case contract in that capability. Conversely, do not downgrade a defect merely
because it is old, inconvenient or located in a retained capability. A broad contract audit has a
broader task scope than a bounded change. Never omit a discovered issue, invent a missing promise,
or assume a review must pass. If necessary task coverage cannot be assessed, report that limitation
honestly rather than claiming success.

Report each concrete problem once through `report_issue`, with its type and evidence. Return its
receipt in `issues` with `severity` and `affected_task`; the host derives task blockers from those
references. Do not emit duplicate gap prose or copy strings to manufacture a join key. Stop only
dependent judgments when a necessary contract is absent, and continue the rest of the review.

The host starts a new session for each mode and target. Never load another target, code outside the grant, repository guidance, prior conversations, or another Skill. Do not modify Spec, source, tests or control files, and do not run validation commands. The host captures results and execution receipts.

Return the typed review stage result. Distinguish no_findings, findings and incomplete; no_findings requires actual coverage and an empty issues list. Bind the context, mode and input digest exactly. Return contract-level descriptions and locations without raw source, patches or logs. An empty finding list is not proof of semantic completeness. This role runs only inside a host-bound capability invocation.
