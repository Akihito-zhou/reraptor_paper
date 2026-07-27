param(
    [string]$DateTag = "20260725"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$PythonExe = "C:\Users\12730\anaconda3\envs\research\python.exe"
$ResultDir = Join-Path $RepoRoot "paper\results\exp3_parameter_sensitivity"
$LogDir = Join-Path $ResultDir "logs"
$QueueLog = Join-Path $LogDir "sensitivity_queue_$DateTag.log"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Required Python environment not found: $PythonExe"
}

New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$OatConfigs = @(
    "default",
    "w10",
    "w25",
    "w100",
    "w200",
    "cap15_10",
    "cap60_40",
    "cap_uncapped",
    "reward5000",
    "reward20000",
    "sph0",
    "sph2p5",
    "sph10",
    "time0",
    "time0p05",
    "time0p2",
    "neg0p5",
    "neg2"
)

$InteractionConfigs = @(
    "int_w25_cap15_10",
    "int_w25_cap60_40",
    "int_w100_cap15_10",
    "int_w100_cap60_40"
)

function Invoke-SensitivityConfig {
    param(
        [Parameter(Mandatory = $true)][string]$Panel,
        [Parameter(Mandatory = $true)][string]$ConfigId,
        [Parameter(Mandatory = $true)][string]$OutputPath,
        [switch]$IncludeDefault
    )

    $Arguments = @(
        "-m",
        "paper.experiments.exp3_parameter_sensitivity.run_sensitivity",
        "--panel", $Panel,
        "--configs", $ConfigId,
        "--resume",
        "--checkpoint-every", "10",
        "--timeout-seconds", "60",
        "--output-tag", "canonical_${Panel}_${ConfigId}_${DateTag}",
        "--output", $OutputPath
    )
    if ($IncludeDefault) {
        $Arguments += "--include-default"
    }

    $Started = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$Started] START panel=$Panel config=$ConfigId output=$OutputPath" |
        Tee-Object -FilePath $QueueLog -Append
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $PythonExe @Arguments 2>&1 |
            Tee-Object -FilePath $QueueLog -Append
        $NativeExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $PreviousErrorActionPreference
    }
    if ($NativeExitCode -ne 0) {
        throw "Sensitivity config failed: panel=$Panel config=$ConfigId exit=$NativeExitCode"
    }
    $Finished = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$Finished] COMPLETE panel=$Panel config=$ConfigId" |
        Tee-Object -FilePath $QueueLog -Append
}

Push-Location $RepoRoot
try {
    foreach ($ConfigId in $OatConfigs) {
        $OutputPath = Join-Path $ResultDir "sensitivity_results_oat_${ConfigId}_${DateTag}.json"
        Invoke-SensitivityConfig `
            -Panel "oat" `
            -ConfigId $ConfigId `
            -OutputPath $OutputPath `
            -IncludeDefault:($ConfigId -eq "default")
    }

    foreach ($ConfigId in $InteractionConfigs) {
        $OutputPath = Join-Path $ResultDir "sensitivity_results_interaction_${ConfigId}_${DateTag}.json"
        Invoke-SensitivityConfig `
            -Panel "interaction" `
            -ConfigId $ConfigId `
            -OutputPath $OutputPath
    }

    $Finished = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$Finished] QUEUE COMPLETE" |
        Tee-Object -FilePath $QueueLog -Append
}
finally {
    Pop-Location
}
