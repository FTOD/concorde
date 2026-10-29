# SWE-bench cases requirements

The Module-wide obligations of [SWE-bench cases](module.md). The [scenarios](scenarios.md) show
them in concrete situations.

### req.swe-bench-cases.repair-specs-only — A case's Specs are repaired in one bounded round

The tool SHALL repair an adopted case's [Specs](../../glossary.json#concept.spec) in one bounded
round: a review, one `specify` only when that review ends `ok` and does not accept the Specs, and a
second review only when that `specify` ends `ok`.

A step that does not end `ok` stops the round with its result, as
[Repairing the adopted Specs](module.md#repairing-the-adopted-specs) explains.

The repair is meant to come before the case's issue is worked. That order is a condition on how the
developer uses the tool, not a promise of the tool: `repair-specs` cannot tell whether the issue has
been worked already, and it does not check.

### req.swe-bench-cases.specs-not-code — A case's repair never changes code

The repair of an adopted case's Specs SHALL NOT change the project's code.

Whether the repair changes the Specs at all is the [bounded round](#req.swe-bench-cases.repair-specs-only)'s
concern: a round whose first review accepts the Specs changes nothing. Such a round closes its
task as completed, without delivery or merge.

### req.swe-bench-cases.graded-apart — A case's tests stay outside the project

The tool SHALL grade a case in a throwaway worktree of the project, applying the case's test patch
only there.

### req.swe-bench-cases.graded-like-swe-bench — Listed tests are graded under their complete identities

The tool SHALL count each listing of a test as passed by SWE-bench's rules for its list, applied to
the status pytest reports under the test's complete node identity.

A test listed twice therefore counts twice. A listed identity cut inside its parameters takes the
status of the reported identities it begins only when they agree on passing by the same list's
rule, as [the verdict](module.md#grading-a-case) explains.

### req.swe-bench-cases.patched-files-reset — Every file the test patch touches is reset

Before it applies a case's test patch, the tool SHALL restore to the case's base commit every file
the patch touches, on either side of the patch, whatever characters the file's path holds.

### req.swe-bench-cases.grading-worktree-removed — The grading worktree does not outlive grading

The tool SHALL remove a case's grading worktree afterwards, whether grading ends with a verdict or
with an error.

### req.swe-bench-cases.cleanup-checked — A grading worktree left behind fails grading

When the grading worktree, its registration or its scratch directory is left after grading, the
tool SHALL fail with `cleanup_failed`, naming what is left and any earlier error of grading.
