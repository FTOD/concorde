"""The Kernel's refusal: a stable code, the JSON pointer or path concerned and a full message.

Every operation of the Kernel's library refuses with a ``KernelError``. It is no error link: the
level that called the library decides why it cannot handle the refusal and builds its own link,
keeping the code and message as its detail (``specs/concorde/kernel/contracts.md#library``).
"""

from __future__ import annotations


class KernelError(Exception):
    """A refusal of the Kernel's library.

    ``code`` is stable, ``field`` the JSON pointer of the offending value or the path of the
    offending file (empty when the refusal concerns the whole input), and ``causes`` the failures
    that led to it, such as each restoration the operating system refused in a file transaction.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        field: str = "",
        causes: list[BaseException] | tuple[BaseException, ...] = (),
    ):
        super().__init__(message)
        self.code = code
        self.field = field
        self.causes = list(causes)

    @property
    def message(self) -> str:
        return str(self)

    def to_dict(self) -> dict:
        """The refusal as plain data, each cause as its own refusal or exception."""
        return {
            "code": self.code,
            "field": self.field,
            "message": str(self),
            "causes": [_cause(item) for item in self.causes],
        }


def _cause(error: BaseException) -> dict:
    if isinstance(error, KernelError):
        return error.to_dict()
    return {
        "code": "system_error" if isinstance(error, OSError) else "unexpected",
        "field": getattr(error, "filename", None) or "",
        "message": f"{type(error).__name__}: {error}",
        "causes": [],
    }


__all__ = ["KernelError"]
