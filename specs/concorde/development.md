# Development environment

The root Module binds the files that set up development of this checkout: the Python project and
lock, the pytest configuration and its evidence plugin, the reference initializer, the Claude
Code documentation fetcher and the docsite type check. These promises concern how Concorde's own
tests and checks run, not what Concorde offers a consumer project.

## Test evidence

### req.concorde.test-evidence — Test runs record why and on what they ran

The pytest evidence plugin SHALL record each run's reason, scope, phase, attempt and input fingerprints in its JSON report.

Callers that pass none of these get `manual` and `unspecified`. The report keeps discovery,
queueing and execution times apart and never presents summed parallel test time as elapsed time.

### scenario.concorde.test-timing — Test runs record reasons and input identity

- GIVEN pytest arguments with or without `--reason`, `--scope`, `--phase`, `--attempt` and `--prior`
- WHEN the suite runs with `--json` reporting
- THEN the report records the reason, scope, phase, attempt, prior run and fingerprints of the tests, inputs, runtime, locks and environment
- AND discovery, queueing, execution and total elapsed times are reported separately
- BUT summed parallel test time is never reported as elapsed time

## Docsite type check

### scenario.concorde.check-docsite-external — The docsite type check works on a disposable copy

- GIVEN this checkout with its docsite
- WHEN `scripts/development/check-docsite-types.py` runs
- THEN it copies the docsite to a temporary directory, derives the sidebar from the project registry there and runs the TypeScript compiler on the copy
- AND dependency installation and generated files stay inside that copy
- AND the command returns the compiler's exit status and removes the copy
