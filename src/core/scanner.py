# -*- coding: utf-8 -*-
"""ファイルシステムのスキャンとデータベースの同期を行います。

FileScannerクラスは、指定されたフォルダをスキャンし、ファイルの追加、削除、
移動を検出して、データベースの状態を最新に保ちます。
"""
import os
import hashlib
import datetime
from typing import Dict, Set
from src.core.database import DatabaseManager
from src.core.parser import FileNameParser
from src.models.book import Book


class FileScanner:
    """ファイルシステムをスキャンし、データベースと同期するクラス。

    Attributes:
        db_manager (DatabaseManager): データベース操作を管理するマネージャー。
        parser (FileNameParser): ファイル名から書籍情報を解析するパーサー。
    """

    def __init__(self, db_manager: DatabaseManager, parser: FileNameParser):
        """FileScannerのコンストラクタ。

        Args:
            db_manager (DatabaseManager): データベースマネージャーのインスタンス。
            parser (FileNameParser): ファイル名パーサーのインスタンス。
        """
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
        print("スキャン処理を開始します...")

        scan_folders, exclude_paths, target_extensions = self._get_scan_settings()
        
        found_files_by_hash, found_files_by_path = self._scan_filesystem(
            scan_folders, exclude_paths, target_extensions
        )
        
        db_books_by_hash, db_books_by_path = self._get_db_books()

        self._process_updates(
            found_files_by_path, db_books_by_path,
            found_files_by_hash, db_books_by_hash
        )
        
        self._process_moves_adds_deletes(
            found_files_by_hash, db_books_by_hash
        )

        print("スキャン処理が完了しました。")

    def _get_scan_settings(self) -> tuple[list, list, set]:
        """スキャン設定をDBから取得する。"""
        scan_folders = self.db_manager.get_scan_folders()
        exclude_paths = [f['path'] for f in self.db_manager.get_exclude_folders()]
        
        # 対象拡張子を取得し、セットに変換
        scan_extensions_str = self.db_manager.get_setting('scan_extensions')
        target_extensions = set()
        if scan_extensions_str:
            target_extensions = {ext.strip().lower() for ext in scan_extensions_str.split(',') if ext.strip()}
            
        return scan_folders, exclude_paths, target_extensions

    def _scan_filesystem(self, scan_folders: list, exclude_paths: list, target_extensions: set) -> tuple[Dict[str, str], Dict[str, str]]:
        """ファイルシステムをスキャンし、ハッシュとパスをキーとする辞書を返す。"""
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
        """DBから書籍情報を取得し、ハッシュとパスをキーとする辞書を返す。"""
        db_books = self.db_manager.get_all_books()
        db_books_by_hash = {book.file_hash: book for book in db_books}
        db_books_by_path = {book.file_path: book for book in db_books}
        return db_books_by_hash, db_books_by_path

    def _process_updates(self, found_files_by_path: Dict[str, str], db_books_by_path: Dict[str, Book], found_files_by_hash: Dict[str, str], db_books_by_hash: Dict[str, Book]):
        """更新されたファイル（パスが同じでハッシュが異なる）を処理する。"""
        updated_paths = {p for p in db_books_by_path if p in found_files_by_path and found_files_by_path[p] != db_books_by_path[p].file_hash}
        for path in updated_paths:
            old_book = db_books_by_path[path]
            new_hash = found_files_by_path[path]
            
            print(f"更新: {old_book.title} ({path})")
            self.db_manager.update_book_hash(old_book.file_hash, new_hash, path)
            
            # 更新済みのものは後続の差分検出から除外
            if old_book.file_hash in db_books_by_hash:
                del db_books_by_hash[old_book.file_hash]
            if new_hash in found_files_by_hash:
                del found_files_by_hash[new_hash]

    def _process_moves_adds_deletes(self, found_files_by_hash: Dict[str, str], db_books_by_hash: Dict[str, Book]):
        """移動、新規追加、削除されたファイルを処理する。"""
        found_hashes = set(found_files_by_hash.keys())
        db_hashes = set(db_books_by_hash.keys())

        new_hashes = found_hashes - db_hashes
        deleted_hashes = db_hashes - found_hashes
        moved_hashes = found_hashes.intersection(db_hashes)

        # 移動 (ハッシュは同じだがパスが異なる)
        for h in moved_hashes:
            if found_files_by_hash[h] != db_books_by_hash[h].file_path:
                self.db_manager.update_book_path(h, found_files_by_hash[h])
                print(f"パス更新: {db_books_by_hash[h].title} -> {found_files_by_hash[h]}")

        # 新規
        for h in new_hashes:
            path = found_files_by_hash[h]
            book_info = self.parser.parse_filename(os.path.basename(path))
            book_info.file_path = path
            book_info.file_hash = h
            book_info.created_at = datetime.datetime.now().isoformat()
            self.db_manager.save_book(book_info)
            print(f"新規登録: {book_info.title} ({path})")

        # 削除
        for h in deleted_hashes:
            self.db_manager.delete_book(h)
            print(f"削除: {db_books_by_hash[h].title} ({db_books_by_hash[h].file_path})")
