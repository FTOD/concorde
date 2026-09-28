# Implementation requirements

The Module-wide obligations of [Implementation](module.md). The shapes of the
[code change](../../../glossary.json#concept.code-change) and the
[test report](../../../glossary.json#concept.test-report) are in the [contracts](contracts.md); the
[scenarios](scenarios.md) show the obligations in concrete situations.

## Implement

### req.implementation.write-scope — Only the bound Modules' code is writable

The implement worker's grant SHALL make writable only files in the ImplementationScope of the
bound Modules that the grant computed from the workspace's Specs.

### req.implementation.no-spec-writes — Workers never change Specs

The implement worker's grant SHALL NOT make any [Spec](../../../glossary.json#concept.spec) document
or metadata file writable.

### req.implementation.pending-precreated — Declared files exist before launch

The implement [Operation](../../../glossary.json#concept.operation) SHALL create every pending file
and directory the grant makes writable before it launches the worker.

### req.implementation.audit — Writes outside the grant fail the run

An implement run whose [write audit](../../../glossary.json#concept.write-audit) finds a change
outside the grant's writable paths SHALL end `failed` with the offending paths as host evidence.

Such a run gets no [resume round](../../../glossary.json#concept.resume-round), since rounds only
repair failed checks.

### req.implementation.host-deletes — Deletions are performed by the Operation

Apart from the pending files and directories it pre-created, the implement Operation SHALL delete a
file only when the worker's result proposes it, the file lies inside the grant's writable paths and
the audit was clean.

A pre-created path that is still empty is removed without a proposal, whatever the status, as
[req.implementation.pending-markers](#req.implementation.pending-markers) describes.

### req.implementation.checks-follow-uses — The checks of users run too

The Operation SHALL run the [configured checks](../../../glossary.json#concept.configured-check) of the bound Modules and of every [Module](../../../glossary.json#concept.module) that uses one of them, directly or through further uses.

### req.implementation.checks-outside — Checks run outside the worker

The implement Operation SHALL run the configured checks through Check execution after every worker
round whose audit is clean and whose worker ended `ok`.

### req.implementation.resume-checks-only — Resume rounds repair failed checks only

The implement Operation SHALL resume the worker only to repair configured checks that failed in the
preceding round.

### req.implementation.worker-status — A blocked or failed worker ends the run

An implement run whose [worker result](../../../glossary.json#concept.worker-result) is `blocked`
or `failed`, including one that reports a [Spec gap](../../../glossary.json#concept.spec-gap),
SHALL end with that status and an [error chain](../../../glossary.json#concept.error-chain) that
ends in the worker's own link.

### req.implementation.round-limit — Resume rounds are bounded

The implement Operation SHALL run at most the configured number of resume rounds: the number
`--rounds` gives, or else the configuration's `workers.rounds`, or else three.

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

The check outcomes in a code change or a test report SHALL be the
[check results](../../../glossary.json#concept.check-result) the Operation recorded, never the
worker's statement of them.
