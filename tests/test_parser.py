# -*- coding: utf-8 -*-
"""FileNameParserクラスのユニットテスト。

ファイル名の解析ロジックが、定義されたルールに基づいて正しく動作することを確認する。
"""
import pytest
from src.core.parser import FileNameParser
from src.models.book import Book


@pytest.fixture
def sample_rules():
    """テスト用のダミー解析ルールを提供するフィクスチャ。

    Returns:
        list: 解析ルールのリスト。
    """
    return [
        {
            "name": "[著者] タイトル 第N巻 (雑誌版対応)",
            "regex": r"^\[(?P<author>.+?)\]\s*(?P<title>.+?)\s+第?(?P<volume>\d+)巻(?P<magazine_flag>\s+\(雑誌寄せ集め\))?.*",
             "priority": 1
        },
        {
            "name": "タイトル N巻 (著者) (雑誌版対応)",
            "regex": r"^(?P<title>.+?)\s*第?(?P<volume>\d+)巻\s+\((?P<author>.+?)\)(?P<magazine_flag>\s+\(雑誌寄せ集め\))?.*",
            "priority": 2
        },
        {
            "name": "シンプルなタイトル",
            "regex": r"(?P<title>.+)",
            "priority": 999
        }
    ]


@pytest.fixture
def parser(sample_rules):
    """FileNameParserのインスタンスを提供するフィクスチャ。

    Args:
        sample_rules (list): 解析ルールのリスト。

    Returns:
        FileNameParser: FileNameParserのインスタンス。
    """
    return FileNameParser(sample_rules)


def test_parser_initialization(sample_rules):
    """テスト観点: FileNameParserの初期化。

    - 有効なルールリストで初期化できること。
    - 空のルールリストで初期化できること。
    """
    parser = FileNameParser(sample_rules)
    assert parser.rules == sample_rules

    empty_parser = FileNameParser([])
    assert empty_parser.rules == []


def test_parse_filename_match_priority_1_1(parser):
    """テスト観点: 優先度1のルールへのマッチ（雑誌フラグあり）。

    - ファイル名が優先度1のルールに正しくマッチし、各情報が抽出されること。
    - is_magazine_collectionフラグがTrueになること。
    """
    filename = "[山田太郎] 異世界転生 第1巻 (雑誌寄せ集め)"
    book = parser.parse_filename(filename)
    assert book.title == "異世界転生"
    assert book.author == "山田太郎"
    assert book.volume == 1
    assert book.is_magazine_collection is True


def test_parse_filename_match_priority_1_2(parser):
    """テスト観点: 優先度1のルールへのマッチ（「第」省略形）。

    - 「第」が省略された巻数表記でも、優先度1のルールに正しくマッチすること。
    """
    filename = "[山田太郎] 異世界転生 1巻 (雑誌寄せ集め)"
    book = parser.parse_filename(filename)
    assert book.title == "異世界転生"
    assert book.author == "山田太郎"
    assert book.volume == 1
    assert book.is_magazine_collection is True


def test_parse_filename_match_priority_2(parser):
    """テスト観点: 優先度2のルールへのマッチ。

    - 優先度1にはマッチしないが、優先度2のルールに正しくマッチすること。
    - is_magazine_collectionフラグがFalseになること。
    """
    filename = "魔法少女まどか☆マギカ 3巻 (虚淵玄)"
    book = parser.parse_filename(filename)
    assert book.title == "魔法少女まどか☆マギカ"
    assert book.author == "虚淵玄"
    assert book.volume == 3
    assert book.is_magazine_collection is False


def test_parse_filename_no_match_specific_rules(parser):
    """テスト観点: 最も優先度の低いルールへのマッチ。

    - どの特定のルールにもマッチしない場合、最終的に「シンプルなタイトル」ルールにマッチすること。
    """
    filename = "ただのファイル名"
    book = parser.parse_filename(filename)
    assert book.title == "ただのファイル名"
    assert book.author is None
    assert book.volume is None
    assert book.is_magazine_collection is False


def test_parse_filename_with_extension(parser):
    """テスト観点: 拡張子付きファイル名の解析。

    - ファイル名に拡張子が含まれていても、正しく解析できること。
    """
    filename = "[田中] プログラミング入門 2巻.pdf"
    book = parser.parse_filename(filename)
    assert book.title == "プログラミング入門"
    assert book.author == "田中"
    assert book.volume == 2
    assert book.is_magazine_collection is False


def test_parse_filename_no_match_all_rules(parser):
    """テスト観点: どのルールにもマッチしない場合の挙動。

    - 実際には「シンプルなタイトル」ルールにマッチするが、その場合の挙動が期待通りであること。
    - 意図としては、ルールがない場合にどうなるかだが、fixtureの都合上、最低でも1つはマッチする。
    """
    filename = "未知のフォーマットのファイル名"
    book = parser.parse_filename(filename)
    assert book.title == "未知のフォーマットのファイル名"
    assert book.author is None
    assert book.volume is None
    assert book.is_magazine_collection is False


def test_parse_filename_magazine_flag_false(parser):
    """テスト観点: 雑誌フラグがない場合の解析。

    - 雑誌フラグを示す文字列がない場合に、is_magazine_collectionがFalseになること。
    """
    filename = "[著者名] タイトル 5巻"
    book = parser.parse_filename(filename)
    assert book.title == "タイトル"
    assert book.author == "著者名"
    assert book.volume == 5
    assert book.is_magazine_collection is False


def test_parse_filename_volume_none(parser):
    """テスト観点: 巻数がないファイル名の解析。

    - 巻数が含まれないファイル名の場合、高優先度のルールにはマッチせず、
      最終的に「シンプルなタイトル」ルールにマッチすることを確認する。
    """
    filename = "[著者名] タイトル"
    book = parser.parse_filename(filename)
    assert book.title == "[著者名] タイトル"
    assert book.author is None
    assert book.volume is None
    assert book.is_magazine_collection is False


@pytest.fixture
def unsorted_rules():
    """ソートされていないダミー解析ルールを提供するフィクスチャ。

    Returns:
        list: ソートされていない解析ルールのリスト。
    """
    return [
        {
            "name": "シンプルなタイトル",
            "regex": r"(?P<title>.+)",
            "priority": 999
        },
        {
            "name": "[著者] タイトル 第N巻",
            "regex": r"\\[(?P<author>.+?)\\]\\s*(?P<title>.+?)\\s*(?:第)?(?P<volume>\\d+)巻.*",
            "priority": 1
        }
    ]


def test_parser_rules_sorted_by_priority(unsorted_rules):
    """テスト観点: ルールの順序維持。

    - FileNameParserは、渡されたルールの順序を変更しないことを確認する。
    - ルールのソートは、このクラスの責務外である（通常はParsingRuleLoaderが担う）。
    """
    parser = FileNameParser(unsorted_rules)
    assert parser.rules == unsorted_rules
