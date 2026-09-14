#!/usr/bin/env python3
"""Deterministic check: every Flow Spec diagram matches the Flow Concorde compiles.

Each executable Flow (a LangGraph StateGraph built by a factory in the Flow catalog) has exactly
one Mermaid flowchart in the Specs bound to it with ``%% flow: <name>``. This check compiles the
catalog with inert nodes and reports every diagram whose nodes, edges, routing labels or state
labels disagree with the compiled topology, and every Flow that has no diagram.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def main() -> int:
    from concorde.development.flow_specs import flow_spec_findings
    from concorde.spec.repository import SpecRepository

    findings = flow_spec_findings(SpecRepository(ROOT, ROOT))
    for finding in findings:
        print(f"{finding.severity}: {finding.rule_id} {finding.source}: {finding.message}")
    print(f"{len(findings)} Flow Spec finding(s)")
    return 1 if any(finding.severity == "error" for finding in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
