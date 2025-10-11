# -*- coding: utf-8 -*-
"""MainWindowのUI定義。

このファイルはUIのレイアウトとウィジェットの配置のみを記述します。
ロジックは含めません。
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableView, QAbstractItemView, QMenuBar, QMenu
)

class Ui_MainWindow(object):
    """MainWindowのUI要素を定義するクラス。"""
    def setupUi(self, MainWindow: QMainWindow):
        """UIのセットアップを行う。

        ウィジェットの生成、レイアウト設定、プロパティ設定など、
        UIの見た目に関するすべての構築処理をここで行う。

        Args:
            MainWindow (QMainWindow): UIを構築する対象のメインウィンドウインスタンス。
        """
        MainWindow.setWindowTitle("Cristalib")
        MainWindow.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        MainWindow.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # メニューバー
        self.menu_bar = MainWindow.menuBar()
        self.view_menu = self.menu_bar.addMenu("表示")
        
        # ツールメニューの追加
        tools_menu = self.menu_bar.addMenu("ツール")
        self.settings_action = tools_menu.addAction("設定")

        # 検索・同期
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索...")
        self.sync_button = QPushButton("同期")
        self.edit_button = QPushButton("編集")
        self.viewer_button = QPushButton("ビューアで開く")
        self.mode_button = QPushButton("プライベートモードへ")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.sync_button)
        search_layout.addWidget(self.edit_button)
        search_layout.addWidget(self.viewer_button)
        search_layout.addWidget(self.mode_button)
        main_layout.addLayout(search_layout)

        # 蔵書テーブル
        self.book_table_view = QTableView()
        self.book_table_view.setSortingEnabled(True)
        self.book_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.book_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.book_table_view.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.book_table_view)
