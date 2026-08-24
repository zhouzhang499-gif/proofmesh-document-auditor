[CmdletBinding()]
param(
    [string]$Version = '0.1.0'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Dist = Join-Path $ProjectRoot 'dist'
$Archive = Join-Path $Dist "proofmesh-modelscope-v$Version.zip"
$Staging = Join-Path $Dist ('.modelscope-' + [guid]::NewGuid().ToString('N'))
$MaximumBytes = 5MB
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
    'config',
    'docs',
    'examples',
    'evaluation',
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
        if (Test-Path -LiteralPath $Source) {
            Copy-Item -LiteralPath $Source -Destination (Join-Path $Staging $Item) -Recurse
        }
    }
    $AssetsTarget = Join-Path $Staging 'assets'
    New-Item -ItemType Directory -Path $AssetsTarget -Force | Out-Null
    foreach ($Asset in @('proofmesh-icon.png', 'architecture.svg')) {
        Copy-Item -LiteralPath (Join-Path $ProjectRoot "assets\$Asset") -Destination (Join-Path $AssetsTarget $Asset)
    }
    $LockFile = Join-Path $ProjectRoot 'requirements.lock'
    if (Test-Path -LiteralPath $LockFile) {
        Copy-Item -LiteralPath $LockFile -Destination (Join-Path $Staging 'requirements.lock')
    }
    $ModelTarget = Join-Path $Staging 'models\bge-small-zh-v1.5-openvino'
    New-Item -ItemType Directory -Path $ModelTarget -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'models\bge-small-zh-v1.5-openvino\model-manifest.json') -Destination $ModelTarget
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'models\model-distribution.json') -Destination (Join-Path $Staging 'models\model-distribution.json')

    # 通用 Agent Skill 规范不接受顶层 version；ModelScope 上传规范要求它。
    # 仅在发布暂存文件中注入版本号，保持仓库内 SKILL.md 可被通用校验器接受。
    $StagedSkillPath = Join-Path $Staging 'SKILL.md'
    $StagedSkillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $StagedSkillPath
    if ($StagedSkillText -notmatch '(?m)^version\s*:') {
        $StagedSkillText = $StagedSkillText -replace '(?m)^(name\s*:\s*.+)$', "`$1`nversion: $Version"
        [IO.File]::WriteAllText($StagedSkillPath, $StagedSkillText, [Text.UTF8Encoding]::new($false))
    }

    Get-ChildItem -LiteralPath $Staging -Directory -Recurse | Where-Object {
        $_.Name -eq '__pycache__' -or $_.Name -like '*.egg-info'
    } | ForEach-Object {
        $Target = [IO.Path]::GetFullPath($_.FullName)
        if (-not $Target.StartsWith($StagingRoot, [StringComparison]::OrdinalIgnoreCase)) {
            throw "拒绝清理发布暂存目录之外的路径：$Target"
        }
        Remove-Item -LiteralPath $Target -Recurse -Force
    }
    Get-ChildItem -LiteralPath $Staging -File -Recurse -Filter '*.pyc' | Remove-Item -Force

    $SkillText = Get-Content -Raw -Encoding UTF8 -LiteralPath $StagedSkillPath
    foreach ($Field in @('name', 'version', 'description')) {
        if ($SkillText -notmatch "(?m)^$Field\s*:\s*.+$") {
            throw "SKILL.md 缺少 frontmatter 字段：$Field"
        }
    }

    Compress-Archive -Path (Join-Path $Staging '*') -DestinationPath $Archive -CompressionLevel Optimal -Force
    $ArchiveInfo = Get-Item -LiteralPath $Archive
    if ($ArchiveInfo.Length -gt $MaximumBytes) {
        throw "ModelScope Skill 包超过 5MB：$($ArchiveInfo.Length) bytes"
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        $SkillEntries = @($Zip.Entries | Where-Object { $_.FullName -match '(^|/)SKILL\.md$' })
        if ($SkillEntries.Count -ne 1 -or $SkillEntries[0].FullName -ne 'SKILL.md') {
            throw 'ZIP 根目录必须恰好包含一个 SKILL.md。'
        }
    }
    finally {
        $Zip.Dispose()
    }

    $Hash = Get-FileHash -LiteralPath $Archive -Algorithm SHA256
    $HashFile = "$Archive.sha256"
    [IO.File]::WriteAllText($HashFile, "$($Hash.Hash.ToLowerInvariant()) *$([IO.Path]::GetFileName($Archive))`n", [Text.UTF8Encoding]::new($false))
    [pscustomobject]@{
        archive = $Archive
        bytes = $ArchiveInfo.Length
        sha256 = $Hash.Hash.ToLowerInvariant()
        sha256_file = $HashFile
        skill_md = 'SKILL.md'
    } | ConvertTo-Json
}
finally {
    $Target = [IO.Path]::GetFullPath($Staging)
    if ($Target.StartsWith($StagingRoot, [StringComparison]::OrdinalIgnoreCase) -or ($Target + [IO.Path]::DirectorySeparatorChar) -eq $StagingRoot) {
        Remove-Item -LiteralPath $Target -Recurse -Force -ErrorAction SilentlyContinue
    }
}
