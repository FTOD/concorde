# General work scenarios

Concrete situations that show the [requirements](requirements.md) at work. The result's shape is in
the [contracts](contracts.md).

## Doing the work

### scenario.general-work.rewrite — A Spec rewrite is done and reviewed

- GIVEN a task worktree bound to a [Module](../../glossary.json#concept.module)
- WHEN the caller runs `general --type specify` with an instruction to rewrite that Module's [Spec](../../glossary.json#concept.spec) document
- THEN the worker may change the Module's Spec documents and nothing else
- AND the result names the rewritten document as modified, with the kept diff and the earlier content
- AND a separate reviewer, which may change nothing, receives the instruction, the workspace's goal, the diff and the earlier content
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

### scenario.general-work.review-inputs — The reviewer reads the admitted inputs

- GIVEN an earlier `ok` run of the same workspace whose output holds an answer
- WHEN the caller runs `general` with `--input` naming that run and an instruction to summarize its answer
- THEN the worker's brief carries that run's output as admitted material
- AND the reviewer's brief carries the same material

### scenario.general-work.reviewer-frozen-grant — The reviewer keeps the worker's grant

- GIVEN a bound Module that uses another Module
- WHEN a `general --type specify` worker breaks the bound Module's metadata, where that use is declared
- THEN the reviewer still launches, under the grant the worker received with every writable level lowered to read
- AND the reviewer's grant has the worker's [context identity](../../glossary.json#concept.context-identity) and still reads the used Module's Spec
- AND the result has status `ok` with the reviewer's findings

### scenario.general-work.read-only-unbound — A read-only run works unbound

- GIVEN the primary worktree, which has no [workspace binding](../../glossary.json#concept.workspace-binding)
- WHEN the caller runs `general --type implement --read-only` with `--modules` and a question
- THEN the worker may read the Modules' code and change nothing
- AND the result carries the worker's answer, an empty change and the review

### scenario.general-work.type-sets-boundary-only — The task type gives no job of its own

- GIVEN a task worktree bound to a Module
- WHEN the caller runs `general --type code-to-spec --read-only` or `general --type review-code` with a question
- THEN neither worker's brief tells it to describe the code in the Specs or to report a `spec-gap` finding
- AND both briefs carry General work's own rule for a promise the Spec does not state

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
- AND the run's host evidence keeps the tree recorded before the worker, but no observed change

### scenario.general-work.after-unobservable — A change Git cannot record gets no review

- GIVEN a worker that ends `ok` with a clean audit
- WHEN Git cannot record the worktree as a tree after the worker
- THEN the run ends `failed` with `change_unobservable` and reason `environment`
- AND the reviewer does not launch

### scenario.general-work.no-instruction — An empty instruction launches nothing

- GIVEN an instruction file that is empty
- WHEN the caller runs `general` with it
- THEN the run ends `failed` with `instruction_unreadable` and reason `input`
- AND no worker launched
