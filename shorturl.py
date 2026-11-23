import sqlite3
import string
import random
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)
DB_NAME = "urls.db"

# Простой HTML-интерфейс прямо в коде
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Сокращатель ссылок</title>
    <style>
        body { font-family: sans-serif; max-width: 500px; margin: 60px auto; padding: 0 20px; }
        input[type="url"] { width: 100%; padding: 10px; margin-bottom: 10px; box-sizing: border-box; }
        button { padding: 10px 20px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; }
        .result { margin-top: 20px; padding: 15px; background: #f1f3f5; border-radius: 4px; word-break: break-all; }
    </style>
</head>
<body>
    <h2>Сократить ссылку</h2>
    <form method="POST">
        <input type="url" name="url" placeholder="https://example.com" required>
        <button type="submit">Сократить</button>
    </form>
    {% if short_url %}
    <div class="result">
        Короткая ссылка: <a href="{{ short_url }}" target="_blank">{{ short_url }}</a>
    </div>
    {% endif %}
</body>
</html>
"""

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                clicks INTEGER DEFAULT 0
            )
        """)

def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

@app.route("/", methods=["GET", "POST"])
def index():
    short_url = None
    if request.method == "POST":
        original_url = request.form.get("url")
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # Генерируем уникальный короткий код
            while True:
                code = generate_code()
                cursor.execute("SELECT 1 FROM links WHERE short_code = ?", (code,))
                if not cursor.fetchone():
                    break
            cursor.execute("INSERT INTO links (short_code, original_url) VALUES (?, ?)", (code, original_url))
            conn.commit()
        short_url = request.host_url + code
    return render_template_string(HTML_TEMPLATE, short_url=short_url)

@app.route("/<code>")
def redirect_to_url(code):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT original_url FROM links WHERE short_code = ?", (code,))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE links SET clicks = clicks + 1 WHERE short_code = ?", (code,))
            conn.commit()
            return redirect(row[0])
    return "Ссылка не найдена", 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
