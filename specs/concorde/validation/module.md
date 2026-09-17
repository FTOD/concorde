# Validation

## Purpose

Validation collects deterministic structural and configured implementation-check evidence for the current candidate and evaluates the applicable readiness gates. It serves explicit validation requests and composing flows; neither a development plan nor dev-loop invocation is universally required.

## Usage

Run `concorde-validate` for the current admitted candidate with target_id and task; optionally
choose whether to run configured checks. This deterministic capability launches no Agent. It
returns structural and configured-check evidence tied to current bytes and evaluates existing
readiness requirements. A directly authored candidate needs no invented plan or attempt; existing
authored tasks and required reviews still apply.

Omitting checks does not satisfy a gate whose evidence is missing or stale. Failed checks,
incomplete tasks or required reviews block ready while preserving the candidate. Repeating
validation evaluates current inputs; prior passing results are not permanent. Checks can read
project files but must write temporary output only to issued external scratch. Unsupported check
isolation fails closed with private diagnostics, not a less restricted fallback. Validation
neither repairs defects nor delivers a change, and structural success or scenario coverage does
not prove semantics. See [validation](validation.md) for results and operational prerequisites.

## Design

<a id="entity.validation.adapter"></a><a id="entity.validation.evidence"></a><a id="entity.validation.readiness"></a>

Validation resolves affected Spec consumers and changed-file users before collecting evidence.
The host admits configured commands and delegates execution to Harness's OS-enforced read-only
executor; only the outside host persists logs and digest-bound results. [Check execution](validation.md#configured-check-execution)
describes scratch, private diagnostics and concurrent-change rechecks.

Readiness combines current structural/check evidence with existing task completion and required
reviews, without inventing a plan for a manual candidate. Unavailable isolation fails closed.
This separation keeps a command's success from granting writes, proving semantics or bypassing a
previously required review.

## Relationships

The diagram separates Validation evidence from the Readiness decision that consumes it. Spec
identifies affected consumers and checks structure, Harness executes admitted commands without
project writes, and Development records results and evaluates existing gates. A passing command
is evidence for its checked inputs, not permission to skip required reviews or a proof of semantic
completeness. These collaborations are capability dependencies; Validation does not own its providers.

```mermaid
flowchart TB
    accTitle: Validation entities and dependencies
    accDescr: Validation resolves affected users and validates Spec structure, runs configured checks through the isolated Harness executor and records evidence and readiness decisions through the host.
    e0["Validation adapter"]
    e1["Development"]
    e2["Harness"]
    e3["Spec"]
    e0 -->|records evidence and readiness through| e1
    e0 -->|runs isolated configured checks through| e2
    e0 -->|validates structure and resolves affected users through| e3
    domain_evidence["Validation evidence"]
    e0 -->|records current check results as| domain_evidence
    domain_readiness["Readiness decision"]
    e0 -->|evaluates current gates for| domain_readiness
```

## Provider collaboration

Validation relies on these providers while retaining responsibility for its own readiness decision.

### Development

<a id="entity.validation.development"></a><a id="agreement.document.validation.module.1"></a>

Admit deterministic validation requests, retain private check logs and store current candidate evidence and readiness decisions.

This collaboration applies when validation is requested, check results are recorded or existing task and review gates are evaluated.

- [Host admission](../development/interfaces.md#capability-execution-boundary); Recheck admitted intent and returned identities before accepting host state; a rejected result cannot advance the dependent step.

### Harness

<a id="entity.validation.harness"></a><a id="agreement.document.validation.module.2"></a>

Execute configured checks with OS-enforced read-only project access, external scratch and bounded process-tree lifetime.

This collaboration applies when run_checks admits a configured command whose result is needed for candidate evidence.

- [Isolated configured-check execution](../harness/execution.md#configured-deterministic-checks); Supply the registered command and timeout; keep raw diagnostics in host records and refuse checks when isolation is unavailable.

### Spec

<a id="entity.validation.spec"></a><a id="agreement.document.validation.module.3"></a>

Validate Spec structure and resolve every affected contract consumer and implementation-file user for candidate checks.

This collaboration applies when computing structural evidence and the affected Module set for current validation.

- [Owner and context resolution](../spec/contracts.md#registry-stable-id-spec-context-queries); Reconstruct current resolutions after input changes; unresolved ownership, missing required definitions or stale revisions block dependent use.
- [Structural validation](../spec/scenarios.md#scenario.spec.validate-success); require consistent registered state without claiming semantic completeness.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Declared files explicitly
share the existing adapter realization with Development; no new runtime package, public Skill,
Agent grant or configurable arbitrary flow is created by this Spec boundary. Host admission,
phase artifacts and permissions remain mandatory. A new flow requires declared composition and
an implementation of its sequencing, artifact admission, recovery and completion policies before
it can execute. The existing host package still realizes common dispatch and provider internals.

## Precise specifications

The Validation Module owns the exact obligations and interface details in [requirements](requirements.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
