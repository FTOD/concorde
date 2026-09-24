---
audience: worker
---

## Reporting an error

When you end `blocked` or `failed`, your `error` is the first link of an **error chain**: the host
adds its own link on top of yours and passes both up, so the main agent, and perhaps the developer,
must be able to act on what you wrote without asking you. Never report a bare "failed" or a
one-line summary. Fill in:

- `code`: a short snake_case name of the error, such as `spec_gap`, `path_outside_boundary` or
  `test_cannot_pass`.
- `detail`: the complete description: what you were doing, what failed, where (the Module, the
  document and section, the file and line, the command), and the exact message or output. When a
  check, a command or a refused tool call caused it, quote its relevant output.
- `evidence`: the files, Spec documents, commands and outputs that show it.
- `attempts`: everything you tried, in order, and what each attempt gave.
- `unhandled`: why you cannot handle the error yourself. `reason` is one of `permission` (you would
  need a path or tool outside your boundary), `decision` (someone above you must decide, for
  example what a Spec should promise), `scope` (the fix lies outside your task or bound Modules),
  `capability` (you have no means to repair it), `exhausted` (you ran out of what you were
  allowed), `environment` (the environment failed: a missing tool, a crashed command) or `input`
  (the task you were given is contradictory or invalid). `explanation` says specifically why, for
  example which path you would need and what for.
- `options`: what the level above could do, each concrete enough to act on; `recommendation`: the
  option you would choose, and why.

For `ok`, `error` is null.
