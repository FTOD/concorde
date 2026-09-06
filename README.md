# Concorde

Concorde runs agent work from explicit, self-contained resolved contexts. A global main coordinator may inspect
main-visible Domain and Service documents on demand to route a request; every routed worker then has one selected
target, one reproducible context and a host-enforced permission boundary.

Domain is a business/problem scope. Service and Module are component kinds: a Service offers Features
through precise exchanges; a Module offers APIs. Domain scope nesting, component composition and
multi-scope participation are independent relationships. Every target registers its complete ordered
Markdown collection; filenames are unrestricted. Each Markdown declares a stable document ID, exact
referencing targets and main visibility. A target's context separates singly referenced Target Spec
from one-hop collective Shared Specs; it never expands a co-referencing entity's remaining files.
Each direct `participates_in` edge is also described inside that Domain's Markdown through a
machine-readable participant entry containing stable ID, kind, local responsibility, selection
condition and relied-upon promises.

The shipped Protocol principles apply to every consumer project. `concorde-main` is the single
public entry for global questions and topology design. Its internal coordinator starts at the entry
Domain or Service and appends only explicitly requested Domain/Service main-visible documents. It
cannot directly expand a Module target or read code. Once it returns typed routes, the host starts different fresh workers and injects
the pinned global principles plus each selected kind definition. Missing task-relevant facts yield
Spec incomplete, not a search for arbitrary files. See [the principles](protocol/principles.md) and
[Concorde's own system Spec](specs/concorde/system.md).

## Install and initialize

The installer distributes canonical runtime, 22 paired public Operations, 7 internal roles and 9
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
and deterministic checks. Domain participant declarations make component routing locally meaningful;
validation keeps them aligned with registry participation. Arbitrary nearby Markdown is not context.
Document declarations are likewise checked against reverse registry membership.

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

Null configuration asks the trusted host to load initialized settings. The `ask` action of
`concorde-main` may omit target_id: a separate coordinator discovers Domain/Service Specs, routes one or more fresh
target readers, then synthesizes only their typed results. A supplied target_id is a routing hint,
not a context grant. The loop executes specification,
context assessment, plan, tasks, implementation, checks and delivery. Each step is also independently
callable with its own named request/response type. `concorde-context` reports the exact membership
and digests without returning raw Spec bodies;
`concorde-context-solve` diagnoses missing information. `describe-policy` previews stage grants without
launching an agent. Delivery removes a verified attempt; it does not merge or push Git changes.
For a Domain, context solving first reports missing or inconsistent participant declarations as
structured Spec gaps, before planning or task generation.

A blocked change preserves evidence and names missing contracts or failed admission. Author missing
facts through an explicit local Spec task, reconcile affected consumer/provider views and resolve a
new context. Changed Spec/intent invalidates an existing attempt; do not reuse stale evidence.
`concorde-taskstoissues` produces local issue drafts only. Reflection investigation is a separate,
read-only implementation invocation; human approval/disposition remains governed by project settings.

For architecture changes, invoke `concorde-main` with `action:design-topology`. It returns a complete
candidate registry and target-local Spec tasks without writing. Send the exact returned proposal with
`action:accept-topology` only after maintainer review. The host then runs private target authors and
stores exact registry/document bytes in an ignored application artifact, returning only its path and
digest. Review that artifact outside agent cognition, then send its ArtifactRef with
`action:apply-topology`. Stale inputs or invalid target state prevent writes; successful application
updates the registry and documents atomically. The former standalone ask Operation does not exist.
Shared truth has no unique owner and cannot be changed by an ordinary single-target author. A
topology change tasks every affected reference and proceeds only when all candidate referencing
authors return identical shared bytes.

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

Canonical `skills/`, `operations/`, and `agent-assets/` produce the tracked checkout agent surfaces.
Never edit `.agents/skills/concorde-*`, `.claude/skills/concorde-*`, or generated reflection agents
directly. After changing their sources, run both commands in the same primary or linked worktree:

```bash
python3 scripts/development/sync-agent-surfaces.py apply --project-root .
python3 scripts/development/sync-agent-surfaces.py check --project-root .
```

Root `AGENTS.md`/`CLAUDE.md` bind an agent to the worktree that supplied its project Skills. If work
targets another worktree, open a new agent there; do not update the primary checkout as a substitute.
See [source-checkout distribution](specs/concorde/services/install-boundary.md#featureinstallationself-distribute).
