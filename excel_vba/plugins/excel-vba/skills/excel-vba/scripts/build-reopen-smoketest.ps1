# Example:
# powershell -ExecutionPolicy Bypass -File .\build-reopen-smoketest.ps1 `
#   -SourceWorkbook C:\work\input.xlsx `
#   -OutputWorkbook C:\work\output.xlsm `
#   -ModulePath C:\work\modAutomation.bas `
#   -EntryMacro RunAutomation `
#   -SmokeMacros FilterExample,ClearFilter `
#   -ExpectedSheets Result,Validation_Errors,LOG `
#   -InspectSheet Result

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceWorkbook,

    [string]$OutputWorkbook = "",
    [string]$ModulePath = "",
    [string]$ModuleName = "",
    [string]$EntryMacro = "",
    [string[]]$SmokeMacros = @(),
    [string[]]$ExpectedSheets = @("Result", "Validation_Errors", "LOG"),
    [string]$InspectSheet = ""
)

$ErrorActionPreference = "Stop"

function Resolve-FullPath {
    param([Parameter(Mandatory = $true)][string]$PathText)

    if (-not (Test-Path -LiteralPath $PathText)) {
        throw "Path not found: $PathText"
    }

    return (Resolve-Path -LiteralPath $PathText).Path
}

function Get-DefaultOutputWorkbook {
    param([Parameter(Mandatory = $true)][string]$SourcePath)

    $sourceDir = Split-Path -Path $SourcePath -Parent
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($SourcePath)
    return (Join-Path $sourceDir ($baseName + "_automation_smoketest.xlsm"))
}

function Get-SafeModuleName {
    param([Parameter(Mandatory = $true)][string]$NameText)

    $clean = ($NameText -replace '[^A-Za-z0-9_]', '_')
    if ([string]::IsNullOrWhiteSpace($clean)) {
        return "modAutomation"
    }
    if ($clean -match '^[0-9]') {
        $clean = "mod_" + $clean
    }
    return $clean
}

function Get-QualifiedMacroName {
    param(
        [Parameter(Mandatory = $true)]$Workbook,
        [Parameter(Mandatory = $true)][string]$MacroName
    )

    if ($MacroName -match "!") {
        return $MacroName
    }

    return "'$($Workbook.Name)'!$MacroName"
}

function Read-VbaModuleText {
    param([Parameter(Mandatory = $true)][string]$PathText)

    $raw = Get-Content -LiteralPath $PathText -Encoding UTF8 -Raw
    return [regex]::Replace($raw, '^(Attribute VB_[^\r\n]*\r?\n)+', '', 'Multiline')
}

function Remove-ModuleIfPresent {
    param(
        [Parameter(Mandatory = $true)]$VBProject,
        [Parameter(Mandatory = $true)][string]$TargetModuleName
    )

    foreach ($component in @($VBProject.VBComponents)) {
        if ($component.Name -eq $TargetModuleName) {
            $VBProject.VBComponents.Remove($component)
            break
        }
    }
}

function Add-StandardModuleFromString {
    param(
        [Parameter(Mandatory = $true)]$VBProject,
        [Parameter(Mandatory = $true)][string]$TargetModuleName,
        [Parameter(Mandatory = $true)][string]$ModuleCode
    )

    $vbext_ct_StdModule = 1
    $module = $VBProject.VBComponents.Add($vbext_ct_StdModule)
    $module.Name = $TargetModuleName
    $module.CodeModule.AddFromString($ModuleCode)
}

function Assert-ExpectedSheets {
    param(
        [Parameter(Mandatory = $true)]$Workbook,
        [Parameter(Mandatory = $true)][string[]]$SheetNames
    )

    foreach ($sheetName in $SheetNames) {
        if ([string]::IsNullOrWhiteSpace($sheetName)) {
            continue
        }

        try {
            $null = $Workbook.Worksheets.Item($sheetName)
        }
        catch {
            throw "Expected sheet missing after smoke test: $sheetName"
        }
    }
}

function Write-InspectSummary {
    param(
        [Parameter(Mandatory = $true)]$Workbook,
        [Parameter(Mandatory = $true)][string]$SheetName
    )

    $ws = $Workbook.Worksheets.Item($SheetName)
    $shapeCount = 0
    $freezePanes = ""
    $autoFilterRef = ""
    $usedAddress = ""

    try { $shapeCount = $ws.Shapes.Count } catch {}
    try { $freezePanes = [string]$ws.Application.ActiveWindow.FreezePanes } catch {}
    try { $autoFilterRef = [string]$ws.AutoFilter.Range.Address(0, 0) } catch {}
    try { $usedAddress = [string]$ws.UsedRange.Address(0, 0) } catch {}

    Write-Host ("InspectSheet.Name={0}" -f $ws.Name)
    Write-Host ("InspectSheet.UsedRange={0}" -f $usedAddress)
    Write-Host ("InspectSheet.ShapeCount={0}" -f $shapeCount)
    Write-Host ("InspectSheet.AutoFilter={0}" -f $autoFilterRef)
    Write-Host ("InspectSheet.FreezePanes={0}" -f $freezePanes)
}

