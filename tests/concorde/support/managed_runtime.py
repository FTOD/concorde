from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import zipfile
from collections.abc import Iterator, Mapping
from pathlib import Path

from tests.concorde.support.environment import scrub_selection

LANGGRAPH_VERSION = "1.2.11"
PI_LOCK = "pi/package-lock.json"
NPM_CACHE_VARIABLES = ("npm_config_cache", "NPM_CONFIG_CACHE")
SEED_LOCK = ".concorde-seed.lock"


class NpmSeedError(RuntimeError):
    """A locked Pi extension tarball is available from no local material."""


def locked_npm_tarballs(package: Path) -> list[tuple[str, str, str]]:
    """``(spec, resolved, integrity)`` for every locked dependency of the Pi worker extension."""
    lock = json.loads((package / PI_LOCK).read_text(encoding="utf-8"))
    entries = []
    for path, entry in lock.get("packages", {}).items():
        if not path or "resolved" not in entry or "integrity" not in entry:
            continue
        name = path.rsplit("node_modules/", 1)[-1]
        entries.append(
            (f"{name}@{entry['version']}", entry["resolved"], entry["integrity"])
        )
    return entries


def _content_path(cache: Path, integrity: str) -> Path:
    # cacache's content-addressed store: <cache>/_cacache/content-v2/<algorithm>/aa/bb/rest.
    # ``npm ci`` with a locked integrity reads a tarball from here, needing no index entry.
    algorithm, _, digest = integrity.partition("-")
    hexdigest = base64.b64decode(digest).hex()
    return (
        cache
        / "_cacache"
        / "content-v2"
        / algorithm
        / hexdigest[:2]
        / hexdigest[2:4]
        / hexdigest[4:]
    )


def _has_content(cache: Path, integrity: str) -> bool:
    path = _content_path(cache, integrity)
    if not path.is_file():
        return False
    algorithm, _, digest = integrity.partition("-")
    observed = hashlib.new(algorithm, path.read_bytes()).digest()
    return base64.b64encode(observed).decode() == digest


