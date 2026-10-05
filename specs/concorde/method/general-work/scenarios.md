# General work scenarios

Concrete situations that show the [requirements](requirements.md) at work. The result's shape is in
the [contracts](contracts.md).

## Doing the work

### scenario.general-work.rewrite — A Spec rewrite is done and reviewed

- GIVEN a task worktree bound to a [Module](../../glossary.json#concept.module)
- WHEN the caller runs `general --type specify` with an instruction to rewrite that Module's [Spec](../../glossary.json#concept.spec) document
- THEN the worker may change the Module's Spec documents and nothing else
- AND the result names the rewritten document as modified, with the kept diff and the earlier content
- AND a separate reviewer, which may change nothing, receives the instruction, the diff and the earlier content
- AND the result has status `ok` with the reviewer's findings and the verdict that follows from them

### scenario.general-work.instruction-file — An instruction file is kept as it was

- GIVEN an instruction written in a file of the task worktree
- WHEN the caller runs `general` with `--instruction-file` naming it
- THEN the worker's [brief](../../glossary.json#concept.brief) carries the instruction after the [Operation](../../glossary.json#concept.operation)'s own prompt
- AND the run's [trace node](../../glossary.json#concept.trace-node) keeps an exact copy, whose digest the result gives

### scenario.general-work.blocking-finding — A blocking finding requires changes

- GIVEN a worker that changed the meaning of a document it was told to keep
- WHEN the reviewer reports a blocking `meaning` finding
- THEN the result has status `ok` and the verdict `changes_required`
- AND the worker's change stays in the worktree for the caller to keep, revise or revert

### scenario.general-work.read-only-unbound — A read-only run works unbound

- GIVEN the primary worktree, which has no [workspace binding](../../glossary.json#concept.workspace-binding)
- WHEN the caller runs `general --type implement --read-only` with `--modules` and a question
- THEN the worker may read the Modules' code and change nothing
- AND the result carries the worker's answer, an empty change and the review

### scenario.general-work.unbound-write — A writing run needs a workspace

- GIVEN the primary worktree, which has no workspace binding
- WHEN the caller runs `general --type specify` without `--read-only`
- THEN the run ends `failed` with `unbound_write`
- AND no worker launched

## Failures

### scenario.general-work.outside-grant — A write outside the grant fails the run

- GIVEN a worker that writes a file its `--type` grant does not make writable
- WHEN the [write audit](../../glossary.json#concept.write-audit) finds it
- THEN the run ends `failed` with `audit_violation`
- AND the reviewer does not launch

### scenario.general-work.worker-blocked — A blocked worker gets no review

- GIVEN a worker that cannot do the work and ends `blocked`
- WHEN the run ends
- THEN the run ends `blocked` with the worker's own link in its [error chain](../../glossary.json#concept.error-chain)
- AND the reviewer does not launch

### scenario.general-work.no-instruction — An empty instruction launches nothing

- GIVEN an instruction file that is empty
- WHEN the caller runs `general` with it
- THEN the run ends `failed` with `instruction_unreadable` and reason `input`
- AND no worker launched
