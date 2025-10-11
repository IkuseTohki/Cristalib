# -*- coding: utf-8 -*-
"""書籍情報の編集用ダイアログUIを定義します。

BookEditDialogクラスは、ユーザーが書籍のメタデータ（タイトル、著者など）を
編集するためのフォームを提供します。
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QSpinBox, QCheckBox, QPushButton, QWidget
)
from src.models.book import Book


class BookEditDialog(QDialog):
    """書籍情報を編集するためのダイアログ。"""

    def __init__(self, parent: Optional[QWidget] = None, book: Optional[Book] = None):
        """BookEditDialogのコンストラクタ。

        Args:
            parent (Optional[QWidget], optional): 親ウィジェット。Defaults to None.
            book (Optional[Book], optional): 編集対象のBookオブジェクト。Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("書籍情報編集")
        self.setMinimumWidth(600)
        self.original_book_id = book.id if book else None

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.title_input = QLineEdit()
        self.subtitle_input = QLineEdit()
        self.volume_input = QSpinBox()
        self.volume_input.setMinimum(0)
        self.volume_input.setMaximum(9999)
        self.author_input = QLineEdit()
        self.original_author_input = QLineEdit()
        self.series_input = QLineEdit()
        self.category_input = QLineEdit()
        self.rating_input = QSpinBox()
        self.rating_input.setMinimum(0)
        self.rating_input.setMaximum(5)
        self.is_magazine_collection_checkbox = QCheckBox()

        form_layout.addRow("タイトル:", self.title_input)
        form_layout.addRow("サブタイトル:", self.subtitle_input)
        form_layout.addRow("巻数:", self.volume_input)
        form_layout.addRow("著者:", self.author_input)
        form_layout.addRow("原作者:", self.original_author_input)
        form_layout.addRow("シリーズ:", self.series_input)
        form_layout.addRow("カテゴリ:", self.category_input)
        form_layout.addRow("評価 (0-5):", self.rating_input)
        form_layout.addRow("雑誌版:", self.is_magazine_collection_checkbox)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        cancel_button = QPushButton("キャンセル")
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

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