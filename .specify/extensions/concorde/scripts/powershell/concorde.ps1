$ErrorActionPreference = "Stop"
$ExtensionRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
& python (Join-Path $ExtensionRoot "scripts/python/concorde.py") @args
exit $LASTEXITCODE
