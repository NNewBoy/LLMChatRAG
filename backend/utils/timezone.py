"""统一时区工具 - 使用东八区 (UTC+8) 时间"""

from datetime import datetime, timezone, timedelta

# 东八区时区
_TZ = timezone(timedelta(hours=8))


def now() -> datetime:
    """返回当前东八区时间"""
    return datetime.now(_TZ)


def now_iso() -> str:
    """返回当前东八区时间的 ISO 格式字符串"""
    return datetime.now(_TZ).isoformat()


def now_str(fmt: str = '%Y年%m月%d日') -> str:
    """返回当前东八区时间的格式化字符串"""
    return datetime.now(_TZ).strftime(fmt)
