$ErrorActionPreference = "Stop"

$packageDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
$skillsRoot = Join-Path $codexHome "skills"
$backupRoot = Join-Path $codexHome "skill-backups"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

$skillMappings = @(
    @{
        Name = "excel-professional-formatting"
        SourceDir = Join-Path $packageDir "excel-professional-formatting"
        DestinationDir = Join-Path $skillsRoot "excel-professional-formatting"
        ExcludeNames = @("install_excel_professional_formatting_skill.ps1")
    },
    @{
        Name = "excel-vba"
        SourceDir = Join-Path $packageDir "excel-vba"
        DestinationDir = Join-Path $skillsRoot "excel-vba"
        ExcludeNames = @("install_excel_vba_skill.ps1")
    },
    @{
        Name = "spreadsheet"
        SourceDir = Join-Path $packageDir "spreadsheet"
        DestinationDir = Join-Path $skillsRoot "spreadsheet"
        ExcludeNames = @()
    },
    @{
        Name = ".system/skill-creator"
        SourceDir = Join-Path $packageDir ".system\skill-creator"
        DestinationDir = Join-Path $skillsRoot ".system\skill-creator"
        ExcludeNames = @()
    }
)

Write-Host "Package root :" $packageDir
Write-Host "Codex home   :" $codexHome
Write-Host "Skills root  :" $skillsRoot

if (-not (Test-Path $skillsRoot)) {
    New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
}

foreach ($mapping in $skillMappings) {
    $sourceDir = $mapping.SourceDir
    $destDir = $mapping.DestinationDir
    $destParent = Split-Path -Parent $destDir
    $backupLeaf = (($mapping.Name -replace '[\\\/]', '__') + ".backup-" + $timestamp)
    $backupDir = Join-Path $backupRoot $backupLeaf

    if (-not (Test-Path $sourceDir)) {
        throw "Missing packaged skill folder: $sourceDir"
    }

    if (-not (Test-Path $destParent)) {
        New-Item -ItemType Directory -Path $destParent -Force | Out-Null
    }

    Write-Host ""
    Write-Host "Installing skill:" $mapping.Name
    Write-Host "Source      :" $sourceDir
    Write-Host "Destination :" $destDir

    if (Test-Path $destDir) {
        if (-not (Test-Path $backupRoot)) {
            New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
        }
        Write-Host "Backing up existing skill to:" $backupDir
        Copy-Item -Path $destDir -Destination $backupDir -Recurse -Force
    }

    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }

    Get-ChildItem -Force $sourceDir | Where-Object {
        $_.Name -notin $mapping.ExcludeNames
    } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $destDir -Recurse -Force
    }
}

Write-Host ""
Write-Host "Installed bundled skills to $skillsRoot"
Write-Host "Existing Codex skills not listed above were intentionally left untouched."
Write-Host "If Codex is already open, restart the app or start a new session to refresh skill discovery."
