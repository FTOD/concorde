"""Protocol 11 repository admission: project configuration, installed Protocol copy and Spec graph."""

from __future__ import annotations

from pathlib import Path

from .content_repository import DocumentUnitRepository, RepositoryCore  # noqa: F401

# Keep the established import surface for shared value types and deterministic helpers.
from .repository_base import *  # noqa: F403 - public facade for shared helpers
from .repository_base import (
    PROFILE_VERSION,
    PROTOCOL_VERSION,
    SpecError,
    decode,
    digest,
    identifier,
    read_file,
)
from .typed_data import TypedDataError, safe_path

CONFIG_FIELDS = {"profile_version", "registry", "protocol", "operation_configuration"}
CHECK_FIELDS = {"id", "module", "argv", "timeout_seconds"}


def configured_checks(config: dict) -> list[dict]:
    """The project's configured checks (``.concorde/config.json`` ``checks``), validated."""
    from .repository_base import check_input_error

    raw = config.get("checks", [])
    if not isinstance(raw, list):
        raise SpecError(
            "configuration checks must be an array", "invalid_spec", "checks"
        )
    result, seen = [], set()
    for check in raw:
        if (
            not isinstance(check, dict)
            or not CHECK_FIELDS <= check.keys()
            or check.keys() - CHECK_FIELDS - {"inputs"}
        ):
            raise SpecError(
                "a configured check requires id, module, argv, timeout_seconds and optional inputs",
                "invalid_spec",
                "checks",
            )
        key = identifier(check["id"])
        if key in seen:
            raise SpecError(
                f"duplicate configured check: {key}", "invalid_spec", "checks"
            )
        seen.add(key)
        identifier(check["module"])
        if (
            not isinstance(check["argv"], list)
            or not check["argv"]
            or any(not isinstance(x, str) or not x for x in check["argv"])
        ):
            raise SpecError("check argv must be a nonempty array of strings")
        if (
            type(check["timeout_seconds"]) is not int
            or not 1 <= check["timeout_seconds"] <= 3600
        ):
            raise SpecError("check timeout must be 1..3600 seconds")
        inputs = check.get("inputs", [])
        if (
            not isinstance(inputs, list)
            or any(not isinstance(x, str) for x in inputs)
            or len(set(inputs)) != len(inputs)
        ):
            raise SpecError("check inputs must be a unique string array")
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
            raise SpecError("project root must be a real directory")
        self.package_root = (
            Path(package_root).resolve()
            if package_root
            else Path(__file__).resolve().parents[3]
        )
        self.config = decode(read_file(root, ".concorde/config.json").decode("utf-8"))
        if not isinstance(self.config, dict):
            raise SpecError("configuration must be an object")
        if (
            type(self.config.get("profile_version")) is not int
            or self.config["profile_version"] != PROFILE_VERSION
        ):
            raise SpecError(
                f"Profile {PROFILE_VERSION} is required",
                "unsupported_profile",
            )
        if (
            not CONFIG_FIELDS <= self.config.keys()
            or self.config.keys() - CONFIG_FIELDS - {"checks"}
        ):
            raise SpecError(
                "configuration fields must be profile_version, registry, protocol, "
                "operation_configuration and optional checks"
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
            if check["module"] not in self.targets:
                raise SpecError(
                    f"configured check {check['id']} names an unregistered Module: {check['module']}",
                    "invalid_spec",
                    "checks",
                )
        self.protocol_manifest, self.protocol_assets = self._protocol()

    def _protocol(self) -> tuple[dict, dict[str, bytes]]:
        """Admit the Protocol copy the installer placed under .concorde/protocol/, as the configuration binds it.

        The binding must name exactly that copy and the installed package must carry the same
        manifest: an updated installation is rejected until the developer accepts it explicitly
        (configure with ``accept_protocol``), never adopted silently.
        """
        from ..distribution.build import BuildError, verify_fresh
        from ..distribution.project_defaults import (
            PROTOCOL_DIR,
            PROTOCOL_MANIFEST_PATH,
            protocol_asset_path,
        )

        try:
            verify_fresh(self.package_root)
        except BuildError as error:
            raise SpecError(str(error), error.code) from error
        try:
            raw = read_file(self.root, PROTOCOL_MANIFEST_PATH)
        except (SpecError, OSError) as error:
            raise SpecError(
                "project has no Protocol copy under .concorde/protocol; run the installer",
                "protocol_mismatch",
            ) from error
        manifest = decode(raw.decode())
        binding = {"version": manifest.get("version"), "digest": digest(raw)}
        if self.config["protocol"] != binding or binding["version"] != PROTOCOL_VERSION:
            raise SpecError(
                "project Protocol binding does not match the installed Protocol copy; accept it "
                "explicitly with concorde-configure",
                "protocol_mismatch",
            )
        if read_file(self.package_root, "protocol/manifest.json") != raw:
            raise SpecError(
                "installed package Protocol differs from the project's Protocol copy; reinstall",
                "protocol_mismatch",
            )
        assets = {}
        for item in manifest["assets"]:
            path = protocol_asset_path(item["path"])
            try:
                content = read_file(self.root, path)
            except (SpecError, OSError) as error:
                raise SpecError(
                    f"installed Protocol asset is missing: {path}", "protocol_mismatch"
                ) from error
            if digest(content) != item["digest"]:
                raise SpecError(
                    f"installed Protocol asset has changed: {path}", "protocol_mismatch"
                )
            assets[path] = content
        if f"{PROTOCOL_DIR}/principles.md" not in assets:
            raise SpecError("Protocol manifest is missing the global principles")
        return manifest, assets

    def fresh(self) -> SpecRepository:
        return SpecRepository(
            self.root,
            self.package_root,
            registry_bytes=self._registry_override,
            document_overrides=self.document_overrides,
        )
