"""LangGraph dev entry points bound to this source checkout."""
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.capabilities.operation_data import OPERATION_CONTRACTS
from concorde.capabilities.studio import build_studio_graph

for operation in OPERATION_CONTRACTS:
    globals()[operation.replace("-", "_")] = build_studio_graph(operation, PACKAGE_ROOT, PACKAGE_ROOT)
