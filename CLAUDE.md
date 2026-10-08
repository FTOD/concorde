# Developing Concorde with Claude Code

This is Concorde's own source checkout. Before any work, load two skills with the Skill tool and
follow both in full: `concorde`, how the main agent and task sessions work in every Concorde
project, and `concorde-development`, what is particular to developing Concorde here. The build
renders them as `generated/skills/<name>/SKILL.md`, which the untracked links
`.claude/skills/<name>`, made by `python3 scripts/development/init-references.py`, point to; in a
worktree not prepared yet, run that script and `python3 scripts/concorde.py build` first, and read
those files directly when the Skill tool does not offer them. In this checkout `concorde` means
`python3 scripts/concorde.py` of the worktree you are in.

The rules that hold before the skills are loaded:

- **The main agent** stays in the primary worktree and never works inside a task worktree: every
  change of Spec meaning or code behaviour is a task (`task open`) handed to a task session
  (`task session <task> --main <its session name>`, after the task's brief is recorded in its
  decision log), even a single task. The only change it makes in the primary worktree itself
  is a small change, such as a typo or a one-line fix, that the developer approved after it said
  what it would change and why it is small, besides `registry --write` and a commit of
  `.concorde/workers.json` alone. It merges only with `task merge <task> --check "python3
  scripts/concorde.py build" --check "python3 scripts/concorde.py spec-validation"`, in background
  Bash, never with `git merge`. After dispatching tasks it shows the developer each task's name
  with its goal in one line and reports on the tasks by those names.
- **A task session** works only inside its task worktree, with that worktree's own
  `python3 scripts/concorde.py`, and follows its first prompt. It prepares that worktree itself
  before anything else: `python3 scripts/development/init-references.py`, `uv sync --locked
  --group dev`, `npm --prefix docsite ci` and `python3 scripts/concorde.py build`. It never asks the developer in
  place: it gathers every decision it needs and escalates them together to the main agent. It
  never merges into the primary branch; its only merge is the primary branch into its task branch
  when the main agent asks for it after a merge conflict or a `concorde update`.
- **Everyone** uses each project term exactly as the glossary below defines it, appends every
  decision taken without the developer and every non-`ok` result to the task's decision log, reads
  error chains in full, runs long commands in background Bash and never waits by polling with
  `sleep`.

The project's terms, which the "Project terms" rule of the `concorde` skill asks you to use exactly
as defined, are loaded from its glossary: @specs/concorde/glossary.json
