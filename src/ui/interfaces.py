# -*- coding: utf-8 -*-
"""UI層とPresenter層間のインターフェースを定義するモジュール。

クリーンアーキテクチャの原則に基づき、PresenterがViewの具体的な実装に
依存しないように、抽象化されたインターフェースを提供します。
"""
from abc import ABC, abstractmethod # IApplicationControllerで使うので残す
from typing import List, Dict, Optional, Any, Callable
from PyQt6.QtCore import QObject, pyqtSignal # QObjectをインポート
from src.models.book import Book


class IMainWindow(QObject): # QObjectを継承し、ABCは継承しない
    """メインウィンドウがPresenterに提供すべきインターフェース。"""

    # Presenterが購読する抽象的なシグナル
    sync_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    viewer_requested = pyqtSignal()
    edit_book_requested = pyqtSignal()
    private_mode_toggled = pyqtSignal()
    book_double_clicked = pyqtSignal()

    def display_books(self, books: List[Book]):
        """書籍のリストをテーブルビューに表示する。

        Args:
            books (List[Book]): 表示するBookオブジェクトのリスト。
        """
        raise NotImplementedError

    def get_selected_book(self) -> Optional[Book]:
        """テーブルビューで現在選択されている行のBookオブジェクトを取得する。

        Returns:
            Optional[Book]: 選択されている行のBookオブジェクト。何も選択されていない場合はNone。
        """
        raise NotImplementedError

    def update_private_mode_view(self, is_private: bool):
        """プライベートモードの状態に応じてUIの表示を更新する。

        Args:
            is_private (bool): 現在のアプリケーションがプライベートモードであるかを示すフラグ。
                               Trueの場合はプライベートモード、Falseの場合は通常モード。
        """
        raise NotImplementedError

    def apply_column_settings(self, settings: Dict[str, Any]):
        """保存された列の設定をテーブルビューに適用する。

        Args:
            settings (Dict[str, Any]): 適用する列設定を格納した辞書。
        """
        raise NotImplementedError

    def get_column_settings(self) -> Dict[str, Any]:
        """現在の列の表示/非表示状態と幅を取得する。

        Returns:
            Dict[str, Any]: 列の表示状態と幅を格納した辞書。
        """
        raise NotImplementedError

    def show(self):
        """メインウィンドウを表示する。"""
        raise NotImplementedError

    def set_sync_button_enabled(self, enabled: bool):
        """同期ボタンの有効/無効を設定する。

        Args:
            enabled (bool): ボタンを有効にする場合はTrue、無効にする場合はFalse。
        """
        raise NotImplementedError

    def show_status_message(self, message: str):
        """ステータスバーにメッセージを表示する。

        Args:
            message (str): ステータスバーに表示するメッセージ。
        """
        raise NotImplementedError

    def show_information(self, title: str, message: str):
        """情報メッセージダイアログを表示する。
        Args:
            title (str): ダイアログのタイトル。
            message (str): 表示するメッセージ。
        """
        raise NotImplementedError

    def show_warning(self, title: str, message: str):
        """警告メッセージダイアログを表示する。
        Args:
            title (str): ダイアログのタイトル。
            message (str): 表示するメッセージ。
        """
        raise NotImplementedError

    def show_critical(self, title: str, message: str):
        """エラーメッセージダイアログを表示する。
        Args:
            title (str): ダイアログのタイトル。
            message (str): 表示するメッセージ。
        """
        raise NotImplementedError

    def ask_question(self, title: str, message: str) -> bool:
        """確認メッセージダイアログを表示し、ユーザーの応答(OK/Cancel)を返す。
        Args:
            title (str): ダイアログのタイトル。
            message (str): 表示するメッセージ。
        
        Returns:
            bool: ユーザーがOKを選択した場合はTrue、それ以外はFalse。
        """
        raise NotImplementedError


