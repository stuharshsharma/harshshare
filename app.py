import os
import re
import hmac
import uuid
import secrets
import sqlite3
import mimetypes
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, request, session, redirect, url_for,
    render_template_string, abort, send_from_directory,
    flash
)
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash


# =====================================================
# HARSHSHARE - CONFIGURATION
# =====================================================

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "harshshare_files"
DATABASE = BASE_DIR / "harshshare.db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.secret_key = os.environ.get("SECRET_KEY", "")

# Set SECRET_KEY in your hosting environment.
# Never deploy with an empty or publicly known key.
if not app.secret_key:
    if os.environ.get("RENDER"):
        raise RuntimeError("Set SECRET_KEY in Render environment variables.")
    app.secret_key = secrets.token_hex(32)
    print("WARNING: Temporary development SECRET_KEY generated.")

OWNER_USERNAME = "Tr!5h@"

# Set ADMIN_PASSWORD_HASH to a Werkzeug password hash.
# Generate one using:
# python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YourStrongPassword'))"
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "50"))
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("COOKIE_SECURE", "1") == "1"
)

# Add extensions here if you want to restrict file types.
ALLOWED_EXTENSIONS = None

# This standalone version uses local disk storage.
# Persistent storage must be configured separately on your host.


# =====================================================
# DATABASE
# =====================================================

