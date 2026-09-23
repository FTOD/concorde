# Distribution interfaces

The exact shapes of the files, records and commands that [Distribution](module.md) produces or
accepts. The [entry](module.md) explains why they exist; this document is for readers who need
field names, rule identities, limits and exit codes.

## Build outputs {#build-outputs}

The build owns these locations and judges nothing else under `generated/`:

- the directories `generated/native/`, `generated/protocol/` and `generated/session/`;
- the files `generated/build-manifest.json` and `generated/schemas.json`;
- the `.pi/agents/` and `.pi/extensions/` files it renders, listed in the build manifest.

Other tools may write elsewhere under `generated/`. A symbolic link or a non-regular file inside an
owned directory stops both `build` and `build --check`.

The source layout renders:

| Output | Content |
| --- | --- |
| `generated/native/<agent>.md` | For `code-reviewer`, `context-assessor`, `issue-solver`, `planner`, `programmer`, `spec-reviewer` and `task-author`: the resolved `prompts/native/<agent>.md` followed by the resolved `agents/<agent>/spec.md` |
| `generated/session/pi/concorde-session.ts` | The private session entry with its capability catalog, as Pi session's [catalog contract](../session/interfaces.md#contract.session.catalog) defines |
| `generated/protocol/principles.md` | The resolved Protocol principles bundle: every normative Protocol chapter except the Module chapter, in reading order, and nothing else (not the migration notes) |
| `generated/protocol/kinds/module.md` | The resolved Module chapter with the Module and Scenario templates |
| `generated/schemas.json` | The JSON Schema of every registered request and record type, keyed by type identity, with sorted keys and two-space indentation |
| `.pi/agents/*.md`, `.pi/extensions/*.ts` | The Task subagent and session extension files rendered by Pi session's projector |

The installed layout prefixes every `generated/` path with `.concorde/framework/`, renders the
session entry at `.pi/extensions/concorde-session.ts`, and omits every source-only file.

## Build manifest

```concorde-contract
{
  "id": "contract.distribution.build-manifest",
  "version": 1,
  "schema": {
    "$defs": {
      "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    },
    "type": "object",
    "properties": {
      "schema_version": {"const": 1},
      "sources": {
        "type": "object",
        "additionalProperties": {"$ref": "#/$defs/digest"}
      },
      "outputs": {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "properties": {
            "sha256": {"$ref": "#/$defs/digest"},
            "sources": {"type": "array", "items": {"type": "string", "minLength": 1}}
          },
          "required": ["sha256", "sources"],
          "additionalProperties": false
        }
      }
    },
    "required": ["schema_version", "sources", "outputs"],
    "additionalProperties": false
  },
  "semantics": "The record generated/build-manifest.json (under .concorde/framework/ in an installed layout) of one build. sources maps every project-relative path the build read to the SHA-256 of its bytes; outputs maps every project-relative output path to the SHA-256 of its bytes and the sorted paths of the sources it was rendered from. A build is fresh exactly when the manifest exists, parses as this schema, and every path in sources exists as a regular file reached through no symbolic link whose current digest equals the recorded one; a missing, unreadable or malformed manifest means not fresh. Freshness never compares output bytes; comparing outputs with a fresh render is the stronger build check. Keys are serialized sorted. The manifest records inputs only and makes no claim that any output is correct.",
  "example": {
    "schema_version": 1,
    "sources": {
      "agents/planner/spec.md": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
      "prompts/native/planner.md": "sha256:2222222222222222222222222222222222222222222222222222222222222222"
    },
    "outputs": {
      "generated/native/planner.md": {
        "sha256": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
        "sources": ["agents/planner/spec.md", "prompts/native/planner.md"]
      }
    }
  }
}
```

`sources` holds every file any output was rendered from, plus every `.py` file under `agents/`
(except `agents/source/` in the installed layout), `operations/` and `src/concorde/`, every file
under `pi/` except `node_modules` and caches (and except the source-only extensions in the installed
layout), and `concorde.json`, `pi/package.json`, `pi/package-lock.json`, `pi/.npmrc`,
`scripts/requirements.lock`, `scripts/concorde.py`, `scripts/install-concorde.py` and
`scripts/run-operation.py` when present.

<a id="participation-build-manifest"></a>

**Participation.** Distribution provides the build manifest to three internal consumers. Request
admission refuses a model-backed capability request while the build is not fresh. Task context
refuses to load an Agent's instructions from `generated/native/` while the build is not fresh.
Pi session refuses to select a candidate whose build is not fresh and takes the recorded digests of
the launcher, the session extension and the private entry from it. Distribution keeps the manifest
exactly as the contract states after every successful `build`, and never writes a manifest for a
build that did not complete.

## Capability catalog participation

<a id="participation-catalog"></a>

