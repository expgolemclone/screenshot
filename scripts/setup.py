"""
uv を使って仮想環境の作成と依存パッケージのインストールを行うセットアップスクリプト。
使い方: python scripts/setup.py
"""

import shutil
import subprocess
import sys

from config import PROJECT_ROOT

VERIFY_PACKAGES = ["pyautogui", "pygetwindow", "PIL", "numpy", "pynput"]


def find_uv():
    uv = shutil.which("uv")
    if uv:
        return uv
    raise RuntimeError(
        "uv が見つかりません。先にインストールしてください:\n"
        "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    )


def run(cmd, **kwargs):
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"コマンド失敗 (exit {result.returncode}): {' '.join(cmd)}")
    return result


def step_sync(uv):
    print("\n[1/2] 仮想環境作成 & 依存パッケージインストール...")
    run([uv, "sync"])


def step_verify(uv):
    print("\n[2/2] インストールを確認中...")
    imports = "; ".join(f"import {p}" for p in VERIFY_PACKAGES)
    run([uv, "run", "python", "-c", imports])
    print("全てのパッケージが正常にインストールされています")


def main():
    print("============================================")
    print("  セットアップ")
    print("============================================")

    try:
        uv = find_uv()
        step_sync(uv)
        step_verify(uv)
    except RuntimeError as e:
        print(f"\n[エラー] {e}")
        return 1

    print("\n============================================")
    print("  セットアップ完了")
    print("============================================")
    print("\n実行方法:")
    print("  uv run python scripts/screenshot.py")
    print("  uv run python scripts/upload.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
