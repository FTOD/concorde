# One-Command Installer CLI Contract

## Purpose

Provide an inspectable convenience command that initializes or reuses one Spec Kit project and
installs the selected Concorde release through Spec Kit's native bundle lifecycle.
After component installation it invokes only the deterministic agent projector shipped by that
installed extension.

## Invocation

```text
uvx --from specify-cli==0.16.4 python install-concorde.py
  [--target PATH]
  [--integration NAME]
  [--integration-options TEXT]
  [--version VERSION | --checkout PATH]
  [--preview]
```

`--target` defaults to the current directory. A fresh target requires `--integration`; an existing
project reuses its recorded default and rejects a different explicitly requested integration.
`--version` selects an immutable published pointer and `--checkout` selects a verified local build;
without either, the current published pointer is used.

## Information

Input carries target, integration intent, release selection, and preview intent. Output carries the
resolved release and supported Spec Kit range, ordered public operations, expanded native bundle
plan, catalog reconciliation decisions, installed component identities and versions, reload status,
native agent target paths/digests/actions/conflicts, projection verification/receipt, next workflow
step, or a failure stage with remediation and residual-state summary.

## Obligations

- The command MUST run with the pinned Spec Kit 0.16.4 tool environment and MUST invoke component
  lifecycle behavior only through public `specify` commands.
- Preview MUST resolve the native expanded bundle information in a disposable project and MUST NOT
  create or change the target. It MUST install the candidate bundle only in that disposable project
  and use its installed projector to preview exact target actions.
- Apply mode MUST initialize only a fresh empty target, preserve an existing integration and authored
  sources, and reconcile only its managed catalog identity: permanent `concorde` entries in
  published mode or transient `concorde-dev` entries in development mode.
- The command MUST print native bundle information before install or update.
- After bundle install/update/no-op, apply MUST run installed `agent-assets preview`, stop on
  conflicts, run `sync`, run `verify`, and report terminal success only when verification succeeds.
- Projection MUST preserve config, plans, worktrees, logs, inactive integrations, unrelated files,
  modified/unowned targets, and user permission settings according to the Feature 005 receipt
  contract.
- A missing bundle MUST use native install; a different installed version MUST use native update; an
  equal installed version MUST perform no target write.
- Development mode MUST build and verify the checkout, serve catalogs only on loopback for the run,
  use the same catalog/bundle sequence, remove all three `concorde-dev` registrations through public
  Spec Kit commands, preserve permanent `concorde` and unrelated sources, and always stop the server.
- A success report MUST name the bundle, preset, extension, versions, reload requirement, and next
  Concorde workflow step, plus projection status, output count, and receipt.

## Exit Status and Failure Semantics

| Status | Meaning |
|---:|---|
| `0` | Preview completed, installation/update completed, or the installation was already current |
| `2` | Request or target validation failed before lifecycle work |
| `3` | Release discovery, build, or verification failed |
| `4` | Spec Kit initialization/catalog/component work or agent projection/verification failed |

Every non-zero result names the failed stage, a remediation, and any known partial target state. It
never prints a success outcome. Temporary files and a development catalog server are cleaned up on
all exits. Native Spec Kit diagnostic output remains visible and is not rewritten into a different
error classification.

## Compatibility

Contract version 1 supports POSIX invocation through `uvx` and Spec Kit 0.16.4. Adding optional
arguments or report fields is compatible. Changing default source selection, either mode's managed
catalog identity or lifetime, action selection, agent target/ownership rules, required inputs, or
exit meanings is breaking.

## Evidence

Unit tests cover pointer validation, request conflicts, catalog-state classification, action
selection, reports, and cleanup. Checkout-isolated acceptance tests compare native and one-command
registries/materialized files, run three repeats, prove preview target hashes are unchanged, exercise
development mode, parse Claude/Codex projections, preserve shared/inactive/modified state, and seed
discovery, integration, component, ownership, and projection failures.
