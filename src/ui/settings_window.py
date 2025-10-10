# -*- coding: utf-8 -*-
import sys
from typing import List, Dict, Tuple, Optional
from PyQt6.QtCore import QStringListModel, Qt
from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLineEdit, QListView, QLabel, QGroupBox, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem

class SettingsWindow(QDialog):
    """設定画面のウィンドウ。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.setMinimumWidth(600)

        main_layout = QVBoxLayout(self)

        # --- フォルダ管理 --- #
        folder_group = QGroupBox("フォルダ管理")
        folder_layout = QVBoxLayout()
        folder_group.setLayout(folder_layout)
        main_layout.addWidget(folder_group)

        folder_layout.addWidget(QLabel("スキャン対象フォルダ"))
        scan_layout = QHBoxLayout()
        self.scan_list_view = QListView()
        self.scan_list_model = QStandardItemModel() # QStringListModelから変更
        self.scan_list_view.setModel(self.scan_list_model)
        scan_layout.addWidget(self.scan_list_view)
        scan_buttons = QVBoxLayout()
        add_scan_btn = QPushButton("追加")
        remove_scan_btn = QPushButton("削除")
        add_scan_btn.clicked.connect(self.add_scan_folder)
        remove_scan_btn.clicked.connect(self.remove_scan_folder)
        scan_buttons.addWidget(add_scan_btn)
        scan_buttons.addWidget(remove_scan_btn)
        scan_buttons.addStretch()
        scan_layout.addLayout(scan_buttons)
        folder_layout.addLayout(scan_layout)

        folder_layout.addWidget(QLabel("除外フォルダ"))
        exclude_layout = QHBoxLayout()
        self.exclude_list_view = QListView()
        self.exclude_list_model = QStringListModel()
        self.exclude_list_view.setModel(self.exclude_list_model)
        exclude_layout.addWidget(self.exclude_list_view)
        exclude_buttons = QVBoxLayout()
        add_exclude_btn = QPushButton("追加")
        remove_exclude_btn = QPushButton("削除")
        add_exclude_btn.clicked.connect(self.add_exclude_folder)
        remove_exclude_btn.clicked.connect(self.remove_exclude_folder)
        exclude_buttons.addWidget(add_exclude_btn)
        exclude_buttons.addWidget(remove_exclude_btn)
        exclude_buttons.addStretch()
        exclude_layout.addLayout(exclude_buttons)
        folder_layout.addLayout(exclude_layout)

        # --- スキャン設定 --- #
        scan_settings_group = QGroupBox("スキャン設定")
        scan_settings_layout = QVBoxLayout()
        scan_settings_group.setLayout(scan_settings_layout)
        main_layout.addWidget(scan_settings_group)

        scan_settings_layout.addWidget(QLabel("対象拡張子 (カンマ区切り): "))
        self.scan_extensions_input = QLineEdit()
        self.scan_extensions_input.setPlaceholderText("例: zip,cbz,rar")
        scan_settings_layout.addWidget(self.scan_extensions_input)

        # --- ビューア設定 --- #
        viewer_group = QGroupBox("ビューア設定")
        viewer_layout = QHBoxLayout()
        self.viewer_path_input = QLineEdit()
        browse_viewer_btn = QPushButton("参照")
        browse_viewer_btn.clicked.connect(self.browse_viewer_path)
        viewer_layout.addWidget(self.viewer_path_input)
        viewer_layout.addWidget(browse_viewer_btn)
        viewer_group.setLayout(viewer_layout)
        main_layout.addWidget(viewer_group)

        # --- セキュリティ設定 --- #
        security_group = QGroupBox("セキュリティ")
        security_layout = QHBoxLayout()
        self.change_password_btn = QPushButton("パスワード変更")
        security_layout.addWidget(self.change_password_btn)
        security_group.setLayout(security_layout)
        main_layout.addWidget(security_group)

        # --- 保存/キャンセル --- #
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        save_button = QPushButton("保存")
        cancel_button = QPushButton("キャンセル")
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

    def add_scan_folder(self):
        path = QFileDialog.getExistingDirectory(self, "スキャン対象フォルダを選択")
        if path:
            item = QStandardItem(path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked) # デフォルトは非プライベート
            self.scan_list_model.appendRow(item)

    def remove_scan_folder(self):
        for index in self.scan_list_view.selectedIndexes():
            self.scan_list_model.removeRow(index.row())

    def add_exclude_folder(self):
        path = QFileDialog.getExistingDirectory(self, "除外フォルダを選択")
        if path:
            self.exclude_list_model.insertRow(self.exclude_list_model.rowCount())
            self.exclude_list_model.setData(self.exclude_list_model.index(self.exclude_list_model.rowCount() - 1), path)

    def remove_exclude_folder(self):
        for index in self.exclude_list_view.selectedIndexes():
            self.exclude_list_model.removeRow(index.row())

    def browse_viewer_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "ビューアを選択")
        if path:
            self.viewer_path_input.setText(path)

    def set_settings(self, scan_folders: List[Dict], exclude_folders: List[Dict], viewer_path: str, scan_extensions: str):
        self.scan_list_model.clear() # モデルをクリア
        for folder in scan_folders:
            item = QStandardItem(folder['path'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if folder.get('is_private', 0) == 1 else Qt.CheckState.Unchecked)
            self.scan_list_model.appendRow(item)

        self.exclude_list_model.setStringList([f['path'] for f in exclude_folders])
        self.viewer_path_input.setText(viewer_path or "")
        self.scan_extensions_input.setText(scan_extensions or "")

    def get_settings(self) -> Tuple[List[Dict], List[Dict], str, str]:
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

class PasswordDialog(QDialog):
    """パスワード入力ダイアログ。"""
    def __init__(self, parent=None, mode: str = "authenticate"):
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle("パスワード認証" if mode == "authenticate" else "パスワード設定")
        
        main_layout = QVBoxLayout(self)

        if self.mode == "authenticate":
            main_layout.addWidget(QLabel("パスワードを入力してください:"))
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            main_layout.addWidget(self.password_input)
        elif self.mode == "set_password":
            main_layout.addWidget(QLabel("新しいパスワードを入力してください:"))
            self.new_password_input = QLineEdit()
            self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            main_layout.addWidget(self.new_password_input)

            main_layout.addWidget(QLabel("新しいパスワード (確認):"))
            self.confirm_password_input = QLineEdit()
            self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            main_layout.addWidget(self.confirm_password_input)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK" if mode == "authenticate" else "設定")
        cancel_button = QPushButton("キャンセル")
        ok_button.clicked.connect(self._handle_ok_button)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

    def _handle_ok_button(self):
        if self.mode == "authenticate":
            self.accept()
        elif self.mode == "set_password":
            if self.validate_password_input():
                self.accept()

    def validate_password_input(self) -> bool:
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
        if self.mode == "authenticate":
            return self.password_input.text()
        elif self.mode == "set_password":
            return self.new_password_input.text()
        return None
