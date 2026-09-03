# Project structure

Concorde separates durable architecture/feature intent, native project control, executable
implementation/evidence, installed framework projections, and generated outputs.

```text
project/
├── .concorde/
│   ├── config.json                         # root module + Profile 7
│   ├── feature.json                        # exactly one selected feature_path
│   ├── constitution.md                     # optional governance authority
│   ├── attempts/<stable-feature-id>/       # optional tracked temporal work
│   ├── reflections/
│   │   ├── index.json                      # tracked allocation high-water only
│   │   ├── R-NNN.md                        # one tracked problem/triage record
│   │   ├── config.json                     # triage configuration
│   │   ├── plans/                          # ignored/disposable
│   │   └── worktrees/                      # ignored/disposable
│   ├── framework/                          # installed standalone package projection
│   └── install.json                        # output path/role/digest ownership receipt
├── .agents/ | .claude/                     # generated selected-integration surfaces
├── specs/<project>/
│   ├── architecture.md
│   ├── diagrams/
│   ├── modules/<child>/                    # recursive module package
│   └── features/<NNN-name>.md              # one complete durable feature
├── src/ | app/ | packages/ | ...           # implementation authority
├── tests/                                  # executable evidence and fixtures
├── generated/                              # reproducible projections
└── docs/                                   # maintained public guidance
```

## Placement rules

- `modules/<child>/` contains an immediate module only. Each child has one `architecture.md` and may recurse.
- `features/<NNN-name>.md` is one level-local feature authority. Features never contain another feature.
- `.concorde/attempts/<stable-feature-id>/` is optional temporal work keyed by the exact globally unique feature ID.
- Module diagrams stay under that module's `diagrams/` and are declared/textually explained in architecture.
- Executed schemas/examples live with source/tests. Human-readable interface semantics live in the feature.
- Each `.concorde/reflections/R-NNN.md` is the only persisted prose record for that reflection;
  `index.json` contains allocation metadata only.
- Generated and installed outputs never become resolver inputs for specification behavior/structure.

## Package source versus installed projection

In the Concorde framework repository, root `skills/`, `operations/`, `templates/`, `src/concorde/`,
`scripts/`, `agent-assets/`, `docsite/` (the packaged docsite template), and `concorde.json` are
distribution authorities. `.agents/**` and `.claude/**` are
generated checkout projections. Consumer projects receive the same sources beneath
`.concorde/framework/` plus selected integration outputs and `.concorde/install.json` ownership.

Every one of 17 leaf directories contains exactly one public/internal effect-declared `SKILL.md`.
Every one of three Operation directories contains exactly `operation.py` plus associated `SKILL.md`
with ordered capabilities/bindings. All leaves/pairs remain in the framework; only 15 public leaves
plus three Operations project to the agent namespace. The two internal planner leaves never project.

Project-authored `.concorde/config.json`, `feature.json`, `constitution.md`, attempts, reflection
documents, and allocation index are never package outputs. Installer defaults create reflection
config/ignore only when absent.

## Control state

`.concorde/config.json` selects specification root/profile. `.concorde/feature.json` contains only one
canonical `feature_path`. Neither defines behavior. Workspace Protocol 13 validates/resolves both
before each path-sensitive phase.
Operations-owned trusted resolution maps returned paths, providing-module locators, exact task tokens,
and required-interface owner feature specs into concrete non-symlink roles before an agent launch.

## Safety

Canonical paths are normalized, project-relative, and symlink-safe. Runtime/installer mutations use
exact proposal or ownership paths and fail closed on stale digests, escapes, symlinks, ambiguous
identity, modified owned outputs, widened/missing agent policy, unavailable native/outer enforcement,
or mixed profile state. Delivery removes only one selected attempt.
