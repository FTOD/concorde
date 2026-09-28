"""Protocol 15 repository admission: project configuration, installed Protocol copy and Spec graph."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .content_repository import DocumentUnitRepository, RepositoryCore  # noqa: F401

# Keep the established import surface for shared value types and deterministic helpers.
from .repository_base import *  # noqa: F403 - public facade for shared helpers
from .repository_base import (
    CHECKS_DIR,
    PROFILE_VERSION,
    REGISTRY_PATH,
    PROTOCOL_DIR,
    PROTOCOL_MANIFEST_PATH,
    PROTOCOL_VERSION,
    SpecError,
    decode,
    digest,
    identifier,
    is_identity,
    protocol_asset_path,
    read_file,
)
from .errors import system_cause
from .typed_data import TypedDataError, checked_path, safe_path

CONFIG_FIELDS = {"profile_version", "protocol"}
# The project interpreter, which Check execution reads.
OPTIONAL_CONFIG_FIELDS = {"python"}
# Fields earlier profiles had, each with where its setting lives now.
MOVED_CONFIG_FIELDS = {
    "checks": f"each Module's configured checks are the file {CHECKS_DIR}/<module id>.json, "
    'holding {"checks": [...]} with entries that have no module field',
    "registry": f"the registry is always {REGISTRY_PATH}; move the registry file there if it is "
    "elsewhere",
    "workers": "the worker limits and runtime paths are limits and runtime of the tracked "
    ".concorde/workers.json, beside the worker models",
}


def checks_files(root: Path) -> list[tuple[str, str]]:
    """The checks files of a worktree as ``(path, Module id)``, in the byte order of their names.

    ``.concorde/checks/`` holds only regular files named ``<module id>.json``; a missing
    directory means the project configures no checks.
    """
    try:
        directory = checked_path(root, CHECKS_DIR)
    except TypedDataError as error:
        raise SpecError(
            f"{CHECKS_DIR} in {root} is reached through a symbolic link",
            "unsafe_path",
            path=CHECKS_DIR,
            reason="the configured checks are read only from the worktree's own files",
            remediation=f"replace the link with a real {CHECKS_DIR} directory",
        ) from error
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise SpecError(
            f"{CHECKS_DIR} in {root} is not a directory",
            "invalid_spec",
            path=CHECKS_DIR,
            reason="the configured checks are one file per Module under this directory",
            remediation="move the file away and put each Module's checks in "
            f"{CHECKS_DIR}/<module id>.json",
        )
    result = []
    for name in sorted(os.listdir(directory)):
        relative = f"{CHECKS_DIR}/{name}"
        module = name.removesuffix(".json") if name.endswith(".json") else ""
        entry = directory / name
        if not is_identity(module) or entry.is_symlink() or not entry.is_file():
            state = (
                "a symbolic link"
                if entry.is_symlink()
                else "not a regular file"
                if not entry.is_file()
                else "not named <module id>.json"
            )
            raise SpecError(
                f"{relative} is {state}",
                "invalid_spec",
                path=relative,
                reason=f"{CHECKS_DIR} holds only the regular files <module id>.json, each "
                "with the configured checks of the Module it names",
                remediation="rename the file after its Module's identity or move it out of "
                f"{CHECKS_DIR}",
            )
        result.append((relative, module))
    return result


def configured_checks(root: Path) -> list[dict]:
    """The project's configured checks, read from ``.concorde/checks/<module id>.json``.

    Each file is ``{"checks": [...]}``; the file name gives every entry its ``module``, which the
    returned checks carry after their ``id``. Spec tooling reads only what it needs: a unique
    ``id`` and the optional unique, canonical ``inputs``. The command fields belong to Check
    execution, which validates them when it runs the check. Files come in the byte order of
    their names and entries in file order.
    """
    from .repository_base import check_input_error

    result, seen = [], {}
    for path, module in checks_files(root):
        value = decode(read_file(root, path).decode("utf-8"))
        if not isinstance(value, dict) or set(value) != {"checks"}:
            raise SpecError(
                f"{path} must be a JSON object with exactly the field checks, not "
                f"{json.dumps(value)[:200]}",
                "invalid_spec",
                path=path,
                reason="a checks file lists, under checks, the configured checks of the "
                "Module it is named after",
                remediation='write {"checks": [...]} with one entry per check',
            )
        raw = value["checks"]
        if not isinstance(raw, list):
            raise SpecError(
                f"the checks of {path} must be an array, not a JSON {type(raw).__name__}",
                "invalid_spec",
                "/checks",
                path=path,
            )
        for position, entry in enumerate(raw):
            pointer = f"/checks/{position}"
            if not isinstance(entry, dict) or "id" not in entry:
                raise SpecError(
                    f"configured check {position} of {path} needs an id: {entry!r}"[
                        :300
                    ],
                    "invalid_spec",
                    pointer,
                    path=path,
                    reason="a configured check is identified by its id",
                )
            if "module" in entry:
                raise SpecError(
                    f"configured check {entry['id']!r} of {path} has a module field",
                    "invalid_spec",
                    pointer + "/module",
                    path=path,
                    reason=f"the check belongs to {module}, the Module its file is named "
                    "after, so a module field could only disagree with it",
                    remediation="remove the field, or move the check into "
                    f"{CHECKS_DIR}/<its module id>.json",
                )
            key = identifier(entry["id"])
            if key in seen:
                raise SpecError(
                    f"the configured check id {key} is used in {seen[key]} and again in "
                    f"{path}",
                    "invalid_spec",
                    pointer + "/id",
                    path=path,
                    reason="a configured check's id identifies it uniquely in results and "
                    "logs",
                    remediation="rename one of the two checks",
                )
            seen[key] = path
            check = {"id": key, "module": module} | entry
            inputs = check.get("inputs", [])
            if (
                not isinstance(inputs, list)
                or any(not isinstance(x, str) for x in inputs)
                or len(set(inputs)) != len(inputs)
            ):
                raise SpecError(
                    f"the inputs of configured check {key} must be an array of distinct "
                    f"strings, not {inputs!r}"[:300],
                    "invalid_spec",
                    pointer + "/inputs",
                    path=path,
                )
            for relative in inputs:
                try:
                    safe_path(relative, relative)
                except TypedDataError as error:
                    raise check_input_error(check, relative, error) from error
            result.append(check)
    return result


class SpecRepository(DocumentUnitRepository):
    """The Spec graph admitted through the installed, explicitly accepted Protocol."""

    def __init__(
        self,
        project_root: Path | str,
        package_root: Path | str | None = None,
        *,
        registry_bytes: bytes | None = None,
        document_overrides: dict[str, bytes] | None = None,
        _defer_document_admission: bool = False,
    ):
        root = Path(project_root)
        if root.is_symlink() or not root.is_dir():
            state = (
                "a symbolic link"
                if root.is_symlink()
                else "missing"
                if not root.exists()
                else "not a directory"
            )
            raise SpecError(
                f"the project root {root} is {state}",
                "unsafe_path",
                path=str(root),
                reason="Spec tooling loads a project only from a real directory",
                remediation="pass the real path of the project's worktree",
            )
        self.package_root = (
            Path(package_root).resolve()
            if package_root
            else Path(__file__).resolve().parents[3]
        )
        self.config = decode(read_file(root, ".concorde/config.json").decode("utf-8"))
        if not isinstance(self.config, dict):
            raise SpecError(
                "the configuration must be a JSON object, not a JSON "
                f"{type(self.config).__name__}",
                "invalid_spec",
                path=".concorde/config.json",
            )
        moved = [name for name in MOVED_CONFIG_FIELDS if name in self.config]
        if moved:
            raise SpecError(
                f"the configuration has {', '.join(moved)}, which profile {PROFILE_VERSION} "
                "keeps elsewhere: "
                + "; ".join(f"{name}: {MOVED_CONFIG_FIELDS[name]}" for name in moved),
                "invalid_spec",
                f"/{moved[0]}",
                path=".concorde/config.json",
                reason=f"the project configuration of profile {PROFILE_VERSION} holds only "
                "profile_version, protocol and python, so that settings changed by different "
                "work live in files of their own",
                remediation="move each setting where the message says, remove the fields and "
                f"set profile_version to {PROFILE_VERSION}",
            )
        if (
            type(self.config.get("profile_version")) is not int
            or self.config["profile_version"] != PROFILE_VERSION
        ):
            raise SpecError(
                f"profile_version {PROFILE_VERSION} is required, but the configuration has "
                f"{self.config.get('profile_version')!r}",
                "unsupported_profile",
                "/profile_version",
                path=".concorde/config.json",
            )
        missing = sorted(CONFIG_FIELDS - self.config.keys())
        extra = sorted(self.config.keys() - CONFIG_FIELDS - OPTIONAL_CONFIG_FIELDS)
        if missing or extra:
            raise SpecError(
                "the configuration's fields must be profile_version, protocol and optionally "
                "python; "
                + "; ".join(
                    part
                    for part in (
                        f"missing: {', '.join(missing)}" if missing else "",
                        f"not allowed: {', '.join(extra)}" if extra else "",
                    )
                    if part
                ),
                "invalid_spec",
                path=".concorde/config.json",
                reason=f"the project configuration of profile {PROFILE_VERSION} has exactly "
                "these fields, so an unknown field is a typo or a setting no tool reads",
                remediation="remove or rename the field that is not allowed, and add the "
                "missing ones",
            )
        checks = configured_checks(root)
        super().__init__(
            root,
            registry_bytes=registry_bytes,
            document_overrides=document_overrides,
            configured_checks=checks,
            _defer_document_admission=_defer_document_admission,
        )
        for path, module in checks_files(root):
            if module not in self.modules:
                raise SpecError(
                    f"{path} holds configured checks of {module}, which the registry does "
                    "not register",
                    "unknown_module",
                    path=path,
                    subject=module,
                    remediation="rename the file after the Module whose checks it holds, or "
                    "remove it together with its Module",
                )
        self.protocol_manifest, self.protocol_assets = self._protocol()

    def _protocol(self) -> tuple[dict, dict[str, bytes]]:
        """Admit the Protocol copy the installer placed under .concorde/protocol/, as the configuration binds it.

        The binding must name exactly that copy and the installed package must carry the same
        manifest: an updated installation is rejected until the developer accepts it explicitly
        (configure with ``accept_protocol``), never adopted silently.
        """
        try:
            raw = read_file(self.root, PROTOCOL_MANIFEST_PATH)
        except (SpecError, OSError) as error:
            raise SpecError(
                f"the project has no readable Protocol copy: {PROTOCOL_MANIFEST_PATH} cannot "
                "be read",
                "protocol_mismatch",
                path=PROTOCOL_MANIFEST_PATH,
                remediation="run the Concorde installer in this project",
                causes=[error if isinstance(error, SpecError) else system_cause(error)],
            ) from error
        manifest = decode(raw.decode())
        binding = {"version": manifest.get("version"), "digest": digest(raw)}
        if self.config["protocol"] != binding or binding["version"] != PROTOCOL_VERSION:
            raise SpecError(
                f"the configuration binds the Protocol {self.config['protocol']!r}, but the "
                f"installed copy is {binding!r} and this Spec tooling reads Protocol "
                f"{PROTOCOL_VERSION}",
                "protocol_mismatch",
                "/protocol",
                path=".concorde/config.json",
            )
        if read_file(self.package_root, "protocol/manifest.json") != raw:
            raise SpecError(
                f"the Protocol copy {PROTOCOL_MANIFEST_PATH} differs from the manifest of the "
                f"Concorde package at {self.package_root}",
                "protocol_mismatch",
                path=PROTOCOL_MANIFEST_PATH,
                remediation="reinstall Concorde so the project's copy matches the package",
            )
        assets = {}
        for item in manifest["assets"]:
            path = protocol_asset_path(item["path"])
            try:
                content = read_file(self.root, path)
            except (SpecError, OSError) as error:
                raise SpecError(
                    f"the installed Protocol asset {path} listed by the manifest is missing",
                    "protocol_mismatch",
                    path=path,
                    causes=[
                        error if isinstance(error, SpecError) else system_cause(error)
                    ],
                ) from error
            if digest(content) != item["digest"]:
                raise SpecError(
                    f"the installed Protocol asset {path} has digest {digest(content)}, but "
                    f"the manifest records {item['digest']}",
                    "protocol_mismatch",
                    path=path,
                )
            assets[path] = content
        if f"{PROTOCOL_DIR}/principles.md" not in assets:
            raise SpecError(
                f"the Protocol manifest {PROTOCOL_MANIFEST_PATH} lists no "
                f"{PROTOCOL_DIR}/principles.md",
                "protocol_mismatch",
                path=PROTOCOL_MANIFEST_PATH,
                reason="every Protocol copy carries the global principles",
            )
        return manifest, assets

    def fresh(self) -> SpecRepository:
        return SpecRepository(
            self.root,
            self.package_root,
            registry_bytes=self._registry_override,
            document_overrides=self.document_overrides,
        )
