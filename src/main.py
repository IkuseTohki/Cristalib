# -*- coding: utf-8 -*-
"""アプリケーションのエントリーポイントとメインコントローラー。

ApplicationControllerクラスが、UI、データベース、ファイルスキャナー間の
やり取りを制御し、アプリケーション全体の動作を管理します。
"""
import sys
import os
import subprocess
import json
from typing import Optional
from PyQt6.QtCore import QModelIndex, Qt, QThread, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog, QFileDialog
from PyQt6.QtGui import QFont
from src.ui.main_window import MainWindow
from src.ui.settings_window import SettingsWindow, PasswordDialog
from src.ui.book_edit_dialog import BookEditDialog
from src.core.database import DatabaseManager
from src.core.security import hash_password, verify_password
from src.core.scanner import FileScanner
from src.core.parser import ParsingRuleLoader, FileNameParser
from src.models.book import Book
from src.ui.interfaces import IMainWindow, IApplicationController, ISettingsWindow, IBookEditDialog, IDialogFactory
from src.ui.dialog_factory import DialogFactory


class ScannerWorker(QObject):
    """FileScannerの処理を別スレッドで実行するためのワーカー。"""
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, scanner: FileScanner, parent=None):
        """ScannerWorkerのコンストラクタ。

        Args:
            scanner (FileScanner): FileScannerのインスタンス。
            parent (QObject, optional): 親オブジェクト。Defaults to None.
        """
        super().__init__(parent)
        self._scanner = scanner
        # ラムダ式を挟むことで、シグナルの引数型変換の問題を回避
        self._scanner.progress.connect(lambda msg: self.progress.emit(str(msg)))
        self._scanner.finished.connect(self.finished.emit)

    def run(self):
        """FileScannerのscan_foldersメソッドを実行する。"""
        self._scanner.scan_folders()


