@echo off
chcp 65001 >nul
echo ============================================
echo   スクリーンショットツール セットアップ
echo ============================================
echo.

REM スクリプトがあるディレクトリに移動
cd /d "%~dp0"

REM ========================================
REM [1/4] MEGAcmdの確認
REM ========================================
echo [1/4] MEGAcmdを確認中...
set "MEGACMD_PATH="

REM MEGAcmdの場所を探す
if exist "%LOCALAPPDATA%\MEGAcmd\mega-put.bat" (
    set "MEGACMD_PATH=%LOCALAPPDATA%\MEGAcmd"
)
if not defined MEGACMD_PATH (
    if exist "C:\Program Files\MEGAcmd\mega-put.bat" (
        set "MEGACMD_PATH=C:\Program Files\MEGAcmd"
    )
)
if not defined MEGACMD_PATH (
    if exist "C:\Program Files (x86)\MEGAcmd\mega-put.bat" (
        set "MEGACMD_PATH=C:\Program Files (x86)\MEGAcmd"
    )
)

if defined MEGACMD_PATH (
    echo MEGAcmd確認OK: %MEGACMD_PATH%
) else (
    echo [警告] MEGAcmdが見つかりません
    echo.
    echo MEGAへのアップロード機能を使用するには、MEGAcmdをインストールしてください:
    echo   https://mega.io/cmd
    echo.
    echo ※スクリーンショット機能のみ使用する場合は、このまま続行できます
    echo.
    set /p CONTINUE_SETUP="続行しますか? (y/n): "
    if /i not "%CONTINUE_SETUP%"=="y" (
        echo セットアップを中止しました
        pause
        exit /b 1
    )
)

REM ========================================
REM [2/4] Pythonの確認
REM ========================================
echo.
echo [2/4] Pythonを確認中...
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

echo Python確認OK: %PYTHON_EXE%
"%PYTHON_EXE%" --version

REM ========================================
REM [3/4] 仮想環境の作成
REM ========================================
echo.
echo [3/4] 仮想環境を作成中...
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

REM ========================================
REM [4/4] 依存パッケージのインストール
REM ========================================
echo.
echo [4/4] 依存パッケージをインストール中...
".venv\Scripts\pip.exe" install --upgrade pip >nul 2>&1
".venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    echo [エラー] パッケージのインストールに失敗しました
    pause
    exit /b 1
)

REM ========================================
REM インストール確認
REM ========================================
echo.
echo パッケージのインストールを確認中...
".venv\Scripts\python.exe" -c "import pyautogui; import pygetwindow; import PIL; import numpy; import pynput; print('全てのパッケージが正常にインストールされています')"
if errorlevel 1 (
    echo [エラー] 一部のパッケージが正しくインストールされていません
    pause
    exit /b 1
)

echo.
echo ============================================
echo   セットアップ完了！
echo ============================================
echo.
echo 必要なもの:
echo   [OK] Python
echo   [OK] 仮想環境 (.venv)
echo   [OK] Pythonパッケージ (pyautogui, pygetwindow, Pillow, numpy, pynput)
if defined MEGACMD_PATH (
    echo   [OK] MEGAcmd
) else (
    echo   [--] MEGAcmd (未インストール - アップロード機能使用不可)
)
echo.
echo 実行方法:
echo   run.bat をダブルクリック
echo.
pause
