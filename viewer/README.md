# Understand Anything graph view

Concorde uses the official Understand Anything Viewer to help developers explore a project's code
relationships alongside its Module architecture. The [`ua-graph` exporter](../specs/concorde/views/ua-graph.md)
can derive a graph from the Spec registry or overlay Module structure onto an existing Understand
Anything graph. The [viewer launcher](../specs/concorde/views/viewer.md) checks an existing graph's
basic JSON shape and opens it; starting it does not analyze code, generate a graph or check whether
the graph is up to date with source.

The [docsite](../docsite/README.md) provides the complementary view of authored Module Specs,
composition, dependencies and architecture diagrams.

## Run from a Concorde source checkout

Use this route when you cloned this repository. Run all commands from the repository root, one
directory above this README. You need Node.js 18+, npm and the Python environment used by the
Concorde CLI.

1. Install the pinned official Viewer. This step needs network access and is only needed on first
   setup or after the Viewer lock changes:

   ```bash
   npm --prefix viewer ci --ignore-scripts
   ```

2. Generate a graph from the project's Spec registry, or update Concorde's overlay on an existing
   UA graph:

   ```bash
   python3 scripts/concorde.py ua-graph --allow-primary-worktree
   ```

   The flag explicitly permits writing the graph in the primary checkout. If you only want to
   inspect a graph that already exists, skip this step. Export requires a loadable Concorde Spec
   registry; the Viewer itself can open an existing graph without loading that registry.

3. Start the Viewer and keep the terminal running:

   ```bash
   node viewer/node_modules/understand-anything-viewer/bin/viewer.mjs . --no-open
   ```

4. Open the complete **Dashboard URL** printed in the terminal, including its access token.
   Stop the server with **Ctrl+C** when finished.

On later runs, step 3 is enough to reopen the saved graph. Repeat step 2 when you want to refresh
the Spec-derived structure. Remove `--no-open` to allow the Viewer to open your browser, or add
`--port 5173` to request a particular port.

The source checkout uses `viewer/node_modules` directly. `scripts/run-viewer.py` expects an
installer-managed runtime and is intended for the installed-project route below.

## Run in a project with Concorde installed

First complete the [Concorde installation](../README.md), including the installer's explicit
`--apply` step. That provisions the managed Viewer; installation preview alone does not install it.
Node.js 18+ must also be available on your PATH.

From the consuming project's root, generate or update the graph:

```bash
python3 .concorde/framework/scripts/concorde.py ua-graph --allow-primary-worktree
```

Then open it using the managed launcher:

```bash
python3 .concorde/framework/scripts/run-viewer.py --project-root . --no-open
```

As in a source checkout, skip export if you just want to open an existing graph, and open the full
Dashboard URL printed by the Viewer. The launcher also accepts `--port 5173`; omit `--no-open`
to allow browser opening. Startup checks the installed runtime and does not install dependencies.

## Graph locations and refresh behavior

The current package looks for graph files relative to the project root in this order:

1. `.understand-anything/knowledge-graph.json`
2. `.ua/knowledge-graph.json`

The exporter updates the first existing graph. If neither exists, it creates
`.ua/knowledge-graph.json`. The managed launcher requires an existing graph and fails on an invalid
first-choice graph instead of falling back to the other path.

Without an existing UA analysis, export produces a skeleton of registered Modules, composition,
dependencies, Spec documents and bound implementation files. It does not infer function calls or
other code relationships, and it does not create a guided tour. For those details, use Understand
Anything's own analysis workflow to produce a graph, then run `ua-graph` to overlay Module structure.
Repeated export replaces Concorde-owned elements while preserving the other graph content.

To check whether the Concorde overlay matches the current registry without writing, run:

```bash
python3 scripts/concorde.py ua-graph --check
```

In an installed project, substitute `.concorde/framework/scripts/concorde.py` for
`scripts/concorde.py`. This checks Spec-derived graph drift, not whether a UA code analysis reflects
the latest source. Opening the Viewer does not refresh either kind of graph data.

## Explore the graph and troubleshoot startup

Select a layer to explore its files, search for a node, and select it to inspect details and
connections. Use **Fit View** to recenter. **Learn** and **Start Tour** are useful when the loaded
graph includes a tour; a fresh Spec-derived skeleton does not supply one.

- **No graph found:** run the export step, or generate a graph with Understand Anything. Check the
  project directory passed to the Viewer and the two graph locations above.
- **Viewer entrypoint missing in a source checkout:** run `npm --prefix viewer ci --ignore-scripts`
  from the repository root.
- **`CONCORDE VIEWER FAILED` reports a missing or mismatched installed runtime:** rerun the
  Concorde installer for that project with `--apply`. Installing packages in the project's own
  `node_modules` does not repair the managed runtime.
- **Export reports a registry or profile-version error:** resolve the reported Concorde
  configuration/runtime compatibility issue before exporting. If a graph already exists, you can
  still launch the Viewer to inspect that saved graph.
- **The browser cannot access the dashboard:** use the complete printed Dashboard URL, including
  its token, and keep the Viewer process running. If the requested port is unavailable, choose a
  different port with `--port`.

## Official viewer runtime lock

This package root pins the self-contained official Viewer published by
[`Egonex-AI/Understand-Anything`](https://github.com/Egonex-AI/Understand-Anything):

- release: `v2.9.0`
- asset: `understand-anything-viewer.tgz`
- SHA-256: `a8626ff3ad90041e807bfdb8994eefdd986e891593c4759d08222667e5405330`
- bytes: `794982`
- npm integrity: recorded in `package-lock.json`
- upstream package license: MIT
- runtime: Node.js 18+

Concorde does not vendor the tarball. Explicit native-install apply runs
`npm ci --ignore-scripts` from this lock inside `.concorde/.venv`; preview and subsequent Viewer
startup do not resolve dependencies. Project package files and `node_modules` are outside this
installer-owned runtime.
