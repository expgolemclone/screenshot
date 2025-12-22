"""
指定座標をクリックし、そのウィンドウのスクリーンショットを保存するプログラム
前回と同じスクリーンショットになったら自動終了
完了後、フォルダ名を英語にリネームしてMEGAにアップロード
使用法: python click_and_screenshot.py
"""

import argparse
import time
import os
import signal
import subprocess
import re
import shutil
import getpass
from datetime import datetime
import pyautogui
import pygetwindow as gw
from PIL import ImageGrab, ImageChops
import numpy as np

# pyautoguiのフェイルセーフを無効化（マウスが角に行っても停止しない）
pyautogui.FAILSAFE = False

# Ctrl+C (SIGINT) を無視する
signal.signal(signal.SIGINT, signal.SIG_IGN)

# スクリプトの場所を基準にしたパス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_BASE_DIR = SCRIPT_DIR

# 設定
CLICK_POSITIONS = {
    1: {"x": 279, "y": 1084, "description": "位置1 (X: 279, Y: 1084)"},
    2: {"x": 3568, "y": 1087, "description": "位置2 (X: 3568, Y: 1087)"},
}
SAVE_DIR = os.path.join(SCRIPT_DIR, "image")  # デフォルト値（後で更新される）
MEGA_REMOTE_PATH = "/lG93yLBL"  # MEGAのアップロード先フォルダID

# グローバル変数（選択後に設定）
CLICK_X = None
CLICK_Y = None

def images_are_same(img1, img2, threshold=0.99):
    """2つの画像が同じかどうかを判定（閾値で許容誤差を設定）"""
    if img1 is None or img2 is None:
        return False
    
    # サイズが違う場合は異なる画像
    if img1.size != img2.size:
        return False
    
    try:
        # 画像をnumpy配列に変換して比較
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # 完全一致のピクセル数を計算
        total_pixels = arr1.size
        matching_pixels = np.sum(arr1 == arr2)
        similarity = matching_pixels / total_pixels
        
        return similarity >= threshold
    except Exception as e:
        print(f"画像比較エラー: {e}")
        return False

def get_window_at_position(x, y):
    """指定座標にあるウィンドウを取得"""
    try:
        # 全てのウィンドウを取得
        windows = gw.getAllWindows()
        for win in windows:
            if win.left <= x <= win.right and win.top <= y <= win.bottom:
                if win.title:  # タイトルがあるウィンドウのみ
                    return win
    except Exception as e:
        print(f"ウィンドウ取得エラー: {e}")
    return None

def screenshot_window(window):
    """ウィンドウ全体のスクリーンショットを撮る"""
    try:
        # ウィンドウの領域を取得
        left = window.left
        top = window.top
        right = window.right
        bottom = window.bottom
        
        # スクリーンショットを撮る
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        return screenshot
    except Exception as e:
        print(f"スクリーンショットエラー: {e}")
        return None

def click_and_capture(iteration, prev_screenshot=None):
    """クリックしてスクリーンショットを保存。前回と同じならNone、違えばscreenshotを返す"""
    print(f"\n--- 実行 {iteration} ---")
    
    try:
        # 1回目はクリックせずにアクティブウィンドウをスクショ
        if iteration == 1:
            print("1ページ目: クリックせずにアクティブウィンドウをスクリーンショット")
            window = gw.getActiveWindow()
        else:
            # 2回目以降は指定座標をクリック
            print(f"クリック: X={CLICK_X}, Y={CLICK_Y}")
            pyautogui.click(CLICK_X, CLICK_Y)
            
            # クリック後少し待機（ウィンドウがアクティブになるのを待つ）
            time.sleep(0.1)
            
            # クリック位置にあるウィンドウを取得
            window = get_window_at_position(CLICK_X, CLICK_Y)
        
        if window:
            print(f"ウィンドウ検出: {window.title}")
            
            # 3. スクリーンショットを撮る
            screenshot = screenshot_window(window)
            
            if screenshot:
                # 前回のスクリーンショットと比較
                if prev_screenshot is not None and images_are_same(screenshot, prev_screenshot):
                    return screenshot, "same"  # 同じ画像 → リトライ判定へ
                
                # 保存ディレクトリが存在しない場合は作成
                os.makedirs(SAVE_DIR, exist_ok=True)
                
                # ファイル名を生成（連番のみでシンプルに）
                filename = f"screenshot_{iteration:04d}.png"
                filepath = os.path.join(SAVE_DIR, filename)
                
                # 保存
                screenshot.save(filepath)
                print(f"保存完了: {filepath}")
                return screenshot, "new"  # 新しい画像 → 続行
            else:
                print("スクリーンショットの撮影に失敗しました")
        else:
            print("指定座標にウィンドウが見つかりませんでした")
    except Exception as e:
        print(f"エラー発生 (実行 {iteration}): {e}")
    
    return prev_screenshot, "error"  # エラー時は前回の画像を維持

