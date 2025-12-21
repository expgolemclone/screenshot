"""
マウス座標をリアルタイムで表示するプログラム
- Enterキーを押すと現在の座標を記録
- Escキーで終了
"""

import pyautogui
import time
import threading
from pynput import keyboard

# グローバル変数
current_x, current_y = 0, 0
saved_positions = []
running = True
enter_pressed = False

def on_press(key):
    global running, enter_pressed
    try:
        if key == keyboard.Key.enter:
            enter_pressed = True
        elif key == keyboard.Key.esc:
            running = False
            return False  # リスナーを停止
    except:
        pass

def main():
    global current_x, current_y, enter_pressed, running
    
    print("マウス座標トラッカー")
    print("Enterキー: 座標を記録 | Escキー: 終了")
    print("-" * 40)
    
    # キーボードリスナーを別スレッドで開始
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    try:
        while running:
            current_x, current_y = pyautogui.position()
            print(f"\rリアルタイム -> X: {current_x:4d}, Y: {current_y:4d}  ", end="", flush=True)
            
            if enter_pressed:
                saved_positions.append((current_x, current_y))
                print(f"\n記録 #{len(saved_positions):2d}: X: {current_x:4d}, Y: {current_y:4d}")
                print("-" * 40)
                enter_pressed = False
            
            time.sleep(0.05)
    except KeyboardInterrupt:
        running = False
    
    listener.stop()
    
    print("\n\n" + "=" * 40)
    print("記録された座標一覧:")
    print("=" * 40)
    for i, (px, py) in enumerate(saved_positions, 1):
        print(f"  #{i:2d}: X: {px:4d}, Y: {py:4d}")
    print("=" * 40)
    print("プログラムを終了しました")

if __name__ == "__main__":
    main()
