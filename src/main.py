# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import json
from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont
from src.ui.main_window import MainWindow
from src.ui.settings_window import SettingsWindow, PasswordDialog
from src.ui.book_edit_dialog import BookEditDialog
from src.core.database import DatabaseManager, hash_password, verify_password
from src.core.scanner import FileScanner
from src.models.book import Book

class ApplicationController:
    """アプリケーション全体のロジックを管理するコントローラー。"""
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()
        self.scanner = FileScanner(self.db_manager)
        self.main_window = MainWindow()
        self.is_private_mode = False # プライベートモードの状態

        self.connect_signals()

    def connect_signals(self):
        """UIのシグナルとロジックのスロットを接続する。"""
        self.main_window.sync_button.clicked.connect(self.run_scan_and_refresh)
        self.main_window.settings_button.clicked.connect(self.authenticate_and_open_settings)
        self.main_window.viewer_button.clicked.connect(self.open_selected_book_in_viewer)
        self.main_window.book_table_view.doubleClicked.connect(self.open_selected_book_in_viewer)
        self.main_window.mode_button.clicked.connect(self.toggle_private_mode)
        self.main_window.edit_button.clicked.connect(self.open_book_edit_dialog)

    def authenticate_and_open_settings(self):
        """パスワード認証後、設定ウィンドウを開く。"""
        stored_hash = self.db_manager.get_setting('password_hash')

        if not stored_hash:
            # パスワードが未設定の場合
            QMessageBox.information(self.main_window, "パスワード設定", "初回起動です。パスワードを設定してください。")
            set_password_dialog = PasswordDialog(self.main_window, mode="set_password")
            if set_password_dialog.exec():
                new_password = set_password_dialog.get_password()
                if new_password:
                    self.db_manager.set_setting('password_hash', hash_password(new_password))
                    QMessageBox.information(self.main_window, "成功", "パスワードが設定されました。")
                    self._open_settings_window_internal() # 設定後、設定画面を開く
            else:
                QMessageBox.warning(self.main_window, "キャンセル", "パスワード設定がキャンセルされました。")
        else:
            # パスワードが設定済みの場合
            auth_dialog = PasswordDialog(self.main_window, mode="authenticate")
            if auth_dialog.exec():
                entered_password = auth_dialog.get_password()
                if verify_password(stored_hash, entered_password):
                    self._open_settings_window_internal()
                else:
                    QMessageBox.warning(self.main_window, "認証失敗", "パスワードが正しくありません。")
            else:
                QMessageBox.information(self.main_window, "キャンセル", "認証がキャンセルされました。")

    def _open_settings_window_internal(self):
        """認証後に設定ウィンドウを開く内部メソッド。"""
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

    def toggle_private_mode(self):
        """プライベートモードの切り替え。"""
        if self.is_private_mode:
            # プライベートモードから通常モードへ
            self.is_private_mode = False
            self.main_window.mode_button.setText("プライベートモードへ")
            self.load_books_to_list() # リストを更新
        else:
            # 通常モードからプライベートモードへ (認証が必要)
            stored_hash = self.db_manager.get_setting('password_hash')
            if not stored_hash:
                QMessageBox.information(self.main_window, "パスワード未設定", "プライベートモードを使用するには、まず設定画面でパスワードを設定してください。")
                return

            auth_dialog = PasswordDialog(self.main_window, mode="authenticate")
            if auth_dialog.exec():
                entered_password = auth_dialog.get_password()
                if verify_password(stored_hash, entered_password):
                    self.is_private_mode = True
                    self.main_window.mode_button.setText("通常モードへ")
                    self.load_books_to_list() # リストを更新
                else:
                    QMessageBox.warning(self.main_window, "認証失敗", "パスワードが正しくありません。")
            else:
                QMessageBox.information(self.main_window, "キャンセル", "認証がキャンセルされました。")

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

    def open_book_edit_dialog(self):
        """選択された書籍の編集ダイアログを開く。"""
        selected_indexes = self.main_window.book_table_view.selectedIndexes()
        if not selected_indexes:
            QMessageBox.information(self.main_window, "情報", "編集する書籍を選択してください。")
            return

        proxy_index = selected_indexes[0]
        source_index = self.main_window.proxy_model.mapToSource(proxy_index)
        book: Book = self.main_window.book_table_model.itemFromIndex(source_index).data(Qt.ItemDataRole.UserRole)

        if not book:
            QMessageBox.warning(self.main_window, "エラー", "選択された書籍情報が見つかりません。")
            return

        edit_dialog = BookEditDialog(self.main_window, book=book)
        if edit_dialog.exec():
            updated_book = edit_dialog.get_book_data()
            # 元の書籍のfile_path, file_hash, created_at は編集しないので引き継ぐ
            updated_book.file_path = book.file_path
            updated_book.file_hash = book.file_hash
            updated_book.created_at = book.created_at
            
            self.db_manager.update_book(updated_book)
            self.load_books_to_list() # リストを更新
            QMessageBox.information(self.main_window, "成功", "書籍情報を更新しました。")

    def run_scan_and_refresh(self):
        self.scanner.scan_folders()
        self.load_books_to_list()

    def load_books_to_list(self):
        """データベースから書籍を読み込み、UIに表示する。"""
        all_books = self.db_manager.get_all_books()

        if self.is_private_mode:
            books_to_display = all_books
        else:
            scan_folders_data = self.db_manager.get_scan_folders()
            
            scan_folder_private_status = {f['path']: f.get('is_private', 0) for f in scan_folders_data}

            books_to_display = []
            for book in all_books:
                if not book.file_path:
                    continue

                book_dir = os.path.dirname(book.file_path)
                book_dir = book_dir.replace("\\", "/")
                
                is_private_for_book = 1 # デフォルトはプライベート扱い
                
                matched_scan_root = None
                for scan_root_path in scan_folder_private_status.keys():
                    normalized_scan_root_path = scan_root_path.replace("\\", "/")
                    
                    common_path_result = os.path.commonpath([normalized_scan_root_path, book_dir])
                    normalized_common_path_result = common_path_result.replace("\\", "/")

                    if normalized_common_path_result == normalized_scan_root_path:
                        if matched_scan_root is None or len(normalized_scan_root_path) > len(matched_scan_root):
                            matched_scan_root = normalized_scan_root_path
                
                if matched_scan_root:
                    is_private_for_book = scan_folder_private_status[matched_scan_root]
                
                if is_private_for_book == 0: # is_privateが0なら通常モードで表示
                    books_to_display.append(book)

        self.main_window.display_books(books_to_display)
        self.load_column_settings() # 列設定をロード

    def run(self):
        """アプリケーションを実行する。"""
        self.main_window.show()
        self.load_books_to_list()

    def load_column_settings(self):
        """保存された列の表示状態と幅を読み込み、適用する。"""
        visibility_json = self.db_manager.get_setting('column_visibility')
        widths_json = self.db_manager.get_setting('column_widths')
        
        settings = {}
        if visibility_json:
            try:
                settings['visibility'] = json.loads(visibility_json)
            except json.JSONDecodeError:
                print("Warning: Failed to decode column visibility settings.")
        if widths_json:
            try:
                settings['widths'] = json.loads(widths_json)
            except json.JSONDecodeError:
                print("Warning: Failed to decode column widths settings.")
        
        if settings:
            self.main_window.apply_column_settings(settings)

    def save_column_settings(self):
        """現在の列の表示状態と幅を保存する。"""
        settings = self.main_window.get_column_settings()
        
        visibility_json = json.dumps(settings['visibility'])
        widths_json = json.dumps(settings['widths'])
        
        self.db_manager.set_setting('column_visibility', visibility_json)
        self.db_manager.set_setting('column_widths', widths_json)
        print("Column settings saved.")

def main():
    """アプリケーションのメインエントリポイント。"""
    app = QApplication(sys.argv)
    # アプリケーション終了時に設定を保存するシグナルを接続
    app.aboutToQuit.connect(lambda: controller.save_column_settings())

    # フォント設定
    font = QFont("Yu Gothic UI", 12) # Windows環境を想定し、Yu Gothic UIを優先
    font.setStyleHint(QFont.StyleHint.System) # システムのフォントヒントを使用
    app.setFont(font)
    controller = ApplicationController()

    # アプリケーション終了時に設定を保存するシグナルを接続
    app.aboutToQuit.connect(lambda: controller.save_column_settings())

    controller.run()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
