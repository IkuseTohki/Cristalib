# -*- coding: utf-8 -*-
import os
import hashlib
import datetime
from typing import Dict, Set
from src.core.database import DatabaseManager
from src.core.parser import FileNameParser
from src.models.book import Book

class FileScanner:
    """
    ファイルシステムをスキャンし、データベースと同期するクラス。
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.parser = FileNameParser()

    def _calculate_hash(self, file_path: str) -> str:
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
        scan_folders = self.db_manager.get_scan_folders()
        exclude_paths = [f['path'] for f in self.db_manager.get_exclude_folders()]

        # 対象拡張子を取得し、セットに変換
        scan_extensions_str = self.db_manager.get_setting('scan_extensions')
        target_extensions = set()
        if scan_extensions_str:
            target_extensions = {ext.strip().lower() for ext in scan_extensions_str.split(',') if ext.strip()}

        # 1. ファイルシステム上の全ファイルをスキャン
        found_files: Dict[str, str] = {}
        for folder in scan_folders:
            scan_path = folder['path']
            for root, _, files in os.walk(scan_path):
                if any(root.startswith(excluded) for excluded in exclude_paths):
                    continue
                for file in files:
                    # 拡張子フィルタリング
                    file_ext = os.path.splitext(file)[1].lstrip('.').lower()
                    if target_extensions and file_ext not in target_extensions:
                        continue

                    file_path = os.path.join(root, file)
                    file_hash = self._calculate_hash(file_path)
                    if file_hash:
                        found_files[file_hash] = file_path

        # 2. データベース上の全書籍情報を取得
        db_books: Dict[str, Book] = {book.file_hash: book for book in self.db_manager.get_all_books()}

        found_hashes = set(found_files.keys())
        db_hashes = set(db_books.keys())

        # 3. 差分を検出して処理
        new_hashes = found_hashes - db_hashes
        deleted_hashes = db_hashes - found_hashes
        
        # 既存ファイルのパス更新チェック (ハッシュは同じだがパスが異なる場合)
        # この処理は、new_hashesとdeleted_hashesの処理とは独立して行う
        for h in found_hashes.intersection(db_hashes):
            if found_files[h] != db_books[h].file_path:
                self.db_manager.update_book_path(h, found_files[h])
                print(f"パス更新: {db_books[h].title} -> {found_files[h]}")

        # 新規ファイル
        for h in new_hashes:
            path = found_files[h]
            book_info = self.parser.parse_filename(os.path.basename(path))
            book_info.file_path = path
            book_info.file_hash = h
            book_info.created_at = datetime.datetime.now().isoformat()
            self.db_manager.save_book(book_info)
            print(f"新規登録: {book_info.title} ({path})")

        # 削除されたファイル (DBにはあるがファイルシステムにないハッシュ)
        for h in deleted_hashes:
            self.db_manager.delete_book(h)
            print(f"削除: {db_books[h].title} ({db_books[h].file_path})")

        print("スキャン処理が完了しました。")