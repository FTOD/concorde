# Concorde

Concorde runs agent work from explicit, self-contained Specs. Every task has one selected target,
one reproducible context and a host-enforced permission boundary.

Domain is a business/problem scope. Service and Module are component kinds: a Service offers Features
through precise exchanges; a Module offers APIs. Domain scope nesting, component composition and
multi-scope participation are independent relationships. Every target registers its complete ordered
Markdown collection; filenames are unrestricted and no ancestor/collaborator context is inherited.

The shipped Protocol principles apply to every consumer project. The host injects the pinned global
principles plus the selected kind definition, starts a fresh agent process per stage and exposes code
only during implementation. Missing task-relevant facts yield Spec incomplete, not a search for more
files. See [the principles](protocol/principles.md) and [Concorde's own system Spec](specs/concorde/system.md).

## Install and initialize

The installer distributes canonical runtime, 22 paired public Operations, 6 internal roles and 9
Markdown templates to Codex or Claude. Check `python scripts/install-concorde.py --help` for installation
administration. Project task inputs use JSON, not positional or flag arguments. Install into a Git
project, then invoke the paired init entry in an isolated worktree (or use the trusted host's explicit
primary-worktree authorization). The Operation host reports any newly created worktree in its result.

```json
{
  "type_id": "concorde-operation-invocation",
  "schema_version": 2,
  "operation_id": "concorde-init",
  "mode": "execute",
  "configuration": {"type_id":"concorde-operation-configuration","schema_version":1,"data":{"integration":"codex","enforcement":"native"}},
  "input": {"type_id":"concorde-init-request","schema_version":1,"data":{"action":"propose","name":"My project","configuration":{"type_id":"concorde-operation-configuration","schema_version":1,"data":{"integration":"codex","enforcement":"native"}}}}
}
```

Send the JSON on stdin to `python .concorde/framework/operations/concorde-init/operation.py`.
Review the returned proposal, then send action apply and that complete proposal. Initialization creates
an honest Domain stub; supply business rules and register Services/Modules before implementation.
`.concorde/config.json` pins the Protocol and references `.concorde/specs.json`; that registry explicitly
records document members, independent relationships, local Feature/API IDs, implementation ownership
and deterministic checks. Arbitrary nearby Markdown is not context.

## Run a change

Send this invocation on stdin to the matching installed paired executable:

```json
{
  "type_id":"concorde-operation-invocation","schema_version":2,
  "operation_id":"concorde-standard-dev-loop","mode":"execute","configuration":null,
  "input":{"type_id":"concorde-standard-dev-loop-request","schema_version":1,
    "data":{"target_id":"service.transfer","task":"Implement the specified transfer contract"}}
}
```

Null configuration asks the trusted host to load initialized settings. The loop executes specification,
context assessment, plan, tasks, implementation, checks and delivery. Each step is also independently
callable with its own named request/response type. `concorde-context` resolves the exact context;
`concorde-context-solve` diagnoses missing information. `describe-policy` previews stage grants without
launching an agent. Delivery removes a verified attempt; it does not merge or push Git changes.

A blocked change preserves evidence and names missing contracts or failed admission. Author missing
facts through an explicit local Spec task, reconcile affected consumer/provider views and resolve a
new context. Changed Spec/intent invalidates an existing attempt; do not reuse stale evidence.
`concorde-taskstoissues` produces local issue drafts only. Reflection investigation is a separate,
read-only implementation invocation; human approval/disposition remains governed by project settings.

[Operation inventory](specs/concorde/services/operation-registry.md) ·
[Complete wire contracts](specs/concorde/services/operation-wire.md)

## Migration and documentation

Concorde 4 uses Package Manifest 3, Architecture Profile 8, Workspace Protocol 14 and Delivery Proposal
10. Profile 7 is rejected for agent execution. `concorde-migrate` accepts an authored replacement
registry and Markdown collection, proposes exact changes, rejects active attempts and applies with
preconditions/rollback. It never guesses new scopes or imports ancestor dependencies. Legacy readers
remain deterministic diagnostic utilities only.

The docsite publishes explicit registry members with separate scope/component navigation and a typed
relationship graph. Run the docsite's validate/build scripts to create a candidate whose routes and
source digests are checked before promotion. Human navigation does not grant agent context access.

## Development

Run Python tests with `PYTHONPATH=src python -m unittest discover -s tests/concorde -v` and docsite checks
with `npm run typecheck`, `npm test`, `npm run validate`, `npm run build`. Regenerate canonical public
projections after prompt changes. `scripts/sync-protocol-assets.py` exports executable wire schemas;
`--bind-project` is an explicit maintainer decision to accept that Protocol in this checkout.
