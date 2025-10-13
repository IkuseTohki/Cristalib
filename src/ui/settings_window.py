# -*- coding: utf-8 -*-
"""アプリケーションの設定ウィンドウとパスワードダイアログを定義します。

- SettingsWindow: スキャンフォルダ、除外フォルダ、ビューアパスなどの
                  アプリケーション設定を行うUIを提供します。
- PasswordDialog: パスワードの認証や新規設定を行うためのUIを提供します。
"""
from typing import List, Dict, Tuple, Optional, Any
from PyQt6.QtCore import QStringListModel, Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog, QWidget, QFileDialog, QMessageBox
from PyQt6.QtGui import QStandardItemModel, QStandardItem

from .base.ui_settings_window import Ui_SettingsWindow
from .base.ui_password_dialog import Ui_PasswordDialog
from .interfaces import ISettingsWindow, IPasswordDialog


class SettingsWindow(QDialog, Ui_SettingsWindow, ISettingsWindow):
    """設定画面のウィンドウ。

    UIのロジックとPresenterとの連携を担当します。
    UIのレイアウト定義はUi_SettingsWindowクラスに分離されています。
    """
    # ISettingsWindowで定義された抽象シグナルを実装
    save_settings_requested = pyqtSignal()
    change_password_requested = pyqtSignal()
    add_scan_path_requested = pyqtSignal()
    remove_scan_path_requested = pyqtSignal()
    add_exclude_path_requested = pyqtSignal()
    remove_exclude_path_requested = pyqtSignal()
    browse_viewer_path_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        """SettingsWindowのコンストラクタ。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。Defaults to None.
        """
        super().__init__(parent)
        self.setupUi(self)

        # --- モデルのセットアップ ---
        self.scan_list_model = QStandardItemModel()
        self.scan_list_view.setModel(self.scan_list_model)
        self.exclude_list_model = QStringListModel()
        self.exclude_list_view.setModel(self.exclude_list_model)

        # --- シグナルの接続 ---
        self.save_button.clicked.connect(self.save_settings_requested.emit)
        self.cancel_button.clicked.connect(self.close)
        self.change_password_btn.clicked.connect(self.change_password_requested.emit)
        self.add_scan_btn.clicked.connect(self.add_scan_path_requested.emit)
        self.remove_scan_btn.clicked.connect(self.remove_scan_path_requested.emit)
        self.add_exclude_btn.clicked.connect(self.add_exclude_path_requested.emit)
        self.remove_exclude_btn.clicked.connect(self.remove_exclude_path_requested.emit)
        self.browse_viewer_btn.clicked.connect(self.browse_viewer_path_requested.emit)

        self.adjustSize()  # ウィジェットのサイズを調整

    def display_settings(self, settings: Dict[str, Any]):
        """設定情報をUIに表示する。

        Args:
            settings (Dict[str, Any]): 表示する設定情報を含む辞書。
        """
        scan_folders = settings.get('scan_folders', [])
        exclude_folders = settings.get('exclude_folders', [])
        viewer_path = settings.get('viewer_path', '')
        scan_extensions = settings.get('scan_extensions', '')

        self.scan_list_model.clear()
        for folder in scan_folders:
            item = QStandardItem(folder['path'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if folder.get('is_private', 0) == 1 else Qt.CheckState.Unchecked)
            self.scan_list_model.appendRow(item)

        self.exclude_list_model.setStringList([f['path'] for f in exclude_folders])
        self.viewer_path_input.setText(viewer_path or "")
        self.scan_extensions_input.setText(scan_extensions or "")

    def get_settings(self) -> Dict[str, Any]:
        """UIから現在の設定値を取得する。

        Returns:
            Dict[str, Any]: 現在の設定値を含む辞書。
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

        return {
            'scan_folders': scan_folders,
            'exclude_folders': exclude_folders,
            'viewer_path': viewer_path,
            'scan_extensions': scan_extensions
        }

    def display_scan_paths(self, scan_paths: List[str]):
        """スキャンパスのリストをUIに表示する。

        Args:
            scan_paths (List[str]): 表示するスキャンパスのリスト。
        """
        self.scan_list_model.clear()
        for path in scan_paths:
            item = QStandardItem(path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked) # デフォルトはUnchecked
            self.scan_list_model.appendRow(item)

    def get_scan_paths(self) -> List[str]:
        """UIから現在のスキャンパスのリストを取得する。

        Returns:
            List[str]: 現在のスキャンパスのリスト。
        """
        scan_paths = []
        for row in range(self.scan_list_model.rowCount()):
            item = self.scan_list_model.item(row)
            scan_paths.append(item.text())
        return scan_paths

    def get_selected_scan_paths(self) -> List[str]:
        """UIから選択されているスキャンパスのリストを取得する。

        Returns:
            List[str]: 選択されているスキャンパスのリスト。
        """
        selected_paths = []
        for index in self.scan_list_view.selectedIndexes():
            item = self.scan_list_model.itemFromIndex(index)
            if item:
                selected_paths.append(item.text())
        return selected_paths

    def get_selected_exclude_paths(self) -> List[str]:
        """UIから選択されている除外パスのリストを取得する。

        Returns:
            List[str]: 選択されている除外パスのリスト。
        """
        selected_paths = []
        for index in self.exclude_list_view.selectedIndexes():
            path = self.exclude_list_model.data(index, Qt.ItemDataRole.DisplayRole)
            if path:
                selected_paths.append(path)
        return selected_paths

    def show(self):
        """設定ウィンドウを表示する。"""
        super().show()

    def close(self):
        """設定ウィンドウを閉じる。"""
        super().close()


class PasswordDialog(QDialog, Ui_PasswordDialog, IPasswordDialog):
    """パスワード入力または設定を行うダイアログ。

    'authenticate'モードと'set_password'モードに応じてUIと動作を切り替えます。
    """
    def __init__(self, parent: Optional[QWidget] = None):
        """PasswordDialogのコンストラクタ。

        Args:
            parent (Optional[QWidget]): 親ウィジェット。Defaults to None.
        """
        super().__init__(parent)
        self.setupUi(self)
        self.set_mode('authenticate')  # 初期モードはauthenticateとする
        self._password_on_accept = None  # 入力されたパスワードを一時的に保持

        # --- シグナルの接続 ---
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

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
        return self._password_on_accept

    def clear_input_fields(self):
        """パスワード入力欄をクリアする。"""
        self.password_input.clear()
        self.new_password_input.clear()
        self.confirm_password_input.clear()

    def set_mode(self, mode: str):
        """ダイアログのモードを設定し、表示ウィジェットを切り替える。

        Args:
            mode (str): ダイアログのモード ("authenticate" または "set_password")。
        """
        self.mode = mode
        if mode == "authenticate":
            self.setWindowTitle("パスワード認証")
            self.auth_widget.show()
            self.set_password_widget.hide()
            self.ok_button.setText("OK")
        elif mode == "set_password":
            self.setWindowTitle("パスワード設定")
            self.auth_widget.hide()
            self.set_password_widget.show()
            self.ok_button.setText("設定")
        self.adjustSize()

    def exec(self) -> bool:
        """ダイアログを表示し、結果をbool値で返す。

        Returns:
            bool: Acceptされた場合はTrue、それ以外はFalse。
        """
        result = super().exec()
        return result == QDialog.DialogCode.Accepted

    def accept(self):
        """OKボタンが押されたとき、またはEnterキーが押されたときに呼び出される。"""
        if self.mode == "set_password":
            if not self.validate_password_input():
                return  # 検証失敗ならダイアログを閉じない
            self._password_on_accept = self.new_password_input.text()
        elif self.mode == "authenticate":
            self._password_on_accept = self.password_input.text()
        super().accept()  # 検証成功、または認証モードならダイアログを閉じる
