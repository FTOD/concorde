"""Explicit optional LangGraph Operation; native business workflows are not mirrored."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from concorde.harness.studio import (
    terminal_agent_operation as terminal_agent_operation,  # noqa: E402
)
