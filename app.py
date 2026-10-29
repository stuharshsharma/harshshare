from flask import (
    Flask, request, render_template_string, abort,
    session, redirect, url_for, flash
)
from werkzeug.utils import secure_filename
from imagekitio import ImageKit
import os
import hmac
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("HARSHSHARE_SECRET_KEY", "")

IMAGEKIT_PRIVATE_KEY = os.environ.get("IMAGEKIT_PRIVATE_KEY", "")
IMAGEKIT_URL_ENDPOINT = os.environ.get("IMAGEKIT_URL_ENDPOINT", "").rstrip("/")
IMAGEKIT_FOLDER = "/harshshare"
ADMIN_PASSWORD = os.environ.get("HARSHSHARE_ADMIN_PASSWORD", "")

imagekit = (
    ImageKit(private_key=IMAGEKIT_PRIVATE_KEY)
    if IMAGEKIT_PRIVATE_KEY else None
)

app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HarshShare</title>

<style>
:root {
    --red: #e5092a;
    --dark: #172235;
    --muted: #52647d;
    --border: #f5d9df;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: linear-gradient(135deg, #ffffff, #fff4f6);
    font-family: Arial, sans-serif;
    color: var(--dark);
}

a {
    color: inherit;
}

.top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
    padding: 18px 3%;
    background: white;
    box-shadow: 0 3px 18px #18243a12;
    flex-wrap: wrap;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    text-decoration: none;
}

.logo {
    background: var(--red);
    color: white;
    border-radius: 14px;
    padding: 12px 18px;
    font-size: 27px;
}

.brand b {
    font-size: 28px;
}

.brand b span {
    color: var(--red);
}

.tag {
    color: var(--muted);
    font-size: 13px;
    margin-top: 4px;
}

nav {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
}

nav a {
    text-decoration: none;
    font-weight: bold;
    padding: 12px;
    border-radius: 20px;
}

nav a:hover {
    background: #fff0f2;
    color: var(--red);
}

.layout {
    max-width: 1450px;
    margin: 25px auto;
    padding: 0 2.5%;
    display: grid;
    grid-template-columns: minmax(0, 2fr) minmax(280px, 0.9fr);
    gap: 24px;
}

