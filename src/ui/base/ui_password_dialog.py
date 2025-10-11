# -*- coding: utf-8 -*-
"""
PasswordDialogのUI定義。
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel
)

class Ui_PasswordDialog(object):
    """PasswordDialogのUI要素を定義するクラス。"""
    def setupUi(self, PasswordDialog: QDialog, mode: str):
        """UIのセットアップを行う。

        Args:
            PasswordDialog (QDialog): UIを構築する対象のダイアログインスタンス。
            mode (str): ダイアログのモード ('authenticate' or 'set_password')。
                        モードに応じて表示するウィジェットを切り替える。
        """
        PasswordDialog.setWindowTitle("パスワード認証" if mode == "authenticate" else "パスワード設定")
        
        main_layout = QVBoxLayout(PasswordDialog)

        if mode == "authenticate":
            main_layout.addWidget(QLabel("パスワードを入力してください:"))
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            main_layout.addWidget(self.password_input)
        elif mode == "set_password":
            main_layout.addWidget(QLabel("新しいパスワードを入力してください:"))
            self.new_password_input = QLineEdit()
            self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            main_layout.addWidget(self.new_password_input)

            main_layout.addWidget(QLabel("新しいパスワード (確認):"))
            self.confirm_password_input = QLineEdit()
            self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            main_layout.addWidget(self.confirm_password_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.ok_button = QPushButton("OK" if mode == "authenticate" else "設定")
        self.cancel_button = QPushButton("キャンセル")
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)