# -*- coding: utf-8 -*-
"""ファイルシステムのスキャンとデータベースの同期を行います。

FileScannerクラスは、指定されたフォルダをスキャンし、ファイルの追加、削除、
移動を検出して、データベースの状態を最新に保ちます。
"""
import os
import hashlib
import datetime
from typing import Dict, Set, Tuple
from PyQt6.QtCore import QObject, pyqtSignal
from src.core.database import DatabaseManager
from src.core.parser import FileNameParser
from src.models.book import Book


class FileScanner(QObject):
    """ファイルシステムをスキャンし、データベースと同期するクラス。

    Attributes:
        db_manager (DatabaseManager): データベース操作を管理するマネージャー。
        parser (FileNameParser): ファイル名から書籍情報を解析するパーサー。
    """
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, db_manager: DatabaseManager, parser: FileNameParser):
        """FileScannerのコンストラクタ。

        Args:
            db_manager (DatabaseManager): データベースマネージャーのインスタンス。
            parser (FileNameParser): ファイル名パーサーのインスタンス。
        """
        super().__init__()
        self.db_manager = db_manager
        self.parser = parser

    def _calculate_hash(self, file_path: str) -> str:
        """ファイルのSHA256ハッシュ値を計算する。

        Args:
            file_path (str): ハッシュを計算するファイルのパス。

        Returns:
            str: 計算されたハッシュ値。IOErrorの場合は空文字列を返す。
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except IOError:
            return ""

    def scan_folders(self):
        """スキャン対象フォルダをスキャンし、データベースと同期する。"""
        self.progress.emit("スキャン処理を開始します...")
        print("スキャン処理を開始します...")

        scan_folders, exclude_paths, target_extensions = self._get_scan_settings()
        
        found_files_by_hash, found_files_by_path = self._scan_filesystem(
            scan_folders, exclude_paths, target_extensions
        )
        
        db_books_by_hash, db_books_by_path = self._get_db_books()

        processed_found_files_by_hash, processed_db_books_by_hash = self._process_updates(
            found_files_by_path, db_books_by_path,
            found_files_by_hash, db_books_by_hash
        )
        
        self._process_moves_adds_deletes(
            processed_found_files_by_hash, processed_db_books_by_hash
        )

        self.progress.emit("スキャン処理が完了しました。")
        print("スキャン処理が完了しました。")
        self.finished.emit()

    def _get_scan_settings(self) -> tuple[list, list, set]:
        """スキャン設定をDBから取得する。

        Returns:
            tuple[list, list, set]: (スキャン対象フォルダのリスト, 除外フォルダのパスリスト, 対象拡張子のセット)
        """
        scan_folders = self.db_manager.get_scan_folders()
        exclude_paths = [f['path'] for f in self.db_manager.get_exclude_folders()]
        
        # 対象拡張子を取得し、セットに変換
        scan_extensions_str = self.db_manager.get_setting('scan_extensions')
        target_extensions = set()
        if scan_extensions_str:
            target_extensions = {ext.strip().lower() for ext in scan_extensions_str.split(',') if ext.strip()}
            
        return scan_folders, exclude_paths, target_extensions

    def _scan_filesystem(self, scan_folders: list, exclude_paths: list, target_extensions: set) -> tuple[Dict[str, str], Dict[str, str]]:
        """ファイルシステムをスキャンし、ハッシュとパスをキーとする辞書を返す。

        Args:
            scan_folders (list): スキャン対象フォルダのリスト。
            exclude_paths (list): 除外フォルダのパスリスト。
            target_extensions (set): スキャン対象のファイル拡張子のセット。

        Returns:
            tuple[Dict[str, str], Dict[str, str]]:
                - found_files_by_hash (Dict[str, str]): ハッシュをキー、ファイルパスを値とする辞書。
                - found_files_by_path (Dict[str, str]): ファイルパスをキー、ハッシュを値とする辞書。
        """
        found_files_by_hash: Dict[str, str] = {}
        found_files_by_path: Dict[str, str] = {}
        for folder in scan_folders:
            scan_path = folder['path']
            for root, _, files in os.walk(scan_path):
                if any(root.startswith(excluded) for excluded in exclude_paths):
                    continue
                for file in files:
                    file_ext = os.path.splitext(file)[1].lstrip('.').lower()
                    if target_extensions and file_ext not in target_extensions:
                        continue

                    file_path = os.path.join(root, file)
                    file_hash = self._calculate_hash(file_path)
                    if file_hash:
                        found_files_by_hash[file_hash] = file_path
                        found_files_by_path[file_path] = file_hash
        return found_files_by_hash, found_files_by_path

    def _get_db_books(self) -> tuple[Dict[str, Book], Dict[str, Book]]:
        """DBから書籍情報を取得し、ハッシュとパスをキーとする辞書を返す。

        Returns:
            tuple[Dict[str, Book], Dict[str, Book]]:
                - db_books_by_hash (Dict[str, Book]): ハッシュをキー、Bookオブジェクトを値とする辞書。
                - db_books_by_path (Dict[str, Book]): ファイルパスをキー、Bookオブジェクトを値とする辞書。
        """
        db_books = self.db_manager.get_all_books()
        db_books_by_hash = {book.file_hash: book for book in db_books}
        db_books_by_path = {book.file_path: book for book in db_books}
        return db_books_by_hash, db_books_by_path

    def _process_updates(self, found_files_by_path: Dict[str, str], db_books_by_path: Dict[str, Book], found_files_by_hash: Dict[str, str], db_books_by_hash: Dict[str, Book]) -> Tuple[Dict[str, str], Dict[str, Book]]:
        """更新されたファイル（パスが同じでハッシュが異なる）を処理する。

        Args:
            found_files_by_path (Dict[str, str]): ファイルパスをキー、ハッシュを値とする辞書。
            db_books_by_path (Dict[str, Book]): ファイルパスをキー、Bookオブジェクトを値とする辞書。
            found_files_by_hash (Dict[str, str]): ハッシュをキー、ファイルパスを値とする辞書。
            db_books_by_hash (Dict[str, Book]): ハッシュをキー、Bookオブジェクトを値とする辞書。

        Returns:
            Tuple[Dict[str, str], Dict[str, Book]]:
                - current_found_files_by_hash (Dict[str, str]): 更新後のファイルシステム上のハッシュとパスの辞書。
                - current_db_books_by_hash (Dict[str, Book]): 更新後のデータベース上のハッシュとBookオブジェクトの辞書。
        """
        # 辞書のコピーを作成し、元の辞書を変更しないようにする
        current_found_files_by_hash = found_files_by_hash.copy()
        current_db_books_by_hash = db_books_by_hash.copy()

        updated_paths = {p for p in db_books_by_path if p in found_files_by_path and found_files_by_path[p] != db_books_by_path[p].file_hash}
        for path in updated_paths:
            old_book = db_books_by_path[path]
            new_hash = found_files_by_path[path]
            
            self.progress.emit(f"更新: {old_book.title} ({path})")
            print(f"更新: {old_book.title} ({path})")
            self.db_manager.update_book_hash(old_book.file_hash, new_hash, path)
            
            # 更新済みのものは後続の差分検出から除外
            if old_book.file_hash in current_db_books_by_hash:
                del current_db_books_by_hash[old_book.file_hash]
            # 更新されたファイルの新しいハッシュをdb_books_by_hashに追加
            current_db_books_by_hash[new_hash] = old_book  # 新しいハッシュで既存のBookオブジェクトを指す
        
        return current_found_files_by_hash, current_db_books_by_hash

    def _process_moves_adds_deletes(self, processed_found_files_by_hash: Dict[str, str], processed_db_books_by_hash: Dict[str, Book]):
        """移動、新規追加、削除されたファイルを処理する。

        Args:
            processed_found_files_by_hash (Dict[str, str]):
                _process_updatesで処理された、ファイルシステム上のハッシュとパスの辞書。
            processed_db_books_by_hash (Dict[str, Book]):
                _process_updatesで処理された、データベース上のハッシュとBookオブジェクトの辞書。
        """
        found_hashes = set(processed_found_files_by_hash.keys())
        db_hashes = set(processed_db_books_by_hash.keys())

        # 削除されたハッシュ
        deleted_hashes = db_hashes - found_hashes

        # 新規追加されたハッシュ (移動されたものも含む可能性があるため、後で調整)
        new_hashes = found_hashes - db_hashes

        # 移動されたハッシュ (ハッシュは同じだがパスが異なる)
        # db_books_by_hash に存在し、found_files_by_hash にも存在し、かつパスが異なるもの
        moved_hashes_to_process = set()
        for h in found_hashes.intersection(db_hashes):
            if processed_found_files_by_hash[h] != processed_db_books_by_hash[h].file_path:
                moved_hashes_to_process.add(h)
        
        # 移動されたファイルのパスを更新
        for h in moved_hashes_to_process:
            self.db_manager.update_book_path(h, processed_found_files_by_hash[h])
            self.progress.emit(f"パス更新: {processed_db_books_by_hash[h].title} -> {processed_found_files_by_hash[h]}")
            print(f"パス更新: {processed_db_books_by_hash[h].title} -> {processed_found_files_by_hash[h]}")
            # 移動されたものは新規ではないので、new_hashesから除外
            if h in new_hashes:
                new_hashes.remove(h)

        # 新規
        for h in new_hashes:
            path = processed_found_files_by_hash[h]
            book_info = self.parser.parse_filename(os.path.basename(path))
            book_info.file_path = path
            book_info.file_hash = h
            book_info.created_at = datetime.datetime.now().isoformat()
            self.db_manager.save_book(book_info)
            self.progress.emit(f"新規登録: {book_info.title} ({path})")
            print(f"新規登録: {book_info.title} ({path})")

        # 削除
        for h in deleted_hashes:
            self.db_manager.delete_book(h)
            self.progress.emit(f"削除: {processed_db_books_by_hash[h].title} ({processed_db_books_by_hash[h].file_path})")
            print(f"削除: {processed_db_books_by_hash[h].title} ({processed_db_books_by_hash[h].file_path})")