def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                size INTEGER NOT NULL,
                mime_type TEXT,
                uploaded_at TEXT NOT NULL,
                deleted_at TEXT,
                share_token TEXT UNIQUE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                file_id TEXT,
                created_at TEXT NOT NULL
            )
        """)


def log_event(action, file_id=None):
    with db() as conn:
        conn.execute(
            """
            INSERT INTO events (action, file_id, created_at)
            VALUES (?, ?, ?)
            """,
            (
                action,
                file_id,
                datetime.now(timezone.utc).isoformat()
            )
        )


init_db()


# =====================================================
# SECURITY HELPERS
# =====================================================

def owner_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_owner"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def protect_post_requests():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        received = request.form.get("csrf_token", "")

        if not expected or not hmac.compare_digest(expected, received):
            abort(400, description="Invalid security token. Refresh and retry.")


def allowed_file(filename):
    if not filename or filename in {".", ".."}:
        return False

    if ALLOWED_EXTENSIONS is None:
        return True

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return extension in ALLOWED_EXTENSIONS


def get_file(file_id, include_deleted=False):
    with db() as conn:
        if include_deleted:
            row = conn.execute(
                "SELECT * FROM files WHERE id = ?",
                (file_id,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM files WHERE id = ? AND deleted_at IS NULL",
                (file_id,)
            ).fetchone()

    return row


def format_size(size):
    size = float(size)

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024

    return "0 B"


app.jinja_env.filters["filesize"] = format_size


# =====================================================
# COMMON DESIGN
# =====================================================

PAGE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} · HarshShare</title>

<style>
:root {
    --red: #c51f3a;
    --red-dark: #94142a;
    --pink: #fff0f2;
    --border: #f1d5d8;
    --text: #292329;
    --muted: #77717a;
    --white: #ffffff;
    --bg: #fffafb;
    --shadow: 0 12px 35px rgba(120, 20, 45, .07);
}

* { box-sizing: border-box; }

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: Inter, system-ui, -apple-system, sans-serif;
}

a { color: var(--red); text-decoration: none; }

button, input, select {
    font: inherit;
}

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 17px 5%;
    background: rgba(255,255,255,.95);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 5;
}

.brand {
    font-size: 23px;
    font-weight: 900;
    letter-spacing: -1px;
}

.brand span { color: var(--red); }

.nav {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
    align-items: center;
}

.nav a {
    font-size: 13px;
    font-weight: 750;
}

.container {
    width: min(1150px, 92%);
    margin: 32px auto 60px;
}

.hero {
    background: linear-gradient(135deg, #fff, #fff0f3);
    border: 1px solid var(--border);
    border-radius: 25px;
    padding: 30px;
    box-shadow: var(--shadow);
    margin-bottom: 24px;
}

.eyebrow {
    color: var(--red);
    font-size: 12px;
    letter-spacing: 2px;
    font-weight: 900;
}

h1 {
    font-size: clamp(28px, 5vw, 42px);
    letter-spacing: -1.5px;
    margin: 12px 0;
}

.muted { color: var(--muted); }

.owner {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    margin-top: 8px;
}

.crown {
    font-size: 32px;
    filter: drop-shadow(0 4px 6px #dca9b0);
}

.owner-name {
    font-size: 21px;
    font-weight: 900;
    color: var(--red-dark);
}

.badge {
    display: inline-block;
    background: var(--red);
    color: white;
    border-radius: 30px;
    padding: 5px 12px;
    font-size: 10px;
    letter-spacing: 1.5px;
    font-weight: 900;
}

.grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 15px;
    margin-bottom: 25px;
}

.card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 20px;
    box-shadow: var(--shadow);
    min-width: 0;
}

.stat-label {
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
}

.stat-value {
    font-size: 27px;
    font-weight: 900;
    margin-top: 8px;
    overflow-wrap: anywhere;
}

.section-title {
    font-size: 20px;
    font-weight: 900;
    margin: 25px 0 15px;
}

.toolbar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 16px;
}

input, select {
    background: white;
    border: 1px solid var(--border);
    border-radius: 11px;
    padding: 12px;
    color: var(--text);
    min-width: 0;
}

input:focus, select:focus {
    outline: 2px solid #f5c5cd;
    border-color: var(--red);
}

.search { flex: 1; min-width: 160px; }

.btn {
    border: 0;
    display: inline-flex;
    justify-content: center;
    align-items: center;
    gap: 7px;
    background: var(--red);
    color: white;
    padding: 11px 15px;
    border-radius: 11px;
    font-weight: 800;
    cursor: pointer;
}

.btn:hover { background: var(--red-dark); }

.btn.secondary {
    color: var(--red);
    background: var(--pink);
    border: 1px solid var(--border);
}

.btn.danger { background: #7e1527; }

.file-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
    border-bottom: 1px solid #f4e8e9;
    padding: 17px 0;
}

.file-row:last-child { border-bottom: 0; }

.file-name {
    font-weight: 850;
    overflow-wrap: anywhere;
}

.file-meta {
    color: var(--muted);
    font-size: 12px;
    margin-top: 5px;
}

.actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.actions .btn {
    padding: 8px 10px;
    font-size: 12px;
}

.flash {
    background: var(--pink);
    border: 1px solid var(--border);
    color: var(--red-dark);
    padding: 13px;
    border-radius: 12px;
    margin-bottom: 15px;
}

.upload-box {
    border: 2px dashed #e9b9c1;
    border-radius: 18px;
    padding: 20px;
    background: #fffafb;
}

footer {
    text-align: center;
    color: var(--muted);
    padding: 25px;
    font-size: 12px;
}

@media (max-width: 800px) {
    .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .topbar { padding: 14px 4%; }
    .hero { padding: 22px; }
}

@media (max-width: 420px) {
    .grid { grid-template-columns: 1fr 1fr; gap: 9px; }
    .card { padding: 14px; }
    .stat-value { font-size: 21px; }
}
</style>
</head>

<body>
<header class="topbar">
    <a class="brand" href="{{ url_for('home') }}">Harsh<span>Share</span> ✦</a>
    <nav class="nav">
        {% if session.get('is_owner') %}
            <a href="{{ url_for('home') }}">Dashboard</a>
            <a href="{{ url_for('recycle_bin') }}">Recycle Bin</a>
            <form method="post" action="{{ url_for('logout') }}" style="margin:0">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <button class="btn secondary" type="submit">Logout</button>
            </form>
        {% else %}
            <a href="{{ url_for('login') }}">Owner Login</a>
        {% endif %}
    </nav>
</header>

<main class="container">
    {% for message in get_flashed_messages() %}
        <div class="flash">{{ message }}</div>
    {% endfor %}

    {{ body|safe }}
</main>

<footer>
    HarshShare · White + Premium Red · Owner Access Protected
</footer>
</body>
</html>
"""


