# Understand Anything viewer service

This deterministic service opens an existing raw Understand Anything knowledge graph with the
installer-owned official viewer. Its entry is `scripts/run-ua-graph-viewer.py` in the Framework package. It
is a developer tool, not an agent Capability or a new Skill, and it launches no model cognition.

```bash
python3 .concorde/framework/scripts/run-ua-graph-viewer.py --project-root . --no-open
```

| Argument | Contract |
| --- | --- |
| `--project-root PATH` | Project directory, default `.`; it must exist and must not itself be a symlink |
| `--port N` | Optional integer from 0 through 65535, forwarded to the official viewer |
| `--no-open` | Optional flag forwarded to the official viewer to suppress its browser opening |

### Relationships and routing

This service participates in Developer view and feedback. Its user-facing contract is owned here;
`module.distribution` supplies viewer provisioning under the Installation entity's ownership.
Changes to viewer launch or graph admission select this service. Changes to runtime acquisition,
package verification or recovery select `module.distribution` through an admitted Module routing
view. No graph or viewer action grants an agent access to another target's implementation. The
deterministic export of a graph skeleton this launcher can open is a separate command, described in
[ua-graph](ua-graph.md).

## Precise specifications

The Views Module owns the exact obligations and interface details in [contracts](contracts.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
