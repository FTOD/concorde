$ErrorActionPreference = "Stop"
& python (Join-Path $PSScriptRoot "concorde.py") @args
exit $LASTEXITCODE
