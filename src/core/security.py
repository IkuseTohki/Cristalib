# -*- coding: utf-8 -*-
"""セキュリティ関連の関数を提供します。

パスワードのハッシュ化や検証など、認証やセキュリティに関する
ヘルパー関数をまとめます。
"""
import hashlib
import secrets
from typing import Optional

def hash_password(password: str) -> str:
    """パスワードをソルト付きのSHA256でハッシュ化する。

    Args:
        password (str): ハッシュ化する平文のパスワード。

    Returns:
        str: "ソルト:ハッシュ値" の形式の文字列。
    """
    salt = secrets.token_hex(16)
    hashed_password = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}:{hashed_password}"


def verify_password(stored_password_hash: str, provided_password: Optional[str]) -> bool:
    """提供されたパスワードが保存されたハッシュと一致するか検証する。

    Args:
        stored_password_hash (str): データベースに保存されている "ソルト:ハッシュ値" 形式の文字列。
        provided_password (Optional[str]): ユーザーが入力した平文のパスワード。

    Returns:
        bool: パスワードが一致すればTrue、そうでなければFalse。
    """
    if not stored_password_hash or not provided_password or ':' not in stored_password_hash:
        return False
    salt, stored_hash = stored_password_hash.split(':')
    provided_hashed_password = hashlib.sha256((provided_password + salt).encode('utf-8')).hexdigest()
    return secrets.compare_digest(stored_hash, provided_hashed_password)