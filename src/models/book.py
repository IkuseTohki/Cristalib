# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Book:
    """蔵書データを表すデータクラス。"""
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