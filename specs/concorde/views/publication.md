# Publication service

Publication turns registered specification sources into a human reading site. Start with a Module's
purpose, correct use and design, then follow the links to its precise obligations when implementing,
testing or reviewing it. The site does not generate a replacement summary or decide whether code
satisfies the specification.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Implementation Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Registry](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Two reading paths, one Module

**Module Specs** contains each Module entry and its explanatory topics, such as Registry or
Publication. **Implementation Specs** contains Module-owned requirements, scenarios and interface
contracts. Both sidebars follow the same registry parentage; topics do not become owners, and a
provider referenced by several consumers still has one canonical page under its own Module.

The source metadata's explicit document role determines the reading path. Both roles remain
human-readable, normative Spec content and remain in the Module's complete agent context. Opening a
tab grants no new implementation access. Page provenance identifies the owner, source members and
inclusion reasons; reading-path links connect explanation pages with the owner's detailed specs.

A document keeps its source-derived route when only its role changes. Moving definitions into a
new document preserves their stable IDs but requires updating the path in links and any explicit
document references. The publisher validates the resulting pages and anchors rather than inventing
historical ownership or silently removing broken navigation.

## Creating and publishing a site

For a new project, request a scaffold proposal, review the exact files and then apply it while the
proposal is still current. Scaffolding is creation-only: it cannot overwrite an existing site or
change business Specs. Prepare the site's dependencies separately; a prerequisite report does not
install them on the developer's behalf.

Builds materialize registered Markdown and paired metadata into a disposable candidate, render
inline Mermaid diagrams, validate source freshness and all internal links, then promote the whole
checked directory. A failed or stale candidate leaves the last successfully published site intact.
Rebuilding removes obsolete generated pages only as part of successful promotion. The
[pipeline](pipeline.md) explains why admission, materialization and promotion are separate steps.

## Project documentation outside the Spec

A project can add an introduction and independent custom-documentation tabs. These are suitable for
onboarding, manuals and project-owned interactive pages, not for hiding Module obligations outside
registered context. Custom docs cannot contain registered Spec sources or conflict with Spec routes.
Concorde's independent Protocol chapters and Agent Flows page use this extension mechanism; they are
not copied into consumer projects by the generic scaffold.

Publication ignores retired unregistered instruction/wire projections, and exposes no standalone
Module/Scenario graph page. UA export and the official viewer are independent developer tools;
inline authored diagrams remain available in registered and custom documentation.

## Precise specifications

The Views Module owns the exact [publication scenarios](scenarios.md#publication-service),
[Module-wide requirements](requirements.md), and
[scaffold exchange](contracts.md#publication-scaffold-proposal-exchange-and-ownership).
Those contracts define configuration fields, failure outcomes and compatibility rules once.
Production and preview keep separate Docusaurus module caches, while both derive reading from the
current registered source model.