class ISettingsWindow(QObject):
    """設定ウィンドウがPresenterに提供すべきインターフェース。"""

    # Presenterが購読する抽象的なシグナル
    save_settings_requested = pyqtSignal()
    change_password_requested = pyqtSignal()
    add_scan_path_requested = pyqtSignal()
    remove_scan_path_requested = pyqtSignal()
    add_exclude_path_requested = pyqtSignal() # 追加
    remove_exclude_path_requested = pyqtSignal() # 追加
    browse_viewer_path_requested = pyqtSignal() # 追加

    def display_settings(self, settings: Dict[str, Any]):
        """設定情報をUIに表示する。

        Args:
            settings (Dict[str, Any]): 表示する設定情報を含む辞書。
        """
        raise NotImplementedError

    def display_scan_paths(self, scan_paths: List[str]):
        """スキャンパスのリストをUIに表示する。

        Args:
            scan_paths (List[str]): 表示するスキャンパスのリスト。
        """
        raise NotImplementedError

    def get_settings(self) -> Dict[str, Any]:
        """UIから現在の設定値を取得する。

        Returns:
            Dict[str, Any]: 現在の設定値を含む辞書。
        """
        raise NotImplementedError

    def get_scan_paths(self) -> List[str]:
        """UIから現在のスキャンパスのリストを取得する。

        Returns:
            List[str]: 現在のスキャンパスのリスト。
        """
        raise NotImplementedError

    def get_selected_scan_paths(self) -> List[str]:
        """UIから選択されているスキャンパスのリストを取得する。

        Returns:
            List[str]: 選択されているスキャンパスのリスト。
        """
        raise NotImplementedError

    def get_selected_exclude_paths(self) -> List[str]:
        """UIから選択されている除外パスのリストを取得する。

        Returns:
            List[str]: 選択されている除外パスのリスト。
        """
        raise NotImplementedError

    def show(self):
        """設定ウィンドウを表示する。"""
        raise NotImplementedError

    def close(self):
        """設定ウィンドウを閉じる。"""
        raise NotImplementedError


class IPasswordDialog(QObject):
    """パスワードダイアログがPresenterに提供すべきインターフェース。"""

    # Presenterが購読する抽象的なシグナル
    ok_button_clicked = pyqtSignal()
    cancel_button_clicked = pyqtSignal()

    def get_password(self) -> Optional[str]:
        """入力されたパスワードを取得する。

        Returns:
            Optional[str]: 入力されたパスワード文字列。キャンセルされた場合はNone。
        """
        raise NotImplementedError

    def validate_password_input(self) -> bool:
        """パスワード設定時の入力値を検証する。

        Returns:
            bool: 検証が通ればTrue、そうでなければFalse。
        """
        raise NotImplementedError

    def set_mode(self, mode: str):
        """ダイアログのモードを設定する。

        Args:
            mode (str): ダイアログのモード ("authenticate" または "set_password")。
        """
        raise NotImplementedError

    def exec(self) -> bool:
        """ダイアログを表示し、結果を返す。

        Returns:
            bool: ユーザーがAcceptした場合はTrue、それ以外はFalse。
        """
        raise NotImplementedError


class IDialogFactory(ABC):
    """ダイアログを生成するファクトリのインターフェース。"""

    @abstractmethod
    def create_password_dialog(self) -> IPasswordDialog:
        """PasswordDialogのインスタンスを生成する。"""
        pass

    @abstractmethod
    def create_book_edit_dialog(self) -> 'IBookEditDialog':
        """BookEditDialogのインスタンスを生成する。"""
        pass


class IBookEditDialog(QObject):
    """書籍編集ダイアログがPresenterに提供すべきインターフェース。"""

    def display_book_data(self, book: Book):
        """書籍データをUIに表示する。

        Args:
            book (Book): 表示するデータを持つBookオブジェクト。
        """
        raise NotImplementedError

    def get_book_data(self) -> Book:
        """UIから書籍データを取得する。

        Returns:
            Book: フォームに入力されたデータを持つ新しいBookオブジェクト。
        """
        raise NotImplementedError

    def exec(self) -> bool:
        """ダイアログを表示し、結果を返す。

        Returns:
            bool: ユーザーがAcceptした場合はTrue、それ以外はFalse。
        """
        raise NotImplementedError


class IApplicationController(ABC): # こちらはABCを継承したままでOK
    """ApplicationControllerがViewに提供すべきインターフェース。"""

    @abstractmethod
    def authenticate_and_open_settings(self):
        """パスワード認証後、設定ウィンドウを開く。"""
        pass

    @abstractmethod
    def change_password(self):
        """パスワードの変更処理を行う。"""
        pass

    @abstractmethod
    def toggle_private_mode(self):
        """プライベートモードのオン/オフを切り替える。"""
        pass

    @abstractmethod
    def open_selected_book_in_viewer(self):
        """テーブルで選択されている書籍を外部ビューアで開く。"""
        pass

    @abstractmethod
    def open_book_edit_dialog(self):
        """選択された書籍のメタデータを編集するダイアログを開く。"""
        pass

    @abstractmethod
    def run_scan_and_refresh(self):
        """ファイルスキャンを実行し、UIを更新する。"""
        pass

    @abstractmethod
    def load_books_to_list(self):
        """データベースから書籍を読み込み、UIに表示する。"""
        pass

    @abstractmethod
    def save_column_settings(self):
        """現在のテーブルの列の表示状態と幅をデータベースに保存する。"""
        pass

    @abstractmethod
    def run(self):
        """アプリケーションを実行する。"""
        pass
