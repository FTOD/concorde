# Concorde Starter bundle

This integration-agnostic bundle pins `concorde-core@0.1.0` and `concorde@0.1.0` and inherits the
project's active coding-agent integration. It declares no workflow or reusable step.

Before installation, register the Concorde preset and extension catalogs as reviewed,
install-allowed sources. Release catalogs use HTTPS artifact URLs; the localhost HTTP catalogs
created by `scripts/release/build-components.py --base-url http://127.0.0.1:8765` are acceptance-only.

```bash
specify bundle validate --path bundles/concorde-starter
specify bundle build --path bundles/concorde-starter --output dist
specify bundle info concorde-starter --json
specify bundle install concorde-starter
```
