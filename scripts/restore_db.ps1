param(
  [Parameter(Mandatory=$true)][string]$Backup,
  [string]$Database = $env:PROMPT_OPTIMIZER_DB
)
if ([string]::IsNullOrWhiteSpace($Database)) { throw "Set PROMPT_OPTIMIZER_DB or pass -Database." }
if (-not (Test-Path -LiteralPath $Backup)) { throw "Backup does not exist: $Backup" }
Copy-Item -LiteralPath $Backup -Destination $Database -Force
Write-Output "Database restored from $Backup"
