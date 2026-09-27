"""Terminal editor with an in-memory draft; only Save writes the worktree's file."""

from __future__ import annotations

import copy
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from .available_models import candidates
from .models import (
    CLIENTS,
    LEVELS,
    ModelConfigError,
    _entry,
    choice,
    config_path,
    load,
    save,
    unset_choice,
    validate_config,
    worker_ids,
)


class Draft:
    def __init__(self, worktree: Path):
        self.worktree = worktree
        self.original_bytes = self._bytes()
        self.original = load(worktree)
        self.config = copy.deepcopy(self.original)
        self.ids = worker_ids()

    def _bytes(self):
        try:
            return config_path(self.worktree).read_bytes()
        except FileNotFoundError:
            return None
        except OSError as error:
            raise ModelConfigError("config_invalid", str(error)) from error

    @property
    def changed(self):
        return self.config != self.original

    def scopes(self):
        scopes: list[tuple[str | None, str | None]] = [(None, None)]
        for operation, workers in self.ids.items():
            scopes.append((operation, None))
            scopes.extend((operation, worker) for worker in workers)
        return scopes

    def own(self, operation, worker):
        return _entry(self.config, operation, worker, False) or {}

    def set_field(self, operation, worker, field, value):
        if field not in ("backend", "model", "reasoning"):
            raise ValueError(field)
        entry = dict(self.own(operation, worker))
        if value is None:
            entry.pop(field, None)
        else:
            if field == "backend" and entry.get(field) != value:
                # A backend selection starts this entry's model and reasoning afresh.
                entry.pop("model", None)
                entry.pop("reasoning", None)
            entry[field] = value
        unset_choice(self.config, operation, worker)
        if entry:
            target = _entry(self.config, operation, worker, True)
            assert target is not None
            target.update(entry)

    def reset(self, operation, worker):
        unset_choice(self.config, operation, worker)

    def commit(self):
        validate_config(self.config)
        if self._bytes() != self.original_bytes:
            raise ModelConfigError(
                "config_changed",
                "the file changed while editing; cancel and reopen to keep the other edit",
            )
        if not self.changed:
            return False
        save(self.worktree, self.config)
        return True


def scope_label(operation, worker):
    if operation is None:
        return "Every worker (default)"
    return f"{operation} / {worker or 'Operation default'}"


def _draw(screen, lines, selected=None):
    import curses

    screen.erase()
    height, width = screen.getmaxyx()
    for row, text in enumerate(lines[:height]):
        # Escape controls from paths and discovery text; curses handles display width.
        text = "".join(char if char.isprintable() else " " for char in text)
        # A resize or wide glyph may reach the bottom-right cell.
        with suppress(curses.error):
            screen.addnstr(
                row,
                0,
                text,
                max(0, width - 1),
                curses.A_REVERSE if row == selected else 0,
            )
    screen.refresh()


@dataclass
class MenuState:
    index: int = 0
    query: str = ""


def _menu(
    screen,
    title,
    rows,
    detail=None,
    footer="Up/Down: select  Enter: open  Esc: back",
    *,
    state=None,
    searchable=False,
    pinned=0,
):
    import curses

    state = state if state is not None else MenuState()
    while True:
        matches = [
            index
            for index, row in enumerate(rows)
            if index >= len(rows) - pinned or state.query.casefold() in row.casefold()
        ]
        if matches and state.index not in matches:
            state.index = matches[0]
        position = matches.index(state.index) if matches else 0
        height, _ = screen.getmaxyx()
        details = detail(state.index) if detail and matches else []
        space = max(1, height - len(details) - 5)
        start = max(0, position - space + 1)
        visible = [rows[index] for index in matches[start : start + space]]
        hint = (
            f"Filter: {state.query or '(all)'}  /: search (empty clears)"
            if searchable
            else ""
        )
        lines = (
            [title, hint]
            + (visible or ["No matches — / to change filter"])
            + [""]
            + details
            + [footer]
        )
        _draw(screen, lines, 2 + position - start if matches else None)
        key = screen.getch()
        if key == 3:
            raise KeyboardInterrupt
        if key in (27, ord("q")):
            return None
        if key == ord("/") and searchable:
            query = _input(screen, "Search (empty shows all)", allow_empty=True)
            if query is not None:
                state.query = query
            continue
        if key == ord("s") and rows[-2:] == ["Save", "Cancel"]:
            return len(rows) - 2
        if not matches:
            continue
        if key == curses.KEY_UP:
            position = (position - 1) % len(matches)
        elif key == curses.KEY_DOWN:
            position = (position + 1) % len(matches)
        elif key == curses.KEY_NPAGE:
            position = min(len(matches) - 1, position + space)
        elif key == curses.KEY_PPAGE:
            position = max(0, position - space)
        elif key in (10, 13, curses.KEY_ENTER):
            return state.index
        state.index = matches[position]


def _input(screen, title, *, allow_empty=False):
    import curses

    text = ""
    while True:
        _draw(screen, [title, "", text, "", "Enter: accept  Esc: cancel"])
        key = screen.get_wch()
        if key == "\x03":
            raise KeyboardInterrupt
        if key == "\x1b":
            return None
        if key in ("\n", "\r"):
            return text.strip() if allow_empty else text.strip() or None
        if key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
            text = text[:-1]
        elif isinstance(key, str) and key.isprintable():
            text += key


