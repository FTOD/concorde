# Command reference

Canonical commands live in root `commands/` and render directly into Codex/Claude skills. The
`speckit-*` IDs are retained compatibility names; every command is authored and executed by
Concorde. All path-sensitive phases resolve Feature Workspace Protocol 12 before other artifact reads.

## Governance and framework operations

### `speckit.constitution`

Creates/amends `.concorde/constitution.md` from the complete root constitution format reference.

### `speckit.concorde.init`

Proposes and explicitly applies Profile 7 configuration, root architecture, and reflection log.

### `speckit.concorde.context <stable-id>`

Returns one bounded module or feature altitude. Strictly read-only.

### `speckit.concorde.validate [target]`

Returns deterministic sorted Profile 7 findings/status/digest. Never repairs.

### `speckit.concorde.ask <question>`

Answers from package guidance and the smallest bounded project context with citations. It is
read-only and never invokes another command.

### `speckit.concorde.deliver [feature]`

Validates a completed stable-ID attempt, applies Delivery Proposal 8, and removes exactly that
temporal workspace. It writes no durable implementation prose.

## Feature lifecycle

### `speckit.specify <description>`

Creates/revises one direct module-level feature with embedded interfaces and Architecture Zoom. For
a new file, the first Protocol 12 result has unresolved attempt fields; after stable front matter is
written, the command resolves again and persists `.concorde/feature.json`.

### `speckit.clarify [focus]`

Resolves up to three high-impact ambiguities inside the selected feature and its requirements checklist.

### `speckit.checklist [focus]`

Creates a reviewer-owned requirements-quality checklist under the matching attempt.

### `speckit.plan [constraints]`

Writes a technical plan/research/useful artifacts only under the selected attempt. It reads bounded
architecture plus current code/tests and leaves durable sources unchanged.

### `speckit.tasks [constraints]`

Creates dependency-ordered, test-first tasks with exact paths/traces and evidence gates.

### `speckit.analyze`

Runs a non-mutating consistency/coverage audit over feature, architecture, plan, tasks, code/tests.

### `speckit.implement`

Executes dependency-ready tasks, reconciles all affected authorities, records passing evidence before
checking tasks, and stops truthfully on blocking failures.

### `speckit.converge`

Compares current repository/evidence with intended outcome and appends only remaining executable work.

### `speckit.taskstoissues`

Converts selected tasks into dependency-aware external issues only with explicit external-write authority.

### `speckit.fast-loop`

Completes one small already-specified, non-structural change without an attempt after deterministic
eligibility/impact preflight.

## Native read-only exploration

### `concorde explore [stable-id]`

Projects one validated Profile 7 module, entity, feature, or interface into a canonical bounded JSON
result. This is a native deterministic operation, not a conversational `speckit-*` command. With no
graph it still returns specification subjects and explicit unknown alignment records.

Optional inputs are:

- `--graph <project-relative-json>`: an Understand Anything graph conforming to the formal model
  pinned at `ba450c43425f3de6d43daf76526950ad8ca93536`;
- `--alignment <project-relative-json>`: schema-1 explicit claims bound to an
  `implementation_revision`;
- `--revision <revision>`: the expected revision used to qualify freshness;
- `--query <text>`: case-insensitive search over already bounded specification subjects and graph
  node ID/type/name/path/summary/tags; and
- repeatable `--status unknown|partial|verified|disagrees`: filters by effective status, never merely
  the requested sidecar status.

The implementation subgraph contains mapped or text-matched nodes plus exactly one edge hop, with
filtered layers/tour and total/returned counts. Invalid inputs return findings without mutation;
missing, unassessed, stale, candidate-only, or insufficient evidence produces unknown state. No
name/similarity inference, graph repair, source scan, persistent index, or output-file mode exists.

Source checkout:

```bash
python3 scripts/concorde.py --project-root . explore feature.example.checkout
```

Installed package:

```bash
python3 .concorde/framework/scripts/concorde.py --project-root . explore feature.example.checkout
```

## Native paths and templates

Source-checkout skills invoke root `scripts/` and read root `templates/`. Installed skills invoke
`.concorde/framework/scripts/` and read `.concorde/framework/templates/`. Commands have no hook,
priority, or layered-template phase. Complete root files are the only package guidance authority.

Protocol 12 returns feature/module identity, native selection, bounded ancestry/relations,
stable-ID attempt/reflection paths, and executable context. It never expands unrelated feature bodies
or invents implementation narrative.
