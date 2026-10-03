---
audience: shared
---

## Operations

Method's Operations and execution commands do bounded work in a bound workspace, each started
inside its worktree with that worktree's own `concorde`. Where the coordination part is installed,
the workspace is a task's and the task session starts them inside the task worktree. Without that
part nothing in Concorde binds a worktree: they run in a workspace something else prepared, and
only the reading Operations `understand`, `survey`, `spec_review`, `spec_panel` and `code_review`
run anywhere else, unbound (see "Unbound runs"):

```bash
concorde run understand  --goal "<question>" [--plan]
concorde run plan_review --plan <file> [--input <run-id> --accept|--reject <finding> "<text>"…]
concorde run specify     --intent "<what the Spec should say>"
concorde run implement   --goal "<what to build>" [--input <run-id>]
concorde run test
concorde run spec_review
concorde run code_review   [--scope module]
concorde task-validation
concorde delivery
```

A typical order is `understand` to assess and plan, optionally `plan_review` of the plan written
for the work, answered finding by finding over several runs until the verdict is `accepted`,
`specify` when the Spec must change first, `implement` and `test`, the reviews when the change
deserves them, then `task-validation` and `delivery`, which validates the whole workspace again and
creates the delivery commit on the workspace's branch, a task branch where the coordination part
is installed; only that commit marks the workspace delivered, while whoever works in it may commit
verified steps before it. Whoever works in the workspace (the task session, where the coordination
part is installed) prepares the workers' environment: a worker writes only the files its Modules
bind and new files inside the directories they bind, and a Module binds only files that exist, so
any other new implementation file the work needs is created first, with the least content its
format needs to be valid, and bound to its Module before the worker that fills it is launched. A new Spec document is not prepared this way: `specify` proposes
it and the Operation creates it and registers it in its Module's `owns`.

`code_review` judges a task's change since its base. With `--scope module` it is a **Module
review** instead: one reviewer per named Module judges that Module's whole code and tests against
all of its Specs, and may challenge a Spec requirement it finds unreasonable or unrealizable. Use it
for a whole-Module check after a large change, on code written before its Specs or by an earlier
version, or on a project just adopted with the brownfield workflow; run unbound in the primary
worktree it needs only `--modules`. The reviews (`spec_review`, `spec_panel`, `code_review`) report
their findings as Issues where the issues part is installed, as "Issues" says, and otherwise keep
them in their run result, where you read them.

**Brownfield.** Concorde works Spec first. Only when Concorde was just installed and initialized in
a project whose code came before its Specs, describe that code with the `brownfield` workflow, run
with `module` set to the root Module (or to the Module to split) in a workspace bound to that
Module: where the coordination part is installed, open a task bound to it and have its task
session run the workflow. It surveys the code, scaffolds child Modules, describes each Module's
code with `code_to_spec`, reviews, validates and delivers. Its workers write down behaviour as it
is and report doubtful intent as open questions instead of promises; show the developer the open
questions, the decisions and the checks the survey proposed, which are never configured
automatically: in a task (or, without the coordination part, a workspace), add each one the
developer accepts to the checks file of the Module it checks, `.concorde/checks/<module id>.json`,
without its `module` and `reason`. Splitting a created Module further is a new run of the workflow
on that Module, in a task of its own where the coordination part is installed. Never use `code_to_spec`
for a project that is already specified: there, a missing promise is a Spec gap for `specify`.
