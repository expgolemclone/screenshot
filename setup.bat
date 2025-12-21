@echo off
chcp 65001 >nul
echo ============================================
echo   スクリーンショットツール セットアップ
echo ============================================
echo.

REM スクリプトがあるディレクトリに移動
cd /d "%~dp0"

REM Pythonを探す
set "PYTHON_EXE="

REM 1. PATHから探す
where python >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('where python') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
    )
)

REM 2. WindowsAppsから探す
if not defined PYTHON_EXE (
    if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
    )
)

REM 3. 一般的なインストール場所から探す
if not defined PYTHON_EXE (
    for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
        if exist "%%d\python.exe" set "PYTHON_EXE=%%d\python.exe"
    )
)

if not defined PYTHON_EXE (
    for /d %%d in ("C:\Python*") do (
        if exist "%%d\python.exe" set "PYTHON_EXE=%%d\python.exe"
    )
)

if not defined PYTHON_EXE (
    echo [エラー] Pythonがインストールされていません
    echo https://www.python.org/downloads/ からインストールしてください
    pause
    exit /b 1
)

echo [1/3] Python確認OK
echo Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version

echo.
echo [2/3] 仮想環境を作成中...
if not exist ".venv" (
    "%PYTHON_EXE%" -m venv .venv
    if errorlevel 1 (
        echo [エラー] 仮想環境の作成に失敗しました
        pause
        exit /b 1
    )
    echo 仮想環境を作成しました
) else (
    echo 仮想環境は既に存在します
)

echo.
echo [3/3] 依存パッケージをインストール中...
".venv\Scripts\pip.exe" install --upgrade pip >nul 2>&1
".venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    echo [エラー] パッケージのインストールに失敗しました
    pause
    exit /b 1
)

echo.
echo ============================================
echo   セットアップ完了！
echo ============================================
echo.
echo 実行方法:
echo   run.bat をダブルクリック
echo.
pause
