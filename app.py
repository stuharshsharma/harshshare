from flask import (
    Flask, request, render_template, render_template_string,
    abort, session, redirect, url_for, flash
)
from werkzeug.utils import secure_filename
from imagekitio import ImageKit
import os
import hmac
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("HARSHSHARE_SECRET_KEY", "")

# Existing ImageKit configuration — unchanged
IMAGEKIT_PRIVATE_KEY = os.environ.get("IMAGEKIT_PRIVATE_KEY", "")
IMAGEKIT_URL_ENDPOINT = os.environ.get("IMAGEKIT_URL_ENDPOINT", "").rstrip("/")
IMAGEKIT_FOLDER = "/harshshare"

imagekit = ImageKit(private_key=IMAGEKIT_PRIVATE_KEY) if IMAGEKIT_PRIVATE_KEY else None

app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
ADMIN_PASSWORD = os.environ.get("HARSHSHARE_ADMIN_PASSWORD", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =========================
# HOMEPAGE DESIGN
# =========================

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#c1121f">
<title>HarshShare | Share & Play</title>

<style>
:root {
    --red: #c1121f;
    --dark-red: #920d17;
    --light-red: #fff0f1;
    --text: #241c1d;
    --muted: #74696a;
    --border: #f0dadd;
    --white: #ffffff;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #fffafa;
    color: var(--text);
    font-family: Arial, Helvetica, sans-serif;
}

a {
    text-decoration: none;
    overflow-wrap: anywhere;
}

.navbar {
    background: white;
    border-bottom: 1px solid var(--border);
}

.nav-inner {
    max-width: 1100px;
    margin: auto;
    padding: 17px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--text);
    font-size: 22px;
    font-weight: 800;
}

.brand-icon {
    display: grid;
    place-items: center;
    width: 40px;
    height: 40px;
    color: white;
    background: var(--red);
    border-radius: 12px;
}

.nav-link {
    color: var(--red);
    font-size: 14px;
    font-weight: bold;
}

.container {
    max-width: 1100px;
    margin: auto;
    padding: 35px 22px 50px;
}

.hero {
    text-align: center;
    padding: 20px 0 35px;
}

.badge {
    display: inline-block;
    padding: 8px 13px;
    color: var(--red);
    background: white;
    border: 1px solid var(--border);
    border-radius: 30px;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
}

.hero h1 {
    margin: 18px 0 12px;
    font-size: clamp(34px, 5vw, 52px);
    letter-spacing: -1.5px;
}

.hero h1 span {
    color: var(--red);
}

.hero p {
    max-width: 570px;
    margin: auto;
    color: var(--muted);
    line-height: 1.7;
}

.grid {
    display: grid;
    grid-template-columns: 1.1fr .9fr;
    gap: 22px;
}

.card {
    min-width: 0;
    padding: 25px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(100, 0, 15, .05);
}

.card-heading {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 20px;
}

.icon {
    flex-shrink: 0;
    width: 48px;
    height: 48px;
    display: grid;
    place-items: center;
    background: var(--light-red);
    border-radius: 14px;
    font-size: 24px;
}

h2 {
    margin: 0 0 7px;
    font-size: 22px;
}

.subtitle {
    margin: 0;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.6;
}

.upload-box {
    padding: 18px;
    background: #fffafa;
    border: 1px dashed #e5bfc3;
    border-radius: 14px;
}

input[type=file] {
    display: block;
    width: 100%;
    margin: 0 0 15px;
}

button, .btn {
    display: inline-block;
    padding: 12px 17px;
    color: white;
    background: var(--red);
    border: none;
    border-radius: 10px;
    font-family: inherit;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
    text-align: center;
}

button:hover, .btn:hover {
    color: white;
    background: var(--dark-red);
}

.outline-btn {
    color: var(--red);
    background: white;
    border: 1px solid var(--border);
}

.outline-btn:hover {
    color: var(--dark-red);
    background: var(--light-red);
}

