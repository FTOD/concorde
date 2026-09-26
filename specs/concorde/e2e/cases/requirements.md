# SWE-bench cases requirements

The Module-wide obligations of [SWE-bench cases](module.md). The [scenarios](scenarios.md) show
them in concrete situations.

### req.swe-bench-cases.repair-specs-only — A case's repair changes Specs, never code

The tool SHALL repair an adopted case's Specs in one bounded round, a review, one `specify` and a second review, before the case's issue is worked, changing the project's Specs and never its code.

### req.swe-bench-cases.graded-apart — A case's tests stay outside the project

The tool SHALL grade a case in a throwaway worktree of the project, applying the case's test patch only there and removing the worktree afterwards.
