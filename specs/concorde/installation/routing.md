```concorde-document
{
  "id": "document.installation.routing",
  "targets": [
    "domain.installation"
  ],
  "main_visible": true
}
```

# Main routing for Installation


The main coordinator selects `service.installation` for install/update receipts, owned outputs and
the public installer boundary. It selects `service.spec-context` for initialization,
configuration binding and context-registry validation. Within those Service responsibilities,
`module.package-assets` owns packaged/projection assets, `module.managed-runtime` owns Python/viewer
provisioning, `module.registry` owns registry admission, `module.wire-contracts` owns typed data
validation and `module.file-transactions` owns rollback-safe file replacement. The Module IDs are
routing facts; their remaining target collections are supplied only to separately launched workers.

The developer-facing viewer launch contract belongs to `service.viewer` within
`domain.developer-view`. Installation still owns package acquisition and runtime provisioning;
route opening or validating a raw graph to the viewer service through that Domain.
