param(
    [string]$SkillName = "excel-professional-formatting"
)

$ErrorActionPreference = "Stop"

$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
$skillsRoot = Join-Path $codexHome "skills"
$destDir = Join-Path $skillsRoot $SkillName
$backupDir = Join-Path $skillsRoot ($SkillName + ".backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))

Write-Host "Source skill :" $sourceDir
Write-Host "Codex home   :" $codexHome
Write-Host "Destination  :" $destDir

if (-not (Test-Path -LiteralPath (Join-Path $sourceDir "SKILL.md"))) {
    throw "Active SKILL.md not found in $sourceDir"
}

if (-not (Test-Path $skillsRoot)) {
    New-Item -ItemType Directory -Path $skillsRoot | Out-Null
}

if (Test-Path $destDir) {
    Write-Host "Backing up existing skill to:" $backupDir
    Copy-Item -Path $destDir -Destination $backupDir -Recurse -Force
}

if (-not (Test-Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir | Out-Null
}

$itemsToCopy = @("SKILL.md", "agents", "references")
foreach ($item in $itemsToCopy) {
    $sourceItem = Join-Path $sourceDir $item
    if (Test-Path -LiteralPath $sourceItem) {
        Copy-Item -Path $sourceItem -Destination $destDir -Recurse -Force
    }
}

Write-Host ""
Write-Host "Installed skill '$SkillName' to $destDir"
Write-Host "If Codex is already open, restart the app or start a new session to refresh skill discovery."
