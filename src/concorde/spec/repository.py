"""Protocol 16 repository admission: project configuration, installed Protocol copy and Spec graph."""

from __future__ import annotations

from pathlib import Path

from .content_repository import DocumentUnitRepository, RepositoryCore  # noqa: F401

# Keep the established import surface for shared value types and deterministic helpers.
from .repository_base import *  # noqa: F403 - public facade for shared helpers
from .repository_base import (
    PROFILE_VERSION,
    REGISTRY_PATH,
    PROTOCOL_DIR,
    PROTOCOL_MANIFEST_PATH,
    PROTOCOL_VERSION,
    SpecError,
    decode,
    digest,
    protocol_asset_path,
    read_file,
)
from .errors import system_cause

CONFIG_FIELDS = {"profile_version", "protocol"}
# The project interpreter, which Check execution reads.
OPTIONAL_CONFIG_FIELDS = {"python"}
# Fields earlier profiles had, each with where its setting lives now.
MOVED_CONFIG_FIELDS = {
    "checks": "configured checks are Check execution's own files, .concorde/checks/<module "
    'id>.json, holding {"checks": [...]} with entries that have no module field',
    "registry": f"the registry is always {REGISTRY_PATH}; move the registry file there if it is "
    "elsewhere",
    "workers": "the worker limits and runtime paths are limits and runtime of the tracked "
    ".concorde/workers.json, beside the worker models",
}


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
        super().__init__(
            root,
            registry_bytes=registry_bytes,
            document_overrides=document_overrides,
            _defer_document_admission=_defer_document_admission,
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
