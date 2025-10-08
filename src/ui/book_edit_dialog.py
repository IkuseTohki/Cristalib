# -*- coding: utf-8 -*-
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QSpinBox, QCheckBox, QPushButton, QLabel
)
from src.models.book import Book

class BookEditDialog(QDialog):
    """書籍情報を編集するためのダイアログ。"""
    def __init__(self, parent=None, book: Optional[Book] = None):
        super().__init__(parent)
        self.setWindowTitle("書籍情報編集")
        self.setMinimumWidth(600) # 編集画面の幅を広くする
        self.original_book_id = book.id if book else None

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.title_input = QLineEdit()
        self.subtitle_input = QLineEdit()
        self.volume_input = QSpinBox()
        self.volume_input.setMinimum(0)
        self.volume_input.setFixedWidth(150) # 数値上げ下げボタンの間隔をあける
        self.author_input = QLineEdit()
        self.original_author_input = QLineEdit()
        self.series_input = QLineEdit()
        self.category_input = QLineEdit()
        self.rating_input = QSpinBox()
        self.rating_input.setMinimum(0)
        self.rating_input.setMaximum(5)
        self.rating_input.setFixedWidth(150) # 数値上げ下げボタンの間隔をあける
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
        """ダイアログのUIに書籍情報を設定する。"""
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
        """UIから入力された書籍情報をBookオブジェクトとして取得する。"""
        return Book(
            id=self.original_book_id, # IDは元の書籍のものを保持
            title=self.title_input.text() or None,
            subtitle=self.subtitle_input.text() or None,
            volume=self.volume_input.value() or None,
            author=self.author_input.text() or None,
            original_author=self.original_author_input.text() or None,
            series=self.series_input.text() or None,
            category=self.category_input.text() or None,
            rating=self.rating_input.value() or None,
            is_magazine_collection=self.is_magazine_collection_checkbox.isChecked(),
            # file_path, file_hash, created_at は編集しないので元の値を保持 (またはNone)
            file_path=None, 
            file_hash=None, 
            created_at=None
        )
