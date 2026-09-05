# Publication service

## feature.publication.publish

The deterministic `concorde docsite --propose` command creates a scaffold proposal using optional
--title, --repository, --url, --base-url and --github-pages. `--apply --proposal PATH` applies the
accepted project-relative JSON proposal under the host's worktree policy. Proposal application checks
before-digests, owns only scaffold files and restores originals on failure; project Specs are inputs.
The entry target's first registered document supplies the source entry without requiring a filename.

The resulting project-local site runs `npm run validate` and `npm run build`. Profile 8 publication
consumes .concorde/config.json and its explicit registry, not recursive filename discovery. It renders
every registered target/document membership under /specs/<target-id>/<source-path-hash>, preserving
all documents in a complete collection. Domain scope and component composition have independent
sidebar trees; a relationship graph also shows multi-scope participation and shared-contract edges.
A shared physical document may have one page in each explicitly registered target collection.

The build manifest has schema_version 14, sourceDigest and a pages array of sourcePath, route and
contentDigest. architecture-graph.json has schema_version 1, sourceDigest, nodes and typed edges.
Each candidate validates exact source identity and route inventory before atomic promotion. Changes
during generation or missing pages invalidate the candidate and preserve the previous build.
Declared diagrams are validated/rendered from exact registry sources, never inferred from filenames.
Local links resolve only registered document membership; unknown or ambiguous links fail validation.

These generated views are human navigation, not Operation context grants. The publication Tool may
read multiple registered collections deterministically; an agent still receives one host-bound target
snapshot. Legacy Profile 7 publication readers remain isolated diagnostics and do not admit agent work.
