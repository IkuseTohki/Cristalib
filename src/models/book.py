# -*- coding: utf-8 -*-
"""アプリケーションのデータモデルを定義します。

Bookクラスは、一冊の書籍に関するすべての情報を保持するデータクラスです。
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Book:
    """蔵書データを表すデータクラス。

    Attributes:
        id (Optional[int]): データベース上のユニークID。
        title (Optional[str]): 書籍のタイトル。
        subtitle (Optional[str]): 書籍のサブタイトル。
        volume (Optional[int]): 巻数。
        author (Optional[str]): 著者。
        original_author (Optional[str]): 原作者。
        series (Optional[str]): シリーズ名。
        category (Optional[str]): カテゴリ。
        rating (Optional[int]): 評価（星の数など）。
        is_magazine_collection (bool): 雑誌や複数の話をまとめたものかどうかのフラグ。
        file_path (Optional[str]): ファイルシステム上のパス。
        file_hash (Optional[str]): ファイルのハッシュ値。
        created_at (Optional[str]): データベースに登録された日時。
    """
    id: Optional[int] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    volume: Optional[int] = None
    author: Optional[str] = None
    original_author: Optional[str] = None
    series: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[int] = None
    is_magazine_collection: bool = False
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    created_at: Optional[str] = None
