"""LangGraph dev entry points bound to this source checkout.

Graphs are derived from the Operation guidance under ``prompts/operation-guidance/`` (one graph per public Operation, named
by the Operation), not from the operation registry: the build's ``generated/langgraph.json`` names
these same functions.
"""

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.harness.studio import build_studio_graph

PUBLIC_OPERATIONS = tuple(
    sorted(
        path.stem for path in (PACKAGE_ROOT / "prompts/operation-guidance").glob("*.md")
    )
)

for _operation_name in PUBLIC_OPERATIONS:
    globals()[_operation_name.replace("-", "_")] = build_studio_graph(
        _operation_name, PACKAGE_ROOT, PACKAGE_ROOT
    )
