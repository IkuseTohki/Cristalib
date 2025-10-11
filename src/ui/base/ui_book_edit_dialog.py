# -*- coding: utf-8 -*-
"""
BookEditDialogのUI定義。
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QCheckBox, QPushButton
)

class Ui_BookEditDialog(object):
    """BookEditDialogのUI要素を定義するクラス。"""
    def setupUi(self, BookEditDialog: QDialog):
        """UIのセットアップを行う。

        Args:
            BookEditDialog (QDialog): UIを構築する対象のダイアログインスタンス。
        """
        BookEditDialog.setWindowTitle("書籍情報編集")
        BookEditDialog.setMinimumWidth(600)

        main_layout = QVBoxLayout(BookEditDialog)
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
        button_layout.addStretch()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("キャンセル")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)