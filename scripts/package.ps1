[CmdletBinding()]
param(
    [string]$Version = '0.1.0'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Dist = Join-Path $ProjectRoot 'dist'
$Archive = Join-Path $Dist "proofmesh-document-auditor-v$Version.zip"
$Staging = Join-Path $Dist (".staging-" + [guid]::NewGuid().ToString('N'))

$Included = @(
    'README.md',
    'SKILL.md',
    'info.json',
    'meta.json',
    'LICENSE',
    'NOTICE',
    'THIRD_PARTY_NOTICES.md',
    'pyproject.toml',
    'requirements.txt',
    'requirements.lock',
    'assets',
    'config',
    'docs',
    'evaluation',
    'examples',
    'models',
    'rules',
    'scripts',
    'src',
    'tests'
)

New-Item -ItemType Directory -Path $Dist -Force | Out-Null
New-Item -ItemType Directory -Path $Staging | Out-Null
$StagingRoot = [IO.Path]::GetFullPath($Staging).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar

try {
    foreach ($Item in $Included) {
        $Source = Join-Path $ProjectRoot $Item
        if (-not (Test-Path -LiteralPath $Source)) {
            throw "发布所需文件不存在：$Item"
        }
        Copy-Item -LiteralPath $Source -Destination (Join-Path $Staging $Item) -Recurse
    }

    $GeneratedDirectories = Get-ChildItem -LiteralPath $Staging -Directory -Recurse | Where-Object {
        $_.Name -eq '__pycache__' -or $_.Name -like '*.egg-info'
    }
    foreach ($Directory in $GeneratedDirectories) {
        $Target = [IO.Path]::GetFullPath($Directory.FullName)
        if (-not $Target.StartsWith($StagingRoot, [StringComparison]::OrdinalIgnoreCase)) {
            throw "拒绝清理发布暂存目录之外的路径：$Target"
        }
        Remove-Item -LiteralPath $Target -Recurse -Force
    }
    Get-ChildItem -LiteralPath $Staging -File -Recurse -Filter '*.pyc' | Remove-Item -Force

    Compress-Archive -Path (Join-Path $Staging '*') -DestinationPath $Archive -CompressionLevel Optimal -Force
    $Hash = Get-FileHash -LiteralPath $Archive -Algorithm SHA256
    [pscustomobject]@{
        archive = $Archive
        bytes = (Get-Item -LiteralPath $Archive).Length
        sha256 = $Hash.Hash.ToLowerInvariant()
    } | ConvertTo-Json
}
finally {
    $Target = [IO.Path]::GetFullPath($Staging)
    if ($Target.StartsWith($StagingRoot, [StringComparison]::OrdinalIgnoreCase) -or ($Target + [IO.Path]::DirectorySeparatorChar) -eq $StagingRoot) {
        Remove-Item -LiteralPath $Target -Recurse -Force -ErrorAction SilentlyContinue
    }
}