def _without_cache_variables(environment: Mapping[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in environment.items()
        if key.lower() != "npm_config_cache"
    }


def default_npm_cache(environment: Mapping[str, str]) -> Path:
    """npm's own cache location without any per-command override (``~/.npm`` unless configured)."""
    result = subprocess.run(
        ["npm", "config", "get", "cache"],
        env={
            **_without_cache_variables(environment),
            "NPM_CONFIG_UPDATE_NOTIFIER": "false",
        },
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return Path(result.stdout.strip()).expanduser()


def npm_cache_in_use(environment: Mapping[str, str]) -> Path:
    for key in NPM_CACHE_VARIABLES:
        if environment.get(key):
            return Path(environment[key]).expanduser()
    return default_npm_cache(environment)


@contextlib.contextmanager
def _seed_lock(cache: Path) -> Iterator[None]:
    # Parallel test workers share one cache: one of them seeds, the others wait and find it.
    path = cache / SEED_LOCK
    with path.open("a+") as handle:
        if (
            os.name == "nt"
        ):  # pragma: no cover - the Linux-only boundaries never run here
            yield
            return
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def seed_npm_cache(environment: Mapping[str, str], package: Path) -> Path:
    """Make every locked Pi extension tarball available to an offline ``npm ci`` from local bytes.

    The installer copies ``pi/package-lock.json`` and runs ``npm ci``; with ``NPM_CONFIG_OFFLINE``
    npm only accepts a cached tarball whose bytes match the locked integrity, so the extracted
    ``pi/node_modules`` cannot serve (packing it yields different bytes). The exact tarball is
    taken from a local populated npm cache: ``CONCORDE_TEST_NPM_CACHE`` when set, else npm's
    default cache, which the README bootstrap ``npm ci --prefix pi`` fills. It is added to the
    cache in use (``npm_config_cache``, the tester's issued scratch) with ``npm cache add``,
    once per cache under a file lock, never over the network. Missing material fails here with
    the input named, not later inside the installer.
    """
    cache = npm_cache_in_use(environment)
    needed = locked_npm_tarballs(package)
    cache.mkdir(parents=True, exist_ok=True)
    with _seed_lock(cache):
        missing = [item for item in needed if not _has_content(cache, item[2])]
        if not missing:
            return cache
        sources: list[Path] = []
        if environment.get("CONCORDE_TEST_NPM_CACHE"):
            sources.append(Path(environment["CONCORDE_TEST_NPM_CACHE"]).expanduser())
        sources.append(default_npm_cache(environment))
        sources = [source for source in sources if source.resolve() != cache.resolve()]
        for spec, resolved, integrity in missing:
            source = next((s for s in sources if _has_content(s, integrity)), None)
            if source is None:
                searched = ", ".join(str(source) for source in sources) or "nothing"
                raise NpmSeedError(
                    f"{spec} ({integrity[:19]}...) locked by {package / PI_LOCK} is neither in"
                    f" the npm cache in use ({cache}) nor in a local populated npm cache"
                    f" (looked in {searched}); the offline Pi extension install cannot fetch"
                    f" {resolved}. Populate npm's cache once with `npm ci --prefix pi` from the"
                    " README bootstrap, or point CONCORDE_TEST_NPM_CACHE at a populated cache."
                )
            with tempfile.TemporaryDirectory(prefix="concorde-npm-seed-") as temporary:
                tarball = Path(temporary) / (spec.replace("/", "-").strip("@") + ".tgz")
                shutil.copyfile(_content_path(source, integrity), tarball)
                subprocess.run(
                    ["npm", "cache", "add", str(tarball)],
                    env={
                        **_without_cache_variables(environment),
                        "npm_config_cache": str(cache),
                        "NPM_CONFIG_OFFLINE": "true",
                        "NPM_CONFIG_AUDIT": "false",
                        "NPM_CONFIG_FUND": "false",
                        "NPM_CONFIG_UPDATE_NOTIFIER": "false",
                    },
                    cwd=temporary,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=120,
                )
            if not _has_content(cache, integrity):
                raise NpmSeedError(
                    f"npm cache add did not store {spec} under its locked integrity in {cache}"
                )
    return cache


def independent_runtime_environment(root: Path, package: Path) -> dict[str, str]:
    """Real local dependencies for installed-admission tests, not forwarding-wheel doubles."""
    wheels = os.environ.get("CONCORDE_TEST_WHEELHOUSE")
    if wheels is None:
        wheels = str(root / "wheels")
        download = root / "download"
        subprocess.run(
            [sys.executable, "-m", "venv", str(download)],
            check=True,
            capture_output=True,
        )
        python = download / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "download",
                "--dest",
                wheels,
                "-r",
                str(package / "scripts/requirements.lock"),
            ],
            check=True,
            capture_output=True,
        )
    environment = {
        **scrub_selection(os.environ),
        "PIP_NO_INDEX": "1",
        "PIP_FIND_LINKS": wheels,
        "PYTHONNOUSERSITE": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "NPM_CONFIG_OFFLINE": "true",
    }
    # The offline install below can only read the cache; fill it from local bytes first.
    seed_npm_cache(environment, package)
    return environment


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
    environment = scrub_selection(os.environ)
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
        "typebox = root / 'node_modules/typebox'\n"
        "typebox.mkdir(parents=True, exist_ok=True)\n"
        "(typebox / 'build').mkdir()\n"
        "(typebox / 'build/index.mjs').write_text('// fixture typebox\\n', encoding='utf-8')\n"
        "(typebox / 'package.json').write_text(json.dumps({'name': 'typebox',\n"
        "    'version': lock['dependencies']['typebox']}), encoding='utf-8')\n",
        encoding="utf-8",
    )
    npm_script.chmod(0o755)
    npx = tools / ("npx.cmd" if os.name == "nt" else "npx")
    if (
        os.name == "nt"
    ):  # pragma: no cover - Windows CI uses the real command shim shape
        npx.write_text(f'@"{sys.executable}" "%~dp0\\npx.py" %*\n', encoding="utf-8")
        npx_script = tools / "npx.py"
    else:
        npx_script = npx
    # Poison stub: the Pi-only installer must never invoke an external Skills CLI.
    npx_script.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        "print('unexpected npx invocation: Concorde supports only Pi', file=sys.stderr)\n"
        "raise SystemExit(99)\n",
        encoding="utf-8",
    )
    npx_script.chmod(0o755)
    return tools
