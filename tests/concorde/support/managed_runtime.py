from __future__ import annotations

import base64
import hashlib
import os
import sys
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
    tools = _create_viewer_tools(index.parent)
    environment = os.environ.copy()
    environment.update(
        {
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_FIND_LINKS": str(index),
            "PIP_NO_INDEX": "1",
            "PYTHONNOUSERSITE": "1",
            "UV_OFFLINE": "1",
            "PATH": str(tools) + os.pathsep + environment.get("PATH", ""),
        }
    )
    return environment


def _create_viewer_tools(root: Path) -> Path:
    tools = root / "viewer-tools"
    tools.mkdir(parents=True, exist_ok=True)
    node = tools / ("node.cmd" if os.name == "nt" else "node")
    npm = tools / ("npm.cmd" if os.name == "nt" else "npm")
    if os.name == "nt":  # pragma: no cover - Windows CI uses the real command shim shape
        node.write_text(f'@"{sys.executable}" "%~dp0\\node.py" %*\n', encoding="utf-8")
        npm.write_text(f'@"{sys.executable}" "%~dp0\\npm.py" %*\n', encoding="utf-8")
        node_script = tools / "node.py"
        npm_script = tools / "npm.py"
    else:
        node_script = node
        npm_script = npm
    node_script.write_text(
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import json,sys\n"
        "if sys.argv[1:] == ['--version']:\n"
        "    print('v20.11.1')\n"
        "else:\n"
        "    print('FAKE NODE ' + json.dumps(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    npm_script.write_text(
        f"#!{sys.executable}\n"
        "from __future__ import annotations\n"
        "import json,sys\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "if args == ['--version']:\n"
        "    print('10.8.2')\n"
        "    raise SystemExit(0)\n"
        "if '--prefix' not in args or 'ci' not in args:\n"
        "    print('unsupported fake npm invocation', file=sys.stderr)\n"
        "    raise SystemExit(2)\n"
        "root = Path(args[args.index('--prefix') + 1])\n"
        "package = root / 'node_modules/understand-anything-viewer'\n"
        "(package / 'bin').mkdir(parents=True, exist_ok=True)\n"
        "(package / 'dist').mkdir(parents=True, exist_ok=True)\n"
        "(package / 'bin/viewer.mjs').write_text('// fixture viewer\\n', encoding='utf-8')\n"
        "(package / 'dist/index.html').write_text('<!doctype html>fixture\\n', encoding='utf-8')\n"
        "(package / 'README.md').write_text('fixture viewer\\n', encoding='utf-8')\n"
        "(package / 'package.json').write_text(json.dumps({\n"
        "    'name': 'understand-anything-viewer',\n"
        "    'version': '2.9.0',\n"
        "    'engines': {'node': '>=18'},\n"
        "    'bin': {'understand-anything-viewer': 'bin/viewer.mjs'},\n"
        "}), encoding='utf-8')\n",
        encoding="utf-8",
    )
    for path in (node_script, npm_script):
        path.chmod(0o755)
    return tools


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
