# -*- coding: utf-8 -*-
"""
SettingsWindowのUI定義。
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListView, QLabel, QGroupBox
)

class Ui_SettingsWindow(object):
    """SettingsWindowのUI要素を定義するクラス。"""
    def setupUi(self, SettingsWindow: QDialog):
        """UIのセットアップを行う。

        Args:
            SettingsWindow (QDialog): UIを構築する対象のダイアログインスタンス。
        """
        SettingsWindow.setWindowTitle("設定")
        SettingsWindow.setMinimumWidth(600)

        main_layout = QVBoxLayout(SettingsWindow)

        # --- フォルダ管理 --- #
        folder_group = QGroupBox("フォルダ管理")
        folder_layout = QVBoxLayout()
        folder_group.setLayout(folder_layout)
        main_layout.addWidget(folder_group)

        folder_layout.addWidget(QLabel("スキャン対象フォルダ (チェックでプライベート設定)"))
        scan_layout = QHBoxLayout()
        self.scan_list_view = QListView()
        scan_layout.addWidget(self.scan_list_view)
        scan_buttons = QVBoxLayout()
        self.add_scan_btn = QPushButton("追加")
        self.remove_scan_btn = QPushButton("削除")
        scan_buttons.addWidget(self.add_scan_btn)
        scan_buttons.addWidget(self.remove_scan_btn)
        scan_buttons.addStretch()
        scan_layout.addLayout(scan_buttons)
        folder_layout.addLayout(scan_layout)

        folder_layout.addWidget(QLabel("除外フォルダ"))
        exclude_layout = QHBoxLayout()
        self.exclude_list_view = QListView()
        exclude_layout.addWidget(self.exclude_list_view)
        exclude_buttons = QVBoxLayout()
        self.add_exclude_btn = QPushButton("追加")
        self.remove_exclude_btn = QPushButton("削除")
        exclude_buttons.addWidget(self.add_exclude_btn)
        exclude_buttons.addWidget(self.remove_exclude_btn)
        exclude_buttons.addStretch()
        exclude_layout.addLayout(exclude_buttons)
        folder_layout.addLayout(exclude_layout)

        # --- スキャン設定 --- #
        scan_settings_group = QGroupBox("スキャン設定")
        scan_settings_layout = QVBoxLayout()
        scan_settings_group.setLayout(scan_settings_layout)
        main_layout.addWidget(scan_settings_group)

        scan_settings_layout.addWidget(QLabel("対象拡張子 (カンマ区切り):"))
        self.scan_extensions_input = QLineEdit()
        self.scan_extensions_input.setPlaceholderText("例: zip,cbz,rar")
        scan_settings_layout.addWidget(self.scan_extensions_input)

        # --- ビューア設定 --- #
        viewer_group = QGroupBox("ビューア設定")
        viewer_layout = QHBoxLayout()
        self.viewer_path_input = QLineEdit()
        self.browse_viewer_btn = QPushButton("参照")
        viewer_layout.addWidget(self.viewer_path_input)
        viewer_layout.addWidget(self.browse_viewer_btn)
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
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("キャンセル")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)