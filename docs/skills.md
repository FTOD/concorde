# Skill and Operation reference

Seventeen canonical public/internal leaves live under `skills/<name>/SKILL.md`; composed leaves own
effects. Three paired public LangGraph Operations live under
`operations/<name>/{operation.py,SKILL.md}` and install their Markdown into the same Codex/Claude
namespace. Only 15 leaves project, for 18 public capabilities per integration. Trusted path-sensitive
launches resolve Protocol 13 into enforced concrete roles before other artifact reads.

## Governance and framework leaf Skills

### `concorde-constitution`

Creates/amends `.concorde/constitution.md` from the complete root constitution format reference.

### `concorde-init`

Proposes and explicitly applies Profile 7 configuration, root architecture, required Archify system
overview, and reflection log.

### `concorde-context <stable-id>`

Returns one bounded module or feature altitude. Strictly read-only.

### `concorde-validate [target]`

Returns deterministic sorted Profile 7 findings/status/digest. Never repairs.

### `concorde-ask <question>`

Answers from package guidance and the smallest bounded project context with citations. It is
read-only and never invokes another Skill.

### `concorde-deliver [feature]`

Validates a completed stable-ID attempt, applies Delivery Proposal 9, and removes exactly that
temporal workspace. It writes no durable implementation prose.

## Feature lifecycle leaf Skills

### `concorde-specify <description>`

Creates/revises one direct module-level feature with embedded interfaces and Architecture Zoom. For
a new file, the first Protocol 13 result has unresolved attempt fields; after stable front matter is
written, the Skill resolves again and persists `.concorde/feature.json`.

### `concorde-clarify [focus]`

Resolves up to three high-impact ambiguities inside the selected feature and its requirements checklist.

### `concorde-checklist [focus]`

Creates a reviewer-owned requirements-quality checklist under the matching attempt.

### `concorde-tasks [constraints]`

Creates dependency-ordered, test-first tasks with exact paths/traces and evidence gates.

### `concorde-analyze`

Runs a non-mutating consistency/coverage audit over feature, architecture, plan, tasks, code/tests.

### `concorde-implement`

Executes dependency-ready tasks, reconciles all affected authorities, records passing evidence before
checking tasks, and stops truthfully on blocking failures.

### `concorde-converge`

Compares current repository/evidence with intended outcome and appends only remaining executable work.

### `concorde-taskstoissues`

Converts selected tasks into dependency-aware external issues only with explicit external-write authority.

### `concorde-fast-loop`

Completes one small already-specified, non-structural change without an attempt after deterministic
eligibility/impact preflight.

## Native read-only Tool

### `concorde explore [stable-id]`

Projects one validated Profile 7 module, entity, feature, or interface into a canonical bounded JSON
result. This is a native deterministic Tool, not a LangGraph Operation. With no
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

## Operation skills

- `concorde-plan [constraints]` invokes read-only internal context then temporal author. Only unique
  required-interface owner feature bodies cross a module boundary; provider internals/other attempts
  are denied and author writes only selected attempt/reflections.
- `concorde-standard-dev-loop` invokes the paired four-stage graph and sees planning only as the
  opaque public nested Operation.
- `concorde-reflections-triage` invokes only the explicitly selected conditional branch; status has no
  model, investigators are read-only, and implementers are worktree-scoped.

Each projected Operation carries source/kind/framework-entrypoint provenance. Internal
`concorde-plan-context` and `concorde-plan-author` remain package-only. Every direct leaf occurrence
receives one narrowing normalized/native policy and enforcement receipt; LangGraph does not enforce files.

## Native paths and templates

Source-checkout skills invoke root `scripts/` and read root `templates/`. Installed skills invoke
`.concorde/framework/scripts/` and read `.concorde/framework/templates/`. Skills have no hook,
priority, or layered-template phase. Complete canonical Skill files are the only leaf guidance authority.

Protocol 13 returns feature/module identity, native selection, bounded ancestry/relations,
stable-ID attempt/reflection paths, and executable context. It never expands unrelated feature bodies
or invents implementation narrative.
