#!/usr/bin/env python3
"""Deterministic check: every Graph Spec diagram matches the Graph Concorde compiles.

Each executable Graph (a LangGraph StateGraph built by a factory in the Graph catalog) has exactly
one Mermaid flowchart in the Specs bound to it with ``%% graph: <name>``. This check compiles the
catalog with inert nodes and reports every diagram whose nodes, edges, routing labels or state
labels disagree with the compiled topology, and every Graph that has no diagram. It also holds
the Graph API rule: a catalog Graph that is not a compiled StateGraph, or a Python file under
``src/`` or ``scripts/`` that imports LangGraph's Functional API (``langgraph.func``), is an
error; the files are parsed, never executed.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def main() -> int:
    from concorde.harness.graph_specs import graph_spec_findings
    from concorde.spec.repository import SpecRepository

    findings = graph_spec_findings(SpecRepository(ROOT, ROOT))
    for finding in findings:
        print(
            f"{finding.severity}: {finding.rule_id} {finding.source}: {finding.message}"
        )
    print(f"{len(findings)} Graph Spec finding(s)")
    return 1 if any(finding.severity == "error" for finding in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
