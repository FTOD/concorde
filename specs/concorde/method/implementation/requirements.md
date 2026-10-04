# Implementation requirements

The Module-wide obligations of [Implementation](module.md). The shapes of the code change and the
test report are in the [contracts](contracts.md). The [scenarios](scenarios.md) show the obligations
in concrete situations.

## Implement

### req.implementation.write-scope — Only the bound Modules' code is writable

The implement worker's grant SHALL make writable only files in the ImplementationScope of the
bound Modules that the grant computed from the workspace's Specs.

### req.implementation.no-spec-writes — Workers never change Specs

The implement worker's grant SHALL NOT make any [Spec](../../glossary.json#concept.spec) document
or metadata file writable.

### req.implementation.no-spec-edits — The Operation never changes a Spec

The implement [Operation](../../glossary.json#concept.operation) SHALL NOT change any Spec
document or metadata file itself.

### req.implementation.audit — Writes outside the grant fail the run

When an implement run's [write audit](../../glossary.json#concept.write-audit) finds a change outside
the grant's writable paths, the run SHALL end `failed` with the offending paths as host evidence.

Such a run gets no [resume round](../../glossary.json#concept.resume-round), since rounds only
repair failed checks.

### req.implementation.host-deletes — Deletions are performed by the Operation

The implement Operation SHALL delete a file only when all of these conditions hold:

- The worker's result proposes it.
- The file lies inside the grant's writable paths.
- The audit was clean.

### req.implementation.checks-follow-uses — The checks of users run too

The Operation SHALL run the [configured checks](../../glossary.json#concept.configured-check) of the
bound Modules and of every [Module](../../glossary.json#concept.module) that uses one of them,
directly or through further uses.

### req.implementation.checks-outside — Checks run outside the worker

After every worker round whose audit is clean and whose worker ended `ok`, the implement Operation
SHALL run the configured checks through Check execution.

### req.implementation.resume-checks-only — Resume rounds repair failed checks only

The implement Operation SHALL resume the worker only to repair configured checks that failed in the
preceding round.

### req.implementation.worker-status — A blocked or failed worker ends the run

When an implement run's [worker result](../../glossary.json#concept.worker-result) is `blocked` or
`failed`, including one that reports a [Spec gap](../../glossary.json#concept.spec-gap), the run
SHALL end with both of these:

- That status.
- An [error chain](../../glossary.json#concept.error-chain) that ends in the worker's own link.

### req.implementation.round-limit — Resume rounds are bounded

The implement Operation SHALL run at most the configured number of resume rounds, selected in this
order:

- The number `--rounds` gives.
- Otherwise, the [worker configuration](../../glossary.json#concept.worker-configuration)'s
  `limits.rounds`.
- Otherwise, three.

## Test

### req.implementation.test-no-writes — Testing changes nothing

The test Operation SHALL leave every file of the workspace unchanged.

### req.implementation.test-no-commands — The test worker runs no command

The test worker's tool list SHALL NOT include Bash or any other tool that runs a command.

### req.implementation.test-reads-logs — The test worker reads every check log

The test Operation SHALL let its worker read the log of every check the Operation ran for the run,
whether the check passed or not.

### req.implementation.test-failures-accounted — Each failed check is interpreted once

When, after one resume round with every mismatch, its worker's `failures` violate any of these
conditions, the test Operation SHALL end the run `failed` with `failures_unaccounted`:

- They hold exactly one entry per check that did not pass.
- Each entry is named by that check's identity.
- They hold no entry for a check that passed.

The test Operation gives the resume round only when the first answer does not hold. The
entries' contents stay the worker's interpretation.

### req.implementation.host-check-facts — Check outcomes come from the Operation

The Operation SHALL use its recorded [check results](../../glossary.json#concept.check-result) as
the check outcomes in a code change or a test report, never the worker's statement of them.
