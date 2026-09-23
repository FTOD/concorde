"""Exact candidate Pi launch inputs, never evidence of loading or execution."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

from ..spec.typed_data import canonical, decode, safe_path
from .build import (
    BuildError,
    PI_SESSION_EXTENSION,
    PRIVATE_PI_SESSION_SHIM,
    check_build,
    verify_fresh,
)


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _exact(root: Path, path: Path, *, exists: bool = True) -> Path:
    if not path.is_absolute() or not path.is_relative_to(root):
        raise BuildError("selection requires exact absolute candidate paths")
    if path.resolve() != path or any(p.is_symlink() for p in (path, *path.parents)):
        raise BuildError(f"selection cannot cross an aliased path: {path}")
    if exists and not path.is_file():
        raise BuildError(f"selection requires a readable regular file: {path}")
    return path


def selection_path(root: Path, path: Path, *, exists: bool = True) -> Path:
    """Only candidate scratch can contain a saved selection; never a source or archive."""
    root = Path(os.path.abspath(root))
    _exact(root, path, exists=exists)
    if (
        not path.is_relative_to(root / ".concorde/work")
        or path == root / ".concorde/work"
    ):
        raise BuildError("selection belongs only in candidate .concorde/work scratch")
    return path


def select_session(candidate: Path, *, pi_entry: Path, runtime: Path) -> dict:
    """The test selection of one candidate: its exact private Pi entry, catalog and launcher."""
    # Relative candidate roots are convenient for the CLI, but aliases are not identities.
    root = Path(os.path.abspath(candidate))
    if (
        root.resolve() != root
        or any(p.is_symlink() for p in (root, *root.parents))
        or not root.is_dir()
    ):
        raise BuildError("candidate must be a real, non-aliased directory")
    if pi_entry is None:
        raise BuildError("a test selection requires the candidate's private Pi entry")
    manifest_path = _exact(root, root / "generated/build-manifest.json")
    manifest_bytes = manifest_path.read_bytes()
    try:
        manifest = decode(manifest_bytes.decode("utf-8"))
        if (
            type(manifest["schema_version"]) is not int
            or manifest["schema_version"] != 1
        ):
            raise ValueError("unsupported build manifest")
        # Validate every recorded path before freshness can read/evaluate any of them.
        for group in ("sources", "outputs"):
            for relative in manifest[group]:
                if (
                    not isinstance(relative, str)
                    or Path(relative).as_posix() != relative
                    or ".." in Path(relative).parts
                ):
                    raise ValueError("unsafe build path")
                safe_path(relative)
                _exact(root, root / relative)
    except (KeyError, TypeError, ValueError, UnicodeError) as error:
        raise BuildError(f"invalid selection manifest: {error}") from error
    # New source members must not smuggle a link into the pure current render either.
    for directory in (
        "src/concorde",
        "agents",
        "operations",
        "prompts",
        "protocol",
        "pi",
        "scripts",
    ):
        for current_root, directories, files in os.walk(
            root / directory, followlinks=False
        ):
            directories[:] = [
                name
                for name in directories
                if name not in {"node_modules", "__pycache__"}
            ]
            for name in [*directories, *files]:
                item = Path(current_root) / name
                if item.is_symlink():
                    raise BuildError(f"aliased candidate source: {item}")
    verify_fresh(root)
    current, differences = check_build(root)
    if not current:
        raise BuildError(f"candidate outputs are stale: {differences}", "stale_build")

    def recorded(path: Path, *, built: bool = False) -> dict:
        data = _exact(root, path).read_bytes()
        relative = path.relative_to(root).as_posix()
        expected = (
            manifest["outputs"].get(relative, {}).get("sha256")
            if built
            else manifest["sources"].get(relative)
        )
        if expected != _digest(data):
            raise BuildError(f"unrecorded or stale selection: {path}", "stale_build")
        return {"path": str(path), "digest": _digest(data)}

    runtime_record = recorded(runtime)
    if runtime != root / "scripts/run-operation.py":
        raise BuildError("private runtime must be the candidate launcher")
    if pi_entry != root / PRIVATE_PI_SESSION_SHIM:
        raise BuildError("only the exact private candidate Pi entry may be selected")
    entry = recorded(pi_entry, built=True)
    content = pi_entry.read_text(encoding="utf-8")
    match = re.search(
        r"const CATALOG: SessionCatalog = (\{.*?\n\});\n\nexport default",
        content,
        re.S,
    )
    if not match:
        raise BuildError("private Pi entry has no embedded catalog")
    # Exact embedded bytes, not just a subset of names or interpreted metadata.
    catalog_content = match.group(1)
    entry.update(
        content=content,
        catalog={
            "content": catalog_content,
            "digest": _digest(catalog_content.encode()),
        },
    )
    return {
        "schema_version": 2,
        "mode": "test",
        "candidate": str(root),
        "fresh_context": True,
        "fork_context": False,
        "discover_catalogs": False,
        "inherit_catalogs": False,
        "task_delegation": False,
        "build_digest": _digest(manifest_bytes),
        "runtime": runtime_record,
        "implementation": recorded(root / PI_SESSION_EXTENSION),
        "pi_entry": entry,
        "launch": {
            "cwd": str(root),
            "pi_args": [
                "--no-session",
                "--no-context-files",
                "--no-skills",
                "--no-prompt-templates",
                "--no-themes",
                "--no-extensions",
                "-e",
                str(pi_entry),
            ],
        },
        "execution_evidence": None,
    }


def load_selection(root: Path, path: Path) -> dict:
    """Reverify saved launch inputs; any other schema or field is refused."""
    try:
        value = decode(selection_path(root, path).read_text(encoding="utf-8"))
        if (
            type(value["schema_version"]) is not int
            or value["schema_version"] != 2
            or value["mode"] != "test"
        ):
            raise BuildError(
                "unsupported private selection schema; reselect the Pi entry"
            )
        expected = select_session(
            root,
            pi_entry=Path(value["pi_entry"]["path"]),
            runtime=Path(value["runtime"]["path"]),
        )
    except BuildError:
        # A refusal of the recomputation keeps its own code (stale_build for changed bytes).
        raise
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise BuildError(f"invalid session selection: {error}") from error
    if canonical(value) != canonical(expected):
        raise BuildError("session selection provenance changed", "stale_build")
    return value


def save_selection(root: Path, path: Path, value: dict) -> None:
    """Persist only ignored candidate scratch, without changing shared Git excludes."""
    from ..harness.status_store import atomic_write

    selection_path(root, path, exists=False)
    atomic_write(
        root.resolve(),
        path.relative_to(root.resolve()).as_posix(),
        (json.dumps(value, sort_keys=True) + "\n").encode(),
    )


def runtime_selection(package_root: Path) -> dict | None:
    """The verified session selection of this launcher run, as its session provenance.

    Fails closed before any capability runs; project data never selects code. A selection pins the
    running package; it may name a disposable consumer project as data, but never redirects into
    a sibling worktree of the same source repository.
    """
    from ..spec.repository import SpecError

    if not os.environ.get("CONCORDE_SESSION_SELECTION"):
        return None
    if package_root.resolve() != Path.cwd().resolve():
        from ..harness.change_worktree import git

        package_common = git(
            package_root,
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
            check=False,
        )
        project_common = git(
            Path.cwd(),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
            check=False,
        )
        if (
            package_common.returncode == 0
            and project_common.returncode == 0
            and package_common.stdout.strip() == project_common.stdout.strip()
        ):
            raise SpecError(
                "private selection cannot redirect into another source worktree",
                "workspace_mismatch",
            )
    return load_selection(package_root, Path(os.environ["CONCORDE_SESSION_SELECTION"]))
