# Distribution requirements

These precise specifications belong directly to the [Distribution Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |
| [Installation](installation.md#terminology) | Defined in Installing and updating Concorde. |
| [Update](installation.md#terminology) | Defined in Installing and updating Concorde. |
| [Installation receipt](installation.md#terminology) | Defined in Installing and updating Concorde. |
| [Protocol binding](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |

## Distribution

### req.distribution.no-silent-protocol-rewrite — No silent Protocol rebinding

Install or update SHALL NOT silently rewrite a consumer's Protocol binding.

### req.distribution.explicit-binding-decision — Changed Protocol assets need explicit acceptance

A package with changed Protocol assets SHALL require the consumer's explicit binding decision
before execution.

### req.distribution.build-idempotent — Build output is deterministic and idempotent

`build` and `build --check` SHALL be idempotent and byte-identical across repeated runs.

### req.distribution.build-no-io — Build performs no network or process I/O

`build` and `build --check` SHALL perform no network or process I/O.

### req.distribution.one-worktree-build — Build stays within its own worktree

Every build invocation SHALL operate only on the worktree containing its named sources.

### req.distribution.no-cross-worktree-build — No cross-worktree build output

Build SHALL NOT point one worktree's build at another worktree's outputs.

### req.distribution.checkout-skills-user-invoked — Source-checkout Skills wait for the developer

Build SHALL render the source checkout's own Claude Skill projections as user-invocable only,
hidden from model-initiated invocation.

Developing the Concorde checkout is direct developer-authorized maintenance by default; a Concorde
graph runs on the checkout only when the developer explicitly asks for it. The installed consumer
projection is unaffected and stays model-invocable.

### req.distribution.pi-session-public-only — The Pi session tool exposes only public Operations

The Pi session extension SHALL offer exactly the public Operations as the operations of its
`concorde` tool.

Internal stage Operations have no Skill and no tool entry; the source checkout's shim additionally
tells the model to run an Operation only on the developer's explicit request, as the Claude Skill
projection is hidden from model invocation there.

### req.distribution.launcher-sigterm-cancels — SIGTERM cancels the launcher like Ctrl-C

The launcher SHALL treat SIGTERM as a host interrupt that cancels a running worker and prints the
result envelope before exiting.

A developer's client, such as the Pi session extension aborting a turn, ends a run it no longer
wants with SIGTERM; dying mid-write would leave the worker process and the change's lifecycle
record behind.

### req.distribution.root-block-ownership — Root rule ownership is block-scoped

A root rule entry SHALL be owned only within its exact bounded block, including its separator.

### req.distribution.no-surrounding-text-rewrite — Surrounding user text stays untouched

Installation SHALL NOT hash or replace user text surrounding an owned root block.

### req.distribution.rollback-on-failure — Installation rolls back atomically on failure

A runtime or setup failure during installation SHALL roll back root bytes, modes and the receipt
together with the other installation outputs.

### req.distribution.guard-inspects-text — Guard decides from the submitted command text

The worktree guard SHALL decide from the submitted command text, including global git options such
as `-C` and `--git-dir=`.

### req.distribution.guard-not-agent-reliant — Guard does not rely on agent memory

The worktree guard SHALL NOT depend on an agent remembering the policy.

### req.distribution.guard-checkout-only — Guard protects only this checkout's sessions

The worktree guard SHALL protect only developer sessions of this source checkout.

### req.distribution.guard-not-in-consumer-projects — Guard is excluded from consumer projects

The worktree guard SHALL NOT be installed into consumer projects.
