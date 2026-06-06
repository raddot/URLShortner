# config.py — reads from env vars set by docker-compose
import os

MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost")   # docker sets this to "mysql"
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER     = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "urlshortener")

REDIS_HOST        = os.getenv("REDIS_HOST", "localhost")   # docker sets this to "redis"
REDIS_PORT        = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB          = int(os.getenv("REDIS_DB", 0))
REDIS_KEY_PREFIX  = os.getenv("REDIS_KEY_PREFIX", "url:")

URL_EXPIRY_DAYS = int(os.getenv("URL_EXPIRY_DAYS", 30))
BASE_URL        = os.getenv("BASE_URL", "http://localhost:5000")