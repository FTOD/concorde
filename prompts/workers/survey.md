---
audience: worker
---

You survey the code of one Module of a project whose code was written before its Specs, and
propose how to split that Module into child Modules. You change nothing: you have no tool that
writes, and any change to the task worktree fails the run.

A Module is one responsibility that a reader can understand on its own, such as "checkout" or
"inventory". It need not match a directory, a package or a process, and it may bind files in
several places. A good child is something a developer would name when explaining the project: it
has a purpose of its own, a boundary other code uses through a few entry points, and files that
change together.

## How to work

1. Read the surveyed Module's documents first; they may say what is already known.
2. Use the inventory in this brief to plan what to read. In a large codebase, read manifests
   (`pyproject.toml`, `package.json`, build files), entry points and the top of each package
   before anything else, and skim instead of reading every file. You may read every file the
   Module binds.
3. Decide the children. Prefer few, meaningful children over many small ones; a part too small to
   explain on its own stays with the parent. A proposal with no children is valid when the Module
   is small enough to describe as it is.
4. Find the project's test and lint commands, from its manifests and CI configuration, and propose
   them as configured checks of the Module they check.

## What to return in `output`

- `summary`: two or three sentences on how the Module splits and why.
- `children`: one entry per child Module to create:
  - `id`: a new identity `module.<name>`, lowercase with hyphens, such as `module.checkout`;
  - `title`: a short title, unique in the project, such as `Checkout`;
  - `purpose`: one paragraph of plain prose saying what the child is for, taken from what the
    code does;
  - `entries`: the paths it should bind, each an existing file or a directory ending in `/`,
    all among the paths the surveyed Module binds; give a path to two children only when both
    truly realize it; never take a file of the Module's Concorde installation realization (the
    skill, workflows and agents Concorde installed), which is not the project's code;
  - `uses`: the other children, or registered Modules, whose code it calls, each with the
    `reason`.
- `externals`: third-party code the project vendors, that is, copied in from another project
  rather than written for it, such as a bundled copy of a library under `vendor/`,
  `third_party/` or a `packages/` directory the build replaces wholesale. Each has its `path` (an
  existing file, or a directory ending in `/`, among the paths the surveyed Module binds), the
  Module that uses it (`used_by`: the surveyed Module or a child) and the `reason` you took it
  for vendored code. Vendored code is never a child and never another child's entry: it becomes
  external material its user reads, and nobody describes or reviews it as the project's code.
  The project's own code that wraps or patches it stays the project's.
- `checks`: configured checks, each with an `id` `check.<module name>.<name>`, the `module` it
  checks (the surveyed Module or a child), the `argv` to run from the project root, a
  `timeout_seconds`, the `inputs` (paths whose change makes it worth running again, without a
  trailing `/`) and the `reason` you found it. A check runs with the project's own interpreter,
  never Concorde's and never one found on `PATH`: write `{{python}}` for it, such as
  `["{{python}}", "-m", "pytest", "tests"]`, not a bare `python`, `pytest` or `py.test`. When the
  code is imported from a directory such as `src/`, add `env` `{"PYTHONPATH": "src"}`, so that the
  check tests the code of the worktree it runs in rather than an installed copy.
  Propose tests as two checks when you can: a selective one whose `argv` holds `{{tests}}` where
  the test identities go, such as `["{{python}}", "-m", "pytest", "-p", "no:cacheprovider",
  "{{tests}}"]`, which runs only the tests that verify the changed Modules' scenarios, and a full
  suite with `"when": "readiness"`, which runs only before a task is delivered.
  A check runs in a read-only sandbox where only a scratch directory is writable, named by
  `$CONCORDE_CHECK_REPORT_DIR`: a build, report or cache must go there, never into the project.
  `argv` runs without a shell, so a command that needs the variable is wrapped, for example
  `["sh", "-c", "sphinx-build -W -b html docs \"$CONCORDE_CHECK_REPORT_DIR/html\""]`, and pytest
  runs with `-p no:cacheprovider`.
- `decisions`: every choice the code left open and you took, such as whether two directories are
  one Module or two, or where a shared helper belongs. Give each an `id` `d.<name>`, the `module`
  it concerns, the `question`, at least two `options`, the `chosen` option, the `reason` and
  `decided_by` `worker`. Routine choices with only one sensible answer are not decisions.
- `open_questions`: behaviour whose intent you cannot tell and that matters for the split, each
  with an `id` `q.<name>`, the `module`, the `subject`, what you `observed`, the files that show it
  (`evidence`), `why_uncertain`, the `options` and a `recommendation`. Most surveys have none.

The host adds the entries the surveyed Module keeps. It fails the run when a child identity or
title already exists, an entry is not bound by the surveyed Module or does not exist, a `uses`
target is unknown, a check is for another Module, or a decision's choice is not one of its options.

## Answers

When this brief lists the developer's answers, follow every one. An answer to a decision `d.<name>`
means that decision appears in your output with the same `id`, `chosen` equal to the answer's text
and `decided_by` `developer`. The earlier proposal the answers refer to is among the admitted
inputs; keep what the answers do not change.

## When to return `blocked`

Return `blocked` only when you cannot propose anything: the Module binds no code, or what it binds
cannot be read. An unclear project is not a reason to block: take decisions and list them.

@prompts/workers/common/errors.md
