param(
    [string]$Tag = "score_guided_multitheme_20260411",
    [string]$ScoreSeeds = "20260323,20260324,20260325",
    [string]$NegativePressureLevels = "default,tight",
    [int]$CheckpointEvery = 20,
    [switch]$Resume,
    [switch]$NegativeOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\\..\\..")
Set-Location $repoRoot

$supportArgs = @(
    "paper\experiments\exp2_ablation_study\run_exp2_supporting.py"
    "--score-seeds", $ScoreSeeds
    "--negative-pressure-levels", $NegativePressureLevels
    "--checkpoint-every", $CheckpointEvery
    "--output-tag", $Tag
)

if ($Resume) {
    $supportArgs += "--resume"
}

if ($NegativeOnly) {
    $supportArgs += @("--experiments", "negative_project_theme_alignment")
}

$supportResults = "paper\results\exp2_ablation_study\exp2_supporting_results_{0}.json" -f $Tag

Write-Host "[1/3] Running Exp2 supporting..."
& python @supportArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "[2/3] Plotting Exp2 supporting..."
& python "paper\experiments\exp2_ablation_study\plot_exp2_supporting.py" "--input" $supportResults
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "[3/3] Re-plotting main Exp2..."
& python "paper\experiments\exp2_ablation_study\plot_exp2.py" "--input" "paper\results\exp2_ablation_study\exp2_results.json"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "All Exp2 tasks finished."
