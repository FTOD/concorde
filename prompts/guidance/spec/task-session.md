---
audience: shared
---

## Project terms

Your session starts with the project's terms, each defined once in its glossary.
Use every term exactly as defined, in Specs, code, the decision log and your reports.
Never coin a synonym for one.
A term the task needs that the glossary lacks is a glossary change within the task's Modules.
When another Module owns that term, it is an escalation instead.

## Spec tooling's errors

Spec tooling's commands, such as `spec-validation`, `registry`, `grant` and `build`, and the Spec
MCP server are the exception to error chains.
They refuse with Spec tooling's own error record (`code`, `message`, `reason`, `location`,
`remediation`, `causes`).
This record is no link.
`concorde task escalate` refuses it as `--error-file` with `invalid_error`.
To escalate one, translate it into a `component` link.
Save that link in a JSON file with these fields:

- `level` set to `component`.
- `actor` set to `Spec tooling (concorde <command>)`.
- `code` set to the record's `code`.
- `detail` holding the record's message, reason, location and remediation.
- `evidence`, `attempts` and `options` empty or what you know.
- `recommendation` holding a recommendation.
- `unhandled` holding the reason that fits and its explanation.
- `causes` holding the record's causes translated the same way.

For `unhandled`, use `input` for Specs or arguments only you or the main agent can correct.
Otherwise, use `environment`.
Then name that file with `--error-file`.
