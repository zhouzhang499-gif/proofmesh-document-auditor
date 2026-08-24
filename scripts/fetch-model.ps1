[CmdletBinding()]
param(
    [string]$Url,
    [string]$Sha256,
    [switch]$Offline
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$Python = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { 'python' }
$Script = Join-Path $PSScriptRoot 'fetch_model.py'
$Arguments = @($Script)
if ($Url) { $Arguments += @('--url', $Url) }
if ($Sha256) { $Arguments += @('--sha256', $Sha256) }
if ($Offline) { $Arguments += '--offline' }

& $Python @Arguments
exit $LASTEXITCODE
