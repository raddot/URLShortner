import json
import time
from datetime import datetime, timezone

import redis

import config

class RedisCache:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
            )
        return self._client

    def get(self, short_code: str) -> dict | None:
        try:
            data = self._get_client().get(self._key(short_code))
            if data is None:
                return None
            return json.loads(data)
        except redis.RedisError as e:
            print(f"[Cache] GET error for {short_code}: {e}")
            return None

    def set(self, short_code: str, long_url: str,
            expires_at=None, ttl_seconds: int = None) -> bool:
        try:
            client = self._get_client()
            payload = json.dumps({
                "long_url": long_url,
                "expires_at": str(expires_at) if expires_at else None,
            })

            if ttl_seconds is None:
                if expires_at:
                    now = datetime.now(timezone.utc)
                    if getattr(expires_at, "tzinfo", None) is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    ttl_seconds = max(int((expires_at - now).total_seconds()), 1)
                else:
                    ttl_seconds = config.URL_EXPIRY_DAYS * 86400

            client.setex(self._key(short_code), ttl_seconds, payload)
            return True
        except redis.RedisError as e:
            print(f"[Cache] SET error for {short_code}: {e}")
            return False

    def delete(self, short_code: str) -> bool:
        try:
            self._get_client().delete(self._key(short_code))
            return True
        except redis.RedisError as e:
            print(f"[Cache] DELETE error for {short_code}: {e}")
            return False

    def increment_click(self, short_code: str) -> int:
        try:
            client = self._get_client()
            counter_key = f"clicks:{short_code}"
            count = client.incr(counter_key)
            if count == 1:
                client.expire(counter_key, config.URL_EXPIRY_DAYS * 86400)
            return count
        except redis.RedisError as e:
            print(f"[Cache] INCR error for {short_code}: {e}")
            return -1

    def get_click_count(self, short_code: str) -> int:
        try:
            val = self._get_client().get(f"clicks:{short_code}")
            return int(val) if val else 0
        except redis.RedisError:
            return 0

    def flush_click_counts(self) -> dict:
        try:
            client = self._get_client()
            keys = client.keys("clicks:*")
            if not keys:
                return {}

            pipe = client.pipeline()
            for key in keys:
                pipe.get(key)
                pipe.delete(key)
            results = pipe.execute()

            counts = {}
            for i in range(0, len(results), 2):
                key = keys[i // 2]
                short_code = key.replace("clicks:", "")
                count = int(results[i]) if results[i] else 0
                if count > 0:
                    counts[short_code] = count
            return counts
        except redis.RedisError as e:
            print(f"[Cache] flush_click_counts error: {e}")
            return {}

    def check_rate_limit(self, ip: str, limit: int = 10, window_seconds: int = 60) -> bool:
        try:
            client = self._get_client()
            window = int(time.time() // window_seconds)
            key = f"ratelimit:{ip}:{window}"
            count = client.incr(key)
            if count == 1:
                client.expire(key, window_seconds * 2)
            return count <= limit
        except redis.RedisError:
            return True

    def ping(self) -> bool:
        try:
            return self._get_client().ping()
        except redis.RedisError:
            return False

    @staticmethod
    def _key(short_code: str) -> str:
        return f"{config.REDIS_KEY_PREFIX}{short_code}"


cache = RedisCache()
