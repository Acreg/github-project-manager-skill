#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$ArchiveLegacy,
    [switch]$IncludeClaude
)
$ErrorActionPreference = 'Stop'
$skillName = 'github-project-manager'
$source = Join-Path $PSScriptRoot 'skills/github-project-manager'
$sourceEntry = Join-Path $source 'SKILL.md'
if (-not (Test-Path -LiteralPath $sourceEntry -PathType Leaf)) {
    throw "Skill source not found. Run this script from the cloned repository."
}
$homePath = [Environment]::GetFolderPath('UserProfile')
$roots = @(
    (Join-Path $homePath '.agents/skills'),
    (Join-Path $homePath '.dsh/skills')
)
if ($IncludeClaude) {
    $roots += (Join-Path $homePath '.claude/skills')
}
$archiveRoot = Join-Path $homePath '.agent-skills-backups'
$stamp = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 6)

function Archive-Existing([string]$path, [string]$from) {
    if (-not (Test-Path -LiteralPath $path)) { return }
    if (-not (Test-Path -LiteralPath $archiveRoot)) {
        New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null
    }
    $dest = Join-Path $archiveRoot ($stamp + '-' + $from + '-' + [IO.Path]::GetFileName($path))
    Move-Item -LiteralPath $path -Destination $dest -ErrorAction Stop
    Write-Output ("BACKUP " + $path + " => " + $dest)
}

foreach ($targetRoot in $roots) {
    New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
    $label = if ($targetRoot -like '*\.dsh\*') { 'dsh' } elseif ($targetRoot -like '*\.claude\*') { 'claude' } else { 'agents' }
    $dest = Join-Path $targetRoot $skillName
    # Existing same-named Skill is backed up, never silently overwritten.
    Archive-Existing $dest $label
    Copy-Item -LiteralPath $source -Destination $dest -Recurse -Force
    $expected = @(Get-ChildItem -LiteralPath $source -File -Recurse)
    foreach ($file in $expected) {
        $relative = $file.FullName.Substring($source.Length + 1)
        $installed = Join-Path $dest $relative
        if (-not (Test-Path -LiteralPath $installed -PathType Leaf)) {
            throw "Missing installed file: $relative"
        }
        if ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne
            (Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash) {
            throw "Installed file hash mismatch: $relative"
        }
    }
    Write-Output ("INSTALLED " + $dest + " (" + $expected.Count + " verified files)")
    if ($ArchiveLegacy) {
        foreach ($legacy in @('github-cli-workflow', 'private-github-source-sync')) {
            Archive-Existing (Join-Path $targetRoot $legacy) $label
        }
    }
}
Write-Output 'COMPLETED: Codex/DSH (and selected optional targets) have one merged skill.'
Write-Output 'The installer did not modify GitHub credentials or application settings.'
