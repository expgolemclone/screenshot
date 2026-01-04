# -*- coding: utf-8 -*-
"""
スクショ済みフォルダを番号で選択して MEGA にアップロードするツール。

前提:
- MEGAcmd がインストールされていること (https://mega.io/cmd)
- Python は仮想環境不要 (標準ライブラリのみ使用)

使い方:
  python upload.py
  python upload.py --dest /book
  python upload.py --folder permutation_city
  python upload.py --skip-if-exists
  python upload.py --dry-run
"""

from __future__ import annotations

import argparse
import getpass
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
DEFAULT_EXCLUDES = {".git", ".venv", "__pycache__"}


@dataclass(frozen=True)
class FolderInfo:
    index: int
    path: Path
    image_files: int
    total_bytes: int
    last_modified: datetime | None


def human_bytes(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(value)}{unit}"
            return f"{value:.1f}{unit}"
        value /= 1024.0
    return f"{num_bytes}B"


def folder_stats(folder: Path) -> tuple[int, int, datetime | None]:
    image_files = 0
    total_bytes = 0
    latest_mtime: float | None = None

    try:
        with os.scandir(folder) as it:
            for entry in it:
                if not entry.is_file():
                    continue
                suffix = Path(entry.name).suffix.lower()
                if suffix in IMAGE_EXTS:
                    image_files += 1
                try:
                    st = entry.stat()
                except OSError:
                    continue
                total_bytes += int(st.st_size)
                latest_mtime = st.st_mtime if latest_mtime is None else max(latest_mtime, st.st_mtime)
    except OSError:
        return 0, 0, None

    last_modified = datetime.fromtimestamp(latest_mtime) if latest_mtime is not None else None
    return image_files, total_bytes, last_modified


def discover_candidate_folders(base_dir: Path, excludes: set[str] | None = None) -> list[FolderInfo]:
    excludes = excludes or set(DEFAULT_EXCLUDES)
    candidates: list[FolderInfo] = []

    for p in sorted(base_dir.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_dir():
            continue
        if p.name in excludes or p.name.startswith("."):
            continue

        image_files, total_bytes, last_modified = folder_stats(p)
        if image_files <= 0:
            continue
        candidates.append(
            FolderInfo(
                index=len(candidates) + 1,
                path=p,
                image_files=image_files,
                total_bytes=total_bytes,
                last_modified=last_modified,
            )
        )

    return candidates


def print_candidates(candidates: Sequence[FolderInfo]) -> None:
    if not candidates:
        print("アップロード対象フォルダが見つかりませんでした。")
        return

    name_width = max(len(c.path.name) for c in candidates)
    print("\nアップロード対象フォルダ:")
    for c in candidates:
        modified = c.last_modified.strftime("%Y-%m-%d %H:%M") if c.last_modified else "-"
        print(
            f" {c.index:>2}) {c.path.name:<{name_width}}  "
            f"images={c.image_files:<5}  size={human_bytes(c.total_bytes):>8}  updated={modified}"
        )


def parse_selection(selection: str, max_index: int) -> list[int]:
    s = selection.strip().lower()
    if s in {"q", "quit", "exit"}:
        return []

    indices: set[int] = set()
    for token in re.split(r"[,\s]+", s):
        if not token:
            continue
        m = re.fullmatch(r"(\d+)-(\d+)", token)
        if m:
            start = int(m.group(1))
            end = int(m.group(2))
            if start > end:
                start, end = end, start
            for i in range(start, end + 1):
                indices.add(i)
            continue
        if token.isdigit():
            indices.add(int(token))
            continue
        raise ValueError(f"無効な入力: {token}")

    bad = [i for i in sorted(indices) if i < 1 or i > max_index]
    if bad:
        raise ValueError(f"範囲外の番号: {bad}")
    return sorted(indices)


def prompt_selection(candidates: Sequence[FolderInfo]) -> tuple[list[FolderInfo], bool]:
    if not candidates:
        return [], False

    while True:
        try:
            raw = input("\n番号を入力 (例: 1 / 1,3 / 2-5 / all / q): ")
        except EOFError:
            return [], False

        normalized = raw.strip().lower()
        if not normalized:
            continue
        if normalized in {"a", "all"}:
            return list(candidates), True

        try:
            indices = parse_selection(normalized, max_index=len(candidates))
        except ValueError as e:
            print(f"[入力エラー] {e}")
            continue
        if not indices:
            return [], False
        selected = [candidates[i - 1] for i in indices]
        return selected, False


def find_megacmd_command(cmd: str) -> str | None:
    # 1) PATH (PATHEXT により .bat も拾えることが多い)
    found = shutil.which(cmd)
    if found:
        return found

    # 2) よくあるインストール場所を探索
    localappdata = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        Path(localappdata) / "MEGAcmd" if localappdata else None,
        Path(r"C:\Program Files\MEGAcmd"),
        Path(r"C:\Program Files (x86)\MEGAcmd"),
    ]
    for folder in [c for c in candidates if c]:
        for ext in [".bat", ".exe"]:
            p = folder / f"{cmd}{ext}"
            if p.exists():
                return str(p)
    return None


