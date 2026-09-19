from __future__ import annotations

import base64
import hashlib
import os
import sys
import sysconfig
import zipfile
from pathlib import Path

LANGGRAPH_VERSION = "1.2.11"


def create_langgraph_index(root: Path) -> Path:
    """Create a tiny local wheel that satisfies the locked ``langgraph==<version>`` requirement.

    The wheel carries only the distribution metadata and one ``.pth`` file that puts this test
    process's own site-packages, where the real LangGraph and its dependencies are installed, on
    the managed runtime's path. A runtime provisioned from this index therefore runs the real
    host inside ``.concorde/.venv``, as a consumer's does, without a network install; the
    launcher's ``--runtime-check`` and re-execution into that runtime are exercised for real.
    """

    index = root / "runtime-index"
    index.mkdir(parents=True, exist_ok=True)
    wheel = index / f"langgraph-{LANGGRAPH_VERSION}-py3-none-any.whl"
    dist_info = f"langgraph-{LANGGRAPH_VERSION}.dist-info"
    files = {
        "concorde_test_runtime.pth": (sysconfig.get_paths()["purelib"] + "\n").encode(),
        f"{dist_info}/METADATA": (
            "Metadata-Version: 2.1\n"
            "Name: langgraph\n"
            f"Version: {LANGGRAPH_VERSION}\n"
            "Summary: Concorde installer test fixture forwarding to the test environment\n"
        ).encode(),
        f"{dist_info}/WHEEL": (
            b"Wheel-Version: 1.0\n"
            b"Generator: concorde-tests\n"
            b"Root-Is-Purelib: true\n"
            b"Tag: py3-none-any\n"
        ),
        f"{dist_info}/top_level.txt": b"langgraph\n",
    }
    record_rows = []
    for name, content in files.items():
        digest = (
            base64.urlsafe_b64encode(hashlib.sha256(content).digest())
            .rstrip(b"=")
            .decode()
        )
        record_rows.append(f"{name},sha256={digest},{len(content)}")
    record_rows.append(f"{dist_info}/RECORD,,")
    files[f"{dist_info}/RECORD"] = ("\n".join(record_rows) + "\n").encode()
    with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            archive.writestr(name, content)
    return index


def runtime_install_environment(index: Path) -> dict[str, str]:
    tools = _create_npm_tools(index.parent)
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


def _create_npm_tools(root: Path) -> Path:
    tools = root / "npm-tools"
    tools.mkdir(parents=True, exist_ok=True)
    npm = tools / ("npm.cmd" if os.name == "nt" else "npm")
    if (
        os.name == "nt"
    ):  # pragma: no cover - Windows CI uses the real command shim shape
        npm.write_text(f'@"{sys.executable}" "%~dp0\\npm.py" %*\n', encoding="utf-8")
        npm_script = tools / "npm.py"
    else:
        npm_script = npm
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
        "if root.name != 'pi':\n"
        "    print('unsupported fake npm prefix', file=sys.stderr)\n"
        "    raise SystemExit(2)\n"
        "lock = json.loads((root / 'package.json').read_text(encoding='utf-8'))\n"
        "subagents = root / 'node_modules/pi-subagents'\n"
        "subagents.mkdir(parents=True, exist_ok=True)\n"
        "(subagents / 'index.ts').write_text('// fixture pi-subagents\\n', encoding='utf-8')\n"
        "(subagents / 'package.json').write_text(json.dumps({'name': 'pi-subagents',\n"
        "    'version': lock['dependencies']['pi-subagents']}), encoding='utf-8')\n",
        encoding="utf-8",
    )
    npm_script.chmod(0o755)
    return tools