.game-card {
    position: relative;
    overflow: hidden;
    color: white;
    background: linear-gradient(145deg, #d51b2a, #850b15);
    border-color: #a80d1a;
}

.game-card h2 {
    color: white;
}

.game-card .subtitle {
    color: #ffe5e7;
}

.game-card .icon {
    background: rgba(255,255,255,.16);
}

.game-tag {
    display: inline-block;
    margin: 8px 0 18px;
    padding: 8px 12px;
    border: 1px solid rgba(255,255,255,.3);
    border-radius: 30px;
    font-size: 12px;
    font-weight: bold;
}

.game-card .btn {
    color: var(--red);
    background: white;
}

.game-card .btn:hover {
    background: #fff0f1;
}

.files-card {
    margin-top: 22px;
}

.files-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 12px;
}

.file-count {
    color: var(--muted);
    font-size: 12px;
}

.file {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 15px 0;
    border-bottom: 1px solid #f4e6e8;
}

.file:last-child {
    border-bottom: none;
}

.file-name {
    min-width: 0;
    overflow-wrap: anywhere;
    font-size: 14px;
    font-weight: bold;
}

.file-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}

.file-actions .btn,
.file-actions button {
    padding: 9px 11px;
    font-size: 12px;
}

.delete-form {
    display: inline;
    margin: 0;
}

.notice {
    margin-bottom: 17px;
    padding: 13px 15px;
    color: var(--dark-red);
    background: var(--light-red);
    border: 1px solid var(--border);
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.5;
}

.empty {
    padding: 25px 10px;
    text-align: center;
    color: var(--muted);
    background: #fffafa;
    border-radius: 12px;
}

.footer {
    padding: 27px 0 0;
    color: #8a7e80;
    text-align: center;
    font-size: 12px;
}

