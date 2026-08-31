---
id: contract.auto-docs.build-interface
kind: contract
module: module.concorde.auto-docs
role: provided
flow: bidirectional
representation:
  kind: standard
  format: npm package scripts and process exit status
  version: 1
  definition: docsite/package.json
counterparties:
  - external.project-maintainer
consumers:
  - external.project-maintainer
features:
  - feature.auto-docs.publish-project-docsite
version: 1
evidence:
  tests:
    - docsite/tests/contract/build-interface.test.ts
evidence_status: verified
---

# Docsite build interface contract

## Purpose

Provide stable `inspect`, `validate`, `render-diagrams`, `start`, `test`, `build`, `typecheck`, and `check` operations from
the private `docsite/` npm project. Complete inputs, outputs, command semantics, and exit behavior are
defined in `specs/concorde/features/002-create-project-docsite/contracts/build-interface.md`.

## Information

Inputs are repository sources—including the installed `.agents/skills/archify` package—and command
arguments; outputs are diagnostics, normalized diagram receipts, preview responses, test results,
and verified static-site artifacts communicated through stdout, stderr, and exit status.

## Obligations

- Preview and production use one source registry and routing policy.
- Preview and production validate and deliver one complete declared diagram set before registry or
  Docusaurus consumption; no committed HTML prerequisite or stale fallback is allowed.
- Success is reported only after validation and promised output complete.
- Production candidates are promoted only after route and manifest verification.
- Commands do not write root `README.md` or beneath `docs/` or `specs/`; diagram and site outputs stay
  beneath ignored generated roots and require no hosted service or LLM.

## Failure Semantics

Non-zero status means the requested output is not current or complete. Diagnostics name the rule,
project-relative source, reason, and remediation.

## Compatibility

Command names, status meaning, and successful output locations remain stable for version 1.

## Evidence

The command contract and failure paths are exercised by `docsite/tests/contract/build-interface.test.ts`
and the production and atomic-promotion integration suites.
