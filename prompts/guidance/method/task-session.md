---
audience: shared
---

## Method's Operations

Method's Operations do bounded steps of the task in your task worktree. Its execution commands
validate and deliver the task:

- **Prepare the workers' environment.** A worker writes only files its Modules bind and new files
  inside the directories they bind. A Module binds only files that exist. The work may need a new
  implementation file anywhere else, such as one an `understand` plan lists in `new_files`. In that
  case, create the file yourself before you launch the worker that fills it, or fill it yourself.
  Create it as follows:

  - Give it the least content its format needs to be valid (empty where an empty file is valid).
  - Add it to the `entries` of the right realization in the metadata of the Module it realizes.
  - Check it with `concorde spec-validation`.
  - Commit both together.

  A new Spec document is not such a file. Never create one for a worker. `specify` proposes it.
  The Operation creates it. The Operation registers it in its Module's `owns`. When a path
  already exists, the Operation refuses it.
- **When your plan deserves it, have it reviewed.** `plan_review` is optional: nothing requires it
  before `task-validation` or `delivery`. When your task brief asks for it or a change deserves a
  second reading, run it before any Spec or code changes. Write the plan yourself in a file of
  your task worktree such as `plan.md`. You can start from an `understand` plan. Since
  `delivery` commits every uncommitted change, delete that file before `task-validation`. Each run
  keeps its own copy of the plan it reviewed. Run `concorde run plan_review --plan plan.md`. While
  its verdict is `changes_required`, answer **every** finding. Either accept it and revise the
  plan, or reject it with your reason. Then, until the verdict is `accepted`, run it again with the previous run as `--input` and the
  answers, `--accept <finding> "<how the plan settles it>"` or `--reject <finding> "<why>"`. When the
  reviewer maintains a finding after your rejection, and you still reject it, it is a
  disagreement. For a disagreement, take these steps:

  - Do not run again on it.
  - Escalate it with both positions.
  - State the answer you receive in your next `--reject` or `--accept`.

  A maintained finding whose renewed reasoning convinces you is no disagreement. Accept it and
  revise the plan.
- **Deliver.** `concorde task-validation` shows what would block. `concorde delivery` validates
  the whole workspace again. It creates the delivery commit on the task branch. That commit alone
  marks the task delivered. Where the "Deliver" step above, or "Merging the primary branch", says
  to validate and deliver, these are the commands.

**Reviews.** Where the issues part is installed, `spec_review`, `spec_panel` and `code_review`
report every finding as an Issue, as "Issues" says. Otherwise they keep them in their run result.
You read them there. Either way fixing is later `specify` or `implement` work of your task, never
the review's. The verdict `changes_required` means a blocking finding still stands. A
`code_review` finding of kind `spec-challenge` says the Spec, not the code, is wrong. It is usually
`decision-needed`. Escalate it rather than change the promise. `code_review --scope module`
judges each named Module's whole code against all its Specs. Run it when your task brief asks for
it or after a change large enough to deserve a whole-Module check.
