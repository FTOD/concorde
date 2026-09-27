# Implementation requirements

The Module-wide obligations of [Implementation](module.md). The shapes of the code change and the
test report are in the [contracts](contracts.md); the [scenarios](scenarios.md) show the
obligations in concrete situations.

## Implement

### req.implementation.write-scope — Only the bound Modules' code is writable

The implement worker's grant SHALL make writable only files in the ImplementationScope of the
bound Modules that the grant computed from the workspace's Specs.

### req.implementation.no-spec-writes — Workers never change Specs

The implement worker's grant SHALL NOT make any Spec document or metadata file writable.

### req.implementation.pending-precreated — Declared files exist before launch

The implement Operation SHALL create every pending file and directory the grant makes writable before
it launches the worker.

### req.implementation.audit — Writes outside the grant fail the run

An implement run whose write audit finds a change outside the grant's writable paths SHALL end
`failed` with the offending paths as host evidence and without a resume round.

### req.implementation.host-deletes — Deletions are performed by the Operation

The implement Operation SHALL delete a file only when the worker's result proposes it, the file lies
inside the grant's writable paths and the audit was clean.

### req.implementation.checks-follow-uses — The checks of users run too

The Operation SHALL run the configured checks of the bound Modules and of every Module that uses one of them, directly or through further uses.

### req.implementation.checks-outside — Checks run outside the worker

The implement Operation SHALL run the bound Modules' configured checks through Check execution after
every audited worker round.

### req.implementation.resume-checks-only — Resume rounds repair failed checks only

The implement Operation SHALL resume the worker only to repair configured checks that failed in the
preceding round.

A worker result of `blocked` or `failed`, including one that reports a Spec gap, ends the run with
that status and an error chain that ends in the worker's own link.

### req.implementation.round-limit — Resume rounds are bounded

The implement Operation SHALL run at most the configured number of resume rounds, three unless
`--rounds` gives another number.

### req.implementation.pending-markers — Pending markers follow the files

At the end of every implement run whose worker was launched, the Operation SHALL clear the pending
marker of exactly those pending entries of the bound Modules whose files or directories exist.

Before markers are cleared, every file or directory the Operation pre-created that is still empty is
removed again, so an unused declaration stays pending.

## Test

### req.implementation.test-no-writes — Testing changes nothing

The test Operation SHALL leave every file of the workspace unchanged.

### req.implementation.test-no-commands — The test worker runs no command

The test worker's tool list SHALL NOT include Bash or any other tool that runs a command.

### req.implementation.test-reads-logs — The test worker reads every check log

The test Operation SHALL let its worker read the log of every check the Operation ran for the run, whether the check passed or not.

### req.implementation.host-check-facts — Check outcomes come from the Operation

The check outcomes in a code change or a test report SHALL be the check results the Operation recorded,
never the worker's statement of them.