def run_megacmd(cmd_path: str, args: Sequence[str], timeout_sec: int = 60) -> subprocess.CompletedProcess[str]:
    # .bat を確実に実行できるように cmd.exe 経由で呼ぶ
    full_cmd = ["cmd.exe", "/c", cmd_path, *args]
    return subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )


def remote_join(dest: str, name: str) -> str:
    dest = (dest or "").strip()
    if not dest:
        return name
    if dest == "/":
        return f"/{name}"
    if dest.endswith("/"):
        return f"{dest}{name}"
    return f"{dest}/{name}"


def remote_entry_exists(mega_ls: str, remote_path: str) -> bool:
    try:
        result = run_megacmd(mega_ls, [remote_path], timeout_sec=30)
    except subprocess.TimeoutExpired:
        raise RuntimeError("MEGAサーバーへの接続がタイムアウトしました")

    if result.returncode == 0:
        return True

    text = f"{result.stdout or ''}\n{result.stderr or ''}".lower()
    not_found_signals = [
        "not found",
        "no such file",
        "could not find",
        "cannot find",
        "does not exist",
        "not exist",
        "no existe",
        "no encontrado",
        "non trouvé",
        "nicht gefunden",
        "不存在",
        "見つかりません",
        "みつかりません",
    ]
    if any(sig in text for sig in not_found_signals):
        return False

    msg = (result.stderr or result.stdout or "").strip()
    raise RuntimeError(f"存在確認に失敗しました (mega-ls): {msg}")


def is_logged_in(mega_whoami: str) -> bool:
    try:
        result = run_megacmd(mega_whoami, [], timeout_sec=30)
    except subprocess.TimeoutExpired:
        raise RuntimeError("MEGAサーバーへの接続がタイムアウトしました")

    out = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    combined = f"{out}\n{err}".lower()

    if result.returncode != 0:
        return False
    if "not logged in" in combined:
        return False
    # mega-whoami がメールアドレスを出すパターンが多い
    return bool(out)


def ensure_login(mega_login: str | None, mega_whoami: str) -> None:
    if is_logged_in(mega_whoami):
        return

    if not mega_login:
        raise RuntimeError("MEGAにログインしていません (mega-login が見つかりません)")

    print("MEGAにログインしていません。ログインします。")
    try:
        email = input("メールアドレス: ").strip()
    except EOFError:
        raise RuntimeError("入力が取得できないためログインできません")
    if not email:
        raise RuntimeError("メールアドレスが空です")
    password = getpass.getpass("パスワード: ")
    if not password:
        raise RuntimeError("パスワードが空です")

    try:
        result = run_megacmd(mega_login, [email, password], timeout_sec=60)
    except subprocess.TimeoutExpired:
        raise RuntimeError("ログインがタイムアウトしました")

    if result.returncode != 0:
        msg = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"ログインに失敗しました: {msg}")


def upload_folder(
    mega_put: str, folder_path: Path, dest: str, dry_run: bool = False, timeout_sec: int = 60
) -> None:
    if dry_run:
        print(f"[dry-run] mega-put -c -q \"{folder_path}\" {dest}")
        return

    try:
        result = run_megacmd(mega_put, ["-c", "-q", str(folder_path), dest], timeout_sec=timeout_sec)
    except subprocess.TimeoutExpired:
        raise RuntimeError("アップロードのキュー追加がタイムアウトしました")

    if result.returncode != 0:
        msg = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"アップロードに失敗しました: {msg}")