Distribution provides Pi session's [capability catalog](../session/interfaces.md#contract.session.catalog)
at version 1: the build renders one catalog per session entry, listing the public Operations of the
Operation catalog in catalog order, each with its session kind, native actions, the resolved
guidance of `prompts/operation-guidance/<name>.md` and the registered schema of `<name>-request`
with its version. The kind is `host` for a `host` Operation, `agent-entry` for an `agent-call`
Operation and `workflow` for a `pi-workflow` Operation, except that a `pi-workflow` Operation whose
workflow hook serves requests in place is `host` with the `action` values its hook declares in
`NATIVE_ACTIONS` as native actions; a hook that serves in place without declaring them fails the
build. Every other Operation has no native actions. Guidance whose front matter is wrong, whose resolved text keeps a
reserved token, or a capability without a registered request schema fails the build.

## Prompt references

A reference is a whole line that starts in column one with `@`, followed by a project-relative path
token and optional bindings:

```text
@prompts/workflow-host/lifecycle-no-cognition.md
@prompts/workflow-host/invoke-operation-opener.md ACTION="plan work for the explicitly selected Module"
```

A line is a reference only when the token after `@` contains no whitespace, `@`, backtick, quote,
parenthesis or angle bracket, and either ends in `.md` or contains a slash or backslash. Every other
line, including indented lines, mentions and email addresses, stays as text.

| Rule | Raised when |
| --- | --- |
| `CONCORDE-PROMPT-MISSING-001` | The target is not a canonical relative path (empty, dot or traversal part, `~`, colon, backslash, control character), not Markdown, missing, not a file, or reached through a symbolic link |
| `CONCORDE-PROMPT-UNRESOLVED-001` | Bindings are not shell-style `KEY=value` tokens, a key is invalid or repeated, a `{KEY}` variable other than the reserved `OPERATION`, `SCRIPT` and `FRAMEWORK` is unbound or left in the output |
| `CONCORDE-PROMPT-AUDIENCE-001` | A root includes a prompt of another audience; `shared` prompts may be included by any root |
| `CONCORDE-PROMPT-AUDIENCE-002` | A prompt under `prompts/` lacks front matter with exactly `audience: worker`, `ambient` or `shared` |
| `CONCORDE-PROMPT-SCOPE-001` | A reference targets capability guidance or `specs/`, an Agent definition references outside `prompts/`, or Protocol text is not Markdown |
| `CONCORDE-PROMPT-PROTOCOL-001` | Protocol prompts (`prompts/protocol/`, `protocol/`) and other prompts reference each other |
| `CONCORDE-PROMPT-CYCLE-001` | A reference chain returns to a file already on it |
| `CONCORDE-PROMPT-DIAMOND-001` | One file is reached twice within one root, with any bindings |

Targets resolve from the project root, never from the including file. Bindings replace `{KEY}` in
the referenced file before its own references are resolved. Capability guidance roots are
`ambient`, Agent definitions under `agents/` are `worker` roots without front matter, and chapters
under `protocol/` are `shared` Markdown without front matter. A resolution error carries the rule
identity and produces no partial result. A prompt under `prompts/` that no root reaches fails the
build.

## Launcher

| Invocation | Effect |
| --- | --- |
| `run-operation.py <capability>` | Resolves `<capability>` in the Operation catalog, reads one capability request from standard input, hands it with the catalog's declarations, Operations' dispatcher, the local installation service and any verified session selection to Request admission, prints one result envelope |
| `run-operation.py <capability> --runtime-check` | Loads the capability's module, imports LangGraph's `StateGraph`, `START` and `END`, prints `{"langgraph", "operation", "prefix", "python", "python_version", "status": "ok"}` |
| `run-operation.py --native-context <step> ...` | Runs one native preparation or acceptance step of Agent execution |

A name that is not a public capability of the Operation catalog, or any other argument list,
prints an `unknown_operation` failure envelope and exits with 3. A runtime check without LangGraph
is `missing_runtime`. SIGTERM is handled as an interrupt; SIGTERM while the launcher is still
reading its request prints a failure envelope with `execution_cancelled`. The launcher never writes
bytecode caches. In a consumer project it re-executes itself first when `.concorde/.venv` holds
Concorde's owner marker and it is not already running there.

## Command line {#command-line}

`scripts/concorde.py [--project-root DIR] <subcommand>` prints one canonical JSON envelope and
returns the exit code of its status. Any unexpected exception becomes a `failed` envelope with
finding `CONCORDE-RUN-001`.

