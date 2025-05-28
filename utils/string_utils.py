import re
import unicodedata


def truncate_text(text: str, max_length: int, ellipsis: str = "…") -> str:
    """テキストを指定長に切り詰め、超過時には省略記号を付与する。"""
    return text if len(text) <= max_length else text[:max_length] + ellipsis


def format_currency(amount: float, symbol: str = "¥") -> str:
    """数値を通貨形式の文字列に変換する。"""
    return f"{symbol}{int(amount):,}"


def slugify(text: str) -> str:
    """テキストを URL やファイル名に安全なスラグに変換する。"""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\-]+", "-", text).strip("-").lower()
    return text
