[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

Set-Location -LiteralPath $PSScriptRoot

$script:PythonExe = $null
$script:PythonDir = $null
$script:MegaCmdPath = $null

function Pause-IfNeeded {
    if (-not $env:SETUP_NOPAUSE) {
        Read-Host 'Enterキーで終了'
    }
}

function Write-Header {
    Write-Host '============================================'
    Write-Host '  スクリーンショットツール セットアップ'
    Write-Host '============================================'
    Write-Host ''
}

function Find-MegaCmd {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'MEGAcmd'),
        'C:\Program Files\MEGAcmd',
        'C:\Program Files (x86)\MEGAcmd'
    )

    foreach ($path in $candidates) {
        if (Test-Path -LiteralPath (Join-Path $path 'mega-put.bat')) {
            return $path
        }
    }

    return $null
}

function Ensure-MegaCmdPath {
    if (-not $MegaCmdPath) {
        return
    }

    if ($env:PATH -notlike "*${MegaCmdPath}*") {
        $env:PATH = "$env:PATH;$MegaCmdPath"
        Write-Host 'MEGAcmdをPATHに追加しました（このウィンドウのみ）'
    } else {
        Write-Host 'MEGAcmdは既にPATHに含まれています'
    }
}

function Invoke-Download {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$OutFile
    )

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    } catch {
    }

    if ($PSVersionTable.PSVersion.Major -lt 6) {
        Invoke-WebRequest -Uri $Uri -OutFile $OutFile -UseBasicParsing
    } else {
        Invoke-WebRequest -Uri $Uri -OutFile $OutFile
    }
}

function Install-MegaCmd {
    $url32 = 'https://mega.nz/MEGAcmdSetup32.exe'
    $url64 = 'https://mega.nz/MEGAcmdSetup64.exe'
    $arch = $env:PROCESSOR_ARCHITECTURE

    if ($arch -ieq 'x86' -and $env:PROCESSOR_ARCHITEW6432) {
        $arch = 'AMD64'
    }

    if ($arch -ieq 'AMD64' -or $arch -ieq 'ARM64') {
        $url = $url64
    } else {
        $url = $url32
    }

    $installer = Join-Path $env:TEMP 'MEGAcmdSetup.exe'

    Write-Host ''
    Write-Host 'MEGAcmdをダウンロード中...'
    try {
        Invoke-Download -Uri $url -OutFile $installer
    } catch {
        Write-Host '[エラー] MEGAcmdのダウンロードに失敗しました'
        return $false
    }

    if (-not (Test-Path -LiteralPath $installer)) {
        Write-Host '[エラー] MEGAcmdのインストーラが見つかりません'
        return $false
    }

    Write-Host 'MEGAcmdをインストール中...（完了まで待ってください）'
    $proc = Start-Process -FilePath $installer -ArgumentList '/S' -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        Write-Host '[エラー] MEGAcmdのインストールに失敗しました'
        return $false
    }

    Write-Host 'MEGAcmdのインストールが完了しました'
    return $true
}

function Step-MegaCmd {
    Write-Host '[1/5] MEGAcmdを確認中...'

    $script:MegaCmdPath = Find-MegaCmd
    if ($MegaCmdPath) {
        Write-Host "MEGAcmd確認OK: $MegaCmdPath"
        Ensure-MegaCmdPath
        return $true
    }

    Write-Host '[注意] MEGAcmdが見つかりません'
    Write-Host ''
    Write-Host 'MEGAへのアップロード機能を使うにはMEGAcmdが必要です。'
    Write-Host 'これからMEGAcmdをインストールします...'

    if (-not (Install-MegaCmd)) {
        Write-Host '[注意] MEGAcmdのインストールに失敗しました'
        Write-Host 'スクリーンショット機能のみ使う場合は、このまま続行できます。'
        Write-Host ''
        return $true
    }

    $script:MegaCmdPath = Find-MegaCmd
    if ($MegaCmdPath) {
        Write-Host "MEGAcmdインストールOK: $MegaCmdPath"
        Ensure-MegaCmdPath
    } else {
        Write-Host '[注意] MEGAcmdが見つかりません（インストール後の検出に失敗）'
        Write-Host 'スクリーンショット機能のみ使う場合は、このまま続行できます。'
        Write-Host ''
    }

    return $true
}

function Find-Python {
    $script:PythonExe = $null
    $script:PythonDir = $null

    $candidates = @()

    $localRoot = Join-Path $env:LOCALAPPDATA 'Programs\Python'
    if (Test-Path -LiteralPath $localRoot) {
        $dirs = Get-ChildItem -Path $localRoot -Directory -Filter 'Python3*' | Sort-Object Name -Descending
        foreach ($dir in $dirs) {
            $candidates += (Join-Path $dir.FullName 'python.exe')
        }
    }

    $dirs = Get-ChildItem -Path 'C:\Python3*' -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending
    foreach ($dir in $dirs) {
        $candidates += (Join-Path $dir.FullName 'python.exe')
    }

    $dirs = Get-ChildItem -Path 'C:\Program Files\Python3*' -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending
    foreach ($dir in $dirs) {
        $candidates += (Join-Path $dir.FullName 'python.exe')
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            $script:PythonExe = $candidate
            break
        }
    }

    if (-not $PythonExe) {
        $where = & where.exe python 2>$null
        foreach ($line in $where) {
            if ($line -notmatch 'WindowsApps') {
                $script:PythonExe = $line
                break
            }
        }
    }

    if ($PythonExe) {
        $script:PythonDir = Split-Path -Parent $PythonExe
        if ($PythonDir) {
            $env:PATH = "$PythonDir;$PythonDir\Scripts;$env:PATH"
        }
    }
}

