[CmdletBinding()]
param(
    [string]$Version = '0.1.0'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ModelDir = Join-Path $ProjectRoot 'models\bge-small-zh-v1.5-openvino'
$Manifest = Join-Path $ModelDir 'model-manifest.json'
$Dist = Join-Path $ProjectRoot 'dist'
$Archive = Join-Path $Dist "proofmesh-openvino-model-v$Version.zip"

if (-not (Test-Path -LiteralPath $Manifest)) {
    throw "模型清单不存在：$Manifest"
}
New-Item -ItemType Directory -Path $Dist -Force | Out-Null
Compress-Archive -LiteralPath $ModelDir -DestinationPath $Archive -CompressionLevel Optimal -Force
$Hash = Get-FileHash -LiteralPath $Archive -Algorithm SHA256
$HashFile = "$Archive.sha256"
[IO.File]::WriteAllText($HashFile, "$($Hash.Hash.ToLowerInvariant()) *$([IO.Path]::GetFileName($Archive))`n", [Text.UTF8Encoding]::new($false))
[pscustomobject]@{
    archive = $Archive
    bytes = (Get-Item -LiteralPath $Archive).Length
    sha256 = $Hash.Hash.ToLowerInvariant()
    sha256_file = $HashFile
} | ConvertTo-Json
