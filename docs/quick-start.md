# Quick start

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- Git
- one supported Spec Kit coding-agent integration (examples below use Codex)

## Install Concorde

Preview a public release installation:

```bash
uv run python scripts/install-concorde.py \
  --target ../sample-project \
  --integration codex \
  --preview
```

The preview validates the release pointer, including Architecture Source Profile 7 and Workspace
Protocol 12, shows catalog/bundle/agent-projection changes, and writes nothing. Apply the reviewed
plan:

```bash
uv run python scripts/install-concorde.py \
  --target ../sample-project \
  --integration codex
```

Omitting `--preview` applies the reviewed installation plan.

For development, install directly from a Concorde checkout:

```bash
uv run python scripts/install-concorde.py \
  --target ../sample-project \
  --integration codex \
  --checkout . \
  --preview
```

## Initialize architecture

Inside the target Spec Kit project, invoke the installed `speckit.concorde.init` command with a root
module ID/name. Review the exact proposal, save it at a project-relative path, and apply it through
the command. Initialization Proposal 2 creates the configured root `architecture.md`,
`.concorde/config.json`, and `.concorde/reflections/log.md`; it does not guess a product hierarchy.

Edit the root architecture to define the product's responsibility/boundary, significant entities,
relationships, interactions, and actual immediate modules/features. Add a child module only when it
owns a coherent recursive boundary.

## Specify a feature

Select a direct `features/<NNN-name>.md` path under its providing module and invoke `speckit.specify`
with a concrete capability description. A complete feature file includes:

- outcome and scope;
- representative success/edge/failure usage;
- scenarios, requirements, assumptions, and success criteria;
- embedded provided/required interfaces; and
- an Architecture Zoom referencing module entity IDs.

Review the generated requirements checklist. Use `speckit.clarify` for material ambiguity and
`speckit.checklist` for focused reviewer questions.

For a new feature, the first Protocol 12 resolution intentionally reports unresolved/null attempt
paths. Write the stable front-matter ID, rerun the resolver, and only then use its exact checklist
path. Never derive the attempt key from the filename.

## Plan and implement

```text
speckit.plan
speckit.tasks
speckit.analyze
speckit.implement
speckit.converge      # only if evidence reveals more work
```

Planning reads the feature file, providing architecture, code, and tests. It creates one temporal
`.concorde/attempts/<stable-feature-id>/`. Tasks carry stable IDs, exact paths, requirement traces,
dependencies, and checks. Implementation
records passed evidence before checking each task and reconciles every explicitly affected
architecture/feature/code/test/projection surface.

Record problems and provisional prototype decisions in `.concorde/reflections/log.md`; keep progressing
when a safe bounded assumption is available.

## Validate and deliver

```bash
python .specify/extensions/concorde/scripts/python/concorde.py --project-root . validate
```

After every task/checklist/evidence gate passes, invoke `speckit.concorde.deliver`. It generates and
applies a digest-bound Proposal 8, removes exactly the selected attempt, and retains architecture,
feature file, code, tests, projections, and reflections unchanged.

## Verify installation state

The installed extension/preset are package projections. In the Concorde repository itself, use the
self-host status command documented in [Self-hosting](self-hosting.md). In a consuming project, use
Spec Kit bundle info/list plus the extension's deterministic validate/context commands.

## Next reading

- [Specification model](specification-model.md)
- [Workflow](concorde-workflow.md)
- [Commands](commands.md)
- [Ontology](ontology.md)
