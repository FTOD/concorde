# Developing Concorde with pi

This is Concorde's own source checkout. Before any work, read two skills in full and follow both:
`concorde`, how the main agent and task sessions work in every Concorde project, and
`concorde-development`, what is particular to developing Concorde here. The build renders them as
`generated/skills/<name>/SKILL.md`, and `.pi/settings.json` loads them once pi trusts the project
(`/skill:concorde`, `/skill:concorde-development`); in a worktree not built yet, run
`python3 scripts/concorde.py build` first, and read those files with the read tool when pi does not
offer them. In this checkout `concorde` means `python3 scripts/concorde.py` of the worktree you are
in. `.pi/settings.json` also loads Concorde's pi extension from `src/concorde/main_session/`,
which adds the project's terms from `specs/concorde/glossary.json` to every prompt and gives the
main agent the `concorde_run` and `concorde_task_session` tools.

The rules that hold before the skills are loaded:

- **The main agent** stays in the primary worktree and never works inside a task worktree: every
  change of Spec meaning or code behaviour is a task (`task open`) handed to a task session with
  the `concorde_task_session` tool (after `python3 scripts/development/init-references.py` in the
  task worktree and the task's brief recorded in its decision log), even a single task. A shell
  `cd` does not enter a task. The only change it makes in the primary worktree itself is a small
  change, such as a typo or a one-line fix, that the developer approved after it said what it would
  change and why it is small, besides `registry --write` and a commit of `.concorde/workers.json`
  alone. It merges only with `task merge <task> --check "python3 scripts/concorde.py build"
  --check "python3 scripts/concorde.py spec-validation"`, in bash without a timeout, never with
  `git merge`. After dispatching tasks it shows the developer each task's name with its goal in
  one line and reports on the tasks by those names.
- **A task session** works only inside its task worktree, with that worktree's own
  `python3 scripts/concorde.py` run in the foreground without a timeout, and follows its first
  prompt. It never asks the developer in place: it gathers every decision it needs and ends its
  round `escalated` with all of them. It never merges into the primary branch; its only merge is
  the primary branch into its task branch when the main agent asks for it after a merge conflict.
- **Everyone** uses each project term exactly as the glossary defines it, appends every decision
  taken without the developer and every non-`ok` result to the task's decision log, reads error
  chains in full and never waits by polling with `sleep`.
