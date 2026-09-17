---
audience: worker
---

Author one complete Module contract with a readable subset. Its module.md starts with level-2
Purpose, Usage, Design and Relationships, followed by optional explanatory topics. The entry and
topic companions have `document.role: module`; never define req.*, scenario.* or concorde-contract
there. Put precise definitions in `document.role: implementation` companions owned directly by the
same Module, with schema-2 paired metadata. A topic is not a new owner. Companions need no enclosing
usage/architecture parts. Explain correct use before detailed
cases, and design before inventories. Consumers may be Modules, and a logical responsibility need
not invent an API. Internal security, concurrency and compatibility obligations remain readable and
normative. Missing meaning is an explicit gap, never inferred from implementation code.

Each registered Markdown path owns a paired `.md.json` source under the same document identity and
owner. Identity, entity/file bindings, dependency provider IDs and interface participant identities
are metadata. Their responsibilities, use conditions, guarantees and obligations belong in readable
prose with local identity anchors. Metadata refers to that meaning rather than copying it. Group
adjacent entity anchors on one line for a coherent shared explanation; do not turn an entity JSON
inventory into another giant reading catalog. The complete context includes both members of every
owned or explicitly referenced unit, without recursive inclusion or a reading-only shortcut.

Requirements are Module-wide stable-ID heading sections with one decidable SHALL sentence.
Scenarios have ordered GIVEN/WHEN/THEN/AND/BUT steps and keep situation-specific guarantees in their
steps or prose. A requirement never belongs to a scenario. A canonical `concorde-contract` definition
keeps schema, semantics and example once; participant metadata binds ID/version/role/peer to local
readable obligations. Necessary provider definitions must be included by explicit references.

Keep explanatory topics coherent and useful, not empty indexes or duplicate formal definitions.
Role labels never trim the complete context. Do not use the retired concorde.publication extension.

Return UTF-8 replacements in `documents` for changed owned reading and/or metadata members only.
They are validated together as one overlay, not independently. Referenced units remain read-only.
Ordinary authoring preserves document identity and ownership; topology authoring reconciles both
members with the accepted candidate registry. A topology author returns every candidate-owned
reading/metadata pair in document order. An inline Mermaid edit is part of its reading member, not
an external diagram artifact. Diagrams explain a stated scope using declared local entities and
labeled edges; they need not include the entire inventory. Stable-ID links must reach the canonical
reading definition. Tests declare scenario IDs in their own code; do not put verification test
locations in reading prose. File bindings in metadata grant neither contents nor write authority.
