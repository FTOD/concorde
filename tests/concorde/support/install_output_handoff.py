"""Source-only test recipe: admit selected source, test its explicit disposable install output.

This is not a production selection mode or installer fallback. Source selection remains in the
parent; only the explicitly scoped subprocess environment crosses to receipt-verified output.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from tests.concorde.support.environment import scrub_selection

SOURCE = Path(__file__).resolve().parents[3]


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def output_environment(environment: dict[str, str]) -> dict[str, str]:
    """Local copy only. These values attest the source, not a newly installed output."""
    # The shared scrub removes the selection, native project root, worker policy and the
    # Concorde binding; an installed output must additionally run its own interpreter paths.
    result = scrub_selection(environment)
    for key in ("PYTHONPATH", "PYTHONHOME"):
        result.pop(key, None)
    if result.get("CONCORDE_STUDIO_URL"):
        raise ValueError("installation fixture cannot redirect to Studio")
    return result


def install_selected_fixture(target: Path, selection: Path) -> tuple[dict, dict]:
    from concorde.distribution.local_installation import admit_package
    from concorde.distribution.session_selection import load_selection

    # Requiring issued tester scratch prevents this helper from becoming a general cross-root bypass.
    scratch = Path(os.environ["CONCORDE_CHECK_TMPDIR"])
    target = target.absolute()
    if (
        target.resolve() != target
        or not target.is_relative_to(scratch.resolve())
        or target == scratch.resolve()
    ):
        raise ValueError(
            "installed test output must be an exact child of issued tester scratch"
        )
    if target.exists() and any(target.iterdir()):
        raise ValueError("fresh empty installation output required")
    active = os.environ.get("CONCORDE_SESSION_SELECTION")
    if active != str(selection):
        raise ValueError("explicit governing source selection must remain active")
    selected = load_selection(SOURCE, selection)
    if selected["mode"] != "test":
        raise ValueError(
            "only explicit source test selection permits this fixture handoff"
        )
    admitted = admit_package(SOURCE)
    environment = output_environment(dict(os.environ))
    target.mkdir(parents=True, exist_ok=True)
    # This exact source was admitted above; no installed code is treated as selected source.
    installed = subprocess.run(
        [
            sys.executable,
            "-I",
            str(SOURCE / "scripts/install-concorde.py"),
            "--target",
            str(target),
            "--apply",
            "--format",
            "json",
        ],
        cwd=target,
        env=environment,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    if installed.returncode:
        raise RuntimeError(
            f"explicit fixture installation failed (exit {installed.returncode}); no output provenance issued"
        )
    framework = target / ".concorde/framework"
    python = target / ".concorde/.venv/bin/python"
    code = """import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from concorde.distribution.local_installation import verify_installation
v=verify_installation(Path.cwd())
print(json.dumps(dict(package=v.package.identity,framework=str(v.framework),entry=str(v.pi_entry),runtime=str(v.launcher),python=str(v.python),prefix=sys.prefix,receipt_digest=v.receipt_digest,runtime_digest=v.runtime_digest)))
"""
    checked = subprocess.run(
        [str(python), "-I", "-c", code, str(framework / "src")],
        cwd=target,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if checked.returncode:
        raise RuntimeError(
            f"installed fixture verification failed (exit {checked.returncode}); no output provenance issued"
        )
    output = json.loads(checked.stdout)
    if (
        output["package"] != admitted.identity
        or output["prefix"] != str(target / ".concorde/.venv")
        or output["python"] != str(python)
    ):
        raise ValueError(
            "installed output identity/interpreter differs from admitted source"
        )
    if (
        load_selection(SOURCE, selection) != selected
        or admit_package(SOURCE) != admitted
    ):
        raise ValueError("source changed during installation handoff")
    entry = Path(output["entry"])
    text = entry.read_text().split("const CATALOG: SessionCatalog = ", 1)[1]
    catalog, end = json.JSONDecoder().raw_decode(text)
    record = {
        "schema_version": 1,
        "source": str(SOURCE),
        "recipe_digest": sha(Path(__file__)),
        "source_selection": str(selection),
        "selection_digest": sha(selection),
        "source_build_digest": selected["build_digest"],
        "destination": str(target),
        "installed": output,
        "entry_digest": sha(entry),
        "catalog_digest": "sha256:" + hashlib.sha256(text[:end].encode()).hexdigest(),
        "catalog_schema": catalog["schema_version"],
        "launcher_digest": sha(Path(output["runtime"])),
        "installed_build_digest": sha(framework / "generated/build-manifest.json"),
        "separated_environment_keys": [
            "CONCORDE_SESSION_SELECTION",
            "PI_SUBAGENT_EXTENSION_BINDINGS.concorde/1",
            "CONCORDE_NATIVE_PROJECT_ROOT",
            "PYTHONPATH",
            "PYTHONHOME",
        ],
    }
    raw = json.dumps(record, indent=2)
    if len(raw.encode()) >= 8000:
        raise ValueError("handoff summary too large")
    evidence = scratch / "installed-output-provenance.json"
    with evidence.open("x") as stream:
        os.chmod(evidence, 0o600)
        stream.write(raw)
    return record, environment
