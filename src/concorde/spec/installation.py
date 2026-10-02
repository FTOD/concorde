"""The spec part's install services, which its part registration names for Distribution's
installer: the docsite template it places and the binding of the installed files.

Each answers plain data, so that the installer needs none of the spec part's code but these
entries, and only where the spec part is installed.
"""

from __future__ import annotations

from pathlib import Path

from .errors import SpecError
from .initialize import bind_installation
from .views.docsite_template import (
    DocsiteTemplateError,
    template_files,
    verify_package_root,
)

# Where the installer places the docsite template, from which `concorde docsite --propose`
# scaffolds a project's site.
FRAMEWORK = ".concorde/framework"


def prepare(package, project) -> dict:
    """What the installer places for the spec part, decided before its first write: the docsite
    template Views' inventory rule selects from ``package``, by project-relative path, as
    ``{"files": {path: bytes}}``; ``{"refusal": {"code", "message"}}`` with
    ``invalid_docsite_template`` when the rule rejects the package's template."""
    try:
        verify_package_root(Path(package))
        files = template_files(Path(package))
    except DocsiteTemplateError as error:
        return {"refusal": {"code": error.code, "message": str(error)}}
    return {
        "files": {f"{FRAMEWORK}/{path}": content for path, content in files.items()}
    }


def bind(project) -> dict | None:
    """Keep the installed files of an initialized project bound after an install or update;
    None when that succeeded or had nothing to do, otherwise Spec core's error record
    (``contract.spec.error``), which the install result carries as ``binding_error``."""
    try:
        bind_installation(Path(project))
    except SpecError as error:
        return error.record()
    return None


__all__ = ["bind", "prepare"]
