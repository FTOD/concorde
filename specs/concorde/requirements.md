# Concorde Framework requirements

These precise specifications belong directly to the [Concorde Framework Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                             | Meaning / definition               |
| ------------------------------------------------ | ---------------------------------- |
| [Module](module.md#terminology)                  | Defined in Concorde Framework.     |
| [Spec](module.md#terminology)                    | Defined in Concorde Framework.     |
| [Operation](module.md#terminology)               | Defined in Concorde Framework.     |
| [Candidate](module.md#terminology)               | Defined in Concorde Framework.     |
| [Context](module.md#terminology)                 | Defined in Concorde Framework.     |
| [Grant](module.md#terminology)                   | Defined in Concorde Framework.     |
| [Worker](module.md#terminology)                  | Defined in Concorde Framework.     |
| [Host](module.md#terminology)                    | Defined in Concorde Framework.     |
| [Issue](module.md#terminology)                   | Defined in Concorde Framework.     |
| [Initialization](spec/initialize.md#terminology) | Defined in Project initialization. |
| [Delivery](module.md#terminology)                | Defined in Concorde Framework.     |
| [Ready](module.md#terminology)                   | Defined in Concorde Framework.     |

## Concorde Framework

### req.concorde.routing-no-access — No access beyond frozen context

An explicit target or scenario focus SHALL NOT by itself grant file access beyond the selected Module's
frozen context.

### req.concorde.read-no-mutate — No mutation from read operations

A read or preview operation SHALL NOT modify project Specs, implementation or topology.

A worker may explicitly report a classified Issue through its host reporting tool; that limited
bookkeeping effect grants no project-file write authority to the worker. Policy previews and
queries of stored issue metadata remain free of issue-creation effects.

### req.concorde.versioned-result — Versioned result per invocation

Every invocation SHALL return a versioned operation result that distinguishes admission failure,
execution failure and the domain outcome.

### req.concorde.preserve-user-content — Preservation of developer-owned content

Installation and configuration changes SHALL preserve content the developer owns.

### req.concorde.no-overwrite-initialized — No overwrite of initialized projects

Initialization SHALL NOT overwrite an already-initialized project.

### req.concorde.delivery-separate — Delivery as a separately authorized step

Delivery to a destination SHALL require a separately authorized transition beyond a ready candidate.

### req.concorde.unsupported-explicit — Explicit failure for unsupported versions

An unsupported operation version or integration SHALL fail explicitly rather than degrading
silently.

### req.concorde.no-stale-replay — No replay of stale effects

A repeated mutation SHALL re-admit current saved state or require a fresh proposal rather than
replaying a stale effect.
