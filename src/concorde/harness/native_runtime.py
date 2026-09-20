"""Explicit admission of the reviewed versionless native artifact producer.

The package version alone is insufficient: the adapter pins the exact selected
serialization/control sources it relies on. This is compatibility provenance,
not a signature or an attestation of every installed third-party byte.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..spec.repository import SpecError, digest
from ..spec.typed_data import decode

FORMAT = "pi-subagents-0.69.0-versionless-workflow-v1"
CONTRACT = Path(__file__).resolve().parents[3] / "pi/native-runtime-contract.json"


@dataclass(frozen=True)
class NativeRuntimeBinding:
    format: str
    package_root: str
    source_digest: str
    artifact_version: None = None


def admit_native_runtime(
    root: Path, *, contract: Path = CONTRACT
) -> NativeRuntimeBinding:
    """Host-selected package only; no installed/global fallback or automatic upgrade."""
    expected = decode(contract.read_text(encoding="utf-8"))
    if (
        expected.get("schema_version") != 1
        or expected.get("format") != FORMAT
        or expected.get("artifact_version") is not None
        or expected.get("package") != "pi-subagents"
        or expected.get("package_version") != "0.69.0"
    ):
        raise SpecError("unsupported native adapter contract", "unsupported_version")
    if not root.is_absolute() or any(p.is_symlink() for p in (root, *root.parents)):
        raise SpecError("native package root is not canonical", "unsafe_path")
    sources = expected.get("sources")
    if not isinstance(sources, dict) or "package.json" not in sources:
        raise SpecError("native adapter source inventory is missing", "invalid_input")
    actual = {}
    for relative, wanted in sources.items():
        from ..spec.typed_data import checked_path

        source = checked_path(root, relative)
        try:
            actual[relative] = digest(source.read_bytes())
        except OSError as error:
            raise SpecError(
                "native runtime source is unavailable", "missing_runtime"
            ) from error
        if actual[relative] != wanted:
            raise SpecError(
                "native runtime differs from the reviewed adapter",
                "unsupported_version",
            )
    package = decode((root / "package.json").read_text(encoding="utf-8"))
    if (package.get("name"), package.get("version")) != ("pi-subagents", "0.69.0"):
        raise SpecError("unsupported native runtime package", "unsupported_version")
    return NativeRuntimeBinding(FORMAT, str(root), digest(actual))
