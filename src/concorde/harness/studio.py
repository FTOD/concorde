"""Optional Studio surface for the actual typed StateGraph Operation boundary."""

# The CLI loads this shipped file directly; neither source nor installed frameworks require
# editable package installation. Bind imports to this exact framework, not ambient modules.
import sys
from pathlib import Path

_source = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(_source), str(_source.parent)]
from concorde.harness.operation_node import OperationNode  # noqa: E402


def build_studio_graph(agent="context_assessor", *, launcher=None):
    """Trusted server configuration selects the terminal Agent service, never model State."""
    return OperationNode(agent).graph(launcher)


terminal_agent_operation = build_studio_graph()
