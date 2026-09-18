"""Protocol-10 / Profile-15 repository admission. No old-format runtime path."""

from __future__ import annotations

from pathlib import Path

from .content_repository import DocumentUnitRepository

# Keep the established import surface for shared value types and deterministic helpers.
from .repository_base import *  # noqa: F403 - public compatibility facade for shared helpers
from .repository_base import PROFILE_VERSION, SpecError, decode, read_file
from .repository_base import _logical_lines as _logical_lines
from .repository_base import _paragraph_end as _paragraph_end
from .repository_base import _parse_definitions as _parse_definitions


class SpecRepository(DocumentUnitRepository):
    """The document-unit backend admitted through the installed, explicitly accepted Protocol."""

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
        if (
            type(self.config.get("profile_version")) is not int
            or self.config["profile_version"] != PROFILE_VERSION
        ):
            raise SpecError(
                "Profile 15 is required; older profiles need explicit migration",
                "unsupported_profile",
            )
        if set(self.config) != {
            "profile_version",
            "registry",
            "protocol",
            "operation_configuration",
        }:
            raise SpecError(
                "configuration fields must be profile_version, registry, protocol, operation_configuration"
            )
        super().__init__(
            root,
            registry_path=self.config["registry"],
            registry_bytes=registry_bytes,
            document_overrides=document_overrides,
            _defer_document_admission=_defer_document_admission,
        )
        self.protocol_manifest, self.protocol_assets = self._protocol()

    def fresh(self) -> SpecRepository:
        return SpecRepository(
            self.root,
            self.package_root,
            registry_bytes=self._registry_override,
            document_overrides=self.document_overrides,
        )
