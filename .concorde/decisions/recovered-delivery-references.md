# Decision log: recovered-delivery-references

Goal: A delivery that finds its work already delivered records in its run node a reference to the existing delivery commit and evidence bundle, of a kind distinct from the commit and bundle references a node creates
# recovered-delivery-references: brief (main agent, 2026-09-29)

The developer asked for this follow-up of task `tracing` (history:
`.concorde/history/tracing/decisions.md`, "A delivery that finds its work already delivered ...").
When `delivery` finds the workspace already delivered, it recovers
(`src/concorde/delivery/command.py`, `recovered: True`). Its run node then carries no
reference to that delivery commit or evidence bundle. The reason: the Tracing contract's `commit`
and `bundle` references mean something the node itself created. Only the output names the existing
commit.

## Goal
- A recovered delivery's run node references the existing delivery commit and its evidence bundle.
- Use reference kinds distinct from `commit` and `bundle`, which keep meaning "created by this node".
- Add the new kinds to contract.tracing's trace node references, with their semantics and a version
  increment (module.tracing), and produce them in Delivery (module.delivery).
- Cover the change with Spec text, scenarios and tests on both sides.

## Left to the session
The names of the reference kinds (for example one kind naming a commit plus its bundle, or
`found_commit` and `found_bundle`) and whether other producers that find existing work should use
them. Record the choice here.

# Task session (2026-09-29)

- **Reference kinds.** Two new relations, `found_commit` (a Git commit an earlier node created that
  this node found and reports) and `found_bundle` (an evidence bundle an earlier node committed that
  this node found, as `<commit>:<path>`), mirroring `commit` and `bundle`. Reason: a reader that
  follows `commit`/`bundle` finds the found counterpart by the same shape and target format, and a
  bundle reference keeps its own target (the bundle path lives in the commit's tree, not in its
  trailers alone). One combined kind would have needed a new target format.
- **Other producers.** Only Delivery produces `commit`/`bundle` references today (the merge node
  keeps its commit as metadata), and no other producer reports existing work as its outcome, so only
  Delivery produces the new kinds now. The contract defines them generally, for any node that
  reports as its outcome a commit or bundle an earlier node created.
- **Versions.** `contract.tracing.node` goes from version 1 to 2. The record's `schema_version`
  stays 1: the change only adds enum values, every existing version-1 record (current tasks and the
  history, which is never changed) still satisfies the contract, and bumping the constant would make
  every existing node invalid.
- **Spec coverage.** Tracing gets `req.tracing.created-or-found` and
  `scenario.tracing.created-or-found`; Delivery's recovery text, `scenario.delivery.recover` and
  `scenario.delivery.redeliver` say the run node references the found commit and bundle, and
  `scenario.delivery.recover-unverified` that it references none.
- **Verification.** `spec-validation` success with no findings, `build --check` no differences,
  full suite 796 passed / 4 skipped; `task-validation` ready; `delivery` ok as `e157810e`
  (`r-20260929T104756-delivery-36634ec2`). Delivering again (`r-20260929T105004-delivery-843f9763`)
  recovered that commit and its run node references it as `found_commit` and `found_bundle`, with
  no new commit.
- **Non-ok along the way (all repaired in the task).** `uvx ruff` could not write
  `~/.local/share/uv/tools` in the sandbox, so I ran it with `UV_TOOL_DIR` under `$TMPDIR`. The first
  `spec-validation` reported the new requirement's two SHALLs (`statement must contain SHALL or
  SHALL NOT exactly once`) and three unlinked terms; I reworded it to one SHALL and linked the terms.

## Closed: merged, 2026-09-29T10:50:51Z
