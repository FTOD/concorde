# Understand Anything graph view

Concorde uses the official Understand Anything Viewer to help developers explore a project's code
relationships alongside its Module architecture. The [`ua-graph` exporter](../specs/concorde/views/ua-graph.md)
can derive a graph from the Spec registry or overlay Module structure onto an existing Understand
Anything graph. The [viewer launcher](../specs/concorde/views/viewer.md) opens an existing graph;
starting it does not analyze code, generate a graph or validate the graph's contents.

The [docsite](../docsite/README.md) provides the complementary view of authored Module Specs,
composition, dependencies and architecture diagrams.

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
