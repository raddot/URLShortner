import mysql.connector
import redis

import config

redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    decode_responses=True,
)

TTL_SECONDS = config.URL_EXPIRY_DAYS * 86400


def _redis_key(short_code: str) -> str:
    return f"{config.REDIS_KEY_PREFIX}{short_code}"


def _get_mysql_connection():
    return mysql.connector.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE,
    )


def url_exists(short_code: str) -> bool:
    if redis_client.exists(_redis_key(short_code)):
        return True

    conn = _get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM urls WHERE short_code = %s "
            "AND (expires_at IS NULL OR expires_at > NOW()) LIMIT 1",
            (short_code,),
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def save_url(short_code: str, original_url: str) -> None:
    conn = _get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO urls (short_code, original_url, expires_at) "
            "VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL %s DAY))",
            (short_code, original_url, config.URL_EXPIRY_DAYS),
        )
        conn.commit()
    finally:
        conn.close()

    redis_client.set(_redis_key(short_code), original_url, ex=TTL_SECONDS)


def get_url(short_code: str) -> str | None:
    cached = redis_client.get(_redis_key(short_code))
    if cached:
        return cached

    conn = _get_mysql_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT original_url FROM urls WHERE short_code = %s "
            "AND (expires_at IS NULL OR expires_at > NOW()) LIMIT 1",
            (short_code,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        original_url = row[0]
        redis_client.set(_redis_key(short_code), original_url, ex=TTL_SECONDS)
        return original_url
    finally:
        conn.close()
