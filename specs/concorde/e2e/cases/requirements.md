# SWE-bench cases requirements

The Module-wide obligations of [SWE-bench cases](module.md). The [scenarios](scenarios.md) show
them in concrete situations.

### req.swe-bench-cases.repair-specs-only — A case's Specs are repaired in one bounded round

The tool SHALL repair an adopted case's Specs in one bounded round: a review and, when that review
does not accept the Specs, one `specify` and a second review.

The repair is meant to come before the case's issue is worked. That order is a condition on how the
developer uses the tool, not a promise of the tool: `repair-specs` cannot tell whether the issue has
been worked already, and it does not check.

### req.swe-bench-cases.specs-not-code — A case's repair never changes code

The repair of an adopted case's Specs SHALL change the project's Specs and never its code.

### req.swe-bench-cases.graded-apart — A case's tests stay outside the project

The tool SHALL grade a case in a throwaway worktree of the project, applying the case's test patch
only there.

### req.swe-bench-cases.grading-worktree-removed — The grading worktree does not outlive grading

The tool SHALL remove a case's grading worktree afterwards, whether grading ends with a verdict or
with an error.