def render_page(title, body, **context):
    return render_template_string(
        PAGE,
        title=title,
        body=render_template_string(body, **context),
    )


# =====================================================
# LOGIN
# =====================================================

LOGIN_TEMPLATE = r"""
<div class="hero" style="max-width:500px;margin:40px auto">
    <div class="eyebrow">PRIVATE OWNER ACCESS</div>

    <div style="text-align:center;margin:20px 0">
        <div class="crown">👑</div>
        <div class="owner-name">Tr!5h@</div>
        <span class="badge">OWNER</span>
    </div>

    <h1 style="text-align:center">Welcome back</h1>
    <p class="muted" style="text-align:center">
        Sign in to manage your files.
    </p>

    <form method="post">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

        <label>Username</label>
        <input name="username" value="Tr!5h@" autocomplete="username"
               required style="width:100%;margin:8px 0 16px">

        <label>Password</label>
        <input name="password" type="password"
               autocomplete="current-password" required
               style="width:100%;margin:8px 0 18px">

        <button class="btn" style="width:100%" type="submit">
            Secure Login →
        </button>
    </form>
</div>
"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if not ADMIN_PASSWORD_HASH:
        return render_page(
            "Setup Required",
            """
            <div class="hero">
                <h1>Admin setup required</h1>
                <p>Set ADMIN_PASSWORD_HASH and SECRET_KEY in your
                environment before enabling login.</p>
            </div>
            """
        ), 503

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        try:
            valid_password = check_password_hash(
                ADMIN_PASSWORD_HASH, password
            )
        except (ValueError, TypeError):
            valid_password = False

        if hmac.compare_digest(username, OWNER_USERNAME) and valid_password:
            session.clear()
            session["is_owner"] = True
            session["csrf_token"] = secrets.token_urlsafe(32)
            flash("Welcome, Tr!5h@ 👑")
            return redirect(url_for("home"))

        flash("Incorrect username or password.")

    return render_page("Owner Login", LOGIN_TEMPLATE)


@app.post("/logout")
@owner_required
def logout():
    session.clear()
    return redirect(url_for("login"))


# =====================================================
# DASHBOARD
# =====================================================

HOME_TEMPLATE = r"""
<section class="hero">
    <div class="eyebrow">YOUR PERSONAL FILE CLOUD</div>
    <h1>Manage everything.<br><span style="color:var(--red)">One place.</span></h1>
    <p class="muted">Upload, organize, preview and share your files.</p>

    <div class="owner">
        <div class="crown">👑</div>
        <div class="owner-name">Tr!5h@</div>
        <span class="badge">OWNER</span>
    </div>
</section>

<section class="grid">
    <div class="card">
        <div class="stat-label">ACTIVE FILES</div>
        <div class="stat-value">{{ total_files }}</div>
    </div>
    <div class="card">
        <div class="stat-label">STORAGE USED</div>
        <div class="stat-value">{{ total_size|filesize }}</div>
    </div>
    <div class="card">
        <div class="stat-label">TRASHED FILES</div>
        <div class="stat-value">{{ trash_count }}</div>
    </div>
    <div class="card">
        <div class="stat-label">MAX UPLOAD</div>
        <div class="stat-value">{{ max_mb }} MB</div>
    </div>
</section>

<section class="card">
    <div class="section-title" style="margin-top:0">＋ Upload Files</div>
    <form class="upload-box" method="post"
          action="{{ url_for('upload') }}" enctype="multipart/form-data">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input type="file" name="files" multiple required
               style="width:100%;margin-bottom:14px">
        <button class="btn" type="submit">Upload Files ↑</button>
    </form>
    <p class="muted">Maximum request size: {{ max_mb }} MB.</p>
</section>

