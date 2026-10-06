---
audience: shared
---

## Operations

Method's Operations and execution commands do bounded work in a bound workspace. Each starts inside
its worktree with that worktree's own `concorde`. Where the coordination part is installed, the
workspace is a task's. In that case, the task session starts them inside the task worktree. Without
that part, nothing in Concorde binds a worktree. In that case, they run in a workspace something
else prepared. Only the reading Operations `understand`, `survey`, `spec_panel`, `code_review` and
`project_review` run anywhere else, unbound (see "Unbound runs"). So does `general` with a task type that writes
nothing or with `--read-only`.

```bash
concorde run understand  --goal "<question>" [--plan]
concorde run plan_review --plan <file> [--input <run-id> --accept|--reject <finding> "<text>"…]
concorde run specify     --intent "<what the Spec should say>"
concorde run implement   --goal "<what to build>" [--input <run-id>]
concorde run test
concorde run spec_panel  [--reviewers <2-5>] [--architects <0-2>]
concorde run code_review   [--scope module]
concorde run project_review [--modules <ids>] [--full] [--parallel <1-8>] [--reviewers <2-5>] [--architects <0-2>]
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
installed, the reviews (`spec_panel`, `code_review`, `project_review`) report their findings as
Issues, as "Issues" says. Otherwise, they keep their findings in their run result, where you read
them.

**Project review.** `project_review` reviews the whole project in one run. Run it unbound in the
primary worktree, in background Bash, when the developer wants to know how the project stands. It
needs no task. It runs these parts:

- The project's structural validation.
- Every configured check of every Module.
- A search for the scenarios no test verifies and the files no Module binds.
- One architecture review of the whole project, by `architect1`, `architect2` and `arch_chair`.
- A Spec panel per Module, by `reviewer1` to `reviewer5` and `chair`, without architects.
- A Module review of each Module's code, by `code_reviewer`.

It skips each panel, code review or architecture review whose Specs and code are unchanged since a
review last judged them. The review record `.concorde/reviews/record.json` keeps what was judged.
The run commits that record on the primary branch itself. Never edit or commit it by hand. A
skipped part's Module takes its outcome from the Issues that stand. `--full` reviews everything
again. `--modules` narrows the per-Module parts. `--architects 0` leaves the architecture review
out. Without the issues part, nothing is skipped. The result gives each Module's outcome, the
project's verdict and the Issues that stand counted by severity and tier. Choose what to fix from
those Issues as "Issues" says. A review of every Module launches several workers per Module.
When only a few Modules changed, the skipping keeps a repeated review cheap.

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
