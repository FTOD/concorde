"""Following the main agent's Claude Code session after it moved to the background or was renamed.

Claude Code's ``/background`` command moves an interactive session to the background: a new
session with a new session id continues the conversation, and, unless the session had a name of its
own, its name becomes the automatic title. Claude Code ends the moved session and appends one record
to its transcript, ``{"type": "continued-in", "continuedInSessionId": "<new id>"}``, before the new
session starts; a copy of a session that goes on leaves no such record. ``/rename`` keeps the id
and changes the name. So the session id a task record keeps leads to the main agent's session
however its name changed: through those records to the newest session, and through
``claude agents --json``, Claude Code's list of the sessions that run, to that session's name.

Claude Code documents neither the record nor its place, so every reader here answers nothing for a
transcript, record or list that is missing or of another form, and its callers then do as before.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from . import session as sessions

# The record a moved session's transcript ends with, and its field naming the new session.
CONTINUED = "continued-in"
NEXT = "continuedInSessionId"
# The records of a conversation that goes on: either after a ``continued-in`` record means the
# session was resumed after its move, so it continues in itself again, as Claude Code's own
# ``/resume`` reads it.
CONVERSATION = ("user", "assistant")
# The end of a transcript read for its last records: the record is its last line or close to it.
TAIL = 256 * 1024
# The moves followed from one session at most, against a loop in records written by hand.
MOVES = 16
# Claude Code's list of the sessions that run now, interactive and background.
LISTING = ("agents", "--json")
LISTING_TIMEOUT = 20


def continued_in(transcript: Path) -> str | None:
    """The session id the transcript's session continues in: the ``continuedInSessionId`` of its
    last ``continued-in`` record when no ``user`` or ``assistant`` record follows it; None when
    the transcript cannot be read or holds no such record."""
    try:
        with transcript.open("rb") as stream:
            size = stream.seek(0, os.SEEK_END)
            stream.seek(max(0, size - TAIL))
            data = stream.read()
    except OSError:
        return None
    lines = data.decode("utf-8", errors="replace").splitlines()
    if len(data) >= TAIL and lines:
        lines = lines[1:]  # the first line read may be cut
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        kind = record.get("type")
        if kind == CONTINUED:
            found = record.get(NEXT)
            return (
                found
                if isinstance(found, str) and sessions.SESSION_ID.match(found)
                else None
            )
        if kind in CONVERSATION:
            return None
    return None


def chain(session_id: str, find) -> list[str]:
    """``session_id`` and every session it continues in, in order, by the ``continued-in`` records
    of the transcripts ``find(id)`` returns (None when there is none); at most ``MOVES`` moves,
    stopping at a session already seen."""
    found = [session_id]
    while len(found) <= MOVES:
        transcript = find(found[-1])
        following = continued_in(transcript) if transcript is not None else None
        if following is None or following in found:
            break
        found.append(following)
    return found


def in_folder(folder: Path):
    """``find`` for :func:`chain`: the transcripts of one Claude Code project folder."""

    def find(session_id: str) -> Path | None:
        if not sessions.SESSION_ID.match(session_id):
            return None
        path = folder / f"{session_id}.jsonl"
        return path if path.is_file() else None

    return find


def of_project(primary: Path, directory: Path | None = None):
    """``find`` for :func:`chain`: the transcripts of the sessions started in ``primary``, in the
    project folder Claude Code keeps for it, else the one transcript of that name it keeps."""

    def find(session_id: str) -> Path | None:
        if not sessions.SESSION_ID.match(session_id):
            return None
        try:
            return sessions.find_transcript(str(primary), session_id, directory)
        except (LookupError, OSError):
            return None

    return find


def listed(run=None) -> dict[str, str] | None:
    """The sessions that run now, each session id with its name, as ``claude agents --json``
    lists them; None when ``claude`` cannot run, fails or prints no such list."""
    run = run or subprocess.run
    try:
        result = run(
            ["claude", *LISTING],
            capture_output=True,
            text=True,
            timeout=LISTING_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout or "")
    except ValueError:
        return None
    if not isinstance(value, list):
        return None
    return {
        item["sessionId"]: item["name"]
        for item in value
        if isinstance(item, dict)
        and isinstance(item.get("sessionId"), str)
        and isinstance(item.get("name"), str)
        and item["name"].strip()
    }


def follow(record: dict, find, run=None) -> dict | None:
    """Where the task record's main agent's session is now: ``{"main", "followed"}``, the name
    Claude Code lists the newest session it continues in under and the session ids from the
    record's ``main_session`` to that one, when that name is not the record's ``main``; None when
    the record keeps no session id, the newest session is not listed, or the name is the same."""
    session_id = record.get("main_session")
    if not isinstance(session_id, str) or not sessions.SESSION_ID.match(session_id):
        return None
    followed = chain(session_id, find)
    names = listed(run)
    name = (names or {}).get(followed[-1])
    if name is None or name == record.get("main"):
        return None
    return {"main": name, "followed": followed}


def watched(record: dict, find) -> tuple[Path, frozenset[str]] | None:
    """The transcripts following the record's main agent's session reads, as the folder of the
    first and the file names of all, which a move or a rename writes; None without a session id
    or its transcript."""
    session_id = record.get("main_session")
    if not isinstance(session_id, str) or not sessions.SESSION_ID.match(session_id):
        return None
    first = find(session_id)
    if first is None:
        return None
    return first.parent, frozenset(f"{item}.jsonl" for item in chain(session_id, find))


def follower(primary: Path, run=None):
    """``follow`` for the records of the project whose primary worktree is ``primary``: its main
    agents' sessions run there, so their transcripts lie in that worktree's project folder."""
    find = of_project(primary)
    return lambda record: follow(record, find, run)


__all__ = [
    "chain",
    "continued_in",
    "follow",
    "follower",
    "in_folder",
    "listed",
    "of_project",
    "watched",
]
