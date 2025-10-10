# -*- coding: utf-8 -*-
import json
import re
import os
from typing import List, Dict
from src.models.book import Book

class ParsingRuleLoader:
    """
    ファイル名解析ルールをJSONファイルから読み込むクラス。
    """
    def __init__(self, rules_path: str):
        self.rules_path = rules_path

    def load_rules(self) -> List[Dict]:
        """
        解析ルールをJSONファイルから読み込み、優先度順にソートして返す。
        """
        if not os.path.exists(self.rules_path):
            # ファイルが存在しない場合は空のルールリストを返す
            # またはデフォルトのハードコードされたルールを返す
            # 現状はハードコードされたルールを返すことで、ファイルがない場合でも動作を保証
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
        
        with open(self.rules_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        
        rules.sort(key=lambda x: x.get('priority', 999))
        return rules

class FileNameParser:
    """
    ファイル名から書籍情報を解析するクラス。
    """
    def __init__(self, rules: List[Dict]):
        """
        コンストラクタ。読み込まれた解析ルールを受け取る。
        :param rules: 読み込まれ、ソート済みの解析ルールリスト。
        """
        self.rules = rules

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