def select_click_position():
    """ユーザーにクリック位置を選択させる"""
    global CLICK_X, CLICK_Y
    
    print("クリック位置を選択してください:")
    for num, pos in CLICK_POSITIONS.items():
        print(f"  {num}: {pos['description']}")
    print("  3: カスタム座標を入力")
    
    while True:
        try:
            choice = input("番号を入力 (1, 2, or 3): ").strip()
            choice_num = int(choice)
            if choice_num in CLICK_POSITIONS:
                CLICK_X = CLICK_POSITIONS[choice_num]["x"]
                CLICK_Y = CLICK_POSITIONS[choice_num]["y"]
                print(f"選択: {CLICK_POSITIONS[choice_num]['description']}")
                return
            elif choice_num == 3:
                # カスタム座標を入力
                while True:
                    try:
                        x_input = input("X座標を入力: ").strip()
                        CLICK_X = int(x_input)
                        break
                    except ValueError:
                        print("数字を入力してください")
                while True:
                    try:
                        y_input = input("Y座標を入力: ").strip()
                        CLICK_Y = int(y_input)
                        break
                    except ValueError:
                        print("数字を入力してください")
                print(f"選択: カスタム座標 (X: {CLICK_X}, Y: {CLICK_Y})")
                return
            else:
                print("1, 2, または 3 を入力してください")
        except ValueError:
            print("数字を入力してください")


def get_english_folder_name():
    """ユーザーに英語のフォルダ名を入力させる"""
    print("\n=== フォルダ名の設定 ===")
    print("スクリーンショットを保存するフォルダの英語名を入力してください")
    print("（例: market_wizards）")
    
    while True:
        folder_name = input("フォルダ名: ").strip()
        # 英数字、アンダースコア、ハイフンのみ許可
        if re.match(r'^[a-zA-Z0-9_-]+$', folder_name):
            return folder_name
        else:
            print("英数字、アンダースコア(_)、ハイフン(-)のみ使用可能です")


def rename_folder_to_english(original_path, new_name):
    """フォルダを英語名にリネーム"""
    parent_dir = os.path.dirname(original_path)
    new_path = os.path.join(parent_dir, new_name)
    
    # 同名フォルダが存在する場合は連番を追加
    if os.path.exists(new_path):
        counter = 1
        while os.path.exists(f"{new_path}_{counter}"):
            counter += 1
        new_path = f"{new_path}_{counter}"
    
    try:
        os.rename(original_path, new_path)
        print(f"フォルダをリネーム: {original_path} → {new_path}")
        return new_path
    except Exception as e:
        print(f"リネームエラー: {e}")
        return original_path


def find_megacmd():
    """MEGAcmdの実行ファイルを探す"""
    possible_paths = [
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'MEGAcmd'),
        r'C:\Users\nakan\AppData\Local\MEGAcmd',
        r'C:\Program Files\MEGAcmd',
        r'C:\Program Files (x86)\MEGAcmd',
    ]
    
    for path in possible_paths:
        # .batファイルを優先して探す
        mega_put = os.path.join(path, 'mega-put.bat')
        if os.path.exists(mega_put):
            return path
        # .exeファイルもチェック
        mega_put = os.path.join(path, 'mega-put.exe')
        if os.path.exists(mega_put):
            return path
    return None


def get_mega_cmd(megacmd_path, cmd_name):
    """MEGAcmdのコマンドパスを取得（.batを優先）"""
    bat_path = os.path.join(megacmd_path, f'{cmd_name}.bat')
    if os.path.exists(bat_path):
        return bat_path
    exe_path = os.path.join(megacmd_path, f'{cmd_name}.exe')
    if os.path.exists(exe_path):
        return exe_path
    return None


