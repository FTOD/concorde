#!/usr/bin/env sh
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
extension_dir=$(CDPATH= cd -- "$script_dir/../.." && pwd)
exec python3 "$extension_dir/scripts/python/concorde.py" "$@"
