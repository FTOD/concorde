# Requirements Checklist: Create Unified Project Docsite

**Purpose**: Requirements-quality review of the docsite scaffold and publication design.
**Created**: 2026-09-03
**Feature**: [specs/concorde/features/002-auto-docsite.md](../../../../specs/concorde/features/002-auto-docsite.md)

**Note**: This built-in checklist is maintained by `$concorde-specify` and `$concorde-clarify`.
**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.
**Marker Semantics**: `[x]` means the criterion has been reviewed and satisfied for requirements quality. It does not mean implementation work is complete.

## Outcome and Boundaries

- [x] CHK001 The outcome names an observable result for both the bootstrapping maintainer and the publishing maintainer.
- [x] CHK002 Prerequisite installation, template upgrade, hosting, and content authoring are explicitly out of scope.
- [x] CHK003 The scaffold is defined as a propose/apply cycle separate from Initialization Proposal 3, so the initialization feature needs no change.

## Interfaces

- [x] CHK004 Every provided interface in front matter is defined; the required interfaces are owned by the auto-docs and distribution features.
- [x] CHK005 Scaffold inputs list their defaults precisely enough to test, including the GitHub Pages URL and base-path derivation.
- [x] CHK006 Scaffold outputs enumerate the applied paths and the single project-owned identity file.
- [x] CHK007 Collision, symlink, stale-proposal, unconfigured-project, and package-inventory failures are specified as non-success without writes.
- [x] CHK008 Publication obligations state that project identity is read only from the identity file, keeping the adapter byte-identical across projects.

## Requirements and Evidence

- [x] CHK009 FR-006 through FR-010 and both NFRs are individually testable from a checkout, an extracted archive, and an installed framework copy.
- [x] CHK010 FR-009 defines a minimal end-to-end evidence case: a project holding only Initialization Proposal 3 outputs.
- [x] CHK011 The Package Manifest 2 inventory change is surfaced as an architecture assumption rather than defined inside the feature.
- [x] CHK012 The site identity schema 1 field list and the Docsite Scaffold Proposal 1 record shape are fixed by planning before implementation.

## Notes

- CHK012 was satisfied by planning: `data-model.md` in this attempt fixes site identity schema 1
  and Docsite Scaffold Proposal 1.
- `$concorde-implement` reads checklist checkbox state as a gate and must not modify markers.