function Install-Python {
    $pythonUrl = 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe'
    $installer = Join-Path $env:TEMP 'python-3.12.8-amd64.exe'

    Write-Host ''
    Write-Host 'Python 3.12をダウンロード中...'
    try {
        Invoke-Download -Uri $pythonUrl -OutFile $installer
    } catch {
        Write-Host '[エラー] ダウンロードに失敗しました'
        return $false
    }

    Write-Host 'Python 3.12をインストール中...（完了まで待ってください）'
    $args = '/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1'
    $proc = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        Write-Host '[エラー] インストールに失敗しました'
        return $false
    }

    Write-Host 'Pythonのインストールが完了しました'
    return $true
}

function Step-Python {
    Write-Host ''
    Write-Host '[2/5] Pythonを確認中...'

    Find-Python

    if (-not $PythonExe) {
        Write-Host '[注意] 使用可能なPythonが見つかりません'
        Write-Host 'WindowsAppsのPythonは仮想環境の作成に向かないため使いません。'
        Write-Host 'これからPython 3.12をインストールします。'

        if (-not (Install-Python)) {
            return $false
        }

        Find-Python
    }

    if (-not $PythonExe) {
        Write-Host '[エラー] Pythonの検出に失敗しました'
        Write-Host 'https://www.python.org/downloads/ から手動でインストールしてください'
        Write-Host 'インストール時に「Add Python to PATH」にチェックを入れてください'
        return $false
    }

    Write-Host "Python: $PythonExe"
    & $PythonExe --version | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[エラー] Pythonの実行に失敗しました'
        Write-Host "パス: $PythonExe"
        return $false
    }

    Write-Host 'Python確認OK'
    return $true
}

function Step-Venv {
    Write-Host ''
    Write-Host '[3/5] 仮想環境を確認中...'

    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $venvPython) {
        & $venvPython --version | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host '既存の仮想環境が壊れている可能性があります'
            Write-Host '既存の仮想環境を削除して作り直します'
            Remove-Item -LiteralPath (Join-Path $PSScriptRoot '.venv') -Recurse -Force
        } else {
            Write-Host '仮想環境は既に存在します'
            return $true
        }
    }

    Write-Host '仮想環境を作成中...'
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.venv')) {
        Write-Host '不完全な仮想環境を削除中...'
        Remove-Item -LiteralPath (Join-Path $PSScriptRoot '.venv') -Recurse -Force
    }

    & $PythonExe -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[エラー] 仮想環境の作成に失敗しました'
        Write-Host ''
        Write-Host 'よくある原因:'
        Write-Host '  - WindowsAppsのPythonを使っている'
        Write-Host '  - ディスク容量が不足している'
        Write-Host ''
        Write-Host '対処方法:'
        Write-Host '  https://www.python.org/downloads/ からPythonをインストールしてください'
        return $false
    }

    Write-Host '仮想環境を作成しました'
    return $true
}

function Step-Packages {
    Write-Host ''
    Write-Host '[4/5] 依存パッケージをインストール中...'

    $requirements = Join-Path $PSScriptRoot 'requirements.txt'
    if (-not (Test-Path -LiteralPath $requirements)) {
        Write-Host '[エラー] requirements.txt が見つかりません'
        return $false
    }

    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    & $venvPython -m ensurepip --upgrade | Out-Null
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[エラー] pipの更新に失敗しました'
        return $false
    }

    & $venvPython -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[エラー] パッケージのインストールに失敗しました'
        return $false
    }

    return $true
}

function Step-Verify {
    Write-Host ''
    Write-Host '[5/5] インストールを確認中...'

    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    & $venvPython -c "import pyautogui; import pygetwindow; import PIL; import numpy; import pynput"
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[エラー] 一部のパッケージが正しくインストールされていません'
        return $false
    }

    Write-Host '全てのパッケージが正常にインストールされています'
    return $true
}

try {
    Write-Header

    if (-not (Step-MegaCmd)) { throw 'MEGAcmd step failed' }
    if (-not (Step-Python)) { throw 'Python step failed' }
    if (-not (Step-Venv)) { throw 'Venv step failed' }
    if (-not (Step-Packages)) { throw 'Packages step failed' }
    if (-not (Step-Verify)) { throw 'Verify step failed' }

    Write-Host ''
    Write-Host '============================================'
    Write-Host '  セットアップ完了'
    Write-Host '============================================'
    Write-Host ''
    Write-Host '確認結果:'
    Write-Host "  [OK] Python: $PythonExe"
    Write-Host '  [OK] 仮想環境 (.venv)'
    Write-Host '  [OK] Pythonパッケージ (pyautogui, pygetwindow, Pillow, numpy, pynput)'
    if ($MegaCmdPath) {
        Write-Host "  [OK] MEGAcmd: $MegaCmdPath"
    } else {
        Write-Host '  [--] MEGAcmd not installed'
    }
    Write-Host ''
    Write-Host 'How to run:'
    Write-Host '  PowerShellで run.ps1 を実行してください'
    Write-Host ''
    Write-Host 'MEGA commands:'
    Write-Host '  mega-transfers    Check upload progress'
    Write-Host '  mega-ls /book     List uploaded files'
    Write-Host '  mega-whoami       Check login status'
    Write-Host ''

    Pause-IfNeeded
    exit 0
} catch {
    Write-Host ''
    Write-Host '[エラー] セットアップに失敗しました'
    Write-Host $_.Exception.Message
    Pause-IfNeeded
    exit 1
}
