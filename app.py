import threading
import time
from urllib.parse import urlparse

from flask import Flask, jsonify, redirect, render_template, request

from src.cache import cache
from src.database import get_analytics, increment_click_db, init_db
from src.redirector import resolve_url
from src.shortener import shorten_url

app = Flask(__name__)

RESERVED_PATHS = frozenset({"health", "shorten", "analytics", "static"})


def get_client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except ValueError:
        return False


def flush_clicks_worker():
    while True:
        time.sleep(60)
        counts = cache.flush_click_counts()
        for short_code, count in counts.items():
            increment_click_db(short_code, count)


@app.before_request
def rate_limit():
    if request.method == "POST" and request.path in ("/shorten", "/"):
        if not cache.check_rate_limit(get_client_ip(), limit=10, window_seconds=60):
            if request.path == "/shorten":
                return jsonify({"error": "Rate limit exceeded"}), 429
            return render_template("index.html", error="Rate limit exceeded. Try again later."), 429


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        long_url = request.form.get("url", "").strip()
        if not is_valid_url(long_url):
            return render_template("index.html", error="Please enter a valid http or https URL."), 400
        try:
            result = shorten_url(long_url)
        except RuntimeError:
            return render_template("index.html", error="Could not create short URL. Please try again."), 500
        return render_template("index.html", result=result)
    return render_template("index.html")


@app.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True)
    if not data or not data.get("long_url"):
        return jsonify({"error": "long_url is required"}), 400

    long_url = data["long_url"].strip()
    if not is_valid_url(long_url):
        return jsonify({"error": "long_url must be a valid http or https URL"}), 400

    try:
        result = shorten_url(long_url)
    except RuntimeError:
        return jsonify({"error": "Could not create short URL"}), 500
    return jsonify(result), 201


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "redis": cache.ping(),
    }), 200


@app.route("/analytics/<short_code>", methods=["GET"])
def analytics(short_code):
    data = get_analytics(short_code)
    if not data:
        return jsonify({"error": "Not found"}), 404

    redis_clicks = cache.get_click_count(short_code)
    data["click_count"] = (data.get("click_count") or 0) + redis_clicks

    for key in ("created_at", "expires_at"):
        if data.get(key) and hasattr(data[key], "isoformat"):
            data[key] = data[key].isoformat()

    return jsonify(data), 200


@app.route("/<short_code>", methods=["GET"])
def redirect_url(short_code):
    if short_code in RESERVED_PATHS:
        return jsonify({"error": "Not found"}), 404

    long_url = resolve_url(short_code)
    if long_url is None:
        return jsonify({"error": "Short URL not found or expired"}), 404
    return redirect(long_url, code=302)


def start_background_tasks():
    thread = threading.Thread(target=flush_clicks_worker, daemon=True)
    thread.start()


if __name__ == "__main__":
    init_db()
    start_background_tasks()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
