param(
    [string]$RootPath = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) "validation-reports"),
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$runDir = Join-Path $OutputRoot $timestamp
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

$skillRoot = $RootPath
$pluginRoot = Join-Path $RootPath "plugins\excel-professional-formatting"
$localSkillRoot = Join-Path $env:USERPROFILE ".codex\skills\excel-professional-formatting"
$localPluginRoot = Join-Path $env:USERPROFILE "plugins\excel-professional-formatting"
$marketplacePath = Join-Path $env:USERPROFILE ".agents\plugins\marketplace.json"
$configPath = Join-Path $env:USERPROFILE ".codex\config.toml"

$jobScript = {
    param($LaneName, $SkillRoot, $PluginRoot, $LocalSkillRoot, $LocalPluginRoot, $MarketplacePath, $ConfigPath)

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
            $openAi = Join-Path $SkillRoot "agents\openai.yaml"
            $refs = @(
                "references\validation-checklist.md",
                "references\sidecar-formatting-pass.md",
                "references\promotion-and-rollback.md",
                "references\parallel-agent-workflow.md"
            ) | ForEach-Object { Join-Path $SkillRoot $_ }

            $checks = @(
                "skill manifest present",
                "openai metadata present",
                "required references present"
            )
            $notes = @()
            $status = "pass"

            if (-not (Test-Path -LiteralPath $skillMd)) { $status = "fail"; $notes += "missing SKILL.md" }
            if (-not (Test-Path -LiteralPath $openAi)) { $status = "fail"; $notes += "missing agents\\openai.yaml" }
            foreach ($ref in $refs) {
                if (-not (Test-Path -LiteralPath $ref)) {
                    $status = "fail"
                    $notes += ("missing {0}" -f [System.IO.Path]::GetFileName($ref))
                }
            }

            New-LaneBlockLocal -Name $LaneName -Status $status -Checks $checks -Notes $notes -Artifacts (@($skillMd, $openAi) + $refs)
        }
        "plugin-package" {
            $pluginJson = Join-Path $PluginRoot ".codex-plugin\plugin.json"
            $embeddedSkill = Join-Path $PluginRoot "skills\excel-professional-formatting"
            $checks = @(
                "plugin manifest exists",
                "plugin manifest parses as JSON",
                "embedded skill tree exists",
                "source and embedded skill files stay aligned"
            )
            $notes = @()
            $status = "pass"

            if (-not (Test-Path -LiteralPath $pluginJson)) {
                $status = "fail"
                $notes += "missing plugin.json"
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

            if (-not (Test-Path -LiteralPath $embeddedSkill)) {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "embedded skill tree not present"
            }
            else {
                $sourceFiles = @("SKILL.md") +
                    (Get-ChildItem -LiteralPath (Join-Path $SkillRoot "agents") -Recurse -File | ForEach-Object {
                        $_.FullName.Substring($SkillRoot.Length).TrimStart('\')
                    }) +
                    (Get-ChildItem -LiteralPath (Join-Path $SkillRoot "references") -Recurse -File | ForEach-Object {
                        $_.FullName.Substring($SkillRoot.Length).TrimStart('\')
                    })

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

            New-LaneBlockLocal -Name $LaneName -Status $status -Checks $checks -Notes $notes -Artifacts @($pluginJson, $embeddedSkill)
        }
        "install-registration" {
            $installScript = Join-Path $SkillRoot "install_excel_professional_formatting_skill.ps1"
            $pluginInstallScript = Join-Path $SkillRoot "install_excel_professional_formatting_plugin.ps1"
            $marketplaceTemplate = Join-Path $SkillRoot ".agents\plugins\marketplace.json"
            $checks = @(
                "skill install script exists",
                "plugin install script exists",
                "repo-local marketplace exists",
                "local skill folder exists",
                "local plugin folder exists",
                "config references plugin"
            )
            $notes = @()
            $status = "pass"

            if (-not (Test-Path -LiteralPath $installScript)) { $status = "fail"; $notes += "missing skill install script" }
            if (-not (Test-Path -LiteralPath $pluginInstallScript)) { $status = "fail"; $notes += "missing plugin install script" }
            if (-not (Test-Path -LiteralPath $marketplaceTemplate)) { if ($status -eq "pass") { $status = "warning" }; $notes += "missing repo-local marketplace template" }
            if (-not (Test-Path -LiteralPath $LocalSkillRoot)) { if ($status -eq "pass") { $status = "warning" }; $notes += "local skill folder not found" }
            if (-not (Test-Path -LiteralPath $LocalPluginRoot)) { if ($status -eq "pass") { $status = "warning" }; $notes += "local plugin folder not found" }

            if (Test-Path -LiteralPath $ConfigPath) {
                $configText = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8
                if ($configText -notmatch 'excel-professional-formatting') {
                    if ($status -eq "pass") { $status = "warning" }
                    $notes += "config does not reference excel-professional-formatting"
                }
            }
            else {
                if ($status -eq "pass") { $status = "warning" }
                $notes += "config.toml not found"
            }

            New-LaneBlockLocal -Name $LaneName -Status $status -Checks $checks -Notes $notes -Artifacts @($installScript, $pluginInstallScript, $marketplaceTemplate, $LocalSkillRoot, $LocalPluginRoot, $MarketplacePath, $ConfigPath)
        }
        "sidecar-contract" {
            $readme = Join-Path $SkillRoot "README.md"
            $validationGuide = Join-Path $SkillRoot "VALIDATION.md"
            $sidecarGuide = Join-Path $SkillRoot "references\sidecar-formatting-pass.md"
            $promotionGuide = Join-Path $SkillRoot "references\promotion-and-rollback.md"
            $validationGuideRef = Join-Path $SkillRoot "references\validation-checklist.md"

            $checks = @(
                "README documents validation runner",
                "validation guide exists",
                "sidecar guide exists",
                "promotion guide exists",
                "validation checklist exists"
            )
            $notes = @()
            $status = "pass"

            foreach ($path in @($readme, $validationGuide, $sidecarGuide, $promotionGuide, $validationGuideRef)) {
                if (-not (Test-Path -LiteralPath $path)) {
                    $status = "fail"
                    $notes += ("missing {0}" -f [System.IO.Path]::GetFileName($path))
                }
            }

            if (Test-Path -LiteralPath $readme) {
                $readmeText = Get-Content -LiteralPath $readme -Raw -Encoding UTF8
                if ($readmeText -notmatch [regex]::Escape("run_excel_professional_formatting_validation.ps1")) {
                    if ($status -eq "pass") { $status = "warning" }
                    $notes += "README does not mention validation runner"
                }
            }

            New-LaneBlockLocal -Name $LaneName -Status $status -Checks $checks -Notes $notes -Artifacts @($readme, $validationGuide, $sidecarGuide, $promotionGuide, $validationGuideRef)
        }
    }
}

$lanes = @("skill-structure", "plugin-package", "install-registration", "sidecar-contract")
$jobs = foreach ($lane in $lanes) {
    Start-Job -ScriptBlock $jobScript -ArgumentList $lane, $skillRoot, $pluginRoot, $localSkillRoot, $localPluginRoot, $marketplacePath, $configPath
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
$markdown += "# Excel Professional Formatting Validation Summary"
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
