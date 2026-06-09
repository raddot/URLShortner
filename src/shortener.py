from datetime import datetime, timedelta, timezone

import config
from src.cache import cache
from src.database import write_url
from src.id_generator import encode_base62, id_gen

MAX_RETRIES = 5


def shorten_url(long_url: str) -> dict:
    for _ in range(MAX_RETRIES):
        snowflake_id = id_gen.generate()
        short_code = encode_base62(snowflake_id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=config.URL_EXPIRY_DAYS)

        if not write_url(short_code, long_url, expires_at):
            continue

        cache.set(short_code, long_url, expires_at=expires_at)
        return {
            "short_url": f"{config.BASE_URL}/{short_code}",
            "short_code": short_code,
            "long_url": long_url,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    raise RuntimeError("Failed to generate a unique short code")
