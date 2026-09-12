"""Compatibility entry for the executable Flow exporter."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("concorde_flow_export", Path(__file__).with_name("flows.py"))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
export = _module.export

if __name__ == "__main__":
    import json
    print(json.dumps(export()))
