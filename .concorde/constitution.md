# Concorde Constitution

Version: 17.0.0. Spec Protocol 6.0.0; Framework Profile 13; registry schema 4;
Workspace Protocol 15; Delivery Proposal 10.

## Protocol and Framework rule sources

The independent specification standard is authored under `protocol/`. Its principles, Module
chapter, Spec management (including Spec and Context), Required format and canonical templates
define the meaning and authored representation of project Specs. The standard is not itself a
registered software Module and need not describe its own chapters as Modules.

Concorde's execution profile is authored separately in `prompts/protocol/framework-profile.md`.
It defines configuration compatibility, bounded worker contexts, permissions, review evidence,
worktree handoffs and Framework authoring/publication conventions. The build combines these with
the Protocol into the rule assets. Source-checkout maintenance refreshes the tracked installed
copy through `python3 scripts/concorde.py protocol-manifest --write --bind-project` after building.
Read `.concorde/protocol/principles.md` as the canonical rule bundle, including P10; this document
references those authorities rather than maintaining another copy of their requirements.

## Project application

The explicit registry is `.concorde/specs.json`, with `module.concorde` as its entry Module.
Every Module owns an English Spec collection. Its `module.md` introduces **Usage & Contract**
for consumers, followed by **Architecture & Realization** for implementers. Usage explains correct
use before formal guarantees; Design explains how responsibilities, flow, state and constraints
fulfill them. Requirements and scenarios are defined once in the appropriate part with stable IDs.
Internal obligations remain normative. Companion documents may cover either or both parts, and
a logical Module need not invent a public API or physical package.

Document ownership and explicit one-level references determine full-file Spec context; part headings
are not context filters or permissions. Entity bindings separately record implementation entries,
and the registry mirrors their union. Several Modules may bind one file; within one Module the most
specific entry owns it. Phase-specific grants decide which workers receive implementation contents,
with code review and investigation read-only. Tests declare their scenario identities in code.
Structural checks and declared coverage are evidence, not semantic proof.

Concorde's source Specs, format validators, initializer, authored worker instructions, build and
publication implement the same reader-oriented model. The runtime and publisher accept Profile 13;
older projects need an explicit migration, not a silent installer rewrite or compatibility guess.
Existing wire versions, unique definition ownership, complete context and worktree authority remain
independent of this document-layout change. The source-checkout `AGENTS.md` governs direct
maintenance and worktree ownership, subject to explicit developer instructions such as no commit.

## Project diagrams and publication

Each Module's Architecture & Realization / Relationships subsection has an inline Mermaid
flowchart whose node labels are exactly its own entity titles and whose directed edges carry
relationship labels. English accessible titles and descriptions accompany Concorde diagrams.
Flow Specs describe execution separately from the entity relationship model. Publication preserves
both reader parts in source order, renders diagrams in place and puts derived implementation-file
listings in the internal part. Rendered pages and navigation create no second contract authority,
context inclusion or write grant.
