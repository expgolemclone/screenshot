@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 仮想環境のPythonを使用
set PYTHON_PATH=%~dp0.venv\Scripts\python.exe

REM 仮想環境が存在するか確認
if not exist "%PYTHON_PATH%" (
    echo [エラー] 仮想環境が見つかりません
    echo 先に setup.bat を実行してください
    pause
    exit /b 1
)

REM 実行
"%PYTHON_PATH%" click_and_screenshot.py %*
