from __future__ import annotations

import base64
import hashlib
import os
import zipfile
from pathlib import Path


LANGGRAPH_VERSION = "1.2.11"


def create_langgraph_index(root: Path) -> Path:
    """Create a tiny local wheel that exercises Concorde's linear LangGraph contract."""

    index = root / "runtime-index"
    index.mkdir(parents=True, exist_ok=True)
    wheel = index / f"langgraph-{LANGGRAPH_VERSION}-py3-none-any.whl"
    dist_info = f"langgraph-{LANGGRAPH_VERSION}.dist-info"
    files = {
        "langgraph/__init__.py": f'__version__ = "{LANGGRAPH_VERSION}"\n'.encode(),
        "langgraph/graph/__init__.py": _graph_source().encode(),
        f"{dist_info}/METADATA": (
            "Metadata-Version: 2.1\n"
            "Name: langgraph\n"
            f"Version: {LANGGRAPH_VERSION}\n"
            "Summary: Minimal Concorde installer test fixture\n"
        ).encode(),
        f"{dist_info}/WHEEL": (
            "Wheel-Version: 1.0\n"
            "Generator: concorde-tests\n"
            "Root-Is-Purelib: true\n"
            "Tag: py3-none-any\n"
        ).encode(),
        f"{dist_info}/top_level.txt": b"langgraph\n",
    }
    record_rows = []
    for name, content in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
        record_rows.append(f"{name},sha256={digest},{len(content)}")
    record_rows.append(f"{dist_info}/RECORD,,")
    files[f"{dist_info}/RECORD"] = ("\n".join(record_rows) + "\n").encode()
    with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            archive.writestr(name, content)
    return index


def runtime_install_environment(index: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_FIND_LINKS": str(index),
            "PIP_NO_INDEX": "1",
            "PYTHONNOUSERSITE": "1",
            "UV_OFFLINE": "1",
        }
    )
    return environment


def _graph_source() -> str:
    return '''from __future__ import annotations

START = "__start__"
END = "__end__"


class StateGraph:
    def __init__(self, state_type):
        self.state_type = state_type
        self.nodes = {}
        self.edges = {}

    def add_node(self, name, callback):
        self.nodes[name] = callback

    def add_edge(self, source, target):
        self.edges[source] = target

    def compile(self):
        return _CompiledGraph(dict(self.nodes), dict(self.edges))


class _CompiledGraph:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def invoke(self, state):
        value = dict(state)
        current = self.edges[START]
        while current != END:
            update = self.nodes[current](value)
            for key, item in update.items():
                if key == "capability_results":
                    value[key] = [*value.get(key, []), *item]
                else:
                    value[key] = item
            current = self.edges[current]
        return value
'''
