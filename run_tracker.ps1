[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'

Set-Location -LiteralPath $PSScriptRoot

$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    Write-Host '[エラー] 仮想環境が見つかりません'
    Write-Host '先に setup.ps1 を実行してください'
    Read-Host 'Enterキーで終了'
    exit 1
}

& $pythonPath 'mouse_tracker.py'
exit $LASTEXITCODE
