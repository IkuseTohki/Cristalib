# -*- coding: utf-8 -*-
"""アプリケーションのメインウィンドウUIを定義します。

MainWindowクラスはUIのロジックとPresenterとの連携を担当します。
UIのレイアウト定義はUi_MainWindowクラスに分離されています。
"""
from typing import List, Dict, Optional
from datetime import datetime
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from src.models.book import Book
from .base.ui_main_window import Ui_MainWindow


class BookFilterProxyModel(QSortFilterProxyModel):
    """書籍テーブルの検索フィルタリングを行うプロキシモデル。

    タイトル、著者、シリーズなどのテキストフィールドに対して、
    大文字小文字を区別しない部分一致検索を実装します。
    """
    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        """行が表示されるべきかを判断する。

        Args:
            source_row (int): ソースモデルの行番号。
            source_parent: ソースモデルの親インデックス。

        Returns:
            bool: 行を表示する場合はTrue、非表示にする場合はFalse。
        """
        index = self.sourceModel().index(source_row, 0, source_parent)
        book = self.sourceModel().data(index, Qt.ItemDataRole.UserRole)
        if not book:
            return False

        filter_text = self.filterRegularExpression().pattern()
        if not filter_text:
            return True
        
        search_fields = [book.title, book.author, book.series, book.original_author, book.category]
        for field in search_fields:
            if field and filter_text.lower() in field.lower():
                return True
        
        return False


class MainWindow(QMainWindow, Ui_MainWindow):
    """アプリケーションのメインウィンドウ。

    UIのロジックとPresenterとの連携を担当します。
    UIのレイアウト定義はUi_MainWindowクラスに分離されています。
    """
    def __init__(self, parent: Optional[QWidget] = None):
        """MainWindowのコンストラクタ。"""
        super().__init__(parent)
        self.setupUi(self) # UI定義からUIを構築

        # --- モデルのセットアップ ---
        self.book_table_model = QStandardItemModel()
        self.proxy_model = BookFilterProxyModel()
        self.proxy_model.setSourceModel(self.book_table_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.book_table_view.setModel(self.proxy_model)

        # --- シグナルの接続 ---
        self.search_input.textChanged.connect(self.proxy_model.setFilterRegularExpression)

    def display_books(self, books: List[Book]):
        """書籍のリストをテーブルビューに表示する。

        Args:
            books (List[Book]): 表示するBookオブジェクトのリスト。
        """
        self.book_table_model.clear()
        
        headers = [
            "タイトル", "サブタイトル", "巻数", "著者", "原作者", 
            "シリーズ", "カテゴリ", "評価", "雑誌版", "登録日"
        ]
        self.book_table_model.setHorizontalHeaderLabels(headers)

        for book in books:
            items = [
                QStandardItem(book.title or ""),
                QStandardItem(book.subtitle or ""),
                QStandardItem(str(book.volume) if book.volume is not None else ""),
                QStandardItem(book.author or ""),
                QStandardItem(book.original_author or ""),
                QStandardItem(book.series or ""),
                QStandardItem(book.category or ""),
                QStandardItem(str(book.rating) if book.rating is not None else ""),
                QStandardItem("✅" if book.is_magazine_collection else ""),
                QStandardItem(datetime.fromisoformat(book.created_at).strftime("%Y-%m-%d") if book.created_at else "")
            ]
            items[0].setData(book, Qt.ItemDataRole.UserRole)
            self.book_table_model.appendRow(items)
            
        self.book_table_view.resizeColumnsToContents()
        self.update_column_visibility_menu()

    def update_column_visibility_menu(self):
        """「表示」メニューを現在の列の表示状態に合わせて更新する。"""
        self.view_menu.clear()
        for i in range(self.book_table_model.columnCount()):
            header_text = self.book_table_model.horizontalHeaderItem(i).text()
            action = self.view_menu.addAction(header_text)
            action.setCheckable(True)
            action.setChecked(not self.book_table_view.isColumnHidden(i))
            action.toggled.connect(lambda checked, col=i: self.book_table_view.setColumnHidden(col, not checked))

    def get_column_settings(self) -> Dict:
        """現在の列の表示/非表示状態と幅を取得する。

        Returns:
            Dict: 列の表示状態と幅を格納した辞書。
        """
        visibility = {i: self.book_table_view.isColumnHidden(i) for i in range(self.book_table_model.columnCount())}
        widths = {i: self.book_table_view.columnWidth(i) for i in range(self.book_table_model.columnCount())}
        return {'visibility': visibility, 'widths': widths}

    def apply_column_settings(self, settings: Dict):
        """保存された列の設定をテーブルビューに適用する。

        Args:
            settings (Dict): 適用する列設定を格納した辞書。
        """
        if 'visibility' in settings:
            for i_str, is_hidden in settings['visibility'].items():
                i = int(i_str)
                if i < self.book_table_model.columnCount():
                    self.book_table_view.setColumnHidden(i, is_hidden)
        if 'widths' in settings:
            for i_str, width in settings['widths'].items():
                i = int(i_str)
                if i < self.book_table_model.columnCount():
                    self.book_table_view.setColumnWidth(i, width)
        self.update_column_visibility_menu()

    def update_private_mode_view(self, is_private: bool):
        """プライベートモードの状態に応じてUIの表示を更新する。

        Args:
            is_private (bool): プライベートモードが有効な場合はTrue。
        """
        if is_private:
            self.mode_button.setText("通常モードへ")
        else:
            self.mode_button.setText("プライベートモードへ")

    def get_selected_book(self) -> Optional[Book]:
        """テーブルビューで現在選択されている行のBookオブジェクトを取得する。

        Returns:
            Optional[Book]: 選択されている行のBookオブジェクト。何も選択されていない場合はNone。
        """
        selected_indexes = self.book_table_view.selectedIndexes()
        if not selected_indexes:
            return None

        proxy_index = selected_indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        item = self.book_table_model.itemFromIndex(source_index)
        if not item:
            return None
        
        return item.data(Qt.ItemDataRole.UserRole)
