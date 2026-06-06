import random
import string

from flask import Flask, redirect, render_template, request

import storage

app = Flask(__name__)


def generate_short_url(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['url']
        short_url = generate_short_url()
        while storage.url_exists(short_url):
            short_url = generate_short_url()
        storage.save_url(short_url, original_url)
        return f"Shortened URL: {request.url_root}{short_url}"
    return render_template('index.html')


@app.route('/<short_url>')
def redirect_url(short_url):
    original_url = storage.get_url(short_url)
    if original_url:
        return redirect(original_url)
    return "URL not found", 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
