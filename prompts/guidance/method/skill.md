---
audience: shared
---

## Operations

Method's Operations and execution commands do bounded work in a bound workspace. Each starts inside
its worktree with that worktree's own `concorde`. Where the coordination part is installed, the
workspace is a task's. In that case, the task session starts them inside the task worktree. Without
that part, nothing in Concorde binds a worktree. In that case, they run in a workspace something
else prepared. Only the reading Operations `understand`, `survey`, `spec_panel` and `code_review`
run anywhere else, unbound (see "Unbound runs"). So does `general` with a task type that writes
nothing or with `--read-only`.

```bash
concorde run understand  --goal "<question>" [--plan]
concorde run plan_review --plan <file> [--input <run-id> --accept|--reject <finding> "<text>"…]
concorde run specify     --intent "<what the Spec should say>"
concorde run implement   --goal "<what to build>" [--input <run-id>]
concorde run test
concorde run spec_panel  [--reviewers <2-5>] [--architects <0-2>]
concorde run code_review   [--scope module]
concorde run general     --type <task type> (--instruction "<text>" | --instruction-file <file>) [--read-only]
concorde task-validation
concorde delivery
```

A typical order is:

- Run `understand` to assess and plan.
- Optionally run `plan_review` of the plan written for the work. Answer it finding by finding over
  several runs until the verdict is `accepted`.
- When the Spec must change first, run `specify`.
- Run `implement`.
- Run `test`.
- When the change deserves them, run the reviews.
- Run `task-validation`.
- Run `delivery`.

**Free-form work.** For bounded AI work that no other Operation fits, run `general`. Examples
are a restyle of one document, a rename across Specs or a question that needs the code. Never
start `pi`, `claude` or another agent program yourself for such work. A program you start takes
your own configuration: your packages, your tools and the project's `CLAUDE.md`. Nothing bounds
its writes. `general` runs its worker through the worker harness, under the grant of the task type
`--type` names, on the model the worker configuration chooses. A second worker, `reviewer`, then
judges the result against your instruction, changing nothing. For a rewrite, it checks that the
meaning is kept. Read its findings and its verdict in the run result. Keep, revise or revert the
change yourself: the reviewer never fixes it. The run result names the changed files, the diff
and the earlier content of each changed file.

`delivery` validates the whole workspace again. It creates the delivery commit on the workspace's
branch. Where the coordination part is installed, this is a task branch. Only that commit marks the
workspace delivered. Before it, whoever works in the workspace may commit verified steps.

Whoever works in the workspace prepares the workers' environment. Where the coordination part is
installed, this is the task session. A worker writes only the files its Modules bind and new files
inside the directories they bind. A Module binds only files that exist. Before launching a worker
to fill any other new implementation file the work needs, whoever works in the workspace takes
these steps:

- Create the file with the least content its format needs to be valid.
- Bind the file to its Module.

Whoever works in the workspace does not prepare a new Spec document this way. `specify` proposes
it. The Operation creates it. The Operation registers it in its Module's `owns`.

`code_review` judges a task's change since its base. With `--scope module` it is a **Module
review** instead: one reviewer per named Module judges that Module's whole code and tests against
all of its Specs. The reviewer may challenge a Spec requirement it finds unreasonable or
unrealizable. Use it for a whole-Module check after a large change, on code written before its
Specs or by an earlier version, or on a project just adopted with the brownfield workflow.

When run unbound in the primary worktree, it needs only `--modules`. Where the issues part is
installed, the reviews (`spec_panel`, `code_review`) report their findings as Issues,
as "Issues" says. Otherwise, they keep their findings in their run result, where you read them.

**Brownfield.** Concorde works Spec first. Only when Concorde was just installed and initialized in
a project whose code came before its Specs, describe that code with the `brownfield` workflow.
Run it with `module` set to the root Module (or to the Module to split) in a workspace bound to that
Module. Where the coordination part is installed, open a task bound to it and have its task session
run the workflow. The workflow takes these steps:

- Survey the code.
- Scaffold child Modules.
- Describe each Module's code with `code_to_spec`.
- Review.
- Validate.
- Deliver.

Its workers write down behaviour as it is. They report doubtful intent as open questions instead of
promises. Show the developer the following:

- The open questions.
- The decisions.
- The checks the survey proposed.

The checks are never configured automatically. In a task (or, without the coordination part, a
workspace), add each check the developer accepts to `.concorde/checks/<module id>.json` for the
Module it checks. Omit its `module` and `reason`. Splitting a created Module
further is a new run of the workflow on that Module. Where the coordination part is installed, this
runs in a task of its own. For a project that is already specified, never use `code_to_spec`.
There, a missing promise is a Spec gap for `specify`.
