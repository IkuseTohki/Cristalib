# -*- coding: utf-8 -*>
"""アプリケーションのエントリーポイントとメインコントローラー。

ApplicationControllerクラスが、UI、データベース、ファイルスキャナー間の
やり取りを制御し、アプリケーション全体の動作を管理します。
"""
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
from src.core.parser import ParsingRuleLoader, FileNameParser
from src.models.book import Book


class ApplicationController:
    """アプリケーション全体のロジックを管理するコントローラー。

    Attributes:
        db_manager (DatabaseManager): データベース管理オブジェクト。
        rule_loader (ParsingRuleLoader): 解析ルール読み込みオブジェクト。
        parser (FileNameParser): ファイル名解析オブジェクト。
        scanner (FileScanner): ファイルスキャンオブジェクト。
        main_window (MainWindow): メインウィンドウのUIオブジェクト。
        is_private_mode (bool): プライベートモードが有効かどうかの状態。
    """

    def __init__(self):
        """ApplicationControllerのコンストラクタ。"""
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()

        self.rule_loader = ParsingRuleLoader(rules_path="config/parsing_rules.json")
        self.parser = FileNameParser(self.rule_loader.load_rules())
        
        self.scanner = FileScanner(self.db_manager, self.parser)
        self.main_window = MainWindow()
        self.is_private_mode = False

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
        """パスワード認証を行い、成功すれば設定ウィンドウを開く。

        パスワードが未設定の場合は、設定を促すダイアログを表示する。
        """
        stored_hash = self.db_manager.get_setting('password_hash')

        if not stored_hash:
            QMessageBox.information(self.main_window, "パスワード設定", "初回起動です。パスワードを設定してください。")
            set_password_dialog = PasswordDialog(self.main_window, mode="set_password")
            if set_password_dialog.exec():
                new_password = set_password_dialog.get_password()
                if new_password:
                    self.db_manager.set_setting('password_hash', hash_password(new_password))
                    QMessageBox.information(self.main_window, "成功", "パスワードが設定されました。")
                    self._open_settings_window_internal()
            else:
                QMessageBox.warning(self.main_window, "キャンセル", "パスワード設定がキャンセルされました。")
        else:
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
        scan_extensions = self.db_manager.get_setting('scan_extensions')
        settings_dialog.set_settings(scan_folders, exclude_folders, viewer_path, scan_extensions)

        if settings_dialog.exec():
            new_scan, new_exclude, new_viewer, new_extensions = settings_dialog.get_settings()
            self.db_manager.save_scan_folders(new_scan)
            self.db_manager.save_exclude_folders(new_exclude)
            self.db_manager.set_setting('viewer_path', new_viewer)
            self.db_manager.set_setting('scan_extensions', new_extensions)
            print("設定を保存しました。")

    def toggle_private_mode(self):
        """プライベートモードのオン/オフを切り替える。

        プライベートモードへ移行する際にはパスワード認証を要求する。
        """
        if self.is_private_mode:
            self.is_private_mode = False
            self.main_window.update_private_mode_view(is_private=self.is_private_mode)
            self.load_books_to_list()
        else:
            stored_hash = self.db_manager.get_setting('password_hash')
            if not stored_hash:
                QMessageBox.information(self.main_window, "パスワード未設定", "プライベートモードを使用するには、まず設定画面でパスワードを設定してください。")
                return

            auth_dialog = PasswordDialog(self.main_window, mode="authenticate")
            if auth_dialog.exec():
                entered_password = auth_dialog.get_password()
                if verify_password(stored_hash, entered_password):
                    self.is_private_mode = True
                    self.main_window.update_private_mode_view(is_private=self.is_private_mode)
                    self.load_books_to_list()
                else:
                    QMessageBox.warning(self.main_window, "認証失敗", "パスワードが正しくありません。")
            else:
                QMessageBox.information(self.main_window, "キャンセル", "認証がキャンセルされました。")

    def open_selected_book_in_viewer(self):
        """テーブルで選択されている書籍を外部ビューアで開く。"""
        book = self.main_window.get_selected_book()
        if not book:
            return

        viewer_path = self.db_manager.get_setting('viewer_path')
        if not viewer_path or not os.path.exists(viewer_path):
            QMessageBox.information(self.main_window, "ビューア未設定", "ビューアが設定されていないか、パスが無効です。設定画面で指定してください。")
            return

        if not book.file_path or not os.path.exists(book.file_path):
            QMessageBox.warning(self.main_window, "エラー", f"蔵書ファイルが見つかりません。\nパス: {book.file_path}")
            return

        try:
            subprocess.Popen([viewer_path, book.file_path])
        except Exception as e:
            QMessageBox.critical(self.main_window, "起動エラー", f"ビューアを起動できませんでした。\n{e}")

    def open_book_edit_dialog(self):
        """選択された書籍のメタデータを編集するダイアログを開く。"""
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
            self.db_manager.update_book(updated_book)
            self.load_books_to_list()
            QMessageBox.information(self.main_window, "成功", "書籍情報を更新しました。")

    def run_scan_and_refresh(self):
        """ファイルスキャンを実行し、UIを更新する。"""
        self.scanner.scan_folders()
        self.load_books_to_list()

    def load_books_to_list(self):
        """データベースから書籍を読み込み、UIテーブルに表示する。
        
        プライベートモードの状態に応じて、表示する書籍をフィルタリングする。
        """
        all_books = self.db_manager.get_all_books()
        books_to_display = all_books

        if not self.is_private_mode:
            scan_folders_data = self.db_manager.get_scan_folders()
            private_paths = {f['path'] for f in scan_folders_data if f.get('is_private', 0)}
            
            # 正規化して比較
            normalized_private_paths = {os.path.normpath(p) for p in private_paths}

            books_to_display = [b for b in all_books if not any(os.path.normpath(b.file_path).startswith(p) for p in normalized_private_paths)]

        self.main_window.display_books(books_to_display)
        self.load_column_settings()

    def run(self):
        """アプリケーションのメインループを開始する。"""
        self.main_window.show()
        self.load_books_to_list()

    def load_column_settings(self):
        """保存された列の表示状態と幅を読み込み、テーブルに適用する。"""
        visibility_json = self.db_manager.get_setting('column_visibility')
        widths_json = self.db_manager.get_setting('column_widths')
        
        settings = {}
        if visibility_json:
            try:
                settings['visibility'] = json.loads(visibility_json)
            except json.JSONDecodeError:
                pass # エラーでも続行
        if widths_json:
            try:
                settings['widths'] = json.loads(widths_json)
            except json.JSONDecodeError:
                pass # エラーでも続行
        
        if settings:
            self.main_window.apply_column_settings(settings)

    def save_column_settings(self):
        """現在のテーブルの列の表示状態と幅をデータベースに保存する。"""
        settings = self.main_window.get_column_settings()
        visibility_json = json.dumps(settings['visibility'])
        widths_json = json.dumps(settings['widths'])
        
        self.db_manager.set_setting('column_visibility', visibility_json)
        self.db_manager.set_setting('column_widths', widths_json)

def main():
    """アプリケーションのメインエントリーポイント。

    QApplicationを作成し、コントローラーを初期化してアプリケーションを実行します。
    終了時に設定を保存する処理も接続します。
    """
    app = QApplication(sys.argv)
    font = QFont("Yu Gothic UI", 12)
    font.setStyleHint(QFont.StyleHint.System)
    app.setFont(font)
    
    controller = ApplicationController()
    app.aboutToQuit.connect(controller.save_column_settings)

    controller.run()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