def resolve_folder_arg(base_dir: Path, folder_arg: str) -> Path:
    p = Path(folder_arg).expanduser()
    if p.is_absolute() or p.exists():
        return p.resolve()
    return (base_dir / folder_arg).resolve()


def main(argv: Sequence[str] | None = None) -> int:
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(description="スクショ済みフォルダを選択して MEGA にアップロードします。")
    parser.add_argument("--base", default=str(script_dir), help="検索するベースディレクトリ (デフォルト: このスクリプトの場所)")
    parser.add_argument("--dest", default="/book", help="MEGAのアップロード先 (デフォルト: /book)")
    parser.add_argument("--folder", help="アップロードするフォルダ名 or パス (指定時は番号選択をスキップ)")
    parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="アップロード先に同名フォルダが既にある場合はアップロードしない",
    )
    parser.add_argument("--yes", action="store_true", help="確認プロンプトをスキップ")
    parser.add_argument("--dry-run", action="store_true", help="実行せずにコマンドだけ表示")
    args = parser.parse_args(argv)

    base_dir = Path(args.base).expanduser().resolve()
    if not base_dir.exists():
        print(f"[エラー] base が存在しません: {base_dir}")
        return 2

    dest = (args.dest or "").strip()
    if not dest:
        print("[エラー] --dest が空です")
        return 2

    selected_all = False
    if args.folder:
        targets = [resolve_folder_arg(base_dir, args.folder)]
    else:
        candidates = discover_candidate_folders(base_dir)
        print_candidates(candidates)
        selected, selected_all = prompt_selection(candidates)
        targets = [c.path for c in selected]

    if not targets:
        print("終了します。")
        return 0

    missing = [str(p) for p in targets if not p.exists() or not p.is_dir()]
    if missing:
        print(f"[エラー] フォルダが見つかりません: {missing}")
        return 2

    print("\n選択フォルダ:")
    for p in targets:
        print(f"- {p.name}  ({p})")
    print(f"MEGAアップロード先: {dest}")
    skip_if_exists = bool(args.skip_if_exists or selected_all)
    if selected_all and not args.skip_if_exists:
        print("※ `all` を選択したため、アップロード先に同名があるフォルダはスキップします。")

    if not args.yes:
        try:
            confirm = input("\nアップロードしますか? (y/n): ").strip().lower()
        except EOFError:
            print("入力が取得できないため中止します。")
            return 1
        if confirm not in {"y", "yes"}:
            print("中止しました。")
            return 0

    mega_put = find_megacmd_command("mega-put")
    mega_whoami = find_megacmd_command("mega-whoami")
    mega_login = find_megacmd_command("mega-login")
    mega_ls = find_megacmd_command("mega-ls") if skip_if_exists else None

    if not mega_put or not mega_whoami:
        print("[エラー] MEGAcmd が見つかりません。https://mega.io/cmd をインストールしてください。")
        return 3

    if skip_if_exists and not mega_ls:
        print("[エラー] --skip-if-exists には mega-ls が必要です (MEGAcmd のインストールを確認してください)。")
        return 3

    try:
        if not args.dry_run:
            ensure_login(mega_login, mega_whoami)
    except RuntimeError as e:
        print(f"[エラー] {e}")
        return 4

    uploaded_any = False
    for folder in targets:
        if skip_if_exists:
            remote_target = remote_join(dest, folder.name)
            if args.dry_run:
                print(f"\n[dry-run] 既存チェック: {remote_target}")
            else:
                try:
                    if remote_entry_exists(mega_ls, remote_target):
                        print(f"\nスキップ: 既に存在します: {remote_target}")
                        continue
                except RuntimeError as e:
                    print(f"[エラー] {e}")
                    return 4

        print(f"\nアップロード中: {folder}")
        try:
            upload_folder(mega_put, folder, dest, dry_run=args.dry_run)
        except RuntimeError as e:
            print(f"[エラー] {e}")
            return 5
        uploaded_any = True

    if args.dry_run:
        print("\n[dry-run] 完了")
    elif uploaded_any:
        print("\n完了: アップロードをキューに追加しました。進捗は `mega-transfers` で確認できます。")
    else:
        print("\n完了: 既に存在するためアップロードは行いませんでした。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