function Release-ComObjectSafe {
    param($ComObject)

    if ($null -ne $ComObject) {
        try {
            [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($ComObject)
        }
        catch {
        }
    }
}

$resolvedSourceWorkbook = Resolve-FullPath -PathText $SourceWorkbook

if ([string]::IsNullOrWhiteSpace($OutputWorkbook)) {
    $OutputWorkbook = Get-DefaultOutputWorkbook -SourcePath $resolvedSourceWorkbook
}

if (-not [System.IO.Path]::IsPathRooted($OutputWorkbook)) {
    $OutputWorkbook = Join-Path (Split-Path -Path $resolvedSourceWorkbook -Parent) $OutputWorkbook
}

$resolvedOutputWorkbook = $OutputWorkbook
$resolvedModulePath = ""

if (-not [string]::IsNullOrWhiteSpace($ModulePath)) {
    $resolvedModulePath = Resolve-FullPath -PathText $ModulePath
    if ([string]::IsNullOrWhiteSpace($ModuleName)) {
        $ModuleName = Get-SafeModuleName -NameText ([System.IO.Path]::GetFileNameWithoutExtension($resolvedModulePath))
    }
}

if (Test-Path -LiteralPath $resolvedOutputWorkbook) {
    Remove-Item -LiteralPath $resolvedOutputWorkbook -Force
}

$excel = $null
$buildWorkbook = $null
$runtimeWorkbook = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false

    $buildWorkbook = $excel.Workbooks.Open($resolvedSourceWorkbook, 0, $true)
    $xlOpenXMLWorkbookMacroEnabled = 52
    $buildWorkbook.SaveAs($resolvedOutputWorkbook, $xlOpenXMLWorkbookMacroEnabled)

    if (-not [string]::IsNullOrWhiteSpace($resolvedModulePath)) {
        try {
            $vbProject = $buildWorkbook.VBProject
        }
        catch {
            throw "Unable to access VBProject. Enable 'Trust access to the VBA project object model' in Excel."
        }

        $moduleCode = Read-VbaModuleText -PathText $resolvedModulePath
        Remove-ModuleIfPresent -VBProject $vbProject -TargetModuleName $ModuleName
        Add-StandardModuleFromString -VBProject $vbProject -TargetModuleName $ModuleName -ModuleCode $moduleCode
    }

    $buildWorkbook.Save()
    $buildWorkbook.Close($false)
    Release-ComObjectSafe -ComObject $buildWorkbook
    $buildWorkbook = $null

    $runtimeWorkbook = $excel.Workbooks.Open($resolvedOutputWorkbook)

    if (-not [string]::IsNullOrWhiteSpace($EntryMacro)) {
        $qualifiedEntryMacro = Get-QualifiedMacroName -Workbook $runtimeWorkbook -MacroName $EntryMacro
        $excel.Run($qualifiedEntryMacro)
        Write-Host ("EntryMacro={0}" -f $qualifiedEntryMacro)
    }

    foreach ($smokeMacro in $SmokeMacros) {
        if ([string]::IsNullOrWhiteSpace($smokeMacro)) {
            continue
        }

        $qualifiedSmokeMacro = Get-QualifiedMacroName -Workbook $runtimeWorkbook -MacroName $smokeMacro
        $excel.Run($qualifiedSmokeMacro)
        Write-Host ("SmokeMacro={0}" -f $qualifiedSmokeMacro)
    }

    Assert-ExpectedSheets -Workbook $runtimeWorkbook -SheetNames $ExpectedSheets

    if (-not [string]::IsNullOrWhiteSpace($InspectSheet)) {
        $runtimeWorkbook.Worksheets.Item($InspectSheet).Activate() | Out-Null
        Write-InspectSummary -Workbook $runtimeWorkbook -SheetName $InspectSheet
    }

    $runtimeWorkbook.Save()

    Write-Host ("Created={0}" -f $resolvedOutputWorkbook)
    Write-Host ("ExpectedSheets={0}" -f ($ExpectedSheets -join ","))
}
finally {
    if ($runtimeWorkbook -ne $null) {
        try { $runtimeWorkbook.Close($false) } catch {}
        Release-ComObjectSafe -ComObject $runtimeWorkbook
    }

    if ($buildWorkbook -ne $null) {
        try { $buildWorkbook.Close($false) } catch {}
        Release-ComObjectSafe -ComObject $buildWorkbook
    }

    if ($excel -ne $null) {
        try { $excel.Quit() } catch {}
        Release-ComObjectSafe -ComObject $excel
    }

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
