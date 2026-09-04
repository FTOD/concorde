# Official Understand Anything Viewer lock

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
