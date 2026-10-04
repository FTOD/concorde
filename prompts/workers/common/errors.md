---
audience: worker
---

## Reporting an error

When you end `blocked` or `failed`, your `error` is the first link of an **error chain**. The host
adds its own link on top of yours. The host passes both up. Therefore, the main agent, and perhaps
the developer, must be able to act on what you wrote without asking you. Never report a bare
"failed" or a one-line summary. Fill in the following fields:

- `code` is a short snake_case name of the error. Examples include:
  - `spec_gap`
  - `path_outside_boundary`
  - `test_cannot_pass`
- `detail` is the complete description. Describe the following:
  - what you were doing
  - what failed
  - where it failed

    Include the following location details:
    - the Module
    - the document and section
    - the file and line
    - the command
  - the exact message or output

  When any of the following caused the error, quote its relevant output:
  - a check
  - a command
  - a refused tool call
- `evidence` contains the following that show the error:
  - files
  - Spec documents
  - commands
  - outputs
- `attempts`: everything you tried, in order, and what each attempt gave.
- `unhandled` states why you cannot handle the error yourself. `reason` is one of the following:
  - `permission`: you would need a path or tool outside your boundary. A refused read or write is
    always `permission`. When the task itself asks you to change a file your boundary lets you
    only read, a refused read or write is also always `permission`. Name the following:
    - the path
    - the access you lack
    - what you need it for
  - `decision`: someone above you must decide, for example what a Spec should promise.
  - `scope`: though your boundary would allow the fix, the fix lies outside your task or bound Modules.
  - `capability`: you have no means to repair it.
  - `exhausted`: you ran out of what you were allowed, such as turns.
  - `environment`: the environment failed. Examples include a missing tool or a crashed command.
  - `input`: the task you were given contradicts itself or cannot be carried out by anyone.
    An example is two instructions that exclude each other. When a task needs a path your boundary
    withholds, the reason is not `input` but `permission`.

  `explanation` says specifically why, for example which path you would need and what for.
- `options`: what the level above could do, each concrete enough to act on.
- `recommendation`: the option you would choose, and why.

For `ok`, `error` is null.
