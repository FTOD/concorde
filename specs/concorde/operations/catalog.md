# Capability declarations and dispatch

The exact declarations behind the capability table in the [Operations entry](module.md): what each
capability declaration contains, the inventory that mirrors them in this document's metadata, the
routes dispatch takes, and the Module-wide obligations of Operations.

## Capability declarations

Each public capability has one Python module `operations/<name>.py`, whose public name is `concorde-`
followed by the module name with `_` replaced by `-`. The module declares:

| Name | Meaning |
| --- | --- |
| `KIND` | `agent-entry` (one prepared native Agent call), `workflow` (one prepared native workflow) or `host` (a finite Host service) |
| `PUBLIC` | `True` for every capability; there is no private capability |
| `CONTEXT_SELECTION` | `bound` when a worker receives the target Module's frozen context, `none` for Host services |
| `DETERMINISTIC` | `True` when no supported path calls a model |
| `USES` | the Agents, or for `concorde-issues` also the capabilities, that the capability composes |
| `PROFILE` | always `None`; execution profiles belong to Agent definitions |
| `EXTERNAL_NAME` | the public `concorde-` name |
| `REQUEST`, `RESPONSE` | the JSON Schemas of the request and response data |
| `STATE`, `run` | the request type and the function that hands the request to Request admission |

`STATE` and `run` exist so that the launcher can call every declaration the same way. They do not
make a capability an Operation: `run` only calls admission.

The package `operations/__init__.py` lists the eleven names in `OPERATIONS` (also exported as
`CAPABILITIES`) and groups them: `WORKFLOWS` holds `plan`, `spec_review`, `code_review` and `issues`;
`HOST_TOOLS` holds `init`, `configure`, `validate` and `deliver`. `STATE_OPERATIONS` names the
Operation catalog's single entry, `terminal_agent_operation`.

| Capability | `KIND` | `CONTEXT_SELECTION` | `DETERMINISTIC` | `USES` |
| --- | --- | --- | --- | --- |
| `concorde-context-solve` | `agent-entry` | `bound` | false | `context_assessor` |
| `concorde-plan` | `workflow` | `bound` | false | `context_assessor`, `planner` |
| `concorde-tasks` | `agent-entry` | `bound` | false | `task_author` |
| `concorde-implement` | `agent-entry` | `bound` | false | `programmer` |
| `concorde-spec-review` | `workflow` | `bound` | false | `spec_reviewer` |
| `concorde-code-review` | `workflow` | `bound` | false | `code_reviewer` |
| `concorde-issues` | `workflow` | `bound` | false | `issue_solver`, `spec_review`, `code_review`, `validate` |
| `concorde-validate` | `host` | `none` | true | none |
| `concorde-deliver` | `host` | `none` | true | none |
| `concorde-init` | `host` | `none` | true | none |
| `concorde-configure` | `host` | `none` | true | none |

## Request fields

A Module-bound request carries `target_id` (required), `task` (required), and optionally `focus_id`,
`constraints` and `change_id`. `concorde-tasks` adds the optional `repair_review` and
`repair_task_scope`; `concorde-validate` adds the optional `run_checks`; `concorde-issues` makes
`target_id` and `task` optional and adds its `action` and Issue fields. `concorde-init`,
`concorde-configure` and `concorde-deliver` have their own request shapes, explained by their
owners.

## The `concorde.operations` inventory

This document's metadata holds, under `extensions`, the key `concorde.operations`: a list with one
record per capability, whose fields are exactly `id` (the name without `concorde-`), `kind`,
`public`, `context_selection`, `deterministic`, `public_name`, `uses`, `state` (the request type as
`input`, and `output`) and `profile`. The package check of [Distribution](../distribution/module.md)
reads the declarations from code, builds the same records and reports any missing, unknown or
different record. Agent definitions are not in this inventory; Agents keeps its own.

## Dispatch routes

Request admission calls dispatch's `select_operation` step first. It chooses one route:

| Route | Taken when | What runs |
| --- | --- | --- |
| `relay` | admission relayed a mutation from the primary worktree to the candidate | the candidate's own launcher; its result envelope is adopted unchanged |
| `deliver` | `concorde-deliver` | Delivery's Host service |
| `project` | `concorde-init` or `concorde-configure` | Spec's project services: propose, apply or configure; `describe-policy` is refused with `use_proposal` |
| `prepare_target` | every other capability | the target check below, then the provider route |

The target check resolves `target_id` and `focus_id` against the registry. It treats
`concorde-context-solve`, both reviews and every non-solving `concorde-issues` action as read-only.
For any other capability in execute mode it binds the candidate's owner to the target. When the
candidate already belongs to another Module, the request is admitted as component work only if some
owner's accepted tasks name the target, the owner uses or directly contains it, the owner's plan is
current for its Spec revision, the request has no focus, and its task and constraints equal the work
derived from those tasks. The check then chooses the provider route:

| Provider route | Capability | Provider |
| --- | --- | --- |
| `context_solve` | `concorde-context-solve` | Planning's native assessor preparation |
| `plan` | `concorde-plan` | Planning's native planning workflow preparation |
| `tasks` | `concorde-tasks` | Planning's native task-author preparation |
| `implement` | `concorde-implement` | Implementation's native programmer preparation |
| `review` | `concorde-spec-review`, `concorde-code-review` | Review's native scope workflow preparation |
| `validate` | `concorde-validate` | Validation's Host service |
| `issues` | `concorde-issues` | Issues' Host services, or its native solving workflow |
| `describe_policy` | any bound capability in `describe-policy` mode | a preview of the intended context and permissions; no worker starts |

A native route calls the native preparation service that the launcher's native preparation entry
supplies. Without that service, reached through the bare launcher, the plan, tasks and implement
routes fail with `native_required`.

## Requirements

### req.operations.public-names — One public name per capability

Operations SHALL expose each capability under exactly one public `concorde-` name and expose no other name.

### req.operations.explicit-target — No substituted target

Dispatch SHALL refuse a Module-bound request whose target or focus does not resolve instead of choosing another Module.

### req.operations.caller-sequences — No chained capabilities

No capability SHALL invoke another public capability as a consequence of its own completion.

The user session chooses every next step. A capability that meets a gap returns it as a blocker
instead of starting a repair, and a provider that needs component work returns that work to the
caller. Issue solving runs reviews and validation as steps of its own workflow, as its `USES` declares;
that is declared composition inside one capability, not a chain started by a finished one.

### req.operations.graph-api — Operations are StateGraphs

Every Operation SHALL be a StateGraph built with LangGraph's Graph API and listed in the Operation catalog.

### req.operations.inventory-matches — The inventory mirrors the declarations

The `concorde.operations` inventory SHALL contain exactly one record per capability declaration, equal to the properties that declaration states in code.

### req.operations.state-carries-data — Trusted services stay out of State

An Operation SHALL receive trusted services, such as its Agent launcher and Host, only through its runtime context and never through its State.
