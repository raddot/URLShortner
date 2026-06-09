# import mysql.connector
# from mysql.connector import pooling

import config

_pool = None

CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS urls (
        id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        short_code   VARCHAR(16)     NOT NULL,
        long_url     TEXT            NOT NULL,
        created_at   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at   TIMESTAMP       NULL,
        click_count  INT             NOT NULL DEFAULT 0,
        PRIMARY KEY (id),
        UNIQUE KEY uk_short_code (short_code),
        KEY idx_expires_at (expires_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="urlpool",
            pool_size=10,
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
        )
    return _pool


def init_db():
    conn = _get_pool().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def write_url(short_code: str, long_url: str, expires_at) -> bool:
    conn = _get_pool().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO urls (short_code, long_url, expires_at) VALUES (%s, %s, %s)",
            (short_code, long_url, expires_at),
        )
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        return False
    finally:
        cursor.close()
        conn.close()


def read_url(short_code: str) -> dict | None:
    conn = _get_pool().get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT long_url, expires_at FROM urls WHERE short_code = %s",
            (short_code,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_analytics(short_code: str) -> dict | None:
    conn = _get_pool().get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT short_code, long_url, click_count, created_at, expires_at "
            "FROM urls WHERE short_code = %s",
            (short_code,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def increment_click_db(short_code: str, count: int = 1):
    if count <= 0:
        return
    conn = _get_pool().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE urls SET click_count = click_count + %s WHERE short_code = %s",
            (count, short_code),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
