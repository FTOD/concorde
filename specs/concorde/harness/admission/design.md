# Request admission in detail

This topic extends the [Request admission](module.md) entry with the reasoning and the less common
paths a maintainer of admission needs. Consumers of admission do not need it: the entry states
every promise they rely on, and the precise definitions are in [requirements](requirements.md),
[scenarios](scenarios.md) and [contracts](contracts.md).

## The admission sequence

Every capability, deterministic or model-backed, passes the same finite steps in the same order:

1. read the request (size, JSON, envelope type and version, launcher argument);
2. admit it: known public capability in the catalog, known mode, fresh build when the capability is
   model-backed and the request is top-level, worktree root, typed configuration and request,
   default task, selected target (registry or provider hook) and restored change owner;
3. bind the workspace (stay, relay, apply in the primary on opt-in, or delivery session);
4. check the configuration and open the run record;
5. dispatch through the dispatcher the launcher supplied;
6. finalize: map the outcome to a status, record execution failures and the lifecycle outcome a
   provider handed over, finish the run record.

A failed step skips the rest and goes straight to finalization. The sequence is plain code, not a
scheduler: it accepts no caller-supplied steps and launches no model. Model work is only prepared
behind it; the Host steps of a running Agent call are not capability requests and are checked by
Agent execution against the call it prepared.

## Why declarations

Admission sits below every provider. Without declarations it would have to import Planning,
Delivery or Issue solving to learn that `concorde-configure` mutates only on `apply`,
`concorde-deliver` runs in a delivery session and `concorde-issues` selects an Issue before its
worktree is chosen. Each capability states these facts in the
[capability declaration](contracts.md#contract.admission.capability-declaration); the Operations
catalog provides them and a provider that needs its own target selection names a hook. Adding a
capability then changes the catalog and its provider, never admission.

## Relay details

From the primary worktree of a consumer project, a mutating request without a `change_id` gets a new
candidate from the committed `HEAD`; the launcher's installation service installs the running
package into it, and only candidate creation installs, a later relay only verifies. A request with a
`change_id` relays into the live candidate recorded for it. The relayed request carries the
candidate's change identity when its type has that field, and the candidate's complete envelope,
including its invocation identity, becomes the result; standard error is forwarded. The relaying
request's own run record names the candidate's run.

Installation belongs to Distribution. When the installation service refuses, admission reports
`local_installation_required` and keeps the new candidate with status `blocked`, so the developer can
install into it and retry the same change. A candidate of Concorde's own source is never installed
into; it must already have its own build and environment.

Three cases do not relay. Concorde's own source checkout refuses a mutation from its primary with
`fresh_session_required`, because source maintenance runs in a candidate the user session hands to a
fresh Task subagent. A directory outside any Git worktree has no committed state and no primary, so
a mutation there is refused with `workspace_mismatch`. And a capability declaring the delivery
session runs where it was started; Delivery checks that the worktree takes part in the change.

## Applying in the primary

`concorde-configure` and an initialization `apply` declare the `primary-opt-in` workspace. Without
`run_in_primary` they are relayed like any other mutation, so the effect reaches the primary only
when the change is delivered, which is what a developer testing these commands wants. With
`run_in_primary: true` in the primary, admission applies the request there without a candidate or a
change registration. The field exists only in those request types; it is refused with
`workspace_mismatch` outside the primary and with `fresh_session_required` in the source checkout.
Because the choice changes where the effect lands, the user session asks the developer before
calling either capability from the primary.

## Configuration as a reviewed proposal

A configuration change decides which models run and how long they may take, so the developer should
see exactly what will be written. `propose` changes nothing and returns the proposal (new value,
the digest of the current configuration file, and the Protocol binding to adopt when
`accept_protocol` was set) with its own digest. `apply` accepts only that proposal, identified by its
digest, and only while the file still has the proposal's source digest, so it never overwrites an
edit made meanwhile. It keeps every other key of the file and keeps the write only if the project
still loads. Because a relayed apply compares against the candidate's committed file, a proposal
computed from uncommitted configuration in the primary can only be applied with `run_in_primary`.
Accepting the installed Protocol is the only way a project adopts a new Protocol version.

Requiring every other request to equal the stored configuration means an Agent's model and limits
cannot be changed by whoever writes a request, and a nested capability request cannot run with
different settings from the request that started it. `concorde-init` takes its configuration from
its own request, because an uninitialized project has none stored.

## Refusals, outcomes and failures

Admission refusals keep their error code and give status `blocked`; a refusal, including a gate
refusal such as `review_required`, stops the request without changing the change's lifecycle
status. A provider's output decides the status by its outcome: `completed`, `ready` and `delivered`
succeed, `failed` fails, anything else blocks; lifecycle outcomes such as `blocked` are recorded by
the provider, which hands them to finalization. Execution failures give status `failed` with
`execution_failed`, `execution_cancelled` or `execution_limit`, and are recorded as the change's
lifecycle status. A relay whose candidate launcher returned no envelope is a transport failure:
status `failed` with `relay_failed`, the candidate's own change status untouched. A failed status or
run record write is reported beside the output as `state_persistence_failed`, never instead of it. An
interrupt ends the request with `execution_cancelled` and keeps the candidate; a relayed launcher
gets thirty seconds to cancel its own work before it is killed.

## Causal feedback

Upper layers add context as causes instead of replacing the original error, so a native schema
rejection stays visible behind a Host refusal behind a Workflow failure. Messages are sanitized:
argument values and model output are removed and credential-like values are redacted. A record too
large for Pi's display is exported whole to a private temporary file, whose path the display shows.
The Pi side produces the same record format, so a failure keeps one shape across processes.
Feedback is diagnostic only.

## Not enforced

Admission cannot tell who started the launcher: an Agent with a shell, such as the programmer, can
run `scripts/run-operation.py` itself, and admission treats that request like any other.

## Open questions

What `describe-policy` shows for each model-backed capability is decided by its provider; admission
promises only that nothing runs and nothing changes. The error code table lists every code because
any code can reach a caller through the envelope, but each code is owned by the Module where it
arises.
