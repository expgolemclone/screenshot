@echo off
chcp 65001 >nul
echo ============================================
echo   スクリーンショットツール セットアップ
echo ============================================
echo.

REM スクリプトがあるディレクトリに移動
cd /d "%~dp0"

REM ========================================
REM [1/5] MEGAcmdの確認とPATH追加
REM ========================================
echo [1/5] MEGAcmdを確認中...
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
    
    REM MEGAcmdがPATHに含まれているか確認
    echo %PATH% | findstr /i /c:"%MEGACMD_PATH%" >nul
    if errorlevel 1 (
        echo MEGAcmdをPATHに追加中...
        REM 現在のセッションに追加
        set "PATH=%PATH%;%MEGACMD_PATH%"
        REM ユーザーPATHに永続的に追加
        for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%b"
        if defined USER_PATH (
            echo %USER_PATH% | findstr /i /c:"%MEGACMD_PATH%" >nul
            if errorlevel 1 (
                setx PATH "%USER_PATH%;%MEGACMD_PATH%" >nul 2>&1
                echo MEGAcmdをユーザーPATHに追加しました
            )
        ) else (
            setx PATH "%MEGACMD_PATH%" >nul 2>&1
            echo MEGAcmdをユーザーPATHに追加しました
        )
    ) else (
        echo MEGAcmdは既にPATHに含まれています
    )
) else (
    echo [警告] MEGAcmdが見つかりません
    echo.
    echo MEGAへのアップロード機能を使用するには、MEGAcmdをインストールしてください:
    echo   https://mega.io/cmd
    echo.
    echo ※スクリーンショット機能のみ使用する場合は、このまま続行できます
    echo.
)

REM ========================================
REM [2/5] Pythonの確認（優先順位を改善）
REM ========================================
echo.
echo [2/5] Pythonを確認中...
set "PYTHON_EXE="

REM 1. LocalAppData\Programs\Python を最優先で探す（公式インストーラー）
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%d\python.exe" (
        REM バージョン番号が大きい方を優先（新しいバージョン）
        set "PYTHON_EXE=%%d\python.exe"
    )
)

REM 2. C:\Python* を探す
if not defined PYTHON_EXE (
    for /d %%d in ("C:\Python3*") do (
        if exist "%%d\python.exe" set "PYTHON_EXE=%%d\python.exe"
    )
)

REM 3. Program Files を探す
if not defined PYTHON_EXE (
    for /d %%d in ("C:\Program Files\Python3*") do (
        if exist "%%d\python.exe" set "PYTHON_EXE=%%d\python.exe"
    )
)

REM 4. PATHから探す（ただしWindowsAppsは除外）
if not defined PYTHON_EXE (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        echo %%i | findstr /i /c:"WindowsApps" >nul
        if errorlevel 1 (
            if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
        )
    )
)

REM Pythonが見つからない場合、自動インストールを提案
if not defined PYTHON_EXE (
    echo [警告] 有効なPythonが見つかりません
    echo.
    echo WindowsApps版Pythonは仮想環境の作成に問題があるため使用できません。
    echo.
    echo Pythonを自動でインストールしますか?
    set /p INSTALL_PYTHON="インストールする場合は y を入力: "
    if /i "%INSTALL_PYTHON%"=="y" (
        echo.
        echo Python 3.12をダウンロード中...
        powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"
        if errorlevel 1 (
            echo [エラー] ダウンロードに失敗しました
            pause
            exit /b 1
        )
        echo Python 3.12をインストール中...（少々お待ちください）
        "%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
        if errorlevel 1 (
            echo [エラー] インストールに失敗しました
            pause
            exit /b 1
        )
        echo Pythonのインストールが完了しました
        
        REM インストール後のパスを設定
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        
        REM インストール後にPATHを更新
        for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "PATH=%%b;%PATH%"
    ) else (
        echo.
        echo https://www.python.org/downloads/ から手動でインストールしてください
        echo ※インストール時に「Add Python to PATH」にチェックを入れてください
        pause
        exit /b 1
    )
)

REM Pythonの動作確認
echo Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version
if errorlevel 1 (
    echo [エラー] Pythonの実行に失敗しました
    echo パス: %PYTHON_EXE%
    pause
    exit /b 1
)
echo Python確認OK

REM ========================================
REM [3/5] 仮想環境の作成
REM ========================================
echo.
echo [3/5] 仮想環境を確認中...
if exist ".venv\Scripts\python.exe" (
    echo 仮想環境は既に存在します
) else (
    echo 仮想環境を作成中...
    if exist ".venv" (
        echo 不完全な仮想環境を削除中...
        rmdir /s /q ".venv"
    )
    "%PYTHON_EXE%" -m venv .venv
    if errorlevel 1 (
        echo [エラー] 仮想環境の作成に失敗しました
        echo.
        echo 考えられる原因:
        echo   - WindowsApps版Pythonを使用している
        echo   - ディスク容量が不足している
        echo.
        echo 解決方法:
        echo   https://www.python.org/downloads/ から公式インストーラーでPythonをインストールしてください
        pause
        exit /b 1
    )
    echo 仮想環境を作成しました
)

REM ========================================
REM [4/5] 依存パッケージのインストール
REM ========================================
echo.
echo [4/5] 依存パッケージをインストール中...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
".venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    echo [エラー] パッケージのインストールに失敗しました
    pause
    exit /b 1
)

REM ========================================
REM [5/5] インストール確認
REM ========================================
echo.
echo [5/5] インストールを確認中...
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
echo 確認結果:
echo   [OK] Python: %PYTHON_EXE%
echo   [OK] 仮想環境 (.venv)
echo   [OK] Pythonパッケージ (pyautogui, pygetwindow, Pillow, numpy, pynput)
if defined MEGACMD_PATH (
    echo   [OK] MEGAcmd: %MEGACMD_PATH%
) else (
    echo   [--] MEGAcmd not installed
)
echo.
echo How to run:
echo   Double-click run.bat
echo.
echo MEGA commands:
echo   mega-transfers    Check upload progress
echo   mega-ls /book     List uploaded files
echo   mega-whoami       Check login status
echo.
pause
