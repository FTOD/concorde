---
audience: shared
---

## Operations

Method's Operations and execution commands do a task's work in its workspace, each started by the
task session inside the task worktree with that worktree's own `concorde`:

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

A typical order is `understand` to assess and plan, optionally `plan_review` of the plan the
task session writes, which the session answers finding by finding over several runs until the
verdict is `accepted`, `specify` when the Spec must change first, `implement` and `test`, the
reviews when the change deserves them, then `task-validation` and
`delivery`, which validates the whole workspace again and creates the delivery commit on the task
branch; only that commit marks the task delivered, while the task session may commit verified
steps before it. The task session prepares the workers' environment: a worker writes only the
files its Modules bind and new files inside the directories they bind, and a Module binds only
files that exist, so the task session itself creates any other new implementation file the work
needs, with the least content its format needs to be valid, and binds it to its Module before it
launches the worker that fills it. A new Spec document is not prepared this way: `specify` proposes
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
a project whose code came before its Specs, describe that code with the `brownfield` workflow: open
a task bound to the root Module (or to the Module to split) and have its task session run it with
`module` set to that Module. It surveys the code, scaffolds child Modules, describes each Module's
code with `code_to_spec`, reviews, validates and delivers. Its workers write down behaviour as it
is and report doubtful intent as open questions instead of promises; show the developer the open
questions, the decisions and the checks the survey proposed, which are never configured
automatically: in a task, add each one the developer accepts to the checks file of the Module it
checks, `.concorde/checks/<module id>.json`, without its `module` and `reason`. Splitting a
created Module further is a new task running the workflow on that Module. Never use `code_to_spec`
for a project that is already specified: there, a missing promise is a Spec gap for `specify`.
