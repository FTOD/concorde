# Agents requirements

These obligations concern Agent identity, limits and interaction. Whether an Agent's result is
accepted is decided by the Module that owns that result.

## Identity

### req.agents.single-definition — One definition per Agent

Every callable Agent SHALL have exactly one canonical definition in this Module, from which its
discovery, rendering and admission are all derived.

The inventory and the `concorde.agents` metadata are two views of the same definitions, and
package validation compares them; see [Inventory metadata](contracts.md#inventory-metadata). A
projection that differs from its definition is refused, never used as a second authority.

### req.agents.family-boundary — Task subagents have no domain stage contract

A Task subagent SHALL NOT receive a domain stage input type, result type or single-Module grant
merely because it is an Agent.

Its limits come from its tools, its explicit extensions and the grant the user session supplies.

## Limits

### req.agents.terminal — No Agent delegates

Every Agent SHALL run without any tool or extension that delegates a task, starts another agent or
invokes a Concorde capability.

### req.agents.proposal-boundary — Results are proposals

An Agent SHALL report its progress and completion as its own claim, never as accepted domain
results or independent evidence.

A Domain Agent's structured output becomes a result only after the Host accepts it. A
maintenance-worker's self-checks are not independent tests, and a tester's observations cover only
the revision and scope it tested.

### req.agents.frozen-continuation — Frozen launch grants

A running Agent SHALL keep the instructions and grant it was launched with until the user session
has verified it stopped and released it.

## Distribution scope

### req.agents.source-only — Source-only assets stay in the source checkout

The maintenance-worker definition and the coordinator instructions SHALL NOT be included in a
consumer installation.

### req.agents.coordinator-user-session-only — Coordinator instructions reach only the user session

The coordinator instructions SHALL be loaded only by the source user session, never by a Task
subagent or a Domain Agent, whether fresh or resumed.
