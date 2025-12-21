@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Pythonのパスを設定
set PYTHON_PATH=C:\Users\nakan\OneDrive\Desktop\local\.venv\Scripts\python.exe

REM Pythonが存在するか確認
if not exist "%PYTHON_PATH%" (
    echo [エラー] Pythonが見つかりません: %PYTHON_PATH%
    pause
    exit /b 1
)

REM 実行
"%PYTHON_PATH%" click_and_screenshot.py %*
