[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet('audit', 'status', 'show', 'shutdown')]
    [string]$Command,

    [string]$Path,
    [string]$RunId
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$Python = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { 'python' }
$Client = Join-Path $PSScriptRoot 'client.py'

$Arguments = @($Client, $Command)
if ($Path) { $Arguments += @('--path', (Resolve-Path -LiteralPath $Path).Path) }
if ($RunId) { $Arguments += @('--run-id', $RunId) }

& $Python @Arguments
exit $LASTEXITCODE

