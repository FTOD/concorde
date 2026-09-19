"""LangGraph dev entry points bound to this source checkout.

Graphs are derived from the Skill sources under ``prompts/skills/`` (one graph per skill, named
by the skill), not from the operation registry: the build's ``generated/langgraph.json`` names
these same functions.
"""

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.harness.studio import build_studio_graph

SKILL_NAMES = tuple(
    sorted(path.stem for path in (PACKAGE_ROOT / "prompts/skills").glob("*.md"))
)

for _skill_name in SKILL_NAMES:
    globals()[_skill_name.replace("-", "_")] = build_studio_graph(
        _skill_name, PACKAGE_ROOT, PACKAGE_ROOT
    )
