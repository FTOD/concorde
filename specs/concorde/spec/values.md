# Identities and versions

The [Spec Module](module.md) uses different identities for responsibilities, documents and the inputs a task examined.
Understanding those differences prevents a familiar filename or successful old check from being
mistaken for the current contract.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Document unit | One reading document and its paired metadata, with one identity and Module owner. |
| Document role | Whether a unit explains the Module or gives its precise implementation specifications; neither role filters complete context. |
| Source-member role | Whether one file contains the reading or the metadata of a document unit. |
| Protocol binding | The project's explicit acceptance of a particular specification-language version and exact distributed rules. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Snapshot](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |
| [Requirement](../module.md#terminology) | Defined in Concorde Framework. |
| [Scenario](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Registry](../module.md#terminology) | Defined in Concorde Framework. |

## What stays the same and what changes

A Module identity names a responsibility. A document identity stays with its paired unit even when
its path or title changes. Requirement and scenario identities similarly name promises rather than
current heading text. This lets links, tests and review history refer to the intended contract.

A snapshot answers a different question: exactly which inputs were available for this task? Its
identity changes when relevant bytes or declarations change. Renaming a heading may preserve a
requirement's identity while still invalidating evidence tied to the old document bytes.

For example, a review that passed before a behavior edit remains useful history but cannot approve
the new behavior automatically. Re-resolving current inputs makes that distinction visible instead
of silently treating the old path as proof of freshness.

## Different versions serve different readers

The Protocol versions specification-language rules. Framework configuration, registry storage and
worker messages have separate compatibility versions. Their numbers need not match. Receiving new
installed rules is not the same as accepting them for a project; acceptance follows any required
migration. The precise version and configuration fields are in the
[configuration contract](contracts.md#values-framework-configuration-and-storage-versions).

Plans and task lists are workflow artifacts rather than additional software specifications. Their
valid shape alone does not prove they belong to this task or authorize implementation access. The
host checks their current relationship to the selected work before using them.

## Precise specifications

The Module-owned [value and selection interfaces](contracts.md#values-selection-and-returned-values),
[requirements](requirements.md) and [scenarios](scenarios.md) define exact records and rejection behavior.