def _edit(screen, draft, scope):
    operation, worker = scope
    message = "Changes remain in the draft until Save."
    while True:
        selected = choice(draft.config, operation, worker)
        own = draft.own(operation, worker)
        fields = ("backend", "model", "reasoning")
        rows = [f"{field}: {own.get(field, '(inherit)')}" for field in fields]
        rows += ["Inherit all fields (remove entry)", "Back"]
        details = [
            f"{field}: {selected[field] or 'backend default'} <- {selected[field + '_source']}"
            for field in fields
        ]
        picked = _menu(
            screen,
            scope_label(*scope),
            rows,
            lambda _, details=details, message=message: details + [message],
        )
        if picked is None or picked == 4:
            return
        if picked == 3:
            draft.reset(*scope)
            continue
        field = fields[picked]
        if field == "backend":
            values = list(CLIENTS)
            note = "Choosing a backend clears this entry's model and reasoning."
        elif field == "reasoning":
            values = list(LEVELS[selected["backend"]])
            note = "Backend levels; model support is advisory, not a Save prerequisite."
        else:
            action = _menu(
                screen,
                "Model",
                ["Inherit", "Custom model name", "Discover candidates", "Back"],
            )
            if action is None or action == 3:
                continue
            if action == 0:
                draft.set_field(*scope, field, None)
                continue
            if action == 1:
                value = _input(
                    screen,
                    "Custom model (pi: provider/model; Claude: alias or full name)",
                )
                if value:
                    draft.set_field(*scope, field, value)
                continue
            _draw(
                screen,
                [
                    "Discovering configured candidates…",
                    "No inference calls are probed.",
                ],
            )
            try:
                found = candidates(selected["backend"])
            except ModelConfigError as error:
                message = f"Discovery unavailable: {error}. Use Custom model name."
                continue
            values = [item["id"] for item in found["models"]]
            note = found["note"]
        picked_value = _menu(
            screen,
            field.capitalize(),
            ["Inherit"] + values + ["Back"],
            lambda _, note=note: [note],
            searchable=field == "model",
            pinned=1,
        )
        if picked_value is None or picked_value == len(values) + 1:
            continue
        draft.set_field(
            *scope, field, None if picked_value == 0 else values[picked_value - 1]
        )
        message = "Draft updated. Save validates all entries."


def _discard(screen, draft):
    """Only an explicit Discard choice loses a dirty draft; repeated Ctrl-C keeps it."""
    if not draft.changed:
        return True
    try:
        return (
            _menu(
                screen,
                "Unsaved changes — discard draft?",
                ["Keep editing", "Discard changes"],
                footer="Enter: choose  Esc/q/Ctrl-C: keep editing",
            )
            == 1
        )
    except KeyboardInterrupt:
        return False


def _editor(screen, draft):
    import curses

    with suppress(curses.error):
        curses.curs_set(0)
    screen.keypad(True)
    message = "Enter: edit  s: Save  q/Esc: Cancel"
    scopes = draft.scopes()
    state = MenuState()
    while True:
        rows = []
        for operation, worker in scopes:
            selected = choice(draft.config, operation, worker)
            marker = " *" if draft.own(operation, worker) else ""
            rows.append(
                f"{scope_label(operation, worker)}{marker}: {selected['backend']} / {selected['model'] or 'backend default'} / {selected['reasoning'] or 'default'}"
            )
        rows += ["Save", "Cancel"]

        def detail(index, message=message):
            if index >= len(scopes):
                return [
                    "Save writes this worktree only. Cancel discards the draft.",
                    message,
                ]
            selected = choice(draft.config, *scopes[index])
            return (
                [f"Selected: {scope_label(*scopes[index])}"]
                + [
                    f"{field} <- {selected[field + '_source']}"
                    for field in ("backend", "model", "reasoning")
                ]
                + [message]
            )

        try:
            picked = _menu(
                screen,
                f"Worker models {'[unsaved]' if draft.changed else ''} — {draft.worktree}",
                rows,
                detail,
                state=state,
                searchable=True,
                pinned=2,
            )
            if picked is None or picked == len(scopes) + 1:
                if _discard(screen, draft):
                    return False
            elif picked == len(scopes):
                try:
                    return draft.commit()
                except ModelConfigError as error:
                    message = f"Save refused: {error}"
            else:
                _edit(screen, draft, scopes[picked])
        except KeyboardInterrupt:
            # Ctrl-C anywhere in the editor returns to a deliberate exit decision.
            if _discard(screen, draft):
                return False


def run(worktree):
    draft = Draft(worktree)
    try:
        import curses
    except ImportError as error:
        raise ModelConfigError(
            "terminal_unavailable",
            "curses is unavailable; edit the JSON directly and use --check",
        ) from error
    try:
        return curses.wrapper(_editor, draft)
    except KeyboardInterrupt:
        return False
    except curses.error as error:
        raise ModelConfigError(
            "terminal_unavailable",
            f"cannot open terminal editor: {error}; use --show --json or edit the file and use --check",
        ) from error
