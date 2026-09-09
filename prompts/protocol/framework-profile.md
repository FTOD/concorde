---
audience: shared
---

## Concorde Framework execution profile

### P5. One complete Module context per bounded task

A bounded invocation selects one Module and freezes its complete document collection, task,
constraints, phase, Protocol and role instructions. Feature/interface focus does not trim that
collection. Planner and task-author inputs contain no Implementation Specs or source locators.
A global coordinator may discover explicitly admitted Module contracts for routing; each selected
worker is a fresh invocation with only its own complete Module context. Routing metadata and typed
worker results are explicit inputs, not permission to inspect implementation. Coordinator discovery
never loads Implementation Specs. Source-code phases use the selected Module's explicit file bindings.

Context identities cover document membership and bytes, Protocol and instructions, declared stage
artifacts and lifecycle identity. Code-writing context identities additionally cover the referenced
Implementation Specs, file bindings and their current file digests. A changed input requires a new
snapshot. Implementation-only changes do not add implementation knowledge to a planner.

### P6. Gaps and review are tied to the affected contract

Missing required behavior is a Module Spec gap. Name the missing promise, blocked step, Module and
snapshot; continue only independent work. Implementation source cannot resolve that gap implicitly.
A failed execution, an explicit prohibition and a missing runtime value with defined failure
behavior are distinct from an unspecified contract.

Spec review uses Module Specs. Code review uses the same Module contracts and authorized code in a
fresh read-only invocation. A review records its exact inputs, coverage, findings and completion.
Changed relevant inputs invalidate it. Skipped, failed, incomplete and successful reviews remain
distinct. Shared implementation changes require checks for all using Modules, with separate Module
contexts and explicit per-consumer evidence. No passing structural check proves semantic completeness.

### P7. Execution authority is explicit

The host binds each normal Framework invocation to declared context and file permissions. Only
implementation invocations receive Implementation Spec bodies; only code-writing invocations may
change bound source. Code review and deterministic checks have separately declared read authority.
The registry's reverse index never grants a writer another Module's Spec or unrelated code.
Unsupported enforcement fails closed. An outer developer-authorized maintenance session may read
and modify the project directly; its explicit authorization does not silently widen normal worker
permissions or become a project business contract.

Agent instructions, Skills, schemas and rule assets are deterministic projections of authored
sources. Generated output is not edited as source. Builds distribute Module and Implementation
kind definitions and the accepted Protocol binding. Configuration, installation and publication
must agree on that binding. Runtime Agent responsibility files are authored implementation assets,
not another category of project Spec.

### P8. Structure and bindings change together

Topology changes reconcile Module parentage, uses, features, interfaces, document memberships and
Implementation references as one consistent proposal. A shared file has one Implementation Spec
owner. The reverse index identifies every affected Module before a shared implementation change.
A new or changed Module's author sees only that Module's contract collection; code-writing work
receives the separately bound Implementation Specs. Other Module contracts are reviewed separately.
An atomic application checks source versions and preserves prior bytes if applying the proposed
structure fails. Human acceptance is explicit where the selected workflow requires it; direct
maintenance follows the developer's explicit task authorization.

### P9. Candidate and delivery evidence belong to a worktree

One candidate worktree holds one change, including its component progress, gaps and implementation
impact evidence. Partial work is inspectable and resumable, not represented as completed delivery.
Validation and review evidence bind to actual candidate inputs. Shared implementation changes
invalidate evidence for every using Module even if only one Module initiated the change.
Delivery preserves unrelated local changes, checks the actual integration and records incomplete
cleanup separately from a completed merge. No component independently delivers its enclosing change.

### P10. Explicit session handoffs

When the selected workflow requires a new outer session, start it in the intended worktree with
fresh context and that worktree's instructions. Changing cwd does not erase prior cognitive inputs.
Supply a self-contained prompt in the developer's language with the absolute directory, branch,
task, authorizations, completed and remaining work, artifacts, checks and next steps. Start the
session automatically when isolation can be established; otherwise provide a complete copyable
prompt. A direct maintenance task explicitly authorized by the developer does not require a
workflow handoff solely because it updates the Framework's own instructions.
