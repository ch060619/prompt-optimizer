#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Rabbit Code CLI installer for Windows.
.DESCRIPTION
  Installs Rabbit Code via pip (PyPI) and verifies the installation.
  Usage: irm https://rabbit-code.dev/install.ps1 | iex
.PARAMETER Version
  Specific version to install (default: latest).
.PARAMETER Python
  Python executable to use (default: python).
#>
param(
  [string]$Version = "",
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "Rabbit Code CLI Installer for Windows" -ForegroundColor Cyan

# Check Python
$pyVersion = & $Python --version 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Error "Python not found. Install Python 3.12+ from https://python.org"
  exit 1
}
Write-Host "Using: $pyVersion"

# Install package
$pkg = "rabbit-code"
if ($Version) { $pkg += "==$Version" }
Write-Host "Installing $pkg from PyPI..."
& $Python -m pip install --upgrade $pkg
if ($LASTEXITCODE -ne 0) {
  Write-Error "Installation failed."
  exit 1
}

# Verify
$rabbitVersion = & rabbit version 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Warning "rabbit command not found in PATH. You may need to restart your terminal."
  Write-Host "Try: python -m prompt_optimizer.cli.app version"
} else {
  Write-Host "Installed: $rabbitVersion" -ForegroundColor Green
  Write-Host "Run 'rabbit --help' to get started."
}
