# -*- coding: utf-8 -*-
"""
PasswordDialogのUI定義。
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QWidget
)

class Ui_PasswordDialog(object):
    """PasswordDialogのUI要素を定義するクラス。"""
    def setupUi(self, PasswordDialog: QDialog):
        """UIのセットアップを行う。"""
        PasswordDialog.setWindowTitle("パスワード認証")
        main_layout = QVBoxLayout(PasswordDialog)

        # --- 認証モード用ウィジェット ---
        PasswordDialog.auth_widget = QWidget()
        auth_layout = QVBoxLayout(PasswordDialog.auth_widget)
        auth_layout.setContentsMargins(0, 0, 0, 0)
        auth_layout.addWidget(QLabel("パスワードを入力してください:"))
        PasswordDialog.password_input = QLineEdit()
        PasswordDialog.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        auth_layout.addWidget(PasswordDialog.password_input)
        main_layout.addWidget(PasswordDialog.auth_widget)

        # --- パスワード設定モード用ウィジェット ---
        PasswordDialog.set_password_widget = QWidget()
        set_password_layout = QVBoxLayout(PasswordDialog.set_password_widget)
        set_password_layout.setContentsMargins(0, 0, 0, 0)
        set_password_layout.addWidget(QLabel("新しいパスワードを入力してください:"))
        PasswordDialog.new_password_input = QLineEdit()
        PasswordDialog.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        set_password_layout.addWidget(PasswordDialog.new_password_input)
        set_password_layout.addWidget(QLabel("新しいパスワード (確認):"))
        PasswordDialog.confirm_password_input = QLineEdit()
        PasswordDialog.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        set_password_layout.addWidget(PasswordDialog.confirm_password_input)
        main_layout.addWidget(PasswordDialog.set_password_widget)

        # --- ボタン ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        PasswordDialog.ok_button = QPushButton("OK")
        PasswordDialog.cancel_button = QPushButton("キャンセル")
        button_layout.addWidget(PasswordDialog.ok_button)
        button_layout.addWidget(PasswordDialog.cancel_button)
        main_layout.addLayout(button_layout)