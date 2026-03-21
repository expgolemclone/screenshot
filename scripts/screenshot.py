"""
矢印キー入力でページを進め、Hyprland上のアクティブウィンドウのスクリーンショットを保存するプログラム。
前回と同じスクリーンショットになったら自動終了。

必要な外部コマンド: hyprctl, grim, wtype
使用法: uv run python -m scripts.screenshot
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from .config import CONTENTS_DIR


ACTION_CHOICES = {
    1: {"key": "Left", "description": "左矢印キー"},
    2: {"key": "Right", "description": "右矢印キー"},
}


@dataclass
class CaptureConfig:
    action_key: str
    save_dir: str


def _check_commands() -> None:
    """必要な外部コマンドが存在するか確認する。"""
    missing = [cmd for cmd in ("hyprctl", "grim", "wtype") if not _which(cmd)]
    if missing:
        print(f"[エラー] 必要なコマンドが見つかりません: {', '.join(missing)}")
        print("Hyprland 環境で hyprctl, grim, wtype をインストールしてください。")
        sys.exit(1)


def _which(cmd: str) -> bool:
    """コマンドがPATH上に存在するか。"""
    from shutil import which
    return which(cmd) is not None


def _watch_stdin(stop_event: threading.Event) -> None:
    """バックグラウンドでEnterキー入力を監視し、停止イベントをセットする。"""
    try:
        input()
        stop_event.set()
        print("\n[Enterキー検出] 停止します...")
    except EOFError:
        pass


def get_active_window() -> dict | None:
    """hyprctl でアクティブウィンドウの情報を取得する。"""
    try:
        result = subprocess.run(
            ["hyprctl", "activewindow", "-j"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        if not data or not data.get("title"):
            return None
        return data
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        print(f"ウィンドウ取得エラー: {e}")
        return None


def screenshot_window(window: dict, filepath: str) -> Image.Image | None:
    """grim でウィンドウ領域のスクリーンショットを撮り、PILイメージとして返す。"""
    at = window.get("at", [0, 0])
    size = window.get("size", [0, 0])
    x, y = at[0], at[1]
    w, h = size[0], size[1]
    if w <= 0 or h <= 0:
        print("ウィンドウサイズが不正です")
        return None

    geometry = f"{x},{y} {w}x{h}"
    try:
        result = subprocess.run(
            ["grim", "-g", geometry, filepath],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            msg = (result.stderr or result.stdout or "").strip()
            print(f"grim エラー: {msg}")
            return None
        return Image.open(filepath)
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"スクリーンショットエラー: {e}")
        return None


def images_are_same(img1: Image.Image | None, img2: Image.Image | None, threshold: float = 0.99) -> bool:
    """2つの画像が同じかどうかを判定する。"""
    if img1 is None or img2 is None:
        return False
    if img1.size != img2.size:
        return False
    try:
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        similarity = np.sum(arr1 == arr2) / arr1.size
        return similarity >= threshold
    except Exception as e:
        print(f"画像比較エラー: {e}")
        return False


def advance_page(config: CaptureConfig) -> None:
    """wtype でキー入力してページを1つ進める。"""
    print(f"キー入力: {config.action_key}")
    subprocess.run(["wtype", "-k", config.action_key], timeout=5, check=False)
    time.sleep(0.1)


def capture_current(
    config: CaptureConfig, iteration: int, prev_screenshot: Image.Image | None,
) -> tuple[Image.Image | None, str]:
    """現在のアクティブウィンドウをスクリーンショットして保存する。"""
    try:
        window = get_active_window()
        if not window:
            print("ウィンドウが見つかりませんでした")
            return prev_screenshot, "error"

        print(f"ウィンドウ検出: {window.get('title', '不明')}")

        os.makedirs(config.save_dir, exist_ok=True)
        filename = f"screenshot_{iteration:04d}.png"
        filepath = os.path.join(config.save_dir, filename)

        screenshot = screenshot_window(window, filepath)
        if not screenshot:
            print("スクリーンショットの撮影に失敗しました")
            # 失敗時は不完全なファイルを削除
            if os.path.exists(filepath):
                os.remove(filepath)
            return prev_screenshot, "error"

        if prev_screenshot is not None and images_are_same(screenshot, prev_screenshot):
            # 同じ画像だったので保存済みファイルを削除
            os.remove(filepath)
            return screenshot, "same"

        print(f"保存完了: {filepath}")
        return screenshot, "new"
    except Exception as e:
        print(f"エラー発生 (実行 {iteration}): {e}")
        return prev_screenshot, "error"


def select_action_key() -> str:
    """ユーザーにページ送りキーを選択させる。"""
    print("ページ送り操作を選択してください:")
    for num, action in ACTION_CHOICES.items():
        print(f"  {num}: {action['description']}")

    while True:
        try:
            choice = int(input("番号を入力 (1 or 2): ").strip())
            if choice in ACTION_CHOICES:
                key = ACTION_CHOICES[choice]["key"]
                print(f"選択: {ACTION_CHOICES[choice]['description']}")
                return key
            print("1 または 2 を入力してください")
        except ValueError:
            print("数字を入力してください")


def get_english_folder_name() -> str:
    """ユーザーに英語のフォルダ名を入力させる。"""
    print("\n=== フォルダ名の設定 ===")
    print("スクリーンショットを保存するフォルダの英語名を入力してください")
    print("（例: market_wizards）")

    while True:
        folder_name = input("フォルダ名: ").strip()
        if re.match(r"^[a-zA-Z0-9_-]+$", folder_name):
            return folder_name
        print("英数字、アンダースコア(_)、ハイフン(-)のみ使用可能です")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Hyprland上でページ送り＆スクリーンショット（前回と同じ内容で自動終了）",
    )
    parser.add_argument("--max", type=int, default=10000, help="最大繰り返し回数（デフォルト: 10000）")
    args = parser.parse_args(argv)

    _check_commands()

    english_name = get_english_folder_name()
    action_key = select_action_key()
    config = CaptureConfig(
        action_key=action_key,
        save_dir=str(CONTENTS_DIR / english_name),
    )

    print(f"\nスクリーンショット開始")
    print(f"最大繰り返し回数: {args.max}")
    print(f"操作: {config.action_key}")
    print(f"保存先: {config.save_dir}")
    print(f"※前回と同じスクリーンショットになったら自動終了します")

    print("\n10秒後に開始します. 対象ウィンドウをアクティブにしてください.")
    time.sleep(10)

    stop_event = threading.Event()
    watcher = threading.Thread(target=_watch_stdin, args=(stop_event,), daemon=True)
    watcher.start()
    print("※ Enterキーで停止できます")

    success_count = 0
    prev_screenshot: Image.Image | None = None

    for i in range(1, args.max + 1):
        if stop_event.is_set():
            print("\n停止が要求されました")
            break

        print(f"\n--- 実行 {i} ---")

        # 1回目はページ送りせずにキャプチャ
        if i > 1:
            advance_page(config)

        prev_screenshot, status = capture_current(config, i, prev_screenshot)

        if status == "new":
            success_count += 1
        elif status == "same":
            # ページ遷移が完了していない可能性 → 5秒待ってリトライ（ページ送りなし）
            print("同じ画像を検出。5秒待ってリトライします...")
            time.sleep(5)
            prev_screenshot, retry_status = capture_current(config, i, prev_screenshot)
            if retry_status == "same":
                print("リトライ後も同じ画像のため終了します")
                break
            elif retry_status == "new":
                success_count += 1

        time.sleep(0.1)

    print(f"\n完了: {success_count} 回保存しました")

    if success_count > 0 and os.path.exists(config.save_dir):
        print(f"\n保存フォルダ: {config.save_dir}")
        print("MEGAへアップロードするには: uv run python -m scripts.upload")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
