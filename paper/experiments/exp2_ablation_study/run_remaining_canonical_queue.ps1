[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$resultsDir = Join-Path $projectRoot "paper\results\exp2_ablation_study"
$manifestDir = Join-Path $projectRoot "paper\results\manifests"
$stateDir = Join-Path $projectRoot "tmp\exp2_queue_20260723"
$statePath = Join-Path $stateDir "queue-state.json"
$lockPath = Join-Path $stateDir "queue.pid"
$runModule = "paper.experiments.exp2_ablation_study.run_exp2"
$manifestModule = "paper.experiments.common.build_canonical_manifest"
$generatorScript = Join-Path $projectRoot "paper\experiments\exp2_ablation_study\run_exp2.py"

New-Item -ItemType Directory -Force $resultsDir, $manifestDir, $stateDir | Out-Null
Set-Location $projectRoot

$condaExe = $env:CONDA_EXE
if ([string]::IsNullOrWhiteSpace($condaExe) -or -not (Test-Path -LiteralPath $condaExe)) {
    $condaCommand = Get-Command conda.exe -ErrorAction Stop
    $condaExe = $condaCommand.Source
}

$queue = @(
    [pscustomobject]@{ Alias = "noneg"; Slug = "noneg"; Label = "Ours (NoNeg)" },
    [pscustomobject]@{ Alias = "nodom"; Slug = "nodom"; Label = "Ours (NoDom)" },
    [pscustomobject]@{ Alias = "nobeam"; Slug = "nobeam"; Label = "Ours (NoBeam)" },
    [pscustomobject]@{ Alias = "nobeamnodom"; Slug = "nobeam_nodom"; Label = "Ours (NoBeam-NoDom)" },
    [pscustomobject]@{ Alias = "nodomnoneg"; Slug = "nodom_noneg"; Label = "Ours (NoDom-NoNeg)" },
    [pscustomobject]@{ Alias = "nobeamnoneg"; Slug = "nobeam_noneg"; Label = "Ours (NoBeam-NoNeg)" },
    [pscustomobject]@{ Alias = "nobeamnodomnoneg"; Slug = "nobeam_nodom_noneg"; Label = "Ours (NoBeam-NoDom-NoNeg)" }
)

$completed = [System.Collections.Generic.List[string]]::new()

function Write-QueueState {
    param(
        [Parameter(Mandatory = $true)][string]$Status,
        [string]$CurrentAlias = "",
        [string]$CurrentLabel = "",
        [int]$QueueIndex = 0,
        [string]$Message = ""
    )

    $payload = [ordered]@{
        updated_at = (Get-Date).ToString("o")
        process_id = $PID
        status = $Status
        current_alias = $CurrentAlias
        current_label = $CurrentLabel
        queue_index = $QueueIndex
        queue_total = $queue.Count
        completed_shards = @($completed)
        message = $Message
    }
    $payload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8
}

function Invoke-ManifestAudit {
    param(
        [Parameter(Mandatory = $true)][string]$ResultPath,
        [Parameter(Mandatory = $true)][string]$ManifestPath
    )

    $auditArgs = @(
        "run", "--no-capture-output", "-n", "research",
        "python", "-u", "-m", $manifestModule,
        "--result", $ResultPath,
        "--output", $ManifestPath,
        "--status", "provisional",
        "--generator-script", $generatorScript
    )
    & $condaExe @auditArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Manifest audit failed for $ResultPath (exit code $LASTEXITCODE)."
    }
}

if (Test-Path -LiteralPath $lockPath) {
    $existingPidText = (Get-Content -LiteralPath $lockPath -Raw).Trim()
    $existingPid = 0
    if ([int]::TryParse($existingPidText, [ref]$existingPid)) {
        $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($null -ne $existingProcess) {
            throw "Another Experiment 2 queue is already running with PID $existingPid."
        }
    }
    Remove-Item -LiteralPath $lockPath -Force
}

$PID | Set-Content -LiteralPath $lockPath -Encoding ASCII

try {
    Write-QueueState -Status "auditing_full" -Message "Validating the completed Full shard before starting the remaining queue."
    $fullResult = Join-Path $resultsDir "exp2_results_canonical_exp2_full_20260723.json"
    $fullManifest = Join-Path $manifestDir "phasea_exp2_full_manifest_20260723.json"
    if (-not (Test-Path -LiteralPath $fullResult)) {
        throw "Completed Full shard is missing: $fullResult"
    }
    Invoke-ManifestAudit -ResultPath $fullResult -ManifestPath $fullManifest

    for ($index = 0; $index -lt $queue.Count; $index++) {
        $item = $queue[$index]
        $position = $index + 1
        $outputTag = "canonical_exp2_$($item.Slug)_20260723"
        $resultPath = Join-Path $resultsDir "exp2_results_$outputTag.json"
        $manifestPath = Join-Path $manifestDir "phasea_exp2_$($item.Slug)_manifest_20260723.json"

        Write-QueueState `
            -Status "running" `
            -CurrentAlias $item.Alias `
            -CurrentLabel $item.Label `
            -QueueIndex $position `
            -Message "Running shard $position of $($queue.Count)."

        Write-Output ""
        Write-Output "======================================================================"
        Write-Output "[$(Get-Date -Format o)] Starting $($item.Label) ($position/$($queue.Count))"
        Write-Output "Result: $resultPath"
        Write-Output "======================================================================"

        $runArgs = @(
            "run", "--no-capture-output", "-n", "research",
            "python", "-u", "-m", $runModule,
            "--resume",
            "--checkpoint-every", "10",
            "--timeout-seconds", "60",
            "--no-pruning-max-labels", "1000000",
            "--score-seeds", "20260323,20260324,20260325,20260326,20260327",
            "--score-min", "1",
            "--score-max", "100",
            "--dwell-minutes", "10",
            "--objective-mode", "score_guided",
            "--origins", "hakata,tenjin,nishijin,ohori-koen,yakuin,kashii,noke,meinohama,kaizuka,fukudaimae",
            "--depart-times", "420,600,840",
            "--budgets", "120,240,360,480",
            "--seeds", "0",
            "--configs", $item.Alias,
            "--output-tag", $outputTag
        )
        & $condaExe @runArgs
        if ($LASTEXITCODE -ne 0) {
            throw "$($item.Label) failed with exit code $LASTEXITCODE."
        }

        Write-QueueState `
            -Status "auditing" `
            -CurrentAlias $item.Alias `
            -CurrentLabel $item.Label `
            -QueueIndex $position `
            -Message "Run finished; validating the 600 expected task keys and row semantics."

        Invoke-ManifestAudit -ResultPath $resultPath -ManifestPath $manifestPath
        $completed.Add($item.Alias)
        Write-Output "[$(Get-Date -Format o)] Completed and audited $($item.Label)."
    }

    Write-QueueState `
        -Status "complete" `
        -QueueIndex $queue.Count `
        -Message "All seven remaining Experiment 2 shards completed and passed provisional integrity audits."
    Write-Output "[$(Get-Date -Format o)] All remaining Experiment 2 shards are complete."
}
catch {
    Write-QueueState `
        -Status "failed" `
        -Message $_.Exception.Message
    Write-Error $_
    exit 1
}
finally {
    if (Test-Path -LiteralPath $lockPath) {
        $ownerPid = (Get-Content -LiteralPath $lockPath -Raw).Trim()
        if ($ownerPid -eq [string]$PID) {
            Remove-Item -LiteralPath $lockPath -Force
        }
    }
}
