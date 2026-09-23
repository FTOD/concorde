"""Read the catalog a rendered Pi session entry embeds."""

import json
import re

CATALOG_PATTERN = re.compile(
    r"const CATALOG: SessionCatalog = (\{.*?\n\});\n\nexport default", re.DOTALL
)


def shim_catalog(content: bytes) -> dict:
    match = CATALOG_PATTERN.search(content.decode("utf-8"))
    assert match, "the shim embeds one CATALOG constant"
    return json.loads(match.group(1))
