import json
import random
import string

from flask import Flask, redirect, render_template, request

app = Flask(__name__)

URLS_FILE = "urls.json"


def load_urls():
    try:
        with open(URLS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_urls():
    with open(URLS_FILE, "w") as f:
        json.dump(shortened_urls, f)


shortened_urls = load_urls()


def generate_short_url(length=6):
    chars = string.ascii_letters + string.digits
    short_url = ''.join(random.choice(chars) for _ in range(length))
    return short_url


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['url']
        short_url = generate_short_url()
        while short_url in shortened_urls:
            short_url = generate_short_url()
        shortened_urls[short_url] = original_url
        save_urls()
        return f"Shortened URL: {request.url_root}{short_url}"
    return render_template('index.html')


@app.route('/<short_url>')
def redirect_url(short_url):
    original_url = shortened_urls.get(short_url)
    if original_url:
        return redirect(original_url)
    return "URL not found", 404


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
