---
audience: shared
---

## Project terms

Your session starts with the project's terms, each defined once in its glossary: use every
term exactly as defined, in Specs, code, the decision log and your reports, and never coin a synonym
for one. A term the task needs that the glossary lacks is a glossary change within the task's
Modules, or an escalation when another Module owns it.

## Spec tooling's errors

Spec tooling's commands, such as `spec-validation`, `registry`, `grant` and `build`, and the Spec
MCP server are the exception to error chains: they refuse with Spec tooling's own error record
(`code`, `message`, `reason`, `location`, `remediation`, `causes`), which is no link, and
`concorde task escalate` refuses it as `--error-file` with `invalid_error`. To escalate one,
translate it into a `component` link and save that in a JSON file: `level` `component`, `actor`
`Spec tooling (concorde <command>)`, the record's `code`, a `detail` holding its message, reason,
location and remediation, `evidence`, `attempts` and `options` empty or what you know, a
`recommendation`, `unhandled` with the reason that fits (`input` for Specs or arguments only you or
the main agent can correct, `environment` otherwise) and its explanation, and as `causes` the
record's causes translated the same way. Then name that file with `--error-file`.
