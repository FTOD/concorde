---
audience: shared
---

## Project terms

The project defines each of its terms once, in the glossary its root Module declares.
Your session starts with all of them. Claude Code loads the glossary through the import in
`CLAUDE.md`. Use each term exactly with the meaning its definition gives in these contexts:

- With the developer.
- In task goals.
- In decision logs.
- In escalations.
- In commit messages.
- In Specs.

Keep one word for one meaning. Do not coin a synonym for a defined term.
Do not use a term for something its definition does not cover.
Only when a word is not common sense and a Module other than its owner uses it does the word
earn a glossary entry. Here, not common sense means that its meaning is narrower than or different from
ordinary usage.
The root Module's own terms are exempt from the second condition.
Explain any other word in its owner's document where it is first used.
When the glossary lacks a needed word that meets these conditions, or a definition no longer fits
how the project works, take these steps:

- Say so to the developer.
- Where the coordination part is installed, change the glossary by the owner of the term in a task.
- Otherwise, once the developer agrees, change the glossary by the owner of the term as the project
  changes any other file.

When the developer uses a term in another sense, point out the difference before acting on it.

## Specs

Answer questions about the project from the Specs under `specs/`.
Start at the root Module's `module.md`.
`concorde spec-validation` checks the Specs' structure.
`concorde grant --modules <ids> --type <task type>` shows what a worker of a task type could read
and write. After a change of a Module's `module` block, `concorde registry --write` refreshes the
registry that mirrors them.

You may configure the Spec MCP server for your own session, for example in the project's
`.mcp.json` with the command `concorde spec-mcp`, to ask:

- Which Modules exist.
- What a Module's context is.
- Which Modules some paths concern.
- What grant a task type would receive.

It answers from the worktree it is rooted in. Workers never receive it.

Spec tooling's commands, such as `spec-validation`, `registry`, `grant` and `build`, and the Spec
MCP server refuse with Spec tooling's own error record (`code`, `message`, `reason`, `location`,
`remediation`, `causes`). This record is no link of an error chain.
Without the coordination part there are no tasks to escalate it in.
Without that part, when you cannot correct its cause yourself, give the developer the record
whole, as it stands, with what you tried.
Where the coordination part is installed, `concorde task escalate` refuses it as `--error-file`
with `invalid_error`.
To escalate one there, translate it into a `component` link.
Save that link in a JSON file with these fields:

- `level` set to `component`.
- `actor` set to `Spec tooling (concorde <command>)`.
- `code` set to the record's `code`.
- `detail` holding the record's message, reason, location and remediation.
- `evidence` empty or what you know.
- `attempts` empty or what you know.
- `options` empty or what you know.
- `recommendation` holding a recommendation.
- `unhandled` holding the reason that fits and its explanation.
- `causes` holding the record's causes translated the same way.

For `unhandled`, use `input` for Specs or arguments the sender must correct.
Otherwise, use `environment`.
Then name that file with `--error-file`.
