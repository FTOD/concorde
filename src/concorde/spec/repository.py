"""Protocol 14 repository admission: project configuration, installed Protocol copy and Spec graph."""

from __future__ import annotations

from pathlib import Path

from .content_repository import DocumentUnitRepository, RepositoryCore  # noqa: F401

# Keep the established import surface for shared value types and deterministic helpers.
from .repository_base import *  # noqa: F403 - public facade for shared helpers
from .repository_base import (
    PROFILE_VERSION,
    PROTOCOL_DIR,
    PROTOCOL_MANIFEST_PATH,
    PROTOCOL_VERSION,
    SpecError,
    decode,
    digest,
    identifier,
    protocol_asset_path,
    read_file,
)
from .errors import system_cause
from .typed_data import TypedDataError, safe_path

CONFIG_FIELDS = {"profile_version", "registry", "protocol"}
# Optional sections: configured checks, read here, and the worker settings and the project
# interpreter (`python`) that the harness reads.
OPTIONAL_CONFIG_FIELDS = {"checks", "workers", "python"}


def configured_checks(config: dict) -> list[dict]:
    """The project's configured checks (``.concorde/config.json`` ``checks``).

    Spec tooling reads only what it needs: a unique ``id``, a registered ``module`` and the
    optional unique, canonical ``inputs``. The command fields belong to Check execution, which
    validates them when it runs the check.
    """
    from .repository_base import check_input_error

    raw = config.get("checks", [])
    if not isinstance(raw, list):
        raise SpecError(
            f"the configuration's checks must be an array, not a JSON {type(raw).__name__}",
            "invalid_spec",
            "/checks",
            path=".concorde/config.json",
        )
    result, seen = [], set()
    for position, check in enumerate(raw):
        if not isinstance(check, dict) or not {"id", "module"} <= check.keys():
            raise SpecError(
                f"configured check {position} needs an id and a module: {check!r}"[
                    :300
                ],
                "invalid_spec",
                f"/checks/{position}",
                path=".concorde/config.json",
                reason="a configured check is identified by its id and belongs to one Module",
            )
        key = identifier(check["id"])
        if key in seen:
            raise SpecError(
                f"the configured check id {key} is used twice",
                "invalid_spec",
                f"/checks/{position}/id",
                path=".concorde/config.json",
                reason="a configured check's id identifies it uniquely in results and logs",
            )
        seen.add(key)
        identifier(check["module"])
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
                f"/checks/{position}/inputs",
                path=".concorde/config.json",
            )
        for path in inputs:
            try:
                safe_path(path, path)
            except TypedDataError as error:
                raise check_input_error(check, path, error) from error
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
                "the configuration's fields must be profile_version, registry, protocol and "
                "optionally checks, workers and python; "
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
        checks = configured_checks(self.config)
        super().__init__(
            root,
            registry_path=self.config["registry"],
            registry_bytes=registry_bytes,
            document_overrides=document_overrides,
            configured_checks=checks,
            _defer_document_admission=_defer_document_admission,
        )
        for check in checks:
            if check["module"] not in self.modules:
                raise SpecError(
                    f"configured check {check['id']} names {check['module']}, which the "
                    "registry does not register",
                    "unknown_module",
                    "/checks",
                    path=".concorde/config.json",
                    subject=check["id"],
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
