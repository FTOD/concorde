# Operations scenarios

Concrete situations for the capability catalog, dispatch and the Operation catalog of the
[Operations Module](module.md). The Module-wide obligations are in the [declarations and dispatch reference](catalog.md).

## Capability names

### scenario.operations.execute-unregistered — An unknown name is refused

- GIVEN a name that is not one of the eleven public capability names, such as the Agent name `concorde-planner`, the bare word `plan` or a name that no longer exists
- WHEN the launcher receives an invocation for it
- THEN the launcher returns a blocked result whose first error is `unknown_operation`
- AND it exits with status 3
- BUT no Agent is launched and no project file changes

This follows from [one public name per capability](catalog.md#req.operations.public-names).

## Dispatch

### scenario.operations.unknown-target — A target that does not resolve is refused

- GIVEN a request for a Module-bound capability whose `target_id` names no registered Module, or whose `focus_id` is not a scenario of that Module
- WHEN dispatch checks the target
- THEN the request is refused with `unknown_target` or `invalid_focus`
- BUT no candidate is bound to the target, no other Module is chosen and no worker starts

### scenario.operations.native-without-pi — A native capability needs its Pi preparation

- GIVEN the capability `concorde-plan`, `concorde-tasks` or `concorde-implement`
- WHEN it is invoked through the bare launcher, without the native preparation that the Pi session uses
- THEN admission and the target check run as usual
- AND the provider route fails with `native_required`
- BUT no model runs and no plan, task or code change is accepted

## Operation catalog

### scenario.operations.inspect-catalog — Operations compile for inspection

- GIVEN the Operation catalog
- WHEN a tool builds its Operations for inspection, as the Graph Spec check does
- THEN each builds as a compiled StateGraph whose nodes and edges equal those execution compiles
- AND `terminal_agent_operation` has exactly the nodes `__start__`, `terminal_agent` and `__end__`
- BUT building reads no project file and starts no Agent

### scenario.operations.operation-without-service — An Operation without a trusted service stops

- GIVEN `terminal_agent_operation` compiled without an Agent service in its runtime context
- WHEN it is invoked with valid typed input
- THEN it fails with an error saying that it is inspection only until a trusted native Agent service is supplied
- BUT no model is called and nothing in its State can supply a service
