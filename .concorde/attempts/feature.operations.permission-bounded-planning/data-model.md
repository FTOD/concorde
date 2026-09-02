# Data Model: Permission-Bounded Operations

## `EffectDeclaration`

Canonical leaf Skill authority parsed from `SKILL.md` front matter.

- `reads: tuple[PathRole, ...]`
- `writes: tuple[PathRole, ...]`
- `network: bool` (default `false`)
- `credentials: "none" | "declared"` (default `none`)

Invariant: every write role also implies read; unknown/duplicate roles fail validation. A leaf used
by an Operation must declare effects.

## `CapabilityPrompt`

- `name`, `description`, `source_path`
- `kind: "skill" | "operation"`
- `exposure: "public" | "internal"`
- `body`
- `operation` entry point for Operations
- ordered direct `capabilities` for Operations
- `effects` for leaf Skills

Invariant: internal Skills may be packaged and composed but are omitted from agent projections.
Operations are always public and may not declare leaf effects directly.

## `WorkspacePermissionContext`

Trusted, concrete resolution for one selected feature and one current revision.

- `project_root`
- selected `feature_path`, `module_architecture`, and `attempt`/reflection/control paths
- `required_feature_specs[{feature_id, feature_path, interface_ids}]`
- `owned_implementation_paths`
- task-authorized durable/write paths
- framework/template paths
- `source_digest`

Invariant: every path is normalized project-relative, exists or is an explicitly authorized creation
target beneath a real parent, and crosses no symlink. Provider-module internals never appear in
`required_feature_specs`.

## `PolicyBinding`

One exact direct capability occurrence in an Operation.

- `operation`, `stage`, `occurrence`
- `capability_name`, `capability_kind`
- `agent` logical identity
- optional narrowing role set

Invariant: `(stage, occurrence)` is unique and order matches the literal topology. A leaf binding is
a subset of its `EffectDeclaration`; a nested Operation binding carries no leaf filesystem union.

## `NormalizedPolicy`

- sorted concrete `read_paths`, `write_paths`, `deny_paths`
- `network_enabled`
- sorted credential file/environment denies
- `outer_sandbox_required`
- SHA-256 digest over canonical JSON

Invariant: paths are pairwise normalized, more-specific rules are preserved, denies cannot be
removed, network defaults false, and the policy contains no unresolved role token.

## `NativeLaunchConfiguration`

Union of:

- `CodexLaunchConfig`: executable/argv, digest-named profile, TOML overrides, model/config identity,
  ephemeral/strict/no-approval flags.
- `ClaudeLaunchConfig`: executable/argv, inline settings JSON, permission mode/tool set, strict
  sandbox and credential rules.
- `OuterSandboxConfig`: provider identity and independently verified effective paths when native
  enforcement is unavailable.

Invariant: native and normalized effective path sets compare equal. A legacy Codex sandbox flag may
not coexist with a permission profile. Claude may not allow unsandboxed retry.

## `LaunchSpecification`

- operation/stage/occurrence/capability identity
- complete prompt plus original request/prior results
- selected integration/model/agent
- normalized policy and native configuration
- workspace and configuration digests

Invariant: frozen/immutable before the executor call; no executor mutation can widen it.

## `EnforcementReceipt`

- launch/config/policy digests
- integration and detected client version
- `enforcement: "native" | "outer"`
- process exit/status and structured result
- explicit limitations

Invariant: a successful leaf result requires a matching receipt. Missing, stale, widened, or
unenforced receipts are failures and prevent later capabilities/stages.

## State transitions

```text
definition -> validate topology/effects -> resolve concrete context -> normalize policy
           -> render native config -> verify enforceability -> launch -> receipt/result

any failure ---------------------------------------------------------------> stop

outer Operation -> nested public Operation -> its own leaf policies/results -> outer result
```
