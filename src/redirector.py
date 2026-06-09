from datetime import datetime, timezone

from src.cache import cache
from src.database import read_url


def resolve_url(short_code: str) -> str | None:
    cached = cache.get(short_code)
    if cached:
        cache.increment_click(short_code)
        return cached["long_url"]

    row = read_url(short_code)
    if not row:
        return None

    if row["expires_at"]:
        expires = row["expires_at"]
        if getattr(expires, "tzinfo", None) is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            return None

    cache.set(short_code, row["long_url"], expires_at=row["expires_at"])
    cache.increment_click(short_code)
    return row["long_url"]
