"""Вспомогательные функции."""
import time
from datetime import datetime


def format_timestamp(ts: float) -> str:
    """Форматирование UNIX-timestamp в читаемую строку."""
    dt = datetime.fromtimestamp(ts)
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    elif dt.year == now.year:
        return dt.strftime("%d %b %H:%M")
    else:
        return dt.strftime("%d.%m.%Y %H:%M")


def truncate_text(text: str, max_len: int = 50) -> str:
    """Обрезка текста с многоточием."""
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def get_local_ip() -> str:
    """Определение локального IP-адреса."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