| Subcommand and options | Result |
| --- | --- |
| `build` | `success` with written artifacts and output count; `invalid` with `CONCORDE-BUILD-001` on a build error |
| `build --check` | `success` with no differences; `invalid` with `CONCORDE-BUILD-001` and the differences |
| `check-package` | `success` without findings; `invalid` with the package check findings |
| `protocol-manifest` | Verifies freshness, then `success` or `invalid` with `CONCORDE-PROTOCOL-MANIFEST-001` when the Protocol manifest's asset digests differ from the build |
| `protocol-manifest --write` | Also rewrites `protocol/manifest.json` with the build's digests |
| `protocol-manifest --bind-project` | Also sets the project's Protocol binding to the manifest's version and digest and rewrites `.concorde/protocol/` |
| `select-session ...` | Routed to Pi session's selection service |
| `validate [target]`, `registry --write\|--check` | Routed to Spec tooling |
| `status ...` | Routed to Candidate worktrees |
| `docsite ...` | Routed to Views' scaffold |

`status` options that change coordination (`--register`, `--child`, `--manual-merge`, `--cleanup`)
are refused outside the primary checkout with `primary_session_required`. `docsite` requires an
isolated worktree unless `--allow-primary-worktree` is given.

## Package check

`check-package` evaluates the package at the project root and reports findings attributed to
`module.distribution`:

