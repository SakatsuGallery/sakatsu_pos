from datetime import datetime, timedelta

def get_current_timestamp(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """現在日時を指定フォーマットで文字列として返す。"""
    return datetime.now().strftime(fmt)

def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> datetime:
    """文字列からdatetimeオブジェクトを生成する。"""
    return datetime.strptime(date_str, fmt)

def format_date(dt: datetime, fmt: str = "%Y-%m-%d") -> str:
    """datetimeオブジェクトを指定フォーマットの文字列に変換する。"""
    return dt.strftime(fmt)

def add_days(dt: datetime, days: int) -> datetime:
    """日時に指定日数を加算して返す。"""
    return dt + timedelta(days=days)
