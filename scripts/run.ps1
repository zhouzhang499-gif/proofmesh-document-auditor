[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet('audit', 'status', 'show', 'shutdown')]
    [string]$Command,

    [string]$Path,
    [string]$RunId
)

$ErrorActionPreference = 'Stop'
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$Python = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { 'python' }
$Client = Join-Path $PSScriptRoot 'client.py'

$Arguments = @($Client, $Command)
if ($Path) { $Arguments += @('--path', (Resolve-Path -LiteralPath $Path).Path) }
if ($RunId) { $Arguments += @('--run-id', $RunId) }

& $Python @Arguments
exit $LASTEXITCODE
