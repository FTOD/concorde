---
title: Contributing to the Docsite
sidebar_position: 2
---

# Contributing to the Docsite

Architecture and feature sources belong in one hierarchical `specs/` tree; project documentation
belongs under `docs/`. At any module level, `module.md` and `contracts/**/contract.md` describe the
architecture boundary, while `features/<feature>/spec.md` describes a feature owned at that level.
The independent `docsite/` directory contains only rendering, validation, search, and presentation
code.

Because Docusaurus cannot apply two docs-plugin MDX pipelines to the same physical directory, preview
and build commands materialize ignored Architecture and Features projections under
`docsite/.generated/content/`. Never edit those projections; change the matching source under `specs/`.

Module and contract Markdown under `specs/` is published in the Architecture view. Feature `spec.md`
files are published in the Features view. A source that
declares `view` or `architecture_view` must point to maintained Archify JSON whose `meta.output`
identifies delivered HTML under `generated/`. The site embeds that HTML in a sandbox and keeps the
Markdown summary visible for accessibility and search.

## Authoring Markdown

Give every page either a `title` in YAML front matter or one level-one heading. Optional
`sidebar_position`, `sidebar_label`, and `slug` values control presentation without registering the
page in site configuration.

Use source-relative `.md` links. Links may cross collections—for example, the
[docsite feature specification](../../specs/concorde/features/002-create-project-docsite/spec.md)—and fragments are
preserved when the build rewrites a source path to a published route. A link to a noncanonical Spec
Kit artifact such as `plan.md` is rejected.

## Commands

From `docsite/`, run:

```bash
npm ci
npm run inspect
npm run validate
npm run start
npm run build
npm run check
```

`inspect` reports discovered and excluded sources. `validate` checks architecture view publication,
metadata, identity, routes, and links without writing source files. `start` validates before serving
a local preview. `build` renders
to a candidate directory, verifies it, then atomically promotes it to `docsite/build/`. The `check`
command runs type checks, tests, validation, and a production build.

## Troubleshooting

Validation errors include a rule ID, source path, reason, and remediation. Correct the canonical
Markdown source and rerun the command. If rendering fails, the previous successful `build/` remains
available; candidate output is never promoted after a failed verification.

Return to the [documentation overview](../index.md).
