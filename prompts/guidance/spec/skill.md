---
audience: shared
---

## Project terms

The project defines each of its terms once, in the glossary its root Module declares, and your
session starts with all of them: Claude Code loads the glossary through the import in `CLAUDE.md`.
Use each term exactly with the
meaning its definition gives, with the developer and in task goals, decision logs, escalations,
commit messages and Specs. Keep one word for one meaning: do not coin a synonym for a defined term,
and do not use a term for something its definition does not cover. A word earns a glossary entry
only when it is not common sense (its meaning here is narrower than or different from ordinary
usage) and a Module other than its owner uses it; the root Module's own terms are exempt from the
second condition. Explain any other word in its owner's document where it is first used. When you
need a word that meets this and the glossary lacks it, or a definition no longer fits how the
project works, say so to the developer and change the glossary, by the owner of the term: in a
task where the coordination part is installed, and otherwise as the project changes any other file
once the developer agreed. When the developer uses a term in another sense, point out the difference before acting on
it.

## Specs

Answer questions about the project from the Specs under `specs/` (start at the root Module's
`module.md`). `concorde spec-validation` checks the Specs' structure;
`concorde grant --modules <ids> --type <task type>` shows what a worker of a task type could read
and write. After a change of a Module's `module` block, `concorde registry --write` refreshes the
registry that mirrors them.

You may configure the Spec MCP server for your own session, for example in the project's
`.mcp.json` with the command `concorde spec-mcp`, to ask which Modules exist, what a Module's
context is, which Modules some paths concern and what grant a task type would receive. It answers
from the worktree it is rooted in. Workers never receive it.

Spec tooling's commands, such as `spec-validation`, `registry`, `grant` and `build`, and the Spec
MCP server refuse with Spec tooling's own error record (`code`, `message`, `reason`,
`location`, `remediation`, `causes`), which is no link of an error chain. Without the coordination
part there are no tasks to escalate it in: when you cannot correct its cause yourself, give the
developer the record whole, as it stands, with what you tried. Where the coordination part is
installed, `concorde task escalate` refuses it as `--error-file` with `invalid_error`. To
escalate one there, translate it into a `component` link
and save that in a JSON file: `level` `component`, `actor` `Spec tooling (concorde <command>)`, the
record's `code`, a `detail` holding its message, reason, location and remediation, `evidence`,
`attempts` and `options` empty or what you know, a `recommendation`, `unhandled` with the reason
that fits (`input` for Specs or arguments the sender must correct, `environment` otherwise) and its
explanation, and as `causes` the record's causes translated the same way. Then name that file with
`--error-file`.
