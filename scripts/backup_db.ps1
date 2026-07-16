param(
  [string]$Database = $env:PROMPT_OPTIMIZER_DB,
  [string]$Output = "prompt-optimizer-backup.sqlite3"
)
if ([string]::IsNullOrWhiteSpace($Database)) { throw "Set PROMPT_OPTIMIZER_DB or pass -Database." }
if (-not (Test-Path -LiteralPath $Database)) { throw "Database does not exist: $Database" }
Copy-Item -LiteralPath $Database -Destination $Output -Force
Write-Output "Backup written to $Output"
