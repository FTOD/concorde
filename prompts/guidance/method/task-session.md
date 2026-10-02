---
audience: shared
---

## Method's Operations

Method's Operations do bounded steps of the task in your task worktree, and its execution
commands validate and deliver it:

- **Prepare the workers' environment.** A worker writes only files its Modules bind and new files
  inside the directories they bind, and a Module binds only files that exist. When the work needs
  a new implementation file anywhere else, such as one an `understand` plan lists in `new_files`,
  create it yourself before you launch the worker that fills it, or fill it yourself: give it the
  least content its format needs to be valid (empty where an empty file is valid), add it to the
  `entries` of the right realization in the metadata of the Module it realizes, check it with
  `concorde spec-validation` and commit both together. A new Spec document is not such a file:
  never create one for a worker, since `specify` proposes it and the Operation creates it and
  registers it in its Module's `owns`, refusing a path that already exists.
- **Have your plan reviewed when it deserves it.** `plan_review` is optional: nothing requires it
  before `task-validation` or `delivery`; run it when your task brief asks for it or a change
  deserves a second reading before any Spec or code changes. Write the plan yourself, possibly
  starting from an `understand` plan, in a file of your task worktree such as `plan.md`, and delete
  that file before `task-validation`, since `delivery` commits every uncommitted change and each run
  keeps its own copy of the plan it reviewed. Run `concorde run plan_review --plan plan.md`. While
  its verdict is `changes_required`, answer **every** finding: accept it and revise the plan, or
  reject it with your reason, then run it again with the previous run as `--input` and the answers,
  `--accept <finding> "<how the plan settles it>"` or `--reject <finding> "<why>"`, until the
  verdict is `accepted`. A finding the reviewer maintains after you rejected it, and that you still
  reject, is a disagreement: do not run again on it, escalate it with both positions, and state the
  answer you receive in your next `--reject` or `--accept`. A maintained finding whose renewed
  reasoning convinces you is no disagreement: accept it and revise the plan.
- **Deliver.** `concorde task-validation` shows what would block; `concorde delivery` validates
  the whole workspace again and creates the delivery commit on the task branch, which alone marks
  the task delivered. Where the "Deliver" step above, or "Merging the primary branch", says to
  validate and deliver, these are the commands.

**Reviews.** `spec_review`, `spec_panel` and `code_review` report every finding as an Issue where
the issues part is installed, as "Issues" says, and otherwise keep them in their run result,
where you read them. Either way fixing is later `specify` or `implement` work of your task, never
the review's, and the verdict `changes_required` means a blocking finding still stands. A
`code_review` finding of kind `spec-challenge` says the Spec, not the code, is wrong: it is usually
`decision-needed`, so escalate it rather than change the promise. `code_review --scope module`
judges each named Module's whole code against all its Specs; run it when your task brief asks for
it or after a change large enough to deserve a whole-Module check.