def upload_to_mega(folder_path):
    """フォルダをMEGAにアップロード"""
    print("\n=== MEGAへのアップロード ===")
    
    megacmd_path = find_megacmd()
    if not megacmd_path:
        print("エラー: MEGAcmdが見つかりません")
        print("https://mega.io/cmd からMEGAcmdをインストールしてください")
        return False
    
    mega_put = get_mega_cmd(megacmd_path, 'mega-put')
    mega_login = get_mega_cmd(megacmd_path, 'mega-login')
    mega_whoami = get_mega_cmd(megacmd_path, 'mega-whoami')
    
    if not mega_put or not mega_whoami:
        print("エラー: MEGAcmdのコマンドが見つかりません")
        return False
    
    # ログイン状態を確認
    try:
        result = subprocess.run([mega_whoami], capture_output=True, text=True, timeout=30, shell=True)
        if result.returncode != 0 or "Not logged in" in result.stderr:
            print("MEGAにログインしていません。ログインしてください:")
            print("（MEGAアカウントを持っていない場合は https://mega.nz で作成してください）")
            email = input("メールアドレス: ").strip()
            if not email:
                print("メールアドレスが入力されませんでした。アップロードをスキップします。")
                return False
            password = getpass.getpass("パスワード: ")
            if not password:
                print("パスワードが入力されませんでした。アップロードをスキップします。")
                return False
            
            login_result = subprocess.run(
                [mega_login, email, password],
                capture_output=True, text=True, timeout=60, shell=True
            )
            if login_result.returncode != 0:
                print(f"ログインエラー: {login_result.stderr}")
                return False
            print("ログイン成功!")
        else:
            print(f"ログイン中: {result.stdout.strip()}")
    except subprocess.TimeoutExpired:
        print("MEGAサーバーへの接続がタイムアウトしました")
        return False
    except Exception as e:
        print(f"ログイン確認エラー: {e}")
        return False
    
    # アップロード実行
    folder_name = os.path.basename(folder_path)
    mega_dest = "/book"  # MEGAのアップロード先フォルダ
    print(f"アップロード中: {folder_path}")
    print(f"アップロード先: MEGA {mega_dest}")
    
    try:
        # mega-put でフォルダをアップロード（-c でフォルダを作成）
        result = subprocess.run(
            f'"{mega_put}" -c "{folder_path}" {mega_dest}',
            capture_output=True, text=True, timeout=600, shell=True  # 10分のタイムアウト
        )
        
        if result.returncode == 0:
            print(f"アップロード完了!")
            print(f"MEGA上のパス: {mega_dest}/{folder_name}")
            return True
        else:
            print(f"アップロードエラー: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("アップロードがタイムアウトしました（10分以上）")
        return False
    except Exception as e:
        print(f"アップロードエラー: {e}")
        return False

def main():
    global CLICK_X, CLICK_Y, SAVE_DIR
    
    # まず英語のフォルダ名を取得
    english_name = get_english_folder_name()
    
    # 保存先を英語名のフォルダに設定
    SAVE_DIR = os.path.join(SCREENSHOT_BASE_DIR, english_name)
    
    # まずクリック位置を選択
    select_click_position()
    
    parser = argparse.ArgumentParser(description="クリック＆スクリーンショット（前回と同じ内容で自動終了）")
    parser.add_argument("--max", type=int, default=1000, help="最大繰り返し回数（デフォルト: 1000）")
    args = parser.parse_args()
    
    print(f"\nクリック＆スクリーンショット開始")
    print(f"最大繰り返し回数: {args.max}")
    print(f"クリック座標: X={CLICK_X}, Y={CLICK_Y}")
    print(f"保存先: {SAVE_DIR}")
    print(f"※前回と同じスクリーンショットになったら自動終了します")
    
    # 開始前に3秒待機
    print("\n10秒後に開始します. kindleのウィンドウをアクティブにしてください.")
    time.sleep(10)
    
    success_count = 0
    prev_screenshot = None
    
    for i in range(1, args.max + 1):
        prev_screenshot, status = click_and_capture(i, prev_screenshot)
        
        if status == "new":
            success_count += 1
        elif status == "same":
            # 同じ画像が出た → 5秒待ってリトライ
            print("同じ画像を検出。5秒待ってリトライします...")
            time.sleep(5)
            
            # リトライ（同じiterationで再度クリック）
            retry_screenshot, retry_status = click_and_capture(i, prev_screenshot)
            
            if retry_status == "same":
                print("リトライ後も同じ画像のため終了します")
                break
            elif retry_status == "new":
                success_count += 1
                prev_screenshot = retry_screenshot
            else:
                # エラーの場合は続行
                pass
        
        # 次の実行まで少し待機
        time.sleep(0.1)
    
    print(f"\n完了: {success_count} 回保存しました")
    
    # スクリーンショットが保存された場合のみアップロード処理
    if success_count > 0 and os.path.exists(SAVE_DIR):
        print(f"\n保存フォルダ: {SAVE_DIR}")
        
        # MEGAへのアップロード確認
        try:
            upload_choice = input("\nMEGAにアップロードしますか? (y/n): ").strip().lower()
            if upload_choice == 'y':
                upload_to_mega(SAVE_DIR)
            else:
                print("アップロードをスキップしました")
        except EOFError:
            print("\n入力がないため、アップロードをスキップしました")
    else:
        print("スクリーンショットが保存されなかったため、アップロードはスキップします")

if __name__ == "__main__":
    main()

# 使用例:
# 最大1000回まで（同じ画像で自動終了）
# python click_and_screenshot.py

# 最大50回まで
# python click_and_screenshot.py --max 50