@media (max-width: 760px) {
    .container {
        padding: 22px 14px 35px;
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .card {
        padding: 20px;
        border-radius: 17px;
    }

    .hero {
        padding: 25px 0;
    }

    .hero h1 {
        letter-spacing: -1px;
    }

    .files-card {
        margin-top: 16px;
    }
}

@media (max-width: 430px) {
    .nav-inner {
        padding: 14px;
    }

    .brand {
        font-size: 19px;
    }

    .file {
        align-items: flex-start;
        flex-direction: column;
    }

    .file-actions {
        width: 100%;
        flex-wrap: wrap;
    }
}
</style>
</head>

<body>
<header class="navbar">
    <nav class="nav-inner">
        <a href="/" class="brand">
            <span class="brand-icon">H</span>
            <span>HarshShare</span>
        </a>

        {% if admin %}
            <a class="nav-link" href="{{ url_for('logout') }}">Admin Logout ↗</a>
        {% else %}
            <a class="nav-link" href="{{ url_for('login') }}">Admin Login ↗</a>
        {% endif %}
    </nav>
</header>

<main class="container">

    <section class="hero">
        <span class="badge">SIMPLE · FAST · YOURS</span>
        <h1>Share files. <span>Play more.</span></h1>
        <p>Your personal space to access shared files and enjoy your gaming zone.</p>
    </section>

    {% with messages = get_flashed_messages() %}
        {% for message in messages %}
            <div class="notice">{{ message }}</div>
        {% endfor %}
    {% endwith %}

    {% if message %}
        <div class="notice">{{ message }}</div>
    {% endif %}

    <section class="grid">

        <div class="card">
            <div class="card-heading">
                <div class="icon">📁</div>
                <div>
                    <h2>File Sharing</h2>
                    <p class="subtitle">Your files, all in one place.</p>
                </div>
            </div>

            {% if admin %}
                <div class="upload-box">
                    <p class="subtitle" style="margin-bottom:15px">
                        Upload a file to your cloud storage.
                    </p>

                    <form action="{{ url_for('upload') }}"
                          method="post"
                          enctype="multipart/form-data">
                        <input type="file" name="file" required>
                        <button type="submit">↑ Upload File</button>
                    </form>
                </div>
            {% else %}
                <p class="subtitle">
                    Browse available files below and download the files you need.
                    Admin access is required to upload or delete files.
                </p>

                <a class="btn outline-btn"
                   href="{{ url_for('login') }}"
                   style="margin-top:17px">
                    Admin Login
                </a>
            {% endif %}
        </div>

        <div class="card game-card">
            <div class="card-heading">
                <div class="icon">🎮</div>
                <div>
                    <h2>Gaming Zone</h2>
                    <p class="subtitle">Take a break. Test your skills.</p>
                </div>
            </div>

            <div class="game-tag">⚡ READY TO PLAY</div>

            <p class="subtitle" style="margin-bottom:22px">
                Enter the arena and play your boxing game.
            </p>

            <a class="btn" href="{{ url_for('boxing_game') }}">
                ▶ Play Now
            </a>
        </div>

    </section>

    <section class="card files-card">
        <div class="files-heading">
            <h2>Available Files</h2>
            <span class="file-count">{{ files|length }} file(s)</span>
        </div>

        {% for item in files %}
            <div class="file">
                <div class="file-name">📄 {{ item.name }}</div>

                <div class="file-actions">
                    <a class="btn"
                       href="{{ url_for('download', file_id=item.id) }}">
                        ↓ Download
                    </a>

                    {% if admin %}
                        <form class="delete-form"
                              action="{{ url_for('delete', file_id=item.id) }}"
                              method="post"
                              onsubmit="return confirm('Delete this file?');">
                            <button type="submit">Delete</button>
                        </form>
                    {% endif %}
                </div>
            </div>
        {% else %}
            <div class="empty">No files found yet.</div>
        {% endfor %}
    </section>

    <footer class="footer">
        HarshShare · Share responsibly
    </footer>
</main>
</body>
</html>
"""


LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HarshShare Admin Login</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    min-height: 100vh;
    display: grid;
    place-items: center;
    padding: 18px;
    background: #fffafa;
    color: #241c1d;
    font-family: Arial, sans-serif;
}
.card {
    width: 100%;
    max-width: 420px;
    padding: 28px;
    background: white;
    border: 1px solid #f0dadd;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(100,0,15,.06);
}
.mark {
    display: grid;
    place-items: center;
    width: 46px;
    height: 46px;
    border-radius: 14px;
    color: white;
    background: #c1121f;
    font-size: 22px;
    font-weight: bold;
}
h1 { font-size: 25px; margin: 18px 0 8px; }
p { color: #74696a; line-height: 1.6; font-size: 14px; }
label { display: block; margin: 20px 0 8px; font-size: 13px; font-weight: bold; }
input {
    width: 100%;
    padding: 12px;
    border: 1px solid #e5bfc3;
    border-radius: 10px;
}
button {
    width: 100%;
    margin-top: 14px;
    padding: 12px;
    color: white;
    background: #c1121f;
    border: 0;
    border-radius: 10px;
    font-weight: bold;
    cursor: pointer;
}
button:hover { background: #920d17; }
a { color: #c1121f; text-decoration: none; font-weight: bold; }
</style>
</head>
<body>
<div class="card">
    <div class="mark">H</div>
    <h1>Admin Login</h1>
    <p>Sign in to manage your HarshShare files.</p>

    <form method="post">
        <label for="password">Admin password</label>
        <input id="password" type="password"
               name="password"
               placeholder="Enter admin password"
               required>
        <button type="submit">Login</button>
    </form>

    <p><a href="/">← Back to HarshShare</a></p>
</div>
</body>
</html>
"""


# =========================
# EXISTING CLOUD FUNCTIONS
# =========================

def _to_dict(obj):
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(by_alias=False)
    if hasattr(obj, "dict"):
        return obj.dict()
    return {}


def _field(obj, *names, default=None):
    data = _to_dict(obj)

    for name in names:
        if name in data and data[name] is not None:
            return data[name]

        camel = name.split("_")[0] + "".join(
            part.title() for part in name.split("_")[1:]
        )

        if camel in data and data[camel] is not None:
            return data[camel]

        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value

    return default


def _require_cloud():
    if not imagekit or not IMAGEKIT_PRIVATE_KEY or not IMAGEKIT_URL_ENDPOINT:
        abort(
            503,
            description="ImageKit configure nahi hai. Render Environment Variables check karein."
        )


def _list_cloud_files():
    """Fetch files from the existing HarshShare ImageKit folder."""
    _require_cloud()

    response = imagekit.assets.list(path=IMAGEKIT_FOLDER, limit=100)
    data = _to_dict(response)

    assets = data.get("assets") or data.get("files") or data.get("results")

    if assets is None and isinstance(response, list):
        assets = response

    if assets is None:
        assets = (
            getattr(response, "assets", None)
            or getattr(response, "files", None)
            or []
        )

    result = []

    for asset in assets:
        file_id = _field(asset, "file_id", "id")
        name = _field(
            asset, "name", "file_name", "filename",
            default="Unnamed file"
        )
        url = _field(asset, "url", "file_url")

        if file_id and name:
            result.append({
                "id": str(file_id),
                "name": str(name),
                "url": url or ""
            })

    return sorted(result, key=lambda item: item["name"].lower())


@app.route("/")
def home():
    try:
        files = _list_cloud_files()
        message = ""
    except Exception:
        logger.exception("Could not list ImageKit files")
        files = []
        message = (
            "Cloud files load nahi ho paayi. "
            "ImageKit credentials ya SDK logs check karein."
        )

    return render_template_string(
        PAGE,
        files=files,
        admin=session.get("admin", False),
        message=message
    )


@app.route("/game")
def boxing_game():
    # Existing game template is preserved.
    return render_template("game.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if not ADMIN_PASSWORD or not app.secret_key:
        return (
            "Render Environment mein HARSHSHARE_ADMIN_PASSWORD "
            "aur HARSHSHARE_SECRET_KEY set karein.",
            503
        )

    if request.method == "POST":
        password = request.form.get("password", "")

        if hmac.compare_digest(password, ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("home"))

        return "Password galat hai. <a href='/login'>Dobara try karein</a>", 401

    return render_template_string(LOGIN_PAGE)


@app.route("/upload", methods=["POST"])
def upload():
    if not session.get("admin"):
        abort(403)

    _require_cloud()

    uploaded = request.files.get("file")

    if not uploaded or not uploaded.filename:
        abort(400, description="File select karein.")

    filename = secure_filename(uploaded.filename)

    if not filename or filename in {".", ".."}:
        abort(400, description="Invalid filename.")

    try:
        file_bytes = uploaded.read()

        response = imagekit.files.upload(
            file=file_bytes,
            file_name=filename,
            folder=IMAGEKIT_FOLDER,
            use_unique_file_name=True,
        )

        uploaded_id = _field(response, "file_id", "id")

        if not uploaded_id:
            logger.error(
                "ImageKit upload response did not contain file_id: %s",
                _to_dict(response)
            )
            abort(502, description="ImageKit upload response incomplete.")

        flash("File cloud par upload ho gayi.")

    except Exception:
        logger.exception("ImageKit upload failed")
        abort(
            502,
            description="Upload fail ho gaya. ImageKit dashboard aur Render logs check karein."
        )

    return redirect(url_for("home"))


@app.route("/download/<path:file_id>")
def download(file_id):
    _require_cloud()

    try:
        files = _list_cloud_files()
        asset = next(
            (item for item in files if item["id"] == file_id),
            None
        )

        if not asset:
            abort(404)

        if not asset["url"]:
            abort(404, description="File URL nahi mili.")

        return redirect(asset["url"])

    except Exception:
        logger.exception("ImageKit download lookup failed")
        abort(502, description="File locate nahi ho paayi.")


@app.route("/delete/<path:file_id>", methods=["POST"])
def delete(file_id):
    if not session.get("admin"):
        abort(403)

    _require_cloud()

    try:
        files = _list_cloud_files()
        asset = next(
            (item for item in files if item["id"] == file_id),
            None
        )

        if not asset:
            abort(404)

        imagekit.files.delete(file_id)
        flash("File cloud se delete kar di gayi.")

    except Exception:
        logger.exception("ImageKit delete failed")
        abort(
            502,
            description="Delete fail ho gaya. ImageKit dashboard aur Render logs check karein."
        )

    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.errorhandler(413)
def file_too_large(_error):
    return "File 100 MB se badi hai. Chhoti file try karein.", 413


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False
    )
