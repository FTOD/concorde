# Understanding requirements

The Module-wide obligations of [Understanding](module.md). The assessment's shape is in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Reading

### req.understanding.names-only — Code is known by name only

The understand worker's grant SHALL give read access only to Spec documents and included external
material, never to the contents of an implementation file.

Implementation files of the bound Modules appear in the brief by path only, so the worker can place
a planned file without learning what existing code does.

### req.understanding.task-worktree — Assessments describe the task's Specs

The understand host SHALL compute the grant from the Specs of the task worktree named by `--task`.

## Answers

### req.understanding.gaps-reported — Missing promises are gaps

An assessment SHALL report every promise the stated goal needs and a bound Module's Spec does not
state as a Spec gap rather than as a fact inferred from code or file names.

### req.understanding.insufficient-no-plan — No plan on an insufficient Spec

An assessment that finds the Spec insufficient for the goal SHALL carry no plan.

### req.understanding.plan-on-request — Plans only when asked

The understand Operation SHALL return a plan only when `--plan` was given.

### req.understanding.known-modules — Assessments name existing Modules

The understand host SHALL end a run `failed` when the assessment names a Module identity that the
task worktree's Specs do not define.

The unknown identities are returned as host evidence; the host never drops or corrects them.

### req.understanding.consistent — Inconsistent assessments fail the run

The understand host SHALL end a run `failed` when the assessment lists Spec gaps although it is
sufficient or none although it is insufficient, carries a plan that was not requested or follows an
insufficient Spec, carries no plan although one was requested and the Spec is sufficient, or has no
entry for a bound Module.

Each inconsistency is returned as host evidence. The run is not resumed to repair it.

## Effects

### req.understanding.no-writes — The worktree is left unchanged

The understand Operation SHALL leave every file of the task worktree unchanged.

The worker has no Edit, Write or Bash tool, and the write audit confirms that nothing changed; a
change it finds ends the run `failed` with the changed paths as host evidence.

### req.understanding.single-round — No resume rounds

The understand host SHALL NOT resume the worker after it has returned its result.
