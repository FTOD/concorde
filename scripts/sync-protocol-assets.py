#!/usr/bin/env python3
"""Maintainer-only export; project Protocol upgrades require explicit --bind-project."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from concorde.capabilities.protocol_contracts import OPERATIONS, dependencies
from concorde.capabilities.operation_data import json_schema
from concorde.specification.repository import digest

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--bind-project",action="store_true")
    args=parser.parse_args()
    names=[f"{op}-{suffix}" for op in OPERATIONS for suffix in ("request","response")]
    names += ["concorde-agent-stage-context","concorde-agent-stage-result"]
    (ROOT/"protocol/schemas.json").write_text(json.dumps({name:json_schema(name) for name in names},indent=2)+"\n")
    for operation in OPERATIONS:
        skill=ROOT/"operations"/operation/"SKILL.md"
        body=skill.read_text().split("\n## Input TypedValue schema\n",1)[0].rstrip()
        body=body.replace("(the initialized concorde-operation-configuration@1)",
                          "(null to load initialized host settings, or a matching concorde-operation-configuration@1)")
        skill.write_text(body+"\n\n## Input TypedValue schema\n\n"+
            "This complete schema is the invocation's input field. It does not grant project reads.\n\n```json\n"+
            json.dumps(json_schema(operation+"-request"),indent=2)+"\n```\n")
    manifest=json.loads((ROOT/"protocol/manifest.json").read_text())
    for item in manifest["assets"]:
        item["digest"]=digest((ROOT/item["path"]).read_bytes())
    path=ROOT/"protocol/manifest.json";path.write_text(json.dumps(manifest,indent=2)+"\n")
    if args.bind_project:
        config_path=ROOT/".concorde/config.json";config=json.loads(config_path.read_text())
        config["protocol"]={"version":manifest["version"],"digest":digest(path.read_bytes())}
        config_path.write_text(json.dumps(config,indent=2)+"\n")
if __name__=="__main__": main()
