# Agents requirements

These obligations concern Agent identity and interaction; business acceptance remains with each domain owner.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Agent](../module.md#terminology) | Defined in Concorde Framework. |
| [Domain Agent](module.md#terminology) | Defined in Agents. |
| [Task subagent](../module.md#terminology) | Defined in Concorde Framework. |

### req.agents.single-definition — One Agent authority

Every callable Pi Agent SHALL have one canonical Agents-owned definition consumed by discovery, rendering and admission.

### req.agents.family-boundary — Family-specific grants

A Task subagent SHALL NOT acquire a domain stage schema or implicit single-Module authority merely by being an Agent.

### req.agents.terminal — No Agent delegation

Every defined Agent SHALL remain terminal with respect to task delegation under its actual tool and file grant.

### req.agents.proposal-boundary — Evidence is not self-acceptance

An Agent SHALL distinguish its progress and proposed completion from independently accepted domain or testing evidence.

### req.agents.frozen-continuation — Frozen grant continuity

Continuation SHALL preserve the active Agent's frozen launch grant until an explicitly authorized stopped-owner handoff.
