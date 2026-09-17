# Checking the current candidate

Validation runs deterministic Spec checks and configured implementation checks, then evaluates
whether the candidate meets its existing completion gates. It does not ask a model to repair work
or turn a passing command into proof of complete correctness.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Structural validation](../spec/structure.md#terminology) | Defined in What structural validation tells you. |

## Normal validation

The host selects the current candidate and affected Modules, checks structural consistency, and runs
the configured commands. Readiness also needs completed tasks and any already-required current,
successful reviews. Skipping a command does not supply missing evidence. A manually authored candidate
can be checked without inventing a development plan, but existing unfinished tasks cannot be bypassed.

For example, if code changes after a passing check, the old result is no longer evidence for those
new bytes. Validation recomputes or rechecks the relevant evidence before reporting readiness.
A failed check leaves the candidate available for inspection and repair; it does not deliver it.

## Checks must not change what they verify

Configured checks run with OS-enforced read-only project access, including child processes. Temporary
caches and reports go to separate issued storage. Formatting source is an implementation action, not
something a check may silently do while claiming to verify the original bytes.

Currently the isolated runner requires Linux, system bubblewrap and working namespace/pidfd support.
If that boundary is unavailable, validation stops instead of running unrestricted commands. The
host retains diagnostics and precise evidence records separately from worker inputs. Exact check
interfaces and freshness rules are in Implementation Specs.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#validation-validation-capability).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
