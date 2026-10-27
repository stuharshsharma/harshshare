from flask import Flask, request, render_template_string, send_from_directory, abort
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import hmac

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

# Admin password environment variable se set hoga.
ADMIN_PASSWORD = os.environ.get("HARSHSHARE_ADMIN_PASSWORD", "")

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Tr*sh@</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #ffffff;
            color: #222222;
            margin: 0;
            padding: 30px 15px;
        }
        main {
            max-width: 700px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 14px;
        }
        h1 { color: #2563eb; }
        .file {
            padding: 14px;
            border-bottom: 1px solid #ddd;
            overflow-wrap: anywhere;
        }
        a { color: #2563eb; }
        button {
            padding: 10px 16px;
            background: #2563eb;
            color: white;
            border: 0;
            border-radius: 6px;
            cursor: pointer;
        }
        input { margin: 10px 0; max-width: 100%; }
        button {
    background: #e60023;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    cursor: pointer;
}
    </style>
</head>
<body>
<main>
    <h1>tr*sh@📁</h1>
    <p>Upload ki gayi files yahan dekho aur download karo.</p>

    {% if message %}
        <p>{{ message }}</p>
    {% endif %}

    {% if admin %}
        <h2>Admin: Upload file</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <br><button type="submit">Upload</button>
        </form>
        <p><a href="/logout">Admin logout</a></p>
    {% else %}
        <p><a href="/login">Admin login</a></p>
    {% endif %}

    <h2>Available files</h2>
    {% for filename in files %}
        <div class="file">
            {{ filename }}
            — <a href="/download/{{ filename }}">Download</a>
            {% if admin %}
                <form action="/delete/{{ filename }}" method="post"
                      style="display:inline">
                    <button type="submit">Delete</button>
                </form>
            {% endif %}
        </div>
    {% else %}
        <p>Abhi koi file upload nahi hui.</p>
    {% endfor %}
</main>
</body>
</html>
"""

from flask import session, redirect, url_for
app.secret_key = os.environ.get("HARSHSHARE_SECRET_KEY", "")

@app.route("/")
def home():
    files = sorted(p.name for p in UPLOAD_DIR.iterdir() if p.is_file())
    return render_template_string(
        PAGE, files=files, admin=session.get("admin", False), message=""
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if not ADMIN_PASSWORD or not app.secret_key:
        return "Admin password aur secret key configure nahi hain.", 503

    if request.method == "POST":
        password = request.form.get("password", "")
        if hmac.compare_digest(password, ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("home"))
        return "Password galat hai. <a href='/login'>Dobara try karein</a>", 401

    return """
    <h2>Admin Login</h2>
    <form method="post">
      <input type="password" name="password" placeholder="Admin password" required>
      <button type="submit">Login</button>
    </form>
    """

@app.route("/upload", methods=["POST"])
def upload():
    if not session.get("admin"):
        abort(403)

    file = request.files.get("file")
    if not file or not file.filename:
        abort(400)

    filename = secure_filename(file.filename)
    if not filename or filename in {".", ".."}:
        abort(400)

    file.save(UPLOAD_DIR / filename)
    return redirect(url_for("home"))

@app.route("/download/<path:filename>")
def download(filename):
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        abort(404)
    return send_from_directory(UPLOAD_DIR, safe_name, as_attachment=True)

@app.route("/delete/<path:filename>", methods=["POST"])
def delete(filename):
    if not session.get("admin"):
        abort(403)

    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        abort(404)

    target = UPLOAD_DIR / safe_name
    if target.is_file():
        target.unlink()

    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=False)
