"""Receipt-owned root entry blocks; Protocol prose stays in the packaged asset."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROLE = "protocol-guidance"
FILES = {"codex": "AGENTS.md", "claude": "CLAUDE.md"}
TOKEN = b"<!-- concorde-protocol:"
START = b"\n<!-- concorde-protocol:start -->\n"
END = b"<!-- concorde-protocol:end -->\n"
PROTOCOL = ".concorde/framework/generated/protocol/principles.md"


class GuidanceError(ValueError):
    pass


def digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def entry(integration: str) -> bytes:
    reference = (f"Read and follow `{PROTOCOL}` before Concorde workflow actions.\n"
                 if integration == "codex" else f"@{PROTOCOL}\n")
    return START + ("## Concorde Protocol\n\n" + reference).encode() + END


def split(content: bytes) -> tuple[bytes, bytes, bytes]:
    """Reject ambiguous/forged delimiters instead of consuming arbitrary user text."""
    if TOKEN not in content:
        return content, b"", b""
    if content.count(TOKEN) != 2 or content.count(START) != 1 or content.count(END) != 1:
        raise GuidanceError("malformed or duplicate Concorde Protocol markers")
    if content.index(END) < content.index(START):
        raise GuidanceError("misordered Concorde Protocol markers")
    before, rest = content.split(START)
    middle, after = rest.split(END)
    if TOKEN in before + after or TOKEN in middle:
        raise GuidanceError("misordered Concorde Protocol markers")
    return before, START + middle + END, after


def plan(target: Path, relative: str, wanted: bytes | None, prior_digest: str | None):
    if relative not in FILES.values():
        raise GuidanceError("Protocol guidance receipt path must be AGENTS.md or CLAUDE.md")
    path = target / relative
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise GuidanceError(f"Protocol guidance must be a regular file: {relative}")
    content = path.read_bytes() if path.exists() else b""
    # Validate encoding without normalizing user newlines or final whitespace.
    content.decode("utf-8")
    before, block, after = split(content)
    if block and (prior_digest is None or digest(block) != prior_digest):
        raise GuidanceError("Protocol block is unowned or modified; preserve it for manual reconciliation")
    # Prepend a new entry so user Markdown fences and the local instruction size limit
    # do not hide it. Existing owned blocks stay at their original position.
    merged = (wanted + content if wanted is not None and not block
              else before + (wanted or b"") + after)
    action = "unchanged" if merged == content else "update" if path.exists() else "create"
    return ({"path": relative, "action": action,
             "role": ROLE if wanted is not None else "protocol-guidance-cleanup",
             "sha256": digest(wanted or b""), "before_sha256": digest(content),
             "before_exists": "yes" if path.exists() else "no"}, merged)