| Rule | Finding |
| --- | --- |
| `CONCORDE-PROMPT-*` | A prompt resolution error, as listed under [Prompt references](#prompt-references) |
| `CONCORDE-PROMPT-UNREACHABLE-001` | A prompt under `prompts/` that no root reaches |
| `CONCORDE-PROMPT-NAME-001` | A guidance file whose `name` differs from its file name |
| `CONCORDE-OPERATION-GUIDANCE-001` | A public capability without guidance, or guidance with wrong front matter or a reserved token left after resolution |
| `CONCORDE-CONTRACT-SCHEMA-001` | A registered type whose schema cannot be exported, or a capability without a registered request schema |
| `CONCORDE-CONTRACT-UNIQUE-001` | A type identity registered twice |
| `CONCORDE-PACKAGE-MANIFEST-001` | A `concorde.json` that breaks the package manifest rules, or a symbolic link in the package |
| `CONCORDE-BUILD-FRESH-001` | A build that is not fresh under the build manifest contract |
| `CONCORDE-BUILD-DRIFT-001` | An owned output that differs from a fresh render, or a Protocol manifest digest that differs from the rendered asset |
| `CONCORDE-SPEC-OPERATIONS-001` | Not exactly one registered document carries the `concorde.operations` mirror, or a mirror record is missing, unknown or different from the record the loaded Operation catalog yields |
| `CONCORDE-SPEC-AGENTS-001` | Not exactly one registered document carries the `concorde.agents` inventory, an inventory entry differs from its Agent definition, or a directory under `agents/` holding a `spec.md` is not a listed Agent |
| `CONCORDE-SPEC-TYPES-001` | A `concorde-<name>@<version>` token in a registered document names no exported identity or another version, or an exported typed value or capability envelope does not appear as `<identity>@<version>` in a document its owner Module owns: for a capability's request and response the Operation's declared owner, otherwise the Module that binds the file of the code that registered the type |
| `CONCORDE-SPEC-ERRORS-001` | An advisory finding for an error code raised under `src/concorde` that is missing from Request admission's error table |

Concorde's own configuration lists it as the configured check `check.distribution.package`, with
argv `{python} scripts/concorde.py check-package` and inputs `agents`, `operations`, `pi`,
`prompts`, `protocol`, `scripts`, `src`, `concorde.json` and `generated`.

## Package manifest

`concorde.json` must have `schema_version` 5, `name` `concorde`, `architecture_profile` 16,
`workspace_protocol` 16, `delivery_proposal` 10, `license` `MIT` with
`license_file` `LICENSE`, `client` `pi`, `package_roots` exactly `agents`, `operations`, `docsite`,
`pi`, `prompts`, `protocol`, `scripts`, `src`, `install` exactly `{"framework_root":
".concorde/framework", "receipt": ".concorde/install.json"}`, and `runtime` exactly
`{"launcher": "scripts/run-operation.py", "python": ">=3.11", "requirements":
"scripts/requirements.lock", "venv": ".concorde/.venv"}`. The package must contain a real
`README.md` and `LICENSE` and no symbolic link.

## Installer

`install-concorde.py --target DIR [--checkout DIR] [--preview | --apply]
[--remove-protocol-guidance] [--preserve-project] [--format text|json]`. `--checkout` defaults to
the package that contains the script. The target must be a real directory path without symbolic
links, and not a Concorde source checkout. An unknown option is refused before the target is read.

The JSON result has `schema_version` 2, `status` (`preview`, `conflict`, `installed` or
`unchanged`), `version`, `client` `pi`, `target`, `receipt`, `preserve_project`, `package` and
`actions`. Each action has `path`, `action`, `role` (`framework`, `extension`, `protocol`,
`project-default`, `protocol-guidance`, `protocol-guidance-cleanup`, `runtime` or `superseded`) and
`sha256`, plus `reason` for a conflict and the before-state fields `before_sha256`, `before_exists`
and `created` for root guidance. A failure prints `{"schema_version": 2, "status": "failed",
"error": "..."}`. Exit codes: 0 for success or a clean preview, 2 for conflicts, 3 for failure.

The root guidance block in `AGENTS.md` is exactly:

```markdown
<!-- concorde-protocol:start -->
## Concorde Spec Protocol

Read and follow `.concorde/protocol/principles.md` before Concorde workflow actions.
<!-- concorde-protocol:end -->
```

The installation lock is an exclusive non-blocking POSIX `flock` on `.concorde/install.lock` in the
target.

## Installation receipt

`.concorde/install.json` (schema 2) holds `schema_version`, `concorde_version`, `client` `pi`,
`architecture_profile`, `workspace_protocol`, `runtime` (the runtime record below), `package` (the package identity), `provider_root` (the package
path it was installed from, provenance only), `preserve_project`, `preserved` (path and role of
unowned files left in place) and `outputs`. Each output has `path`, `role` and `sha256`: the digest
of the whole file, or for root guidance the digest of the block only, plus `"created": true` when the
installer created that root file. Project defaults are never recorded. A receipt of any other
schema is refused, as is one that repeats a path or records a whole root file.

## Package identity

`{"version", "digest", "build_digest"}`: `digest` is the SHA-256 of the compact sorted JSON mapping
every path the installer would write to its role and content digest; `build_digest` is the SHA-256
of the installed-layout build manifest. All digests are `sha256:` followed by 64 lowercase
hexadecimal digits.

## Local installation service

| Function | Behaviour |
| --- | --- |
| `admit_package(root) -> PackageSource` | Loads a canonical package root and returns `root`, `version`, `digest`, `build_digest` |
| `verify_installation(target, *, expected=None) -> LocalInstallation` | Read-only verification; raises `InstallError` |
| `ensure_installation(target, source, *, bootstrap=False, preserve_project=True) -> LocalInstallation` | Verifies, or with `bootstrap=True` installs a current plan under the lock and verifies again |
| `installation_lock(target)` | The installation lock |

`LocalInstallation` has `target`, `framework`, `pi_entry`, `python`, `launcher`, `receipt`,
`package`, `provider_root`, `receipt_digest`, `runtime_digest`, `protocol_matches_package` and
`status` `verified`. `protocol_matches_package` compares the project's Protocol copy manifest with
the package's; it is reported, not enforced, because Protocol acceptance is a separate decision.
The launcher passes this service to Request admission, which calls `verify_installation` before a
top-level run in a consumer project and `ensure_installation` with an explicit bootstrap before it
relays into a consumer candidate.

## Managed runtime

`scripts/requirements.lock` holds exactly one line `langgraph==X.Y.Z`. `pi/package.json` pins
`typebox` to one exact version. The runtime digest combines the lock digest with the digest of
`pi/package.json`, `pi/package-lock.json` and `pi/.npmrc`.

Provisioning installs the lock with pip and runs `npm ci --ignore-scripts` from the package's
`pi/package.json` and `pi/package-lock.json` into `share/concorde/pi` inside the runtime. The owner
marker `.concorde/.venv/.concorde-runtime.json` (schema 4) holds `owner` `concorde`, `path`,
`concorde_version`, `requirements_sha256`, `runtime_sha256`, `python_version`, `pi_lock_sha256`,
`typebox_version` and `verified_operations`, the capabilities whose runtime check passed. The
runtime record returned by provisioning and stored in the receipt holds `path`, `python`,
`python_version`, `requirements`, `requirements_sha256`, `runtime_sha256`, `launcher`,
`verified_operations` and `pi` (`install_relative` `share/concorde/pi`, `lock_sha256`, `typebox`).
Planning, provisioning and verification failures raise `ManagedRuntimeError`.

## Build Python interface

| Name | Shape |
| --- | --- |
| `BuildOutput` | Frozen `{path, content: bytes, sources: tuple[str, ...]}` |
| `BuildResult` | Frozen `{outputs: tuple[BuildOutput, ...], manifest: bytes}` |
| `build(root, *, framework_prefix="")` | Pure render; raises `BuildError` |
| `write_build(root)` | Renders and writes under the ownership rules; raises `BuildError` |
| `check_build(root) -> (current, differences)` | Renders in memory and lists every owned path whose bytes differ from the render, including extra and missing files, and every `protocol/manifest.json:<asset>` whose recorded digest differs from the rendered asset |
| `recompute_protocol_manifest(root)` | Returns the Protocol manifest with digests from the rendered assets, writing nothing |

`BuildError(ValueError)` carries `code`: `invalid_build` by default or `stale_build`.
`PromptResolverError(ValueError)` carries `rule_id`.