class ApplicationController(IApplicationController):
    """アプリケーション全体のロジックを管理するコントローラー。

    Attributes:
        db_manager (DatabaseManager): データベース管理オブジェクト。
        rule_loader (ParsingRuleLoader): 解析ルール読み込みオブジェクト。
        parser (FileNameParser): ファイル名解析オブジェクト。
        scanner (FileScanner): ファイルスキャンオブジェクト。
        main_window (IMainWindow): メインウィンドウのUIインターフェース。
        settings_window (ISettingsWindow): 設定ウィンドウのUIインターフェース。
        dialog_factory (IDialogFactory): ダイアログ生成ファクトリのインターフェース。
        is_private_mode (bool): プライベートモードが有効かどうかの状態。
    """

    def __init__(self, main_window_view: IMainWindow,
                 settings_window_view: ISettingsWindow,
                 dialog_factory: IDialogFactory):
        """ApplicationControllerのコンストラクタ。

        Args:
            main_window_view (IMainWindow): メインウィンドウのViewインターフェース。
            settings_window_view (ISettingsWindow): 設定ウィンドウのViewインターフェース。
            dialog_factory (IDialogFactory): ダイアログファクトリのインターフェース。
        """
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()

        self.rule_loader = ParsingRuleLoader(rules_path="config/parsing_rules.json")
        self.parser = FileNameParser(self.rule_loader.load_rules())
        
        self.scanner = FileScanner(self.db_manager, self.parser)
        self.main_window = main_window_view
        self.settings_window = settings_window_view
        self.dialog_factory = dialog_factory
        self.is_private_mode = False

        self.worker_thread = None
        self.current_scanner_worker = None

        self.connect_signals()

    def connect_signals(self):
        """UIのシグナルとロジックのスロットを接続する。"""
        # Viewの抽象シグナルに接続
        self.main_window.settings_requested.connect(self.authenticate_and_open_settings)
        self.main_window.private_mode_toggled.connect(self.toggle_private_mode)
        self.main_window.sync_requested.connect(self.run_scan_and_refresh)
        self.main_window.viewer_requested.connect(self.open_selected_book_in_viewer)
        self.main_window.edit_book_requested.connect(self.open_book_edit_dialog)
        self.main_window.book_double_clicked.connect(self.open_selected_book_in_viewer)
        # 設定ウィンドウ関連のシグナル
        self.settings_window.save_settings_requested.connect(self._save_settings)
        self.settings_window.change_password_requested.connect(self.change_password)
        self.settings_window.add_scan_path_requested.connect(self._add_scan_path)
        self.settings_window.remove_scan_path_requested.connect(self._remove_scan_path)
        self.settings_window.add_exclude_path_requested.connect(self._add_exclude_path)
        self.settings_window.remove_exclude_path_requested.connect(self._remove_exclude_path)
        self.settings_window.browse_viewer_path_requested.connect(self._browse_viewer_path)

    def authenticate_and_open_settings(self):
        """設定画面を開く前に認証を行う。"""
        password_hash = self.db_manager.get_setting('password_hash')

        # --- パスワードが設定されているか確認 ---
        if password_hash:
            # 認証ダイアログを表示
            password_dialog = self.dialog_factory.create_password_dialog()
            password_dialog.set_mode('authenticate')
            if password_dialog.exec() == QDialog.DialogCode.Accepted:
                password = password_dialog.get_password()
                if verify_password(password_hash, password):
                    self._open_settings_window() # 認証成功
                else:
                    QMessageBox.warning(None, "認証エラー", "パスワードが正しくありません。")
            return # キャンセルされた場合も何もしない
        
        # --- パスワードが未設定の場合（初回設定） ---
        reply = QMessageBox.information(None, "初回パスワード設定", 
                                        "設定画面を保護するためのパスワードを初回設定します。",
                                        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        
        if reply == QMessageBox.StandardButton.Ok:
            password_dialog = self.dialog_factory.create_password_dialog()
            password_dialog.set_mode('set_password')
            if password_dialog.exec() == QDialog.DialogCode.Accepted:
                new_password = password_dialog.get_password()
                # _update_password_in_dbを直接呼び出す
                if self._update_password_in_db("", new_password):
                    self._open_settings_window() # 初回設定成功後に設定画面を開く

    def _open_settings_window(self):
        """認証後に設定ウィンドウを準備して表示する。"""
        settings = {
            'scan_folders': self.db_manager.get_scan_folders(),
            'exclude_folders': self.db_manager.get_exclude_folders(),
            'viewer_path': self.db_manager.get_setting('viewer_path'),
            'scan_extensions': self.db_manager.get_setting('scan_extensions')
        }
        self.settings_window.display_settings(settings)
        self.settings_window.show()

    def _save_settings(self):
        """設定ウィンドウから取得した設定をデータベースに保存する。"""
        settings = self.settings_window.get_settings()
        self.db_manager.save_scan_folders(settings['scan_folders'])
        self.db_manager.save_exclude_folders(settings['exclude_folders'])
        self.db_manager.set_setting('viewer_path', settings['viewer_path'])
        self.db_manager.set_setting('scan_extensions', settings['scan_extensions'])
        self.settings_window.close()
        # 設定変更後に書籍リストを再読み込みするなどの処理が必要であればここに追加

    def toggle_private_mode(self):
        """プライベートモードの切り替えを処理する。認証を伴う場合がある。"""
        # プライベートモードから通常モードへの切り替え (認証不要)
        if self.is_private_mode:
            self.is_private_mode = False

        # 通常モードからプライベートモードへの切り替え (認証が必要な場合がある)
        else:
            if not self._can_enter_private_mode():
                return # プライベートモードへ移行できない場合は処理を中断
            self.is_private_mode = True

        # UIの更新とリストの再読み込み
        self.main_window.update_private_mode_view(self.is_private_mode)
        self.load_books_to_list()

    def run_scan_and_refresh(self):
        """ファイルスキャンを非同期で実行し、リストを更新する。"""
        self.main_window.set_sync_button_enabled(False)
        self.main_window.show_status_message("スキャン準備中...")

        # 既にスキャンが実行中の場合は何もしない
        if self.worker_thread and self.worker_thread.isRunning():
            self.main_window.show_status_message("スキャンは既に実行中です。")
            self.main_window.set_sync_button_enabled(True)
            return

        self.worker_thread = QThread()
        self.current_scanner_worker = ScannerWorker(self.scanner)  # 新しいScannerWorkerを作成
        self.current_scanner_worker.moveToThread(self.worker_thread)

        # シグナルとスロットを接続
        self.worker_thread.started.connect(self.current_scanner_worker.run)
        self.current_scanner_worker.progress.connect(self.main_window.show_status_message)
        self.current_scanner_worker.finished.connect(self._on_scan_finished)

        self.worker_thread.start()

    def _on_scan_finished(self):
        """スキャン完了後に呼び出されるスロット。"""
        self.main_window.show_status_message("スキャン完了。リストを更新しています...")
        self.load_books_to_list()
        self.main_window.show_status_message("更新完了")
        self.main_window.set_sync_button_enabled(True)

        # スレッドとワーカーをクリーンアップ
        if self.worker_thread is not None:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread.deleteLater()  # スレッドオブジェクトを適切に破棄
            self.worker_thread = None
        if self.current_scanner_worker is not None:
            self.current_scanner_worker.deleteLater()  # ワーカーオブジェクトを適切に破棄
            self.current_scanner_worker = None

    def open_selected_book_in_viewer(self, index=None):
        """選択された書籍を外部ビューアで開く。

        Args:
            index (QModelIndex, optional): 選択されたアイテムのインデックス。
                                           通常はmain_windowから取得するためNoneでよい。
        """
        book = self.main_window.get_selected_book()
        if not book:
            self.main_window.show_status_message("書籍が選択されていません。")
            return

        viewer_path = self.db_manager.get_setting('viewer_path')
        if not viewer_path or not os.path.exists(viewer_path):
            QMessageBox.warning(None, "ビューア未設定", "ビューアのパスが設定されていないか、パスが無効です。\n設定画面から設定してください。")
            return

        if not book.file_path or not os.path.exists(book.file_path):
            QMessageBox.warning(None, "ファイルエラー", f"書籍ファイルが見つかりません。\nパス: {book.file_path}")
            return

        try:
            subprocess.Popen([viewer_path, book.file_path])
            self.main_window.show_status_message(f"ビューアで {os.path.basename(book.file_path)} を開きました。")
        except Exception as e:
            QMessageBox.critical(None, "起動エラー", f"ビューアの起動に失敗しました。\nエラー: {e}")

    def open_book_edit_dialog(self, index=None):
        """書籍編集ダイアログを開く。

        Args:
            index (QModelIndex, optional): 選択されたアイテムのインデックス。
                                           通常はmain_windowから取得するためNoneでよい。
        """
        book = self.main_window.get_selected_book()
        if not book:
            QMessageBox.information(None, "情報", "書籍が選択されていません。")
            return

        latest_book_data = self.db_manager.get_book_by_id(book.id)
        if not latest_book_data:
            QMessageBox.warning(None, "エラー", "データベースから書籍情報を取得できませんでした。")
            return

        book_edit_dialog = self.dialog_factory.create_book_edit_dialog()
        book_edit_dialog.display_book_data(latest_book_data)
        if book_edit_dialog.exec() == QDialog.DialogCode.Accepted:
            updated_book = book_edit_dialog.get_book_data()
            self.db_manager.update_book(updated_book)
            self.load_books_to_list() # リストを更新

    def save_column_settings(self):
        """カラム設定をJSON形式でデータベースに保存する。"""
        try:
            settings = self.main_window.get_column_settings()
            settings_json = json.dumps(settings)
            self.db_manager.set_setting('column_settings', settings_json)
            self.main_window.show_status_message("列設定を保存しました。")
        except Exception as e:
            self.main_window.show_status_message(f"列設定の保存に失敗しました: {e}")

    def run(self):
        """アプリケーションの実行を開始する。"""
        self.main_window.show()
        self.main_window.update_private_mode_view(self.is_private_mode)  # ボタンの初期表示を更新
        self.load_books_to_list()
        self._load_column_settings()  # 起動時に列設定を読み込む

    def _load_column_settings(self):
        """データベースから列設定を読み込み、適用する。"""
        try:
            settings_json = self.db_manager.get_setting('column_settings')
            if settings_json:
                settings = json.loads(settings_json)
                self.main_window.apply_column_settings(settings)
                self.main_window.show_status_message("列設定を復元しました。")
        except Exception as e:
            self.main_window.show_status_message(f"列設定の復元に失敗しました: {e}")

    def load_books_to_list(self):
        """書籍リストをロードする。"""
        books = self.db_manager.get_books_for_display(private_mode=self.is_private_mode)
        self.main_window.display_books(books)

    def _update_password_in_db(self, old_password: str, new_password: str) -> bool:
        """パスワードのハッシュ化とデータベースへの保存を行うヘルパーメソッド。

        Args:
            old_password (str): 現在のパスワード。
            new_password (str): 新しいパスワード。

        Returns:
            bool: パスワードの更新が成功した場合はTrue、失敗した場合はFalse。
        """
        current_hash = self.db_manager.get_setting('password_hash')

        if not new_password:
            QMessageBox.warning(None, "パスワードエラー", "新しいパスワードは空にできません。")
            return False

        # パスワードが設定済みの場合、古いパスワードを検証
        if current_hash:
            if not verify_password(current_hash, old_password):
                QMessageBox.warning(None, "認証エラー", "古いパスワードが正しくありません。")
                return False

        # 新しいパスワードをハッシュ化して保存
        try:
            new_hash = hash_password(new_password)
            self.db_manager.set_setting('password_hash', new_hash)
            QMessageBox.information(None, "成功", "パスワードが正常に設定されました。")
            return True
        except Exception as e:
            QMessageBox.critical(None, "エラー", f"パスワードの設定に失敗しました。\n{e}")
            return False

    def change_password(self):
        """パスワード変更ダイアログを表示し、パスワードの変更処理を調整する。"""
        current_hash = self.db_manager.get_setting('password_hash')
        old_password = ""
        new_password = ""

        # パスワードが設定済みの場合、まず古いパスワードの認証を求める
        if current_hash:
            password_dialog = self.dialog_factory.create_password_dialog()
            password_dialog.set_mode('authenticate')
            if password_dialog.exec() == QDialog.DialogCode.Accepted:
                old_password = password_dialog.get_password()
                # ここではverify_passwordは呼ばない。_update_password_in_dbで検証される
            else:
                return # キャンセルされたら終了
        
        # 新しいパスワードの設定を求める
        password_dialog = self.dialog_factory.create_password_dialog()
        password_dialog.set_mode('set_password')
        if password_dialog.exec() == QDialog.DialogCode.Accepted:
            new_password = password_dialog.get_password()
        else:
            return # キャンセルされたら終了

        # 実際のパスワード更新処理を呼び出す
        self._update_password_in_db(old_password, new_password)

    def _can_enter_private_mode(self) -> bool:
        """プライベートモードへ移行可能か（認証が必要な場合は認証成功したか）を判定する。

        Returns:
            bool: プライベートモードへ移行可能な場合はTrue、そうでない場合はFalse。
        """
        password_hash = self.db_manager.get_setting('password_hash')
        
        # パスワードが設定されていなければ認証不要
        if not password_hash:
            return True

        # パスワードが設定されていれば認証を行う
        password_dialog = self.dialog_factory.create_password_dialog()
        password_dialog.set_mode('authenticate')
        if password_dialog.exec() != QDialog.DialogCode.Accepted:
            return False # キャンセルされたら認証失敗
        
        password = password_dialog.get_password()
        if not verify_password(password_hash, password):
            QMessageBox.warning(None, "認証エラー", "パスワードが正しくありません。")
            return False # 認証失敗
        
        return True # 認証成功

    def _open_folder_dialog(self, caption: str) -> Optional[str]:
        """フォルダ選択ダイアログを開き、選択されたフォルダパスを返すヘルパーメソッド。

        Args:
            caption (str): ダイアログのタイトル。

        Returns:
            Optional[str]: 選択されたフォルダの絶対パス。キャンセルされた場合はNone。
        """
        folder_path = QFileDialog.getExistingDirectory(None, caption)
        return folder_path if folder_path else None

    def _open_file_dialog(self, caption: str, filter: str) -> Optional[str]:
        """ファイル選択ダイアログを開き、選択されたファイルパスを返すヘルパーメソッド。

        Args:
            caption (str): ダイアログのタイトル。
            filter (str): ファイルフィルタ（例: "Images (*.png *.jpg);;Text files (*.txt)"）。

        Returns:
            Optional[str]: 選択されたファイルの絶対パス。キャンセルされた場合はNone。
        """
        file_path, _ = QFileDialog.getOpenFileName(None, caption, "", filter)
        return file_path if file_path else None

    def _add_scan_path(self):
        """スキャン対象フォルダを追加する。"""
        folder_path = self._open_folder_dialog("スキャン対象フォルダを選択")
        if folder_path:
            # 現在の設定を取得し、新しいパスを追加してUIを更新
            current_settings = self.settings_window.get_settings()
            scan_folders = current_settings.get('scan_folders', [])
            # 重複チェック
            if not any(f['path'] == folder_path for f in scan_folders):
                scan_folders.append({'path': folder_path, 'is_private': 0})
                current_settings['scan_folders'] = scan_folders
                self.settings_window.display_settings(current_settings)
            else:
                QMessageBox.information(None, "情報", "選択されたフォルダは既に追加されています。")

    def _remove_scan_path(self):
        """スキャン対象フォルダを削除する。"""
        selected_paths = self.settings_window.get_selected_scan_paths()
        if not selected_paths:
            QMessageBox.information(None, "情報", "削除するスキャン対象フォルダを選択してください。")
            return

        current_settings = self.settings_window.get_settings()
        scan_folders = current_settings.get('scan_folders', [])
        
        # 選択されたパスを除外した新しいリストを作成
        updated_scan_folders = [f for f in scan_folders if f['path'] not in selected_paths]
        current_settings['scan_folders'] = updated_scan_folders
        self.settings_window.display_settings(current_settings)

    def _add_exclude_path(self):
        """除外対象フォルダを追加する。"""
        folder_path = self._open_folder_dialog("除外対象フォルダを選択")
        if folder_path:
            current_settings = self.settings_window.get_settings()
            exclude_folders = current_settings.get('exclude_folders', [])
            if not any(f['path'] == folder_path for f in exclude_folders):
                exclude_folders.append({'path': folder_path})
                current_settings['exclude_folders'] = exclude_folders
                self.settings_window.display_settings(current_settings)
            else:
                QMessageBox.information(None, "情報", "選択されたフォルダは既に追加されています。")

    def _remove_exclude_path(self):
        """除外対象フォルダを削除する。"""
        selected_paths = self.settings_window.get_selected_exclude_paths()
        if not selected_paths:
            QMessageBox.information(None, "情報", "削除する除外対象フォルダを選択してください。")
            return

        current_settings = self.settings_window.get_settings()
        exclude_folders = current_settings.get('exclude_folders', [])

        # 選択されたパスを除外した新しいリストを作成
        updated_exclude_folders = [f for f in exclude_folders if f['path'] not in selected_paths]
        current_settings['exclude_folders'] = updated_exclude_folders
        self.settings_window.display_settings(current_settings)

    def _browse_viewer_path(self):
        """外部ビューアのパスを参照する。"""
        file_path = self._open_file_dialog("外部ビューアを選択", "実行ファイル (*.exe);;すべてのファイル (*.*)")
        if file_path:
            current_settings = self.settings_window.get_settings()
            current_settings['viewer_path'] = file_path
            self.settings_window.display_settings(current_settings)

def main():
    """アプリケーションのメインエントリーポイント。

    QApplicationを作成し、コントローラーを初期化してアプリケーションを実行します。
    終了時に設定を保存する処理も接続します。
    """
    app = QApplication(sys.argv)
    font = QFont("Yu Gothic UI", 12)
    font.setStyleHint(QFont.StyleHint.System)
    app.setFont(font)

    main_window_instance = MainWindow()
    settings_window_instance = SettingsWindow()
    dialog_factory_instance = DialogFactory()

    controller = ApplicationController(
        main_window_view=main_window_instance,
        settings_window_view=settings_window_instance,
        dialog_factory=dialog_factory_instance
    )
    app.aboutToQuit.connect(controller.save_column_settings)

    controller.run()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
