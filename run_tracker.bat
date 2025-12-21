@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 仮想環境が存在するか確認
if not exist ".venv\Scripts\activate.bat" (
    echo [エラー] 仮想環境が見つかりません
    echo 先に setup.bat を実行してください
    pause
    exit /b 1
)

REM 仮想環境をアクティベートして実行
call .venv\Scripts\activate.bat
python mouse_tracker.py
