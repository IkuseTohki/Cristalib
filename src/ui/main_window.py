# -*- coding: utf-8 -*-
import sys
from typing import List
from datetime import datetime
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLineEdit, QTableView, QLabel, QAbstractItemView, QMenuBar, QMenu
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from src.models.book import Book

class BookFilterProxyModel(QSortFilterProxyModel):
    """書籍テーブルのフィルタリングを行うプロキシモデル。"""
    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        # 最初の列のアイテムからBookオブジェクトを取得
        index = self.sourceModel().index(source_row, 0, source_parent)
        book = self.sourceModel().data(index, Qt.ItemDataRole.UserRole)
        if not book:
            return False

        filter_text = self.filterRegularExpression().pattern()
        if not filter_text:
            return True
        
        # タイトル、著者、シリーズなどを検索対象とする
        search_fields = [book.title, book.author, book.series, book.original_author, book.category]
        for field in search_fields:
            if field and filter_text.lower() in field.lower():
                return True
        
        return False

class MainWindow(QMainWindow):
    """アプリケーションのメインウィンドウ。"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cristalib")
        self.setGeometry(100, 100, 1200, 800) # ウィンドウサイズを少し大きく

        # --- モデルのセットアップ ---
        self.book_table_model = QStandardItemModel()
        self.proxy_model = BookFilterProxyModel()
        self.proxy_model.setSourceModel(self.book_table_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # --- UIのセットアップ --- #
        self.setup_ui()

        # --- シグナルの接続 ---
        self.search_input.textChanged.connect(self.proxy_model.setFilterRegularExpression)

    def setup_ui(self):
        """UIウィジェットの初期化とレイアウト設定。"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # メニューバー
        self.menu_bar = self.menuBar()
        self.view_menu = self.menu_bar.addMenu("表示")

        # ヘッダー
        header_layout = QHBoxLayout()
        self.mode_button = QPushButton("プライベートモードへ")
        self.settings_button = QPushButton("設定")
        header_layout.addWidget(QLabel("蔵書管理"))
        header_layout.addStretch()
        header_layout.addWidget(self.mode_button)
        header_layout.addWidget(self.settings_button)
        main_layout.addLayout(header_layout)

        # 検索・同期
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索...")
        self.sync_button = QPushButton("同期")
        self.edit_button = QPushButton("編集")
        self.viewer_button = QPushButton("ビューアで開く")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.sync_button)
        search_layout.addWidget(self.edit_button)
        search_layout.addWidget(self.viewer_button)
        main_layout.addLayout(search_layout)

        # 蔵書テーブル
        self.book_table_view = QTableView()
        self.book_table_view.setModel(self.proxy_model)
        self.book_table_view.setSortingEnabled(True) # ヘッダクリックによるソートを有効化
        self.book_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.book_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.book_table_view.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.book_table_view)

    def display_books(self, books: List[Book]):
        """書籍のリストをテーブルに表示する。"""
        self.book_table_model.clear()
        
        # すべての書籍属性をヘッダーとして定義
        headers = [
            "タイトル", "サブタイトル", "巻数", "著者", "原作者", 
            "シリーズ", "カテゴリ", "評価", "雑誌版", "登録日"
        ]
        self.book_table_model.setHorizontalHeaderLabels(headers)

        for book in books:
            title_item = QStandardItem(book.title or "")
            title_item.setData(book, Qt.ItemDataRole.UserRole) # フィルタリングとデータアクセスのためにBookオブジェクトを格納
            
            subtitle_item = QStandardItem(book.subtitle or "")
            volume_item = QStandardItem(str(book.volume) if book.volume is not None else "")
            author_item = QStandardItem(book.author or "")
            original_author_item = QStandardItem(book.original_author or "")
            series_item = QStandardItem(book.series or "")
            category_item = QStandardItem(book.category or "")
            rating_item = QStandardItem(str(book.rating) if book.rating is not None else "")
            is_magazine_item = QStandardItem("✅" if book.is_magazine_collection else "")
            created_at_display = ""
            if book.created_at:
                try:
                    dt_object = datetime.fromisoformat(book.created_at)
                    created_at_display = dt_object.strftime("%Y-%m-%d")
                except ValueError:
                    created_at_display = book.created_at # パース失敗時はそのまま表示
            created_at_item = QStandardItem(created_at_display)

            self.book_table_model.appendRow([
                title_item, subtitle_item, volume_item, author_item, original_author_item,
                series_item, category_item, rating_item, is_magazine_item, created_at_item
            ])
        self.book_table_view.resizeColumnsToContents()

        # 列の表示/非表示メニューを更新
        self.update_column_visibility_menu()

    def update_column_visibility_menu(self):
        """列の表示/非表示を切り替えるメニューを更新する。"""
        self.view_menu.clear()
        for i in range(self.book_table_model.columnCount()):
            header_item = self.book_table_model.horizontalHeaderItem(i)
            if header_item:
                header_text = header_item.text()
                action = self.view_menu.addAction(header_text)
                action.setCheckable(True)
                action.setChecked(not self.book_table_view.isColumnHidden(i))
                action.toggled.connect(lambda checked, col=i: self.book_table_view.setColumnHidden(col, not checked))
