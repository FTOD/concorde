# Understanding requirements

The Module-wide obligations of [Understanding](module.md). The assessment's shape is in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Reading

### req.understanding.names-only — Code is known by name only

The understand worker's grant SHALL give read access only to
[Spec](../../../glossary.json#concept.spec) documents and included external material, never to the
contents of an implementation file.

Implementation files of the bound Modules appear in the brief by path only, so the worker can place
a planned file without learning what existing code does.

### req.understanding.task-worktree — Assessments describe the run worktree's Specs

The understand [Operation](../../../glossary.json#concept.operation) SHALL compute the grant from the Specs of the worktree the run starts in, which for a bound run is its workspace.

## Answers

### req.understanding.gaps-reported — Missing promises are gaps

An assessment SHALL report every promise the stated goal needs and a bound
[Module](../../../glossary.json#concept.module)'s Spec does not state as a
[Spec gap](../../../glossary.json#concept.spec-gap) rather than as a fact inferred from code or file
names.

### req.understanding.insufficient-no-plan — No plan on an insufficient Spec

An assessment that finds the Spec insufficient for the goal SHALL carry no plan.

### req.understanding.plan-on-request — Plans only when asked

The understand Operation SHALL return a plan only when `--plan` was given.

### req.understanding.known-modules — Assessments name existing Modules

The understand Operation SHALL end a run `failed` when the assessment names a Module identity that
the Specs of the run's worktree do not define.

The unknown identities are returned as host evidence; the Operation never drops or corrects them.

### req.understanding.consistent — Inconsistent assessments fail the run

The understand Operation SHALL end a run `failed` when the assessment lists Spec gaps although it is
sufficient or none although it is insufficient, carries a plan that was not requested or follows an
insufficient Spec, carries no plan although one was requested and the Spec is sufficient, or has no
entry for a bound Module.

Each inconsistency is returned as host evidence. The run is not resumed to repair it.

## Effects

### req.understanding.no-writes — The worker may write nothing

The understand Operation SHALL run its worker under a grant with no writable path.

The worker has no editing or shell tool.

### req.understanding.change-fails — A change to the worktree fails the run

The understand Operation SHALL end a run `failed` when the
[write audit](../../../glossary.json#concept.write-audit) finds any violation in the worktree the
run works on, such as a changed, new or deleted file.

The changed paths are returned as host evidence and the change is left in place for the
[main agent](../../../glossary.json#concept.main-agent), never reverted. The run's own
[run progress file](../../../glossary.json#concept.run-progress-file) and
[run result](../../../glossary.json#concept.run-result), and its worker's
[progress file](../../../glossary.json#concept.progress-file) and
[run record](../../../glossary.json#concept.run-record), are written into the
[run store](../../../glossary.json#concept.run-store), which Git ignores; they are not changes the
audit judges.

### req.understanding.single-round — No resume rounds

The understand Operation SHALL NOT resume the worker after it has returned its result.
