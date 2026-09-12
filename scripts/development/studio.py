"""LangGraph dev entry points bound to this source checkout.

Graphs are derived from ``skills/`` (one graph per skill, named by the skill), not from the
capability registry: the build's ``generated/langgraph.json`` names these same functions.
"""
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from concorde.harness.studio import build_studio_flow

SKILL_NAMES = tuple(sorted(
    path.parent.name for path in (PACKAGE_ROOT / "skills").glob("*/SKILL.md")
))

for _skill_name in SKILL_NAMES:
    globals()[_skill_name.replace("-", "_")] = build_studio_flow(_skill_name, PACKAGE_ROOT, PACKAGE_ROOT)
