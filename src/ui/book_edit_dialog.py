# -*- coding: utf-8 -*-
"""書籍情報の編集用ダイアログUIを定義します。

BookEditDialogクラスは、ユーザーが書籍のメタデータ（タイトル、著者など）を
編集するためのフォームを提供します。
"""
from typing import Optional
from PyQt6.QtWidgets import QDialog, QWidget
from src.models.book import Book
from .base.ui_book_edit_dialog import Ui_BookEditDialog


class BookEditDialog(QDialog, Ui_BookEditDialog):
    """書籍情報を編集するためのダイアログ。"""

    def __init__(self, parent: Optional[QWidget] = None, book: Optional[Book] = None):
        """BookEditDialogのコンストラクタ。

        Args:
            parent (Optional[QWidget], optional): 親ウィジェット。Defaults to None.
            book (Optional[Book], optional): 編集対象のBookオブジェクト。Defaults to None.
        """
        super().__init__(parent)
        self.setupUi(self)
        
        self.original_book_id = book.id if book else None

        # --- シグナルの接続 ---
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        if book:
            self.set_book_data(book)

    def set_book_data(self, book: Book):
        """ダイアログのUIに既存の書籍情報を設定する。

        Args:
            book (Book): 表示するデータを持つBookオブジェクト。
        """
        self.title_input.setText(book.title or "")
        self.subtitle_input.setText(book.subtitle or "")
        self.volume_input.setValue(book.volume or 0)
        self.author_input.setText(book.author or "")
        self.original_author_input.setText(book.original_author or "")
        self.series_input.setText(book.series or "")
        self.category_input.setText(book.category or "")
        self.rating_input.setValue(book.rating or 0)
        self.is_magazine_collection_checkbox.setChecked(bool(book.is_magazine_collection))

    def get_book_data(self) -> Book:
        """UIから入力された書籍情報をBookオブジェクトとして取得する。

        Returns:
            Book: フォームに入力されたデータを持つ新しいBookオブジェクト。
                  IDは元の書籍のものを引き継ぐ。
        """
        return Book(
            id=self.original_book_id,
            title=self.title_input.text() or None,
            subtitle=self.subtitle_input.text() or None,
            volume=self.volume_input.value() if self.volume_input.value() > 0 else None,
            author=self.author_input.text() or None,
            original_author=self.original_author_input.text() or None,
            series=self.series_input.text() or None,
            category=self.category_input.text() or None,
            rating=self.rating_input.value() if self.rating_input.value() > 0 else None,
            is_magazine_collection=self.is_magazine_collection_checkbox.isChecked(),
        )
