# -*- coding: utf-8 -*-
import sys
import os
import subprocess
from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont
from src.ui.main_window import MainWindow
from src.ui.settings_window import SettingsWindow
from src.core.database import DatabaseManager
from src.core.scanner import FileScanner
from src.models.book import Book

# convert_path_for_wsl 関数は削除

class ApplicationController:
    """アプリケーション全体のロジックを管理するコントローラー。"""
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()
        self.scanner = FileScanner(self.db_manager)
        self.main_window = MainWindow()
        self.connect_signals()

    def connect_signals(self):
        """UIのシグナルとロジックのスロットを接続する。"""
        self.main_window.sync_button.clicked.connect(self.run_scan_and_refresh)
        self.main_window.settings_button.clicked.connect(self.open_settings_window)
        self.main_window.viewer_button.clicked.connect(self.open_selected_book_in_viewer)
        self.main_window.book_table_view.doubleClicked.connect(self.open_selected_book_in_viewer)

    def open_settings_window(self):
        """設定ウィンドウを開き、設定を管理する。"""
        settings_dialog = SettingsWindow(self.main_window)
        scan_folders = self.db_manager.get_scan_folders()
        exclude_folders = self.db_manager.get_exclude_folders()
        viewer_path = self.db_manager.get_setting('viewer_path')
        settings_dialog.set_settings(scan_folders, exclude_folders, viewer_path)

        if settings_dialog.exec():
            new_scan, new_exclude, new_viewer = settings_dialog.get_settings()
            self.db_manager.save_scan_folders(new_scan)
            self.db_manager.save_exclude_folders(new_exclude)
            self.db_manager.set_setting('viewer_path', new_viewer)
            print("設定を保存しました。")

    def open_selected_book_in_viewer(self):
        """テーブルで選択されている書籍をビューアで開く。"""
        selected_indexes = self.main_window.book_table_view.selectedIndexes()
        if not selected_indexes:
            return

        proxy_index = selected_indexes[0]
        source_index = self.main_window.proxy_model.mapToSource(proxy_index)
        book: Book = self.main_window.book_table_model.itemFromIndex(source_index).data(Qt.ItemDataRole.UserRole)

        if not book:
            QMessageBox.warning(self.main_window, "エラー", "選択された蔵書情報が見つかりません。")
            return

        # まずビューアパスの状況をチェック
        viewer_path = self.db_manager.get_setting('viewer_path')
        if not viewer_path:
            QMessageBox.information(self.main_window, "ビューア未設定",
                "ビューアが設定されていません。\n設定画面から使用するビューアのパスを指定してください。")
            return
        
        # ビューアパスが存在するかチェック
        if not os.path.exists(viewer_path):
            QMessageBox.warning(self.main_window, "ビューアが見つかりません",
                f"設定されたビューアが見つかりません。\nパス: {viewer_path}\n設定画面でパスを確認してください。")
            return

        # 次に蔵書ファイルパスの状況をチェック
        if not book.file_path:
            QMessageBox.warning(self.main_window, "エラー", "選択された蔵書にファイルパスが登録されていません。")
            return

        if not os.path.exists(book.file_path):
            QMessageBox.warning(self.main_window, "エラー", f"蔵書ファイルが見つかりません。\nパス: {book.file_path}")
            return

        try:
            subprocess.Popen([viewer_path, book.file_path])
        except Exception as e:
            QMessageBox.critical(self.main_window, "起動エラー", f"ビューアを起動できませんでした。\n{e}")

    def run_scan_and_refresh(self):
        self.scanner.scan_folders()
        self.load_books_to_list()

    def load_books_to_list(self):
        books = self.db_manager.get_all_books()
        self.main_window.display_books(books)

    def run(self):
        self.main_window.show()
        self.load_books_to_list()

def main():
    """アプリケーションのメインエントリポイント。"""
    app = QApplication(sys.argv)
    # フォント設定
    font = QFont("Yu Gothic UI", 12) # Windows環境を想定し、Yu Gothic UIを優先
    font.setStyleHint(QFont.StyleHint.System) # システムのフォントヒントを使用
    app.setFont(font)
    controller = ApplicationController()
    controller.run()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()