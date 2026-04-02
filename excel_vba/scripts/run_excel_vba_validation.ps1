param(
    [string]$RootPath = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) "validation-reports"),
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$runDir = Join-Path $OutputRoot $timestamp
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

$skillRoot = Join-Path $RootPath "excel-vba"
$pluginRoot = Join-Path $RootPath "plugins\excel-vba"
$localSkillRoot = Join-Path $env:USERPROFILE ".codex\skills\excel-vba"
$localPluginRoot = Join-Path $env:USERPROFILE "plugins\excel-vba"
$marketplacePath = Join-Path $env:USERPROFILE ".agents\plugins\marketplace.json"
$configPath = Join-Path $env:USERPROFILE ".codex\config.toml"

$jobScript = {
    param($LaneName, $SkillRoot, $RepoRoot, $PluginRoot, $LocalSkillRoot, $LocalPluginRoot, $MarketplacePath, $ConfigPath)

    function New-LaneBlockLocal {
        param(
            [string]$Name,
            [string]$Status,
            [string[]]$Checks,
            [string[]]$Notes = @(),
            [string[]]$Artifacts = @()
        )

        [pscustomobject]@{
            lane      = $Name
            status    = $Status
            checks    = $Checks
            notes     = $Notes
            artifacts = $Artifacts
        }
    }

    switch ($LaneName) {
        "skill-structure" {
            $skillMd = Join-Path $SkillRoot "SKILL.md"
            $skillDisabled = Join-Path $SkillRoot "SKILL.md.disabled"
            $openAi = Join-Path $SkillRoot "agents\openai.yaml"
            $openAiDisabled = Join-Path $SkillRoot "agents\openai.yaml.disabled"
            $refs = Join-Path $SkillRoot "references"

            $checks = @(
                "skill manifest present",
                "openai metadata present",
                "reference directory present",
                "reopen smoke script present"
            )
            $notes = @()
            $status = "pass"

            if (-not (Test-Path -LiteralPath $refs)) { $status = "fail"; $notes += "missing references directory" }
            if (-not (Test-Path -LiteralPath (Join-Path $SkillRoot "scripts\build-reopen-smoketest.ps1"))) { $status = "fail"; $notes += "missing smoke script" }

            if (Test-Path -LiteralPath $skillMd) {
                $notes += "active SKILL.md found"
            }
            elseif (Test-Path -LiteralPath $skillDisabled) {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "SKILL.md is still disabled"
            }
            else {
                $status = "fail"
                $notes += "missing SKILL.md and SKILL.md.disabled"
            }

            if (Test-Path -LiteralPath $openAi) {
                $notes += "active openai.yaml found"
            }
            elseif (Test-Path -LiteralPath $openAiDisabled) {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "openai.yaml is still disabled"
            }
            else {
                $status = "fail"
                $notes += "missing openai.yaml and openai.yaml.disabled"
            }

            New-LaneBlockLocal -Name $LaneName -Status $status -Checks $checks -Notes $notes -Artifacts @($skillMd, $skillDisabled, $openAi, $openAiDisabled)
        }
        "plugin-package" {
            $pluginJson = Join-Path $PluginRoot ".codex-plugin\plugin.json"
            $pluginSkills = Join-Path $PluginRoot "skills"
            $embeddedSkill = Join-Path $pluginSkills "excel-vba"
            $marketplace = Join-Path $RepoRoot ".agents\plugins\marketplace.json"

            $checks = @(
                "plugin manifest exists",
                "plugin skill tree exists",
                "marketplace file exists",
                "plugin manifest parses as JSON",
                "source and embedded skill files stay aligned"
            )
            $notes = @()
            $status = "pass"

            if (-not (Test-Path -LiteralPath $pluginJson)) {
                $status = "fail"
                $notes += "missing .codex-plugin\\plugin.json"
            }
            else {
                try {
                    $null = Get-Content -LiteralPath $pluginJson -Raw -Encoding UTF8 | ConvertFrom-Json
                    $notes += "plugin manifest parsed"
                }
                catch {
                    $status = "fail"
                    $notes += "plugin manifest JSON parse failed"
                }
            }

            if (-not (Test-Path -LiteralPath $pluginSkills)) {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "plugin skill tree not present yet"
            }
            elseif (-not (Test-Path -LiteralPath $embeddedSkill)) {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "embedded excel-vba skill tree not present yet"
            }
            else {
                $sourceFiles = Get-ChildItem -LiteralPath $SkillRoot -Recurse -File | ForEach-Object {
                    $_.FullName.Substring($SkillRoot.Length).TrimStart('\')
                }
                $embeddedFiles = Get-ChildItem -LiteralPath $embeddedSkill -Recurse -File | ForEach-Object {
                    $_.FullName.Substring($embeddedSkill.Length).TrimStart('\')
                }

                $sourceDiff = Compare-Object -ReferenceObject $sourceFiles -DifferenceObject $embeddedFiles
                if ($sourceDiff) {
                    if ($status -eq "pass") { $status = "warning" }
                    $notes += "embedded skill tree differs from source skill tree"
                }
                else {
                    $notes += "embedded skill tree matches source file list"
                }
            }

            if (-not (Test-Path -LiteralPath $marketplace)) {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "repo-local marketplace file not present yet"
            }

            New-LaneBlockLocal -Name $LaneName -Status $status -Checks $checks -Notes $notes -Artifacts @($pluginJson, $pluginSkills, $embeddedSkill, $marketplace)
        }
        "install-registration" {
            $installScript = Join-Path $RepoRoot "install_excel_vba_skill.ps1"
            $pluginInstallScript = Join-Path $RepoRoot "install_excel_vba_plugin.ps1"
            $checks = @(
                "local install script exists",
                "plugin install script exists",
                "Codex skill folder exists",
                "plugin folder exists",
                "marketplace path exists",
                "config indicates plugin support"
            )
            $notes = @()
            $status = "pass"

            if (-not (Test-Path -LiteralPath $installScript)) {
                $status = "fail"
                $notes += "missing install_excel_vba_skill.ps1"
            }
            if (-not (Test-Path -LiteralPath $pluginInstallScript)) {
                $status = "fail"
                $notes += "missing install_excel_vba_plugin.ps1"
            }

            if (Test-Path -LiteralPath $LocalSkillRoot) {
                $notes += "local Codex skill folder present"
            }
            else {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "local Codex skill folder not found"
            }

            if (Test-Path -LiteralPath $LocalPluginRoot) {
                $notes += "local plugin folder present"
            }
            else {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "local plugin folder not found"
            }

            if (Test-Path -LiteralPath $MarketplacePath) {
                $notes += "marketplace file present"
            }
            else {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "marketplace file not found"
            }

            if (Test-Path -LiteralPath $ConfigPath) {
                $configText = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8
                if ($configText -match 'excel-vba') {
                    $notes += "config references excel-vba"
                }
                else {
                    if ($status -eq "pass") { $status = "warning" }
                    $notes += "config does not reference excel-vba"
                }
            }
            else {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "config.toml not found"
            }

            New-LaneBlockLocal -Name $LaneName -Status $status -Checks $checks -Notes $notes -Artifacts @($installScript, $pluginInstallScript, $LocalSkillRoot, $LocalPluginRoot, $MarketplacePath, $ConfigPath)
        }
        "qa-contract" {
            $qaGuide = Join-Path $SkillRoot "references\qa-and-operations.md"
            $windowsGuide = Join-Path $SkillRoot "references\windows-com-and-unicode.md"
            $contract = Join-Path $SkillRoot "references\output-contract.md"
            $conflict = Join-Path $SkillRoot "references\conflict-checklist.md"
            $smoke = Join-Path $SkillRoot "scripts\build-reopen-smoketest.ps1"
            $readme = Join-Path $RepoRoot "README.md"
            $validationGuide = Join-Path $RepoRoot "VALIDATION.md"

            $checks = @(
                "QA reference present",
                "Windows/Unicode reference present",
                "output contract present",
                "conflict checklist present",
                "smoke script present",
                "README documents validation",
                "validation guide present"
            )
            $notes = @()
            $status = "pass"

            foreach ($path in @($qaGuide, $windowsGuide, $contract, $conflict, $smoke, $readme, $validationGuide)) {
                if (-not (Test-Path -LiteralPath $path)) {
                    $status = "fail"
                    $notes += "missing $([System.IO.Path]::GetFileName($path))"
                }
            }

            $readmeText = if (Test-Path -LiteralPath $readme) { Get-Content -LiteralPath $readme -Raw -Encoding UTF8 } else { "" }
            $validationText = if (Test-Path -LiteralPath $validationGuide) { Get-Content -LiteralPath $validationGuide -Raw -Encoding UTF8 } else { "" }

            if ($readmeText -notmatch [regex]::Escape("scripts/run_excel_vba_validation.ps1")) {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "README does not mention validation runner"
            }

            if ($validationText -notmatch [regex]::Escape("validation-reports")) {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "validation guide does not mention report output path"
            }

            New-LaneBlockLocal -Name $LaneName -Status $status -Checks $checks -Notes $notes -Artifacts @($qaGuide, $windowsGuide, $contract, $conflict, $smoke, $readme, $validationGuide)
        }
    }
}

$lanes = @("skill-structure", "plugin-package", "install-registration", "qa-contract")
$jobs = foreach ($lane in $lanes) {
    Start-Job -ScriptBlock $jobScript -ArgumentList $lane, $skillRoot, $RootPath, $pluginRoot, $localSkillRoot, $localPluginRoot, $marketplacePath, $configPath
}

Wait-Job -Job $jobs | Out-Null
$results = foreach ($job in $jobs) { Receive-Job -Job $job }
Remove-Job -Job $jobs | Out-Null

$statusRank = @{ pass = 0; warning = 1; fail = 2 }
$overall = "pass"
foreach ($result in $results) {
    if ($statusRank[$result.status] -gt $statusRank[$overall]) {
        $overall = $result.status
    }
}

$jsonReport = [pscustomobject]@{
    timestamp   = $timestamp
    rootPath    = $RootPath
    outputPath  = $runDir
    overall     = $overall
    lanes       = $results
}

$markdown = @()
$markdown += "# Excel-VBA Validation Summary"
$markdown += ""
$markdown += "- Timestamp: $timestamp"
$markdown += "- Root: $RootPath"
$markdown += "- Overall: $overall"
$markdown += ""
$markdown += "## Lane Results"
foreach ($result in $results) {
    $markdown += ""
    $markdown += "### $($result.lane)"
    $markdown += "- Status: $($result.status)"
    $markdown += "- Checks: $($result.checks -join '; ')"
    if ($result.notes.Count -gt 0) {
        $markdown += "- Notes:"
        foreach ($note in $result.notes) {
            $markdown += "  - $note"
        }
    }
    if ($result.artifacts.Count -gt 0) {
        $markdown += "- Artifacts:"
        foreach ($artifact in $result.artifacts) {
            $markdown += "  - $artifact"
        }
    }
}

$markdown += ""
$markdown += "## Output Files"
$markdown += "- $($runDir)\summary.md"
$markdown += "- $($runDir)\summary.json"

$mdPath = Join-Path $runDir "summary.md"
$jsonPath = Join-Path $runDir "summary.json"

$markdown -join "`r`n" | Set-Content -LiteralPath $mdPath -Encoding UTF8
$jsonReport | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

Write-Host "Summary written to:"
Write-Host "  $mdPath"
Write-Host "  $jsonPath"
Write-Host "Overall status: $overall"

if ($Strict -and $overall -ne "pass") {
    throw "Validation completed with status '$overall' under -Strict."
}
