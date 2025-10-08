# -*- coding: utf-8 -*-
import sqlite3
import os
from contextlib import contextmanager
from typing import List, Optional
from src.models.book import Book

class DatabaseManager:
    """
    データベースの接続、操作、管理を行うクラス。
    """
    def __init__(self, db_path="data/library.db"):
        self.db_path = db_path
        self._ensure_db_directory()

    def _ensure_db_directory(self):
        """データベースファイルが格納されるディレクトリの存在を保証する。"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    @contextmanager
    def get_connection(self):
        """データベース接続を管理するコンテキストマネージャ。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_tables(self):
        """データベース内に必要なテーブルをすべて作成する。"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # books, scan_folders, exclude_folders, app_settings テーブルを作成
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, subtitle TEXT, 
                    volume INTEGER, author TEXT, original_author TEXT, series TEXT, 
                    category TEXT, rating INTEGER, is_magazine_collection INTEGER DEFAULT 0, 
                    file_path TEXT NOT NULL, file_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
                )'''
            )
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS scan_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL UNIQUE, is_private INTEGER DEFAULT 0
                )'''
            )
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS exclude_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL UNIQUE
                )'''
            )
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)'''
            )
            conn.commit()

    # --- Book --- #
    def save_book(self, book: Book):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO books (title, subtitle, volume, author, original_author, series, category, rating, is_magazine_collection, file_path, file_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (book.title, book.subtitle, book.volume, book.author, book.original_author, book.series, book.category, book.rating, book.is_magazine_collection, book.file_path, book.file_hash, book.created_at)
            )
            conn.commit()

    def get_book_by_hash(self, file_hash: str) -> Optional[Book]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM books WHERE file_hash = ?", (file_hash,))
            row = cursor.fetchone()
            return Book(**row) if row else None

    def get_all_books(self) -> List[Book]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM books")
            return [Book(**row) for row in cursor.fetchall()]

    def update_book_path(self, file_hash: str, new_path: str):
        with self.get_connection() as conn:
            conn.execute("UPDATE books SET file_path = ? WHERE file_hash = ?", (new_path, file_hash))
            conn.commit()

    def delete_book(self, file_hash: str):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM books WHERE file_hash = ?", (file_hash,))
            conn.commit()

    # --- ScanFolder --- #
    def get_scan_folders(self) -> List[dict]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM scan_folders")
            return [dict(row) for row in cursor.fetchall()]

    def save_scan_folders(self, folders: List[dict]):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM scan_folders")
            conn.executemany(
                "INSERT INTO scan_folders (path, is_private) VALUES (?, ?)",
                [(f['path'], f.get('is_private', 0)) for f in folders]
            )
            conn.commit()

    # --- ExcludeFolder --- #
    def get_exclude_folders(self) -> List[dict]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM exclude_folders")
            return [dict(row) for row in cursor.fetchall()]

    def save_exclude_folders(self, folders: List[dict]):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM exclude_folders")
            conn.executemany(
                "INSERT INTO exclude_folders (path) VALUES (?)",
                [(f['path'],) for f in folders]
            )
            conn.commit()

    # --- AppSettings --- #
    def get_setting(self, key: str) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else None

    def set_setting(self, key: str, value: str):
        with self.get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
