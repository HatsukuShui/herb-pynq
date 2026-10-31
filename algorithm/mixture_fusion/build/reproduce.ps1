param(
    [Parameter(Mandatory=$true)][string]$Archive,
    [string]$Python = 'python',
    [string]$Compiler = 'g++'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$rawArchive = (Resolve-Path -LiteralPath $Archive).Path
$stages = @(
    @{ Script='build_dataset.py'; Args=@('--archive',$rawArchive) },
    @{ Script='train_compare.py'; Args=@() },
    @{ Script='export_baselines.py'; Args=@() },
    @{ Script='export_verify.py'; Args=@('--compiler',$Compiler) },
    @{ Script='verify_inputs.py'; Args=@() },
    @{ Script='make_report.py'; Args=@() },
    @{ Script='package_delivery.py'; Args=@() }
)
$env:PYTHONIOENCODING='utf-8'
foreach ($stage in $stages) {
    $scriptPath = Join-Path $projectRoot ('src/' + $stage.Script)
    $arguments = @($scriptPath) + $stage.Args
    & $Python @arguments
    if ($LASTEXITCODE -ne 0) { throw ('Failed stage: ' + $stage.Script) }
}
