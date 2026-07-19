[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Command,
    [Parameter(ValueFromRemainingArguments = $true, Position = 1)]
    [string[]]$Arguments
)

# RC IDs: RC-185, RC-199. Keep PowerShell user-scoped and never invoke elevation.
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $python) {
    throw "Python 3 is required to run the local model installer."
}

$separator = [IO.Path]::PathSeparator
$env:PYTHONPATH = "$(Join-Path $root 'backend\src')$separator$(Join-Path $root 'backend')$separator$(Join-Path $root 'packages\protocol')$separator$($env:PYTHONPATH)"
& $python (Join-Path $PSScriptRoot "local_model_install.py") $Command @Arguments
exit $LASTEXITCODE
