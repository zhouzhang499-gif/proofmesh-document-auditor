[CmdletBinding()]
param(
    [switch]$SkipModel,
    [string]$ModelUrl,
    [string]$ModelSha256
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $ProjectRoot '.venv'
$VenvPython = Join-Path $Venv 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $VenvPython)) {
    $Launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($Launcher) {
        & py -3.11 -m venv $Venv
    } else {
        & python -m venv $Venv
    }
}

& $VenvPython -m pip install --upgrade pip
$LockFile = Join-Path $ProjectRoot 'requirements.lock'
if (Test-Path -LiteralPath $LockFile) {
    & $VenvPython -m pip install --require-hashes -r $LockFile
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $VenvPython -m pip install --no-deps -e $ProjectRoot
} else {
    & $VenvPython -m pip install -e $ProjectRoot
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $VenvPython -c "from openvino import Core; print('OpenVINO devices:', Core().available_devices)"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not $SkipModel) {
    $FetchParameters = @{}
    if ($ModelUrl) { $FetchParameters['Url'] = $ModelUrl }
    if ($ModelSha256) { $FetchParameters['Sha256'] = $ModelSha256 }
    & (Join-Path $PSScriptRoot 'fetch-model.ps1') @FetchParameters
}
exit $LASTEXITCODE
