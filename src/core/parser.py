# -*- coding: utf-8 -*-
import json
import re
import os
from src.models.book import Book

class FileNameParser:
    """
    ファイル名から書籍情報を解析するクラス。
    """
    def __init__(self, rules_path='config/parsing_rules.json'): # 引数は残しますが、現在使用しません
        """
        コンストラクタ。解析ルールをコード内に直接定義して読み込む。
        """
        self.rules = self._load_rules()

    def _load_rules(self):
        """
        解析ルールをハードコードされたリストから読み込み、優先度順にソートして返す。
        JSONファイルの読み込みは一時的に停止しています。
        """
        hardcoded_rules = [
          {
            "name": "[著者] タイトル 第N巻 (雑誌版対応)",
            "regex": r"\[(?P<author>.+?)\]\s*(?P<title>.+?)\s*第(?P<volume>\d+)巻(?P<magazine_flag>\s*\(雑誌寄せ集め\))?.*",
            "priority": 1
          },
          {
            "name": "タイトル N巻 (著者) (雑誌版対応)",
            "regex": r"(?P<title>.+?)\s*(?P<volume>\d+)\s*\((?P<author>.+?)\)(?P<magazine_flag>\s*\(雑誌寄せ集め\))?.*",
            "priority": 2
          }
        ]
        
        hardcoded_rules.sort(key=lambda x: x.get('priority', 999))
        return hardcoded_rules

    def parse_filename(self, filename: str) -> Book:
        """
        ファイル名（拡張子なし）を受け取り、解析ルールに基づいて書籍情報を抽出する。
        
        :param filename: 解析対象のファイル名（拡張子なし）。
        :return: 抽出された情報を持つBookオブジェクト。
        """
        base_filename = os.path.splitext(filename)[0]

        for rule in self.rules:
            match = re.search(rule['regex'], base_filename)
            if match:
                data = match.groupdict()
                
                is_magazine = 'magazine_flag' in data and data['magazine_flag'] is not None

                return Book(
                    title=data.get('title'),
                    subtitle=data.get('subtitle'),
                    volume=int(data['volume']) if data.get('volume') else None,
                    author=data.get('author'),
                    original_author=data.get('original_author'),
                    series=data.get('series'),
                    is_magazine_collection=is_magazine
                )

        return Book(title=base_filename)
