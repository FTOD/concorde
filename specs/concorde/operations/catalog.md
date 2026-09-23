# Catalog and dispatch reference

The exact declarations behind the [Operations entry](module.md): the fields of an Operation
declaration, the catalog mirror in this document's metadata, what the loader refuses, the dispatch
routes, nested child resolution, the Graph catalog, and the requirements and scenarios of
Operations.

## Declarations

Each Operation has one Python module `operations/<name>.py`, bound by the Module that owns the
Operation. Its public name is `concorde-` followed by the module name with `_` replaced by `-`. The
package `operations/__init__.py` lists every declared module name in `OPERATIONS`; the loader imports
exactly those and nothing else. A declaration states these fields:

| Field | Meaning |
| --- | --- |
| `KIND` | `host`, `agent-call` or `pi-workflow`; `graph` is reserved for LangGraph Graph Operations and refused while no route exists |
| `PUBLIC` | `True` when the user session may call the Operation; every cataloged Operation is public today |
| `DETERMINISTIC` | `True` exactly when no path of the Operation calls a model; equal to `KIND == "host"` |
| `OWNER` | the identity of the Module that owns the Operation's behaviour and binds its declaration file |
| `AGENTS` | the ordered Agent steps the Operation runs, each `(agent, phase)`: an Agent name that resolves to an Agent definition, and the [phase](../harness/context/module.md#concept.context.phase) of that step |
| `USES` | the public names of child Operations the Operation may run; empty for all but `concorde-issues` |
| `REQUEST`, `RESPONSE` | the JSON Schemas of the request and response data |
| `REQUEST_VERSION`, `RESPONSE_VERSION` | the positive schema versions under which those schemas are registered |
| capability-declaration fields | the facts that [contract.admission.capability-declaration](../harness/admission/contracts.md#contract.admission.capability-declaration) defines, including the entry point |

The entry point is a string `package.module:function`. For a Host service it names the function that
runs the Operation. For a single Agent call it names the Agent hook of the Operation's only Agent,
and must equal the hook that Agent's definition names. For a pi workflow it names the provider's
workflow hook.

| Capability | `KIND` | `OWNER` | `AGENTS` | `USES` |
| --- | --- | --- | --- | --- |
| `concorde-context-solve` | `agent-call` | `module.planning` | `context_assessor` in `context-solve` | none |
| `concorde-plan` | `pi-workflow` | `module.planning` | `context_assessor` in `context-solve`, then `planner` in `plan` | none |
| `concorde-tasks` | `agent-call` | `module.planning` | `task_author` in `tasks` | none |
| `concorde-implement` | `agent-call` | `module.implementation` | `programmer` in `implementation` | none |
| `concorde-spec-review` | `pi-workflow` | `module.review` | `spec_reviewer` in `spec-review` | none |
| `concorde-code-review` | `pi-workflow` | `module.review` | `code_reviewer` in `code-review` | none |
| `concorde-issues` | `pi-workflow` | `module.issue-solving` | `issue_solver` in `issue-solve` | `concorde-spec-review`, `concorde-code-review`, `concorde-validate` |
| `concorde-validate` | `host` | `module.validation` | none | none |
| `concorde-deliver` | `host` | `module.delivery` | none | none |
| `concorde-init` | `host` | `module.spec` | none | none |
| `concorde-configure` | `host` | `module.harness.admission` | none | none |

The loader registers each `REQUEST` as the typed value `concorde-<name>-request` and each `RESPONSE`
as `concorde-<name>-response`, each at the schema version its declaration states; changing a schema
increments that version.

## Loading

The loader imports each listed declaration once and refuses the whole catalog, naming the
declaration and field, when:

- a listed module is missing, or a module under `operations/` is not listed;
- a field is missing, has the wrong type, or `KIND` is not a routed kind;
- `DETERMINISTIC` disagrees with `KIND`, or a `host` Operation declares Agents, or an `agent-call`
  Operation declares other than exactly one Agent;
- an Agent name has no Agent definition, or a phase is not a phase of Task context;
- a `USES` entry is not a cataloged public name, is the Operation itself, or makes composition cyclic;
- the capability-declaration fields do not satisfy their contract, or an entry point does not
  resolve to a callable;
- a schema does not register as a typed value.

A refused catalog stops the launcher before any request is admitted. Looking up a name the catalog
does not hold returns `unknown_operation`.

## The `concorde.operations` mirror

This document's metadata holds, under `extensions`, the key `concorde.operations`: a list with one
record per declaration, whose fields are exactly `id` (the name without `concorde-`),
`public_name`, `kind`, `public`, `deterministic`, `owner`, `agents` (a list of
`{"agent", "phase"}`) and `uses`. The package check of [Distribution](../distribution/module.md)
builds the same records from the loaded catalog and reports any missing, unknown or different
record. Request and response schemas are not mirrored.

## Dispatch routes

Request admission calls dispatch with the admitted request and its declaration. Dispatch chooses one
route by `KIND`:

| Route | Kind | What runs |
| --- | --- | --- |
| `host` | `host` | the declared entry point, with the admitted request and the Host's services; its return value is the Operation's response |
| `agent-call` | `agent-call` | the native driver of Agent execution, given the admitted request and the declared Agent hook; it returns a prepared Agent call, or a preview in `describe-policy` mode |
| `pi-workflow` | `pi-workflow` | the native driver, given the admitted request and the declared workflow hook; it returns a prepared workflow call, a Host result that needs no workflow, or a preview |

The `agent-call` and `pi-workflow` routes require the native driver that the Pi session's native
preparation entry supplies. Without it, reached through the bare launcher, they fail with
`native_required` before any Agent hook or workflow step runs; only a `pi-workflow` request that its
workflow hook's in-place service answers, such as an Issue bookkeeping action, is served as a Host
result there. Dispatch passes `describe-policy` mode through unchanged; the
entry point or native driver produces the preview. Dispatch performs no target, workspace or stage
check of its own.

## Child Operations

A running Operation reaches another only through dispatch's child entry, giving its own public
name, the child's public name and the child's request. Dispatch:

1. refuses with `unknown_operation` when either name is not cataloged;
2. refuses with `undeclared_operation` when the child is not in the parent's `USES`;
3. otherwise hands the child request to Request admission as a new capability request, with the
   parent's configuration and workspace, and returns the child's result envelope unchanged.

The child is admitted, dispatched and recorded exactly like a direct request. A parent never passes
a child a service, a context or a workspace that admission would not grant it.

## Graph catalog

The Graph catalog maps each compiled Graph name to a factory that builds the Graph with inert nodes
and no runtime services. It holds one entry, `terminal_agent_operation`, built from Agent
execution's Terminal Agent Operation factory. The catalog also returns a Graph's topology: its node
names and its edges with their source, target and whether they are conditional, in the form the
Graph Spec check reads.

## Requirements

### req.operations.public-names — One public name per capability

Operations SHALL expose each public Operation under exactly one `concorde-` name and expose no other name.

### req.operations.caller-sequences — No chained capabilities

No Operation SHALL invoke another Operation as a consequence of its own completion.

The user session chooses every next step. An Operation that meets a gap returns it as a blocker
instead of starting a repair, and a provider that needs component work returns that work to the
caller. Issue solving runs reviews and validation as steps of its own workflow through declared
child requests; that is composition inside one Operation, not a chain started by a finished one.

### req.operations.declared-entry — Providers are reached only through declarations

Dispatch SHALL reach a provider's behaviour only through the entry point that the Operation's declaration names.

Dispatch and the loader import no provider module by name. A static check of the dispatch and
loader sources finds no import of a provider package.

### req.operations.declared-children — Only declared children run

Dispatch SHALL run a child Operation only when the parent's declaration lists it in `USES`.

### req.operations.catalog-valid — Only valid declarations are loaded

The catalog loader SHALL refuse the whole catalog when any declaration violates a rule listed under [Loading](#loading).

### req.operations.inventory-matches — The mirror equals the declarations

The `concorde.operations` mirror SHALL contain exactly one record per declaration, equal to the fields that declaration states.

### req.operations.graph-catalog-complete — Every Graph is cataloged

The Graph catalog SHALL list every LangGraph Graph that Concorde compiles, built without runtime services.

## Scenarios

### scenario.operations.execute-unregistered — An unknown name is refused

- GIVEN a name that is not a cataloged public name, such as the Agent name `concorde-planner`, the bare word `plan` or a name that does not exist
- WHEN the launcher receives a capability request for it
- THEN the result envelope is blocked with the error `unknown_operation`
- BUT no Agent is launched and no project file changes

### scenario.operations.native-without-pi — A native Operation needs the native driver

- GIVEN an admitted request for `concorde-plan`, `concorde-tasks` or `concorde-implement`
- WHEN it is dispatched through the bare launcher, without the native driver the Pi session supplies
- THEN dispatch refuses it with `native_required`
- BUT no hook runs, no model runs and no plan, task or code change is accepted

### scenario.operations.host-dispatch — A Host service runs its declared entry point

- GIVEN an admitted request for `concorde-validate`
- WHEN dispatch routes it
- THEN it calls the entry point that the `concorde-validate` declaration names and returns that function's response as the Operation's output
- AND no native driver is involved

### scenario.operations.child-declared — A declared child runs as its own request

- GIVEN a running `concorde-issues` solve whose declaration lists `concorde-spec-review` in `USES`
- WHEN it asks dispatch to run a Spec review of a Module
- THEN the child request passes Request admission as a new capability request
- AND the child's result envelope is returned to the parent unchanged

### scenario.operations.child-undeclared — An undeclared child is refused

- GIVEN a running Operation whose declaration does not list `concorde-deliver` in `USES`
- WHEN it asks dispatch to run `concorde-deliver`
- THEN dispatch refuses with `undeclared_operation`
- BUT nothing is admitted for the child and no worktree changes

### scenario.operations.invalid-declaration — An invalid declaration stops the catalog

- GIVEN a declaration whose Agent name has no Agent definition, or whose kind is `graph`
- WHEN the launcher loads the catalog
- THEN the loader refuses the catalog and names the declaration and the offending field
- BUT no request is admitted

### scenario.operations.inspect-catalog — Graphs compile for inspection

- GIVEN the Graph catalog
- WHEN a tool builds its Graphs for inspection, as the Graph Spec check does
- THEN each builds as a compiled `StateGraph` whose nodes and edges equal those execution compiles
- AND `terminal_agent_operation` has exactly the nodes `__start__`, `terminal_agent` and `__end__`
- BUT building reads no project file and starts no Agent

### scenario.operations.operation-without-service — A cataloged Graph built for inspection cannot run a model

- GIVEN `terminal_agent_operation` built by the Graph catalog, without any service in its runtime context
- WHEN it is invoked with valid typed input
- THEN it fails with an error saying that it is inspection only until a trusted native Agent service is supplied
- BUT no model is called and nothing in its State can supply a service
