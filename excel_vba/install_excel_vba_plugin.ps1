param(
    [string]$PluginName = "excel-vba",
    [string]$SourcePluginRoot = "",
    [string]$TargetPluginsRoot = "",
    [string]$MarketplacePath = "",
    [string]$ConfigPath = "",
    [switch]$Force,
    [switch]$Register,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($SourcePluginRoot)) {
    $SourcePluginRoot = Join-Path $repoRoot ("plugins\" + $PluginName)
}

if ([string]::IsNullOrWhiteSpace($TargetPluginsRoot)) {
    $TargetPluginsRoot = Join-Path $env:USERPROFILE "plugins"
}

if ([string]::IsNullOrWhiteSpace($MarketplacePath)) {
    $MarketplacePath = Join-Path $env:USERPROFILE ".agents\plugins\marketplace.json"
}

if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
    $ConfigPath = Join-Path $env:USERPROFILE ".codex\config.toml"
}

$TargetPluginRoot = Join-Path $TargetPluginsRoot $PluginName
$backupStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupRoot = $TargetPluginRoot + ".backup-" + $backupStamp

function Write-Plan {
    param([string]$Message)
    Write-Host $Message
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Copy-Tree {
    param(
        [string]$Source,
        [string]$Destination
    )

    Ensure-Directory -Path $Destination
    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $Destination -Recurse -Force
    }
}

function Read-JsonFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Write-JsonFile {
    param(
        [string]$Path,
        $InputObject
    )

    $directory = Split-Path -Parent $Path
    Ensure-Directory -Path $directory
    $json = $InputObject | ConvertTo-Json -Depth 12
    Set-Content -LiteralPath $Path -Value $json -Encoding UTF8
}

function Update-Marketplace {
    param(
        [string]$Path,
        [string]$PluginName,
        [string]$SourcePath
    )

    $marketplace = Read-JsonFile -Path $Path
    if ($null -eq $marketplace) {
        $marketplace = [ordered]@{
            name = "local-marketplace"
            interface = [ordered]@{
                displayName = "Local Plugins"
            }
            plugins = @()
        }
    }

    $entry = [ordered]@{
        name = $PluginName
        source = [ordered]@{
            source = "local"
            path = $SourcePath
        }
        policy = [ordered]@{
            installation = "AVAILABLE"
            authentication = "ON_INSTALL"
        }
        category = "Productivity"
    }

    $filtered = @()
    foreach ($plugin in @($marketplace.plugins)) {
        if ($plugin.name -ne $PluginName) {
            $filtered += $plugin
        }
    }

    $marketplace.plugins = @($filtered + $entry)
    Write-JsonFile -Path $Path -InputObject $marketplace
}

function Enable-PluginInConfig {
    param(
        [string]$Path,
        [string]$PluginName
    )

    $sectionHeader = "[plugins.""{0}""]" -f $PluginName
    $enabledLine = "enabled = true"
    $current = ""

    if (Test-Path -LiteralPath $Path) {
        $current = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    }

    if ($current -match [regex]::Escape($sectionHeader)) {
        if ($current -notmatch ('(?ms)^\[plugins\."' + [regex]::Escape($PluginName) + '"\]\s*^enabled = true$')) {
            $pattern = '(?ms)(^\[plugins\."' + [regex]::Escape($PluginName) + '"\]\s*)(^enabled = .*$)?'
            if ($current -match $pattern) {
                $replacement = $sectionHeader + "`r`n" + $enabledLine
                $current = [regex]::Replace($current, $pattern, $replacement, 1)
            }
        }
    }
    else {
        if ($current -and -not $current.EndsWith("`n")) {
            $current += "`r`n"
        }
        $current += $sectionHeader + "`r`n" + $enabledLine + "`r`n"
    }

    $directory = Split-Path -Parent $Path
    Ensure-Directory -Path $directory
    Set-Content -LiteralPath $Path -Value $current -Encoding UTF8
}

if (-not (Test-Path -LiteralPath $SourcePluginRoot)) {
    throw "Source plugin root not found: $SourcePluginRoot"
}

if ($DryRun) {
    Write-Plan "Dry run"
    Write-Plan ("Source plugin root : {0}" -f $SourcePluginRoot)
    Write-Plan ("Target plugin root : {0}" -f $TargetPluginRoot)
    Write-Plan ("Marketplace path   : {0}" -f $MarketplacePath)
    Write-Plan ("Config path        : {0}" -f $ConfigPath)
    if ($Register) {
        Write-Plan "Will update marketplace entry and enable excel-vba in config.toml"
    }
    exit 0
}

Ensure-Directory -Path $TargetPluginsRoot

if (Test-Path -LiteralPath $TargetPluginRoot) {
    if (-not $Force) {
        throw "Target plugin already exists: $TargetPluginRoot. Re-run with -Force to replace it."
    }

    Write-Host ("Backing up existing plugin to {0}" -f $backupRoot)
    Copy-Item -LiteralPath $TargetPluginRoot -Destination $backupRoot -Recurse -Force
    Remove-Item -LiteralPath $TargetPluginRoot -Recurse -Force
}

Write-Host ("Copying plugin bundle from {0} to {1}" -f $SourcePluginRoot, $TargetPluginRoot)
Copy-Tree -Source $SourcePluginRoot -Destination $TargetPluginRoot

if ($Register) {
    Write-Host ("Updating marketplace file {0}" -f $MarketplacePath)
    Update-Marketplace -Path $MarketplacePath -PluginName $PluginName -SourcePath ("./plugins/{0}" -f $PluginName)
    Write-Host ("Enabling plugin in config {0}" -f $ConfigPath)
    Enable-PluginInConfig -Path $ConfigPath -PluginName $PluginName
}

Write-Host ""
Write-Host ("Installed plugin '{0}' to {1}" -f $PluginName, $TargetPluginRoot)
if ($Register) {
    Write-Host ("Marketplace entry updated at {0}" -f $MarketplacePath)
    Write-Host ("Config updated at {0}" -f $ConfigPath)
}
Write-Host "Restart Codex or open a new session to refresh plugin discovery."