.hero {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 28px;
    margin-bottom: 20px;
    border: 1px solid var(--border);
    border-radius: 18px;
    background: linear-gradient(110deg, #fff0f2, #fffafa);
}

.crown {
    font-size: 48px;
    color: var(--red);
}

h1 {
    color: var(--red);
    font-size: 46px;
    margin: 0 0 10px;
}

.hero p {
    font-size: 16px;
    line-height: 1.5;
    margin: 0 0 16px;
}

.pill {
    display: inline-block;
    padding: 9px 14px;
    background: #ffe8ec;
    color: #b90925;
    border-radius: 25px;
    font-weight: bold;
}

.panel {
    background: white;
    border: 1px solid var(--border);
    border-radius: 17px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 4px 15px #c31b2a08;
}

.heading {
    display: flex;
    align-items: center;
    gap: 13px;
    margin-bottom: 18px;
}

.icon {
    width: 53px;
    height: 53px;
    flex-shrink: 0;
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: #ffe9ed;
    color: var(--red);
    font-size: 25px;
}

h2 {
    margin: 0 0 6px;
}

.sub {
    color: var(--muted);
    font-size: 14px;
    margin: 0;
}

.upload {
    display: flex;
    gap: 12px;
}

input[type="file"] {
    flex: 1;
    min-width: 0;
    padding: 12px;
    border: 1px solid #dce3ec;
    border-radius: 12px;
    background: white;
}

.btn {
    display: inline-flex;
    justify-content: center;
    align-items: center;
    padding: 14px 20px;
    border: 0;
    border-radius: 12px;
    background: var(--red);
    color: white;
    text-decoration: none;
    font-size: 15px;
    font-weight: bold;
    cursor: pointer;
}

.btn:hover {
    background: #b90925;
}

.grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.file {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
    flex-wrap: wrap;
    padding: 13px;
    border: 1px solid #dfe5ed;
    border-radius: 13px;
}

.filetype {
    display: grid;
    place-items: center;
    width: 45px;
    height: 48px;
    flex-shrink: 0;
    border-radius: 10px;
    background: linear-gradient(135deg, #ff5a5f, #e5092a);
    color: white;
    font-size: 12px;
    font-weight: bold;
}

.info {
    flex: 1;
    min-width: 80px;
}

.info b {
    display: block;
    overflow-wrap: anywhere;
    font-size: 14px;
    margin-bottom: 7px;
}

.download {
    padding: 10px;
    border-radius: 9px;
    background: var(--red);
    color: white;
    text-decoration: none;
    font-size: 12px;
    font-weight: bold;
}

.delete {
    padding: 9px;
    border: 0;
    border-radius: 9px;
    background: #fff0f2;
    color: var(--red);
    cursor: pointer;
    font-weight: bold;
}

.notice {
    padding: 12px;
    border-radius: 10px;
    background: #fff0f2;
    color: #9d1024;
}

.thanks {
    text-align: center;
    color: var(--red);
    font-weight: bold;
    margin-top: 20px;
}

/* GAMING ZONE */

.game {
    min-height: 480px;
    padding: 24px 18px;
    border-radius: 18px;
    color: white;
    text-align: center;
    background: radial-gradient(
        ellipse at center,
        #67111f,
        #21070d 60%,
        #10070a
    );
}

.gamehead {
    display: flex;
    align-items: center;
    gap: 12px;
    text-align: left;
}

.gamehead .icon {
    background: var(--red);
    color: white;
}

.gamehead h2 {
    font-size: 25px;
}

.gamehead p {
    color: #d2c4c8;
    margin: 0;
}

.art {
    margin: 48px 0 22px;
}

.gloves {
    font-size: 70px;
}

.boxing {
    font-size: 42px;
    font-weight: 900;
    font-style: italic;
}

.boxing span {
    display: block;
    color: #ff1737;
    font-size: 49px;
}

.caption {
    color: #d2c4c8;
    font-size: 14px;
    margin: 22px 0;
}

.play {
    width: 90%;
    padding: 16px;
    border-radius: 30px;
}

.features {
    margin-top: 20px;
    padding: 20px;
    border: 1px solid var(--border);
    border-radius: 16px;
    background: #fff7f8;
}

.feature {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 18px;
}

.feature:last-child {
    margin-bottom: 0;
}

.feature .icon {
    width: 43px;
    height: 43px;
}

.feature p {
    margin: 5px 0 0;
    font-size: 13px;
    color: var(--muted);
}

.signature {
    text-align: center;
    color: var(--red);
    font-weight: bold;
    font-style: italic;
    margin: 22px 0;
}

@media (max-width: 900px) {
    .layout {
        grid-template-columns: 1fr;
    }

    .right {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
    }

    .features {
        margin-top: 0;
    }
}

@media (max-width: 600px) {
    .top {
        padding: 15px 4%;
    }

    .brand b {
        font-size: 23px;
    }

    nav {
        width: 100%;
        justify-content: space-between;
    }

    nav a {
        padding: 8px;
        font-size: 13px;
    }

    .layout {
        padding: 0 4%;
        margin: 15px auto;
        gap: 15px;
    }

    .hero {
        padding: 20px 14px;
        gap: 12px;
    }

    .crown {
        font-size: 32px;
    }

    h1 {
        font-size: 34px;
    }

    .panel {
        padding: 16px 13px;
    }

    .upload {
        flex-direction: column;
    }

    .upload .btn {
        width: 100%;
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .right {
        display: flex;
        flex-direction: column;
    }

    .boxing {
        font-size: 37px;
    }

    .boxing span {
        font-size: 43px;
    }
}
</style>
</head>

<body>
<header class="top">
    <a class="brand" href="/">
        <div class="logo">⬆</div>
        <div>
            <b>Harsh<span>Share</span></b>
            <div class="tag">Upload · Share · Download</div>
        </div>
    </a>

    <nav>
        <a href="/">⌂ Home</a>
        <a href="/game">🎮 Game</a>
        {% if admin %}
            <a href="{{ url_for('logout') }}">Admin Logout</a>
        {% else %}
            <a href="{{ url_for('login') }}">Admin Login</a>
        {% endif %}
    </nav>
</header>

<main class="layout">
<section class="left">

    <section class="hero">
        <div class="crown">♛</div>
        <div>
            <h1>Tr!5h@</h1>
            <p>Upload ki gayi files yahan dekho aur download karo.</p>
            <span class="pill">⚡ Fast · Safe · Easy</span>
        </div>
    </section>

    {% if message %}
        <p class="notice">{{ message }}</p>
    {% endif %}

    {% with messages = get_flashed_messages() %}
        {% for message in messages %}
            <p class="notice">{{ message }}</p>
        {% endfor %}
    {% endwith %}

    {% if admin %}
    <section class="panel">
        <div class="heading">
            <div class="icon">⇧</div>
            <div>
                <h2>File Upload</h2>
                <p class="sub">Apni file select karo aur upload karo.</p>
            </div>
        </div>

        <form class="upload" action="{{ url_for('upload') }}"
              method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <button class="btn" type="submit">⇧ Upload</button>
        </form>
    </section>
    {% endif %}

    <section class="panel">
        <div class="heading">
            <div class="icon">▱</div>
            <div>
                <h2>Available Files</h2>
                <p class="sub">Yahan se files download karo.</p>
            </div>
        </div>

        {% if files %}
        <div class="grid">
            {% for item in files %}
            <article class="file">
                <div class="filetype">
                    {{ (item.name.rsplit('.', 1)[-1]
                    if '.' in item.name else 'FILE')[:4]|upper }}
                </div>

                <div class="info">
                    <b>{{ item.name }}</b>
                    <span class="sub">Ready to download</span>
                </div>

                <a class="download"
                   href="{{ url_for('download', file_id=item.id) }}">
                    ⇩ Download
                </a>

                {% if admin %}
                <form action="{{ url_for('delete', file_id=item.id) }}"
                      method="post"
                      onsubmit="return confirm('Delete this file?');">
                    <button class="delete" type="submit">Delete</button>
                </form>
                {% endif %}
            </article>
            {% endfor %}
        </div>
        {% else %}
            <p class="sub">Abhi koi file available nahi hai.</p>
        {% endif %}

        <p class="thanks">♥ Thanks for using HarshShare!</p>
    </section>
</section>

<aside class="right">
    <section class="game">
        <div class="gamehead">
            <div class="icon">🎮</div>
            <div>
                <h2>Gaming Zone</h2>
                <p>Play. Enjoy. Relax.</p>
            </div>
        </div>

        <div class="art">
            <div class="gloves">🥊 🥊</div>
            <div class="boxing">BOXING<span>ARENA</span></div>
        </div>

        <p class="caption">Fight · Win · Be the Champion</p>

        <a class="btn play" href="{{ url_for('boxing_game') }}">
            ▶ Play Now
        </a>
    </section>

    <section class="features">
        <div class="feature">
            <div class="icon">ϟ</div>
            <div>
                <b>Fast &amp; Secure</b>
                <p>Your files are ready to access.</p>
            </div>
        </div>

        <div class="feature">
            <div class="icon">🎮</div>
            <div>
                <b>Fun Gaming</b>
                <p>Take a break and play.</p>
            </div>
        </div>

        <div class="feature">
            <div class="icon">♢</div>
            <div>
                <b>Easy Access</b>
                <p>Files and games in one place.</p>
            </div>
        </div>
    </section>

    <p class="signature">Made with ♥ by Harsh</p>
</aside>
</main>
</body>
</html>
"""


LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HarshShare Admin Login</title>
</head>
<body style="font-family:Arial;max-width:500px;margin:40px auto;padding:20px">
<h2>Admin Login</h2>
<form method="post">
    <input type="password" name="password"
           placeholder="Admin password" required>
    <button type="submit">Login</button>
</form>
<p><a href="/">Back to HarshShare</a></p>
</body>
</html>
"""


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

        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value

    return default


def _require_cloud():
    if not imagekit or not IMAGEKIT_PRIVATE_KEY or not IMAGEKIT_URL_ENDPOINT:
        abort(503, description="ImageKit Environment Variables check karein.")


def _list_cloud_files():
    response = imagekit.assets.list(path=IMAGEKIT_FOLDER, limit=100)
    data = _to_dict(response)

    assets = (
        data.get("assets")
        or data.get("files")
        or data.get("results")
    )

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
        file_url = _field(asset, "url", "file_url")

        if file_id and name:
            result.append({
                "id": str(file_id),
                "name": str(name),
                "url": file_url or ""
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
        message = "Files load nahi hui. ImageKit settings aur logs check karein."

    return render_template_string(
        PAGE,
        files=files,
        admin=session.get("admin", False),
        message=message
    )


@app.route("/game")
def boxing_game():
    return render_template("game.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if not ADMIN_PASSWORD or not app.secret_key:
        return (
            "Render Environment mein "
            "HARSHSHARE_ADMIN_PASSWORD aur "
            "HARSHSHARE_SECRET_KEY set karein.",
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
        abort(400, description="Pehle file select karein.")

    filename = secure_filename(uploaded.filename)

    if not filename or filename in {".", ".."}:
        abort(400, description="Invalid filename.")

    try:
        response = imagekit.files.upload(
            file=uploaded.read(),
            file_name=filename,
            folder=IMAGEKIT_FOLDER,
            use_unique_file_name=True
        )

        uploaded_id = _field(response, "file_id", "id")

        if not uploaded_id:
            logger.error("ImageKit upload response: %s", _to_dict(response))
            abort(502, description="ImageKit upload response incomplete.")

        flash("File cloud par upload ho gayi.")

    except Exception:
        logger.exception("ImageKit upload failed")
        abort(502, description="Upload fail hua. Render logs check karein.")

    return redirect(url_for("home"))


@app.route("/download/<path:file_id>")
def download(file_id):
    _require_cloud()

    try:
        asset = next(
            (item for item in _list_cloud_files()
             if item["id"] == file_id),
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
        asset = next(
            (item for item in _list_cloud_files()
             if item["id"] == file_id),
            None
        )

        if not asset:
            abort(404)

        imagekit.files.delete(file_id)
        flash("File cloud se delete kar di gayi.")

    except Exception:
        logger.exception("ImageKit delete failed")
        abort(502, description="Delete fail hua. Render logs check karein.")

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