<div class="section-title">Your Files</div>

<form class="toolbar" method="get">
    <input class="search" name="q" value="{{ query }}"
           placeholder="Search by filename...">

    <select name="type">
        <option value="">All file types</option>
        <option value="image" {% if kind == 'image' %}selected{% endif %}>Images</option>
        <option value="pdf" {% if kind == 'pdf' %}selected{% endif %}>PDF</option>
        <option value="text" {% if kind == 'text' %}selected{% endif %}>Text</option>
        <option value="other" {% if kind == 'other' %}selected{% endif %}>Other</option>
    </select>

    <button class="btn" type="submit">Search</button>
</form>

<section class="card">
{% if files %}
    {% for f in files %}
    <div class="file-row">
        <div style="flex:1;min-width:170px">
            <div class="file-name">📄 {{ f['filename'] }}</div>
            <div class="file-meta">
                {{ f['size']|filesize }} · {{ f['uploaded_at'] }}
            </div>
        </div>

        <div class="actions">
            {% if f['mime_type'] and
                  (f['mime_type'].startswith('image/') or
                   f['mime_type'] == 'application/pdf' or
                   f['mime_type'].startswith('text/')) %}
                <a class="btn secondary"
                   href="{{ url_for('preview', file_id=f['id']) }}">Preview</a>
            {% endif %}

            <a class="btn"
               href="{{ url_for('download', file_id=f['id']) }}">Download</a>

            <form method="post"
                  action="{{ url_for('create_share', file_id=f['id']) }}">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <button class="btn secondary" type="submit">Share</button>
            </form>

            <form method="post"
                  action="{{ url_for('delete_file', file_id=f['id']) }}"
                  onsubmit="return confirm('Move this file to Recycle Bin?')">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <button class="btn danger" type="submit">Delete</button>
            </form>
        </div>
    </div>
    {% endfor %}
{% else %}
    <p class="muted">No files found. Upload your first file above.</p>
{% endif %}
</section>
"""


@app.get("/")
@owner_required
def home():
    query = request.args.get("q", "").strip()[:100]
    kind = request.args.get("type", "")

    with db() as conn:
        files = conn.execute(
            """
            SELECT * FROM files
            WHERE deleted_at IS NULL
            ORDER BY uploaded_at DESC
            """
        ).fetchall()

        trash_count = conn.execute(
            "SELECT COUNT(*) FROM files WHERE deleted_at IS NOT NULL"
        ).fetchone()[0]

    selected = []

    for f in files:
        if query and query.casefold() not in f["filename"].casefold():
            continue

        mime = f["mime_type"] or ""

        if kind == "image" and not mime.startswith("image/"):
            continue
        if kind == "pdf" and mime != "application/pdf":
            continue
        if kind == "text" and not mime.startswith("text/"):
            continue
        if kind == "other" and (
            mime.startswith("image/")
            or mime == "application/pdf"
            or mime.startswith("text/")
        ):
            continue

        selected.append(dict(f))

    total_size = sum(f["size"] for f in files)

    return render_page(
        "Dashboard",
        HOME_TEMPLATE,
        files=selected,
        total_files=len(files),
        total_size=total_size,
        trash_count=trash_count,
        max_mb=MAX_UPLOAD_MB,
        query=query,
        kind=kind,
    )


# =====================================================
# UPLOAD
# =====================================================

@app.post("/upload")
@owner_required
def upload():
    incoming = request.files.getlist("files")

    if not incoming:
        flash("Select at least one file.")
        return redirect(url_for("home"))

    successful = 0

    for file in incoming:
        if not file or not file.filename:
            continue

        filename = secure_filename(file.filename)

        if not filename or not allowed_file(filename):
            continue

        file_id = uuid.uuid4().hex
        stored_name = uuid.uuid4().hex
        destination = UPLOAD_DIR / stored_name

        # Stream the upload to disk instead of reading it all into memory.
        file.save(destination)

        size = destination.stat().st_size
        mime_type = mimety
