# Project structure

Concorde separates canonical architecture/feature sources, executable implementation/evidence,
temporary work memory, and generated projections.

```text
project/
├── .concorde/
│   ├── config.json                         # root module + Profile 7 selection
│   ├── attempts/<stable-feature-id>/       # optional tracked temporal work
│   └── reflections/
│       ├── log.md                           # tracked process memory
│       ├── config.json                      # triage configuration
│       ├── plans/                           # ignored/disposable
│       └── worktrees/                       # ignored/disposable
├── .specify/
│   ├── feature.json                       # selected feature control state
│   ├── presets/concorde/                  # installed canonical-package projection
│   └── extensions/concorde/               # installed runtime/package projection
├── specs/<project>/
│   ├── architecture.md
│   ├── diagrams/
│   ├── modules/<child>/                    # recursive module package
│   └── features/<NNN-name>.md              # one complete durable feature
├── src/ | app/ | packages/ | ...              # implementation authority
├── tests/                                     # executable evidence and fixtures
├── generated/                                 # reproducible projections
└── docs/                                      # public maintained guidance
```

## Placement rules

- `modules/<child>/` contains an immediate module only. Each child has its own `architecture.md` and
  may recurse.
- `features/<NNN-name>.md` is one level-local feature authority. Features never contain another feature.
- `.concorde/attempts/<stable-feature-id>/` is optional temporal work keyed by the exact globally
  unique feature ID, independent of its mutable filename or module path.
- Module diagrams stay under that module's `diagrams/` and are declared/textually explained in its
  architecture.
- Executed interface schemas/examples live with source or tests. Human-readable interface semantics
  stay embedded in the owning feature file.
- `.concorde/reflections/log.md` is the only persisted reflection record.
- Generated outputs never sit in a source location or become a resolver input.

## Canonical versus installed package sources

In the Concorde framework repository, `presets/concorde/` and `extensions/concorde/` are distribution
authorities. `.specify/**`, `.agents/**`, and `.claude/**` are installed/materialized projections.
Edit canonical sources first and regenerate through self-hosting. Do not patch an installed copy as
the source of a release.

## Control state

`.concorde/config.json` selects the specification root and architecture profile. `.specify/feature.json`
stores only one canonical `feature_path`. Neither defines behavior. Workspace Protocol 12 validates
and resolves control state before each phase.

## Safety

Canonical paths are normalized, project-relative, and symlink-safe. Runtime mutations operate on
exact proposal paths and fail closed on stale digests, path escape, symlink traversal, ambiguous
identity, or mixed profile state. Delivery removes only one selected attempt.
