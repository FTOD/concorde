"""Creation-only publication of scaffold files: never replaces a file, never deletes one it did not create."""

from __future__ import annotations

import errno
import os
import tempfile
from pathlib import Path

from ..errors import system_cause
from ..repository import SpecError
from ..typed_data import checked_path

# Filesystems without hard links refuse os.link with one of these; the file is then created with
# O_EXCL, which is just as exclusive but shows the file before its last byte is written.
_NO_HARD_LINKS = frozenset(
    {errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV, errno.EMLINK}
)


def _create(path: Path, data: bytes) -> tuple[int, int]:
    """Create ``path`` with ``data`` if it is absent, returning the identity of the file created."""
    descriptor, temporary = tempfile.mkstemp(
        prefix=".concorde-create-", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            status = os.fstat(stream.fileno())
        try:
            # A link fails with FileExistsError when anything, even a dangling link, is there.
            os.link(temporary, path)
            return status.st_dev, status.st_ino
        except OSError as error:
            if isinstance(error, FileExistsError) or error.errno not in _NO_HARD_LINKS:
                raise
    finally:
        Path(temporary).unlink(missing_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    with os.fdopen(descriptor, "wb") as stream:
        status = os.fstat(stream.fileno())
        identity = (status.st_dev, status.st_ino)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        except OSError:
            _remove_own(path, identity)
            raise
    return identity


def _remove_own(path: Path, identity: tuple[int, int]) -> bool:
    """Remove ``path`` only while it is still the file this application created."""
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return False
    if (status.st_dev, status.st_ino) != identity:
        return False
    path.unlink()
    return True


def create_files(root: Path, files: dict[str, bytes]) -> list[str]:
    """Create every file, in path order, each only where nothing exists; on any failure remove
    the files this call created that are still its own, and raise. A file another process
    created or put in place of one of ours is never replaced or removed."""
    created: list[tuple[str, Path, tuple[int, int]]] = []
    current = None
    try:
        for relative in sorted(files):
            current = relative
            path = checked_path(root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            # A directory created meanwhile may be a link; the path is checked again under it.
            path = checked_path(root, relative)
            created.append((relative, path, _create(path, files[relative])))
        current = None
    except Exception as error:
        kept, unremoved = [], []
        for relative, path, identity in reversed(created):
            try:
                if not _remove_own(path, identity):
                    kept.append(relative)
            except OSError as problem:
                unremoved.append(system_cause(problem, path=relative))
        if not isinstance(error, OSError) or current is None:
            raise
        appeared = isinstance(error, FileExistsError)
        message = (
            f"{current} appeared while the proposal was being applied"
            if appeared
            else f"creating {current} failed"
        )
        if unremoved:
            message += (
                "; the files this application created were removed except "
                + ", ".join(problem.path for problem in unremoved)
                + ", which could not be removed and still hold the proposal's content"
            )
        else:
            message += "; every file this application had created was removed"
        if kept:
            message += (
                "; "
                + ", ".join(sorted(kept))
                + " had been replaced by another process "
                "and keep that process's bytes"
            )
        causes = [system_cause(error, path=current), *unremoved]
        if unremoved:
            raise SpecError(
                message,
                "system_error",
                path=current,
                reason="applying a scaffold proposal removes the files it created when it "
                "fails, and the operating system refused a removal",
                remediation="remove the named files by hand, fix the cause of the first "
                "failure, and apply again",
                causes=causes,
            ) from error
        raise SpecError(
            message,
            "stale_proposal" if appeared else "system_error",
            path=current,
            reason="applying a scaffold proposal only creates files, and creates either "
            "all of them or none",
            causes=causes,
        ) from error
    return [relative for relative, _path, _identity in created]
