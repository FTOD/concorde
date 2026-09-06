# How projects adopt Concorde

This Domain scopes the relationship among a Package, an Installation, an Integration, a Project
configuration and a Protocol binding. A Package contains versioned runtime, canonical internal roles,
paired public Operations, global principles/kind definitions, schemas and templates. An Installation
owns only the outputs recorded in its receipt. An Integration is a projected invocation surface for
Codex or Claude; it must preserve the same executable boundary and typed request identities.

The Installation Service verifies package inventory and plans owned output changes before applying
them. The package assets Module renders public wrappers; the managed runtime Module provisions the
locked Python Operation runtime and the optional official viewer. User changes to receipt-owned
outputs cause a conflict rather than silent replacement. Failed provisioning or target validation
restores previously owned output bytes. Updating an installation does not author business Specs.
Project defaults are created only when absent and are not receipt-owned. They include Reflection
settings/scratch exclusions and the local ignore rule for exact topology application artifacts.

Initialization configures the integration and enforcement mode, pins the distributed Protocol and
creates an honest Domain stub with an explicit one-document registry. A stub states that business
facts have not yet been supplied. It does not claim completeness or infer behavior from source code.
Direct initialization or migration also creates the topology-artifact ignore rule when installation
has not already supplied it.
The context Service subsequently injects the pinned principles and matching kind definition for every
consumer project. The consumer chooses its own scopes and components; Concorde's own decomposition
is not a mandatory template.

A Profile 7 project requires an explicit migration proposal with authored target classifications,
complete document membership and replacement local contracts. Migration preserves code and reflection
history, rejects active attempts and binds to the original configuration digest. It applies only the
proposal's approved paths and rolls back if the target registry is invalid. Running Profile 7 through
Profile 8 is rejected rather than guessing scope boundaries from old filenames or ancestry.

Installation is complete when receipt-owned assets and managed runtime verify. Initialization is
complete when the configured registry and Protocol binding validate; it is a separate lifecycle.
Delivery and Git publication are separate user decisions. Retrying an unchanged install is idempotent;
retrying a stale proposal requires a new preview against current bytes.

Concorde also distributes its public invocation and reflection-agent surfaces into its own source
worktrees directly from canonical assets, without a duplicate installed framework. Each generated
surface belongs to one Git worktree. Checkout status reports drift, check enforces freshness, and
apply refreshes only that worktree's projections. Repository agent policy requires the loaded project
Skill and active worktree to share that identity, even when two worktrees have identical generated
bytes; crossing that boundary requires a newly opened agent in the target worktree.

## Main routing view

The main coordinator selects `service.installation` for install/update receipts, owned outputs and
the public installer boundary. It selects `service.spec-context` for initialization, migration,
configuration binding and context-registry validation. Within those Service responsibilities,
`module.package-assets` owns packaged/projection assets, `module.managed-runtime` owns Python/viewer
provisioning, `module.registry` owns registry admission, `module.wire-contracts` owns typed data
validation and `module.file-transactions` owns rollback-safe file replacement. The Module IDs are
routing facts; their Specs are supplied only to separately launched workers.
