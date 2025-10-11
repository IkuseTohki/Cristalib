# -*- coding: utf-8 -*-
"""アプリケーションの設定ウィンドウとパスワードダイアログを定義します。

- SettingsWindow: スキャンフォルダ、除外フォルダ、ビューアパスなどの
                  アプリケーション設定を行うUIを提供します。
- PasswordDialog: パスワードの認証や新規設定を行うためのUIを提供します。
"""
from typing import List, Dict, Tuple, Optional, Callable
from PyQt6.QtCore import QStringListModel, Qt
from PyQt6.QtWidgets import QDialog, QWidget, QFileDialog, QMessageBox
from PyQt6.QtGui import QStandardItemModel, QStandardItem

from .base.ui_settings_window import Ui_SettingsWindow
from .base.ui_password_dialog import Ui_PasswordDialog


class SettingsWindow(QDialog, Ui_SettingsWindow):
    """設定画面のウィンドウ。

    UIのロジックとPresenterとの連携を担当します。
    UIのレイアウト定義はUi_SettingsWindowクラスに分離されています。
    """
    def __init__(self, parent: Optional[QWidget] = None, change_password_callback: Optional[Callable] = None):
        """SettingsWindowのコンストラクタ。

        Args:
            parent (Optional[QWidget], optional): 親ウィジェット。Defaults to None.
            change_password_callback (Optional[Callable], optional): パスワード変更ボタンが押されたときに呼び出されるコールバック関数。
        """
        super().__init__(parent)
        self.setupUi(self)

        # --- モデルのセットアップ ---
        self.scan_list_model = QStandardItemModel()
        self.scan_list_view.setModel(self.scan_list_model)
        self.exclude_list_model = QStringListModel()
        self.exclude_list_view.setModel(self.exclude_list_model)

        # --- シグナルの接続 ---
        self.add_scan_btn.clicked.connect(self.add_scan_folder)
        self.remove_scan_btn.clicked.connect(self.remove_scan_folder)
        self.add_exclude_btn.clicked.connect(self.add_exclude_folder)
        self.remove_exclude_btn.clicked.connect(self.remove_exclude_folder)
        self.browse_viewer_btn.clicked.connect(self.browse_viewer_path)
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        if change_password_callback:
            self.change_password_btn.clicked.connect(change_password_callback)

    def add_scan_folder(self):
        """「スキャン対象フォルダを追加」ボタンのアクション。"""
        path = QFileDialog.getExistingDirectory(self, "スキャン対象フォルダを選択")
        if path:
            item = QStandardItem(path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.scan_list_model.appendRow(item)

    def remove_scan_folder(self):
        """「スキャン対象フォルダを削除」ボタンのアクション。"""
        for index in self.scan_list_view.selectedIndexes():
            self.scan_list_model.removeRow(index.row())

    def add_exclude_folder(self):
        """「除外フォルダを追加」ボタンのアクション。"""
        path = QFileDialog.getExistingDirectory(self, "除外フォルダを選択")
        if path:
            self.exclude_list_model.insertRow(self.exclude_list_model.rowCount())
            self.exclude_list_model.setData(self.exclude_list_model.index(self.exclude_list_model.rowCount() - 1), path)

    def remove_exclude_folder(self):
        """「除外フォルダを削除」ボタンのアクション。"""
        for index in self.exclude_list_view.selectedIndexes():
            self.exclude_list_model.removeRow(index.row())

    def browse_viewer_path(self):
        """「ビューア参照」ボタンのアクション。"""
        path, _ = QFileDialog.getOpenFileName(self, "ビューアを選択")
        if path:
            self.viewer_path_input.setText(path)

    def set_settings(self, scan_folders: List[Dict], exclude_folders: List[Dict], viewer_path: str, scan_extensions: str):
        """既存の設定をダイアログに表示する。

        Args:
            scan_folders (List[Dict]): スキャン対象フォルダのリスト。
            exclude_folders (List[Dict]): 除外フォルダのリスト。
            viewer_path (str): ビューアのパス。
            scan_extensions (str): 対象拡張子のカンマ区切り文字列。
        """
        self.scan_list_model.clear()
        for folder in scan_folders:
            item = QStandardItem(folder['path'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if folder.get('is_private', 0) == 1 else Qt.CheckState.Unchecked)
            self.scan_list_model.appendRow(item)

        self.exclude_list_model.setStringList([f['path'] for f in exclude_folders])
        self.viewer_path_input.setText(viewer_path or "")
        self.scan_extensions_input.setText(scan_extensions or "")

    def get_settings(self) -> Tuple[List[Dict], List[Dict], str, str]:
        """ダイアログで設定された内容を取得する。

        Returns:
            Tuple[List[Dict], List[Dict], str, str]:
                スキャン対象フォルダ、除外フォルダ、ビューアパス、対象拡張子のタプル。
        """
        scan_folders = []
        for row in range(self.scan_list_model.rowCount()):
            item = self.scan_list_model.item(row)
            scan_folders.append({
                'path': item.text(),
                'is_private': 1 if item.checkState() == Qt.CheckState.Checked else 0
            })

        exclude_folders = [{'path': path} for path in self.exclude_list_model.stringList()]
        viewer_path = self.viewer_path_input.text()
        scan_extensions = self.scan_extensions_input.text()
        return scan_folders, exclude_folders, viewer_path, scan_extensions


class PasswordDialog(QDialog, Ui_PasswordDialog):
    """パスワード入力または設定を行うダイアログ。

    'authenticate'モードと'set_password'モードに応じてUIと動作を切り替えます。
    """
    def __init__(self, parent: Optional[QWidget] = None, mode: str = "authenticate"):
        """PasswordDialogのコンストラクタ。

        Args:
            parent (Optional[QWidget], optional): 親ウィジェット。Defaults to None.
            mode (str, optional): ダイアログのモード ('authenticate' or 'set_password')。
                                  Defaults to "authenticate".
        """
        super().__init__(parent)
        self.setupUi(self, mode)
        self.mode = mode

        # --- シグナルの接続 ---
        self.ok_button.clicked.connect(self._handle_ok_button)
        self.cancel_button.clicked.connect(self.reject)

    def _handle_ok_button(self):
        """OKボタンがクリックされたときの処理。"""
        if self.mode == "authenticate":
            self.accept()
        elif self.mode == "set_password":
            if self.validate_password_input():
                self.accept()

    def validate_password_input(self) -> bool:
        """パスワード設定時の入力値を検証する。

        Returns:
            bool: 検証が通ればTrue、そうでなければFalse。
        """
        if self.mode == "set_password":
            new_pass = self.new_password_input.text()
            confirm_pass = self.confirm_password_input.text()
            if not new_pass:
                QMessageBox.warning(self, "エラー", "パスワードを入力してください。")
                return False
            if new_pass != confirm_pass:
                QMessageBox.warning(self, "エラー", "パスワードが一致しません。")
                return False
        return True

    def get_password(self) -> Optional[str]:
        """入力されたパスワードを取得する。

        Returns:
            Optional[str]: 入力されたパスワード文字列。キャンセルされた場合はNone。
        """
        if self.mode == "authenticate":
            return self.password_input.text()
        elif self.mode == "set_password":
            return self.new_password_input.text()
        return None
