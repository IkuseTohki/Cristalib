# -*- coding: utf-8 -*-
"""UI要素を生成するFactoryクラスを定義します。"""
from .settings_window import PasswordDialog
from .book_edit_dialog import BookEditDialog
from .interfaces import IPasswordDialog, IBookEditDialog, IDialogFactory


class DialogFactory(IDialogFactory):
    """ダイアログのインスタンスを生成するファクトリ。"""
    def create_password_dialog(self) -> IPasswordDialog:
        """PasswordDialogの新しいインスタンスを生成して返す。

        Returns:
            IPasswordDialog: PasswordDialogの新しいインスタンス。
        """
        return PasswordDialog()

    def create_book_edit_dialog(self) -> IBookEditDialog:
        """BookEditDialogの新しいインスタンスを生成して返す。

        Returns:
            IBookEditDialog: BookEditDialogの新しいインスタンス。
        """
        return BookEditDialog()