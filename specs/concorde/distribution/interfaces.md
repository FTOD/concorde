# Distribution interfaces

This document gives the exact shapes of the files, records and commands that
[Distribution](module.md) produces or accepts. The [entry](module.md) explains why they exist;
this document is for readers who need field names, rule identities and exit codes.

## Build outputs and ownership

The build owns these locations and judges nothing else:

- directories `generated/native/`, `generated/agents/`, `generated/protocol/`, `generated/docs/`
  and `generated/session/`;
- the file `generated/build-manifest.json`;
- the `.pi/agents/` and `.pi/extensions/` files it renders, listed in the build manifest.

Other tools may write elsewhere under `generated/`. A symbolic link or a non-regular file inside an
owned directory stops both `build` and `build --check`.

The source layout renders: `generated/native/<agent>.md` and `generated/agents/<agent>.md` with
identical bytes for `code-reviewer`, `context-assessor`, `issue-solver`, `planner`, `programmer`,
`spec-reviewer` and `task-author`; `generated/session/pi/concorde-session.ts`;
`generated/protocol/principles.md`, `generated/protocol/kinds/module.md` and
`generated/protocol/schemas.json`; and the Task subagent files listed in
[Pi session integration](session.md#task-subagent-files). Each native instruction file is the
resolved `prompts/native/<agent>.md` followed by the resolved `agents/<agent>/spec.md`. The
installed layout prefixes every `generated/` path with `.concorde/framework/`, renders the session
entry at `.pi/extensions/concorde-session.ts`, and omits every source-only file.

## Build manifest

`generated/build-manifest.json` is JSON with sorted keys:

```json
{
  "schema_version": 1,
  "sources": {"prompts/native/planner.md": "sha256:<64 hex>"},
  "outputs": {
    "generated/native/planner.md": {
      "sha256": "sha256:<64 hex>",
      "sources": ["agents/planner/spec.md", "prompts/native/planner.md"]
    }
  }
}
```

`sources` holds every file any output was rendered from, plus every `.py` file under `agents/`
(except `agents/source/` in the installed layout), `operations/` and `src/concorde/`, every file
under `pi/` except `node_modules` and caches (and except the maintenance and brief lifecycle
extensions in the installed layout), and `concorde.json`, `pi/package.json`,
`pi/package-lock.json`, `pi/.npmrc`, `scripts/requirements.lock`, `scripts/concorde.py`,
`scripts/install-concorde.py` and `scripts/run-operation.py` when present.

`verify_fresh(root)` fails with `BuildError` code `stale_build` when the manifest is missing,
unreadable or lacks `sources`, or when any recorded source is missing, a symbolic link or has a
different digest. It never compares output bytes. `check_build(root)` returns `(current,
differences)`: it renders in memory and lists every owned path whose bytes differ from the render,
including extra and missing files, and every `protocol/manifest.json:<asset>` whose recorded digest
differs from the rendered asset.

## Capability guidance

`prompts/operation-guidance/<name>.md` exists for each public capability and starts with front
matter of exactly three keys: `name` (equal to the file's capability name), a nonempty
`description`, and `operation`, the capability module's name (`plan` for `concorde-plan`, `spec_review`
for `concorde-spec-review`). The body is resolved as described below; after resolution it may not
contain `{SCRIPT}`, `{FRAMEWORK}` or `{OPERATION}`, and three or more consecutive newlines are
reduced to two.

## Prompt references

A reference is a whole line that starts in column one with `@`, followed by a project-relative path
token and optional bindings:

```text
@prompts/workflow-host/gap-reporting.md
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
under `protocol/` are `shared` Markdown without front matter. A prompt under `prompts/` that no root
reaches fails the build.

## Capability catalog

The session entry embeds `const CATALOG: SessionCatalog = {...};` with sorted keys:

| Field | Value |
| --- | --- |
| `schema_version` | `2` |
| `launcher` | `scripts/run-operation.py`, or `.concorde/framework/scripts/run-operation.py` when installed |
| `interpreters` | `.venv/bin/python` and `.venv/Scripts/python.exe`, or the same under `.concorde/.venv` when installed |
| `explicit_request_only` | `true` for the source layout, `false` when installed |
| `operations` | One object per public capability, in the order of the public capability inventory |

Each capability object has `name`, `kind` (`host`, `agent-entry` or `workflow`), `description`,
`guidance`, `request_version` (the `schema_version` constant of the `<name>-request` schema) and
`request_schema`. The entry calls `concordeSession(<project root>, CATALOG, <entry path>)` from the
tracked extension.

A `run` through the launcher sends this envelope on standard input:

```json
{
  "type_id": "concorde-operation-invocation",
  "schema_version": 3,
  "operation_id": "concorde-validate",
  "mode": "execute",
  "configuration": null,
  "input": {"type_id": "concorde-validate-request", "schema_version": 1, "data": {"...": "the tool's input"}}
}
```

The shape of the invocation and of its result envelope belongs to Request admission; the values
above are only what the tool fills in.

## Launcher

| Invocation | Effect |
| --- | --- |
| `run-operation.py <capability>` | Reads one invocation from standard input, hands it to admission, prints one result envelope |
| `run-operation.py <capability> --runtime-check` | Loads the capability module, imports LangGraph's `StateGraph`, `START` and `END`, prints `{"langgraph", "operation", "prefix", "python", "python_version", "status": "ok"}` |
| `run-operation.py --native-context <step> ...` | Runs one native preparation or acceptance step of Agent execution |

Any other argument list prints an `unknown_operation` failure envelope and exits with 3. A module
without a `run` function and `REQUEST` schema is `unknown_operation`; a runtime check without
LangGraph is `missing_runtime`. The launcher never writes bytecode caches. In a consumer project
it re-executes itself first when `.concorde/.venv` holds Concorde's owner marker and it is not
already running there.

## Command line

`scripts/concorde.py [--project-root DIR] <subcommand>` prints one canonical JSON envelope and
returns the exit code of its status. Any unexpected exception becomes a `failed` envelope with
finding `CONCORDE-RUN-001`.

| Subcommand and options | Result |
| --- | --- |
| `build` | `success` with written artifacts and output count; `invalid` with `CONCORDE-BUILD-001` on a build error |
| `build --check` | `success` with no differences; `invalid` with `CONCORDE-BUILD-001` and the differences |
| `protocol-manifest` | Verifies freshness, then `success` or `invalid` with `CONCORDE-PROTOCOL-MANIFEST-001` when tracked digests differ from the build |
| `protocol-manifest --write` | Also rewrites `protocol/manifest.json` with the build's digests |
| `protocol-manifest --bind-project` | Also sets `.concorde/config.json` `protocol` to the manifest's version and digest and rewrites `.concorde/protocol/` |
| `select-session --mode maintenance\|test\|task --runtime P [--pi-entry P] [--output P]` | The selection record, optionally saved |
| `select-session --verify P` | The reverified saved record; refuses any other selection option |
| `validate [target]` | The Spec checks' result |
| `status`, `usage`, `docsite` | Routed to Candidate worktrees, Agent execution and Views |

`status` options that change coordination (`--register`, `--child`, `--manual-merge`, `--cleanup`)
are refused outside the primary checkout with `primary_session_required`. `docsite` requires an
isolated worktree unless `--allow-primary-worktree` is given.

## Package manifest

`concorde.json` must have `schema_version` 5, `name` `concorde`, `architecture_profile` 16,
`workspace_protocol` 16, `delivery_proposal` 10, `license` `MIT` with `license_file` `LICENSE`,
`client` `pi`, `package_roots` exactly `agents`, `operations`, `docsite`, `pi`, `prompts`,
`protocol`, `scripts`, `src`, `install` exactly `{"framework_root": ".concorde/framework",
"receipt": ".concorde/install.json"}`, and `runtime` exactly `{"launcher":
"scripts/run-operation.py", "python": ">=3.11", "requirements": "scripts/requirements.lock",
"venv": ".concorde/.venv"}`. The package must contain a real `README.md` and `LICENSE` and no
symbolic link.

## Installer command line

`install-concorde.py --target DIR [--checkout DIR] [--preview | --apply]
[--remove-protocol-guidance] [--preserve-project] [--format text|json]`. `--checkout` defaults to
the package that contains the script. The target must be a real directory path without symbolic
links, and not a Concorde source checkout.

The JSON result has `schema_version` 2, `status` (`preview`, `conflict`, `installed` or
`unchanged`), `version`, `client` `pi`, `target`, `receipt`,
`preserve_project`, `package` and `actions`. Each action has `path`, `action`, `role` (`framework`,
`extension`, `protocol`, `project-default`, `protocol-guidance`, `protocol-guidance-cleanup`,
`runtime` or `superseded`) and `sha256`, plus `reason` for a conflict and the before-state fields
`before_sha256`, `before_exists` and `created` for root guidance. A failure prints `{"schema_version":
2, "status": "failed", "error": "..."}`. Exit codes: 0 for success or a clean preview, 2 for
conflicts, 3 for failure.

## Installation receipt

`.concorde/install.json` (schema 2) holds `schema_version`, `concorde_version`, `client` `pi`,
`architecture_profile`, `workspace_protocol`, `runtime` (the runtime record below), `package` (the
package identity), `provider_root` (the package path it was installed from, provenance only),
`preserve_project`, `preserved` (path and role of unowned files left in place) and `outputs`. Each
output has `path`, `role` and `sha256`: the digest of the whole file, or for root guidance the digest
of the block only, plus `"created": true` when the installer created that root file. Project
defaults are never recorded. A receipt of any other schema is refused, as is one that repeats a
path or records a whole root file.

## Package identity

`{"version", "digest", "build_digest"}`: `digest` is the SHA-256 of the compact sorted JSON
mapping every path the installer would write to its role and content digest; `build_digest` is the
SHA-256 of the installed-layout build manifest. All digests are `sha256:` followed by 64 lowercase
hexadecimal digits.

## Local installation service

| Function | Behaviour |
| --- | --- |
| `admit_package(root) -> PackageSource` | Loads a canonical package root and returns `root`, `version`, `digest`, `build_digest` |
| `verify_installation(target, *, expected=None) -> LocalInstallation` | Read-only verification; raises `InstallError` |
| `ensure_installation(target, source, *, bootstrap=False, preserve_project=True) -> LocalInstallation` | Verifies, or with `bootstrap=True` installs a current plan under the lock and verifies again |
| `installation_lock(target)` | Exclusive non-blocking `flock` on `.concorde/install.lock` |

`LocalInstallation` has `target`, `framework`, `pi_entry`, `python`, `launcher`, `receipt`,
`package`, `provider_root`, `receipt_digest`, `runtime_digest`, `protocol_matches_package` and
`status` `verified`. `protocol_matches_package` compares the project's Protocol copy manifest with
the package's; it is reported, not enforced, because Protocol acceptance is a separate decision.

## Managed runtime

`scripts/requirements.lock` holds exactly one line `langgraph==X.Y.Z`. `pi/package.json` pins
`typebox` to one exact version. The runtime digest combines the lock digest with the digest of
`pi/package.json`, `pi/package-lock.json` and `pi/.npmrc`.

The owner marker `.concorde/.venv/.concorde-runtime.json` (schema 4) holds `owner` `concorde`,
`path`, `concorde_version`, `requirements_sha256`, `runtime_sha256`, `python_version`,
`pi_lock_sha256`, `typebox_version` and `verified_operations`, the list of capabilities whose
runtime check passed. The runtime record returned by provisioning and stored in the receipt holds
`path`, `python`, `python_version`, `requirements`, `requirements_sha256`, `runtime_sha256`,
`launcher`, `verified_operations` and `pi` (`install_relative` `share/concorde/pi`, `lock_sha256`,
`typebox`). Planning, provisioning and verification failures raise `ManagedRuntimeError`; process
and file-system errors may also propagate.

## Session selection record

`select-session` returns (schema 2):

| Field | Value |
| --- | --- |
| `mode` | `maintenance`, `test` or `task` |
| `candidate` | The absolute candidate root |
| `fresh_context`, `fork_context`, `discover_catalogs`, `inherit_catalogs`, `task_delegation` | `true`, `false`, `false`, `false`, `false` |
| `build_digest` | Digest of the candidate's build manifest bytes |
| `runtime` | `{path, digest}` of `scripts/run-operation.py` |
| `implementation` | `{path, digest}` of `pi/extensions/concorde-session.ts` |
| `pi_entry` | `null` in maintenance mode; otherwise `{path, digest, content, catalog: {content, digest}}` of the private entry |
| `launch` | `{cwd, pi_args}` with `--no-session --no-context-files --no-skills --no-prompt-templates --no-themes --no-extensions` and, outside maintenance, `-e <entry>` |
| `execution_evidence` | `null` |

Refusals raise `BuildError`, with code `stale_build` for stale or changed bytes. A saved selection
must lie strictly below `<candidate>/.concorde/work/`; loading it recomputes the record and compares
the whole canonical value.

## Tester command

Standard input: `{"command": string of at most 32768 characters, "timeout": number in (0, 3600],
"reports"?: [names]}`; any other key is refused. Standard output: first
`{"tester_check_ready": true, "execution_id": "..."}`, then one object with `returncode`,
`timed_out`, `cancelled`, `cancellation_requested`, `error`, `evidence`, and for each of `stdout`
and `stderr` the last 20000 bytes, the total byte count and a `_truncated` flag. When
`CONCORDE_SESSION_SELECTION` is set, the bridge reverifies the selection before reading its request.

## Build Python interface

| Name | Shape |
| --- | --- |
| `BuildOutput` | Frozen `{path, content: bytes, sources: tuple[str, ...]}` |
| `BuildResult` | Frozen `{outputs: tuple[BuildOutput, ...], manifest: bytes}` |
| `build(root, *, framework_prefix="")` | Pure render; raises `BuildError` |
| `write_build(root)`, `check_build(root)`, `verify_fresh(root)` | As described above |
| `recompute_protocol_manifest(root)` | Returns `protocol/manifest.json` with digests from the rendered assets, writing nothing |
| `load_model_instructions(root, name) -> ModelInstructions` | Frozen `{name, description, source_path, body, effects, binding}` for one domain Agent |

`BuildError(ValueError)` carries `code`: `invalid_build` by default, `stale_build`, and the Agent
resolution codes `unknown_agent` and `invalid_agent_binding`. `PromptResolverError(ValueError)`
carries `rule_id`.

## Package validation rules

`validate_package(root)` returns findings attributed to `module.distribution` with these rule
identities: `CONCORDE-PROMPT-*` (above, plus `CONCORDE-PROMPT-UNREACHABLE-001` and
`CONCORDE-PROMPT-NAME-001`), `CONCORDE-OPERATION-INVENTORY-001`, `CONCORDE-OPERATION-CONSTANTS-001`,
`CONCORDE-OPERATION-CONTEXT-001`, `CONCORDE-OPERATION-USES-001`, `CONCORDE-OPERATION-STATE-001`,
`CONCORDE-OPERATION-EXTERNALNAME-001`, `CONCORDE-OPERATION-GUIDANCE-001`,
`CONCORDE-OPERATION-DETERMINISTIC-001`, `CONCORDE-AGENT-PROFILE-001`, `CONCORDE-AGENT-SPEC-001`,
`CONCORDE-CONTRACT-SCHEMA-001`, `CONCORDE-CONTRACT-UNIQUE-001`, `CONCORDE-SPEC-OPERATIONS-001`,
`CONCORDE-SPEC-AGENTS-001`, `CONCORDE-SPEC-TYPES-001`, `CONCORDE-SPEC-ERRORS-001` (advisory),
`CONCORDE-BUILD-FRESH-001` and `CONCORDE-BUILD-DRIFT-001`. The Spec alignment rules read the
`concorde.operations` and `concorde.agents` metadata inventories that Operations and Agents keep
in their own Spec documents.
