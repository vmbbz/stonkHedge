[CmdletBinding()]
param(
    [string]$ManifestPath = (Join-Path (Split-Path $PSScriptRoot -Parent) "manifests\baseline\2026-09-08.json"),
    [string]$ProductPath,
    [string]$CorePath,
    [string]$SdkPath,
    [switch]$AllowDirty
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-CheckedGit {
    param(
        [Parameter(Mandatory)] [string]$RepositoryPath,
        [Parameter(Mandatory)] [string[]]$Arguments
    )

    $output = & git -c "safe.directory=$RepositoryPath" -C $RepositoryPath @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed in $RepositoryPath`n$($output -join "`n")"
    }

    return ($output -join "`n").Trim()
}

function Write-Check {
    param(
        [Parameter(Mandatory)] [ValidateSet("PASS", "FAIL", "BLOCKED", "SKIPPED")] [string]$Status,
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [string]$Detail
    )

    Write-Host ("[{0}] {1}: {2}" -f $Status, $Name, $Detail)
    if ($Status -in @("FAIL", "BLOCKED")) {
        $script:BaselineFailed = $true
    }
}

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Baseline manifest not found: $ManifestPath"
}

$manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$productRoot = Split-Path $PSScriptRoot -Parent

$pathOverrides = @{
    product = if ($ProductPath) { $ProductPath } else { $productRoot }
    core = $CorePath
    sdk = $SdkPath
}

$script:BaselineFailed = $false

foreach ($repository in $manifest.repositories) {
    $repositoryPath = $pathOverrides[$repository.id]
    if (-not $repositoryPath) {
        $repositoryPath = $repository.localPath
    }

    if (-not (Test-Path -LiteralPath $repositoryPath -PathType Container)) {
        Write-Check -Status "FAIL" -Name "$($repository.id) checkout" -Detail "missing at $repositoryPath"
        continue
    }

    try {
        $actualCommit = Invoke-CheckedGit -RepositoryPath $repositoryPath -Arguments @("rev-parse", "HEAD")
        if ($repository.commitPolicy -eq "ancestor") {
            & git -c "safe.directory=$repositoryPath" -C $repositoryPath merge-base --is-ancestor $repository.commit HEAD 2>&1 | Out-Null
            $commitStatus = if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" }
            $commitExpectation = "must contain baseline $($repository.commit)"
        }
        else {
            $commitStatus = if ($actualCommit -eq $repository.commit) { "PASS" } else { "FAIL" }
            $commitExpectation = "expected exact $($repository.commit)"
        }
        Write-Check -Status $commitStatus -Name "$($repository.id) commit" -Detail "$actualCommit ($commitExpectation)"

        $actualBranch = Invoke-CheckedGit -RepositoryPath $repositoryPath -Arguments @("branch", "--show-current")
        $branchStatus = if ($actualBranch -eq $repository.branch) { "PASS" } else { "FAIL" }
        Write-Check -Status $branchStatus -Name "$($repository.id) branch" -Detail "$actualBranch (expected $($repository.branch))"

        foreach ($remote in $repository.remotes.PSObject.Properties) {
            $actualUrl = Invoke-CheckedGit -RepositoryPath $repositoryPath -Arguments @("remote", "get-url", $remote.Name)
            $remoteStatus = if ($actualUrl -eq $remote.Value) { "PASS" } else { "FAIL" }
            Write-Check -Status $remoteStatus -Name "$($repository.id) remote $($remote.Name)" -Detail "$actualUrl (expected $($remote.Value))"
        }

        foreach ($requiredPath in $repository.requiredPaths) {
            $fullRequiredPath = Join-Path $repositoryPath $requiredPath
            $requiredStatus = if (Test-Path -LiteralPath $fullRequiredPath) { "PASS" } else { "FAIL" }
            Write-Check -Status $requiredStatus -Name "$($repository.id) path" -Detail $requiredPath
        }

        if ($repository.requireInitializedSubmodules) {
            $submoduleStatus = Invoke-CheckedGit -RepositoryPath $repositoryPath -Arguments @("submodule", "status", "--recursive")
            $badSubmodules = @($submoduleStatus -split "`r?`n" | Where-Object { $_ -match "^[+-]" })
            if ($badSubmodules.Count -eq 0) {
                Write-Check -Status "PASS" -Name "$($repository.id) submodules" -Detail "all recursive submodules are initialized at recorded gitlinks"
            }
            else {
                Write-Check -Status "FAIL" -Name "$($repository.id) submodules" -Detail ($badSubmodules -join "; ")
            }
        }

        if ($AllowDirty) {
            Write-Check -Status "SKIPPED" -Name "$($repository.id) worktree" -Detail "dirty-tree enforcement disabled explicitly"
        }
        else {
            $worktree = Invoke-CheckedGit -RepositoryPath $repositoryPath -Arguments @("status", "--porcelain=v1", "--untracked-files=all")
            if ([string]::IsNullOrWhiteSpace($worktree)) {
                Write-Check -Status "PASS" -Name "$($repository.id) worktree" -Detail "clean"
            }
            else {
                Write-Check -Status "FAIL" -Name "$($repository.id) worktree" -Detail ($worktree -replace "`r?`n", "; ")
            }
        }
    }
    catch {
        Write-Check -Status "FAIL" -Name "$($repository.id) verification" -Detail $_.Exception.Message
    }
}

foreach ($gate in $manifest.gates) {
    Write-Check -Status $gate.status -Name "manifest gate $($gate.id)" -Detail $gate.detail
}

if ($script:BaselineFailed) {
    Write-Host "Baseline verification did not pass. Resolve or explicitly update the recorded blockers before changing inherited protocol behavior."
    exit 1
}

Write-Host "Baseline verification passed."
exit 0
