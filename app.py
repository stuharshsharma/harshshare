from flask import (
    Flask, request, render_template_string, abort, session, redirect,
    url_for, flash
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

imagekit = ImageKit(private_key=IMAGEKIT_PRIVATE_KEY) if IMAGEKIT_PRIVATE_KEY else None

app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
ADMIN_PASSWORD = os.environ.get("HARSHSHARE_ADMIN_PASSWORD", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tr!5h@ | Share • Play • Grow</title>

<style>
:root {
 --red:#d10d1b;
 --deep:#8f0610;
 --ink:#17202b;
 --muted:#647184;
 --card:#fff;
 --line:#f1dadd;
 --shadow:0 10px 28px rgba(120,0,15,.09);
}

* {box-sizing:border-box}
html {scroll-behavior:smooth}

body {
 margin:0;
 background:linear-gradient(135deg,#fff,#fff6f7,#fff);
 color:var(--ink);
 font-family:Arial,sans-serif;
}

a {color:inherit;text-decoration:none}
button,input,select {font:inherit}

.topbar {
 position:sticky;
 top:0;
 z-index:10;
 display:flex;
 align-items:center;
 justify-content:space-between;
 gap:18px;
 padding:14px 4%;
 background:#ffffffed;
 border-bottom:1px solid var(--line);
}

.brand {
 font-size:30px;
 font-weight:900;
 font-style:italic;
 letter-spacing:-1.5px;
}

.brand span {color:var(--red)}

.nav {
 display:flex;
 gap:8px;
 flex-wrap:wrap;
 align-items:center;
}

.nav a,.nav button {
 border:0;
 background:transparent;
 border-radius:12px;
 padding:11px;
 cursor:pointer;
}

.nav a:hover,.nav button:hover {
 background:#fff0f1;
 color:var(--red);
}

.login {
 border:1px solid var(--red)!important;
 color:var(--red)!important;
}

.wrap {
 max-width:1440px;
 margin:auto;
 padding:26px 20px 0;
}

.welcome {
 display:grid;
 grid-template-columns:1fr 1fr;
 gap:20px;
 align-items:stretch;
}

.intro {padding:22px 10px}

.eyebrow {
 color:var(--red);
 font-size:12px;
 font-weight:800;
 letter-spacing:3px;
}

.intro h1 {
 font-size:clamp(38px,5vw,70px);
 line-height:1;
 margin:12px 0;
}

.intro h1 span {color:var(--red)}

.intro p {
 color:var(--muted);
 line-height:1.7;
}

.pills {
 display:flex;
 gap:10px;
 flex-wrap:wrap;
 margin-top:20px;
}

.pill {
 background:#fff;
 border:1px solid var(--line);
 border-radius:30px;
 padding:9px 13px;
 font-size:13px;
}

.arena {
 min-height:250px;
 border-radius:22px;
 padding:28px;
 color:white;
 background:radial-gradient(ellipse at top,#ff515b,#51030a 55%,#09090c);
 display:flex;
 flex-direction:column;
 align-items:center;
 justify-content:center;
 text-align:center;
}

.arena h2 {
 font-size:clamp(30px,4vw,48px);
 margin:12px 0;
 text-transform:uppercase;
 font-style:italic;
}

.arena p {color:#f6dfe1}

.btn {
 display:inline-flex;
 align-items:center;
 justify-content:center;
 background:linear-gradient(135deg,#f51b2b,#a4000c);
 color:white;
 border:0;
 border-radius:12px;
 padding:13px 20px;
 font-weight:bold;
 cursor:pointer;
}

.btn:hover {filter:brightness(1.1)}

.section-title {
 display:flex;
 justify-content:space-between;
 align-items:end;
 margin:28px 0 14px;
}

.section-title h2 {margin:0}

.stats {
 display:grid;
 grid-template-columns:repeat(4,1fr);
 gap:13px;
 margin-top:22px;
}

.stat,.panel,.quick {
 background:var(--card);
 border:1px solid var(--line);
 border-radius:17px;
 box-shadow:var(--shadow);
}

.stat {padding:16px}
.stat .icon {font-size:22px}
.stat strong {
 display:block;
 font-size:25px;
 margin:8px 0 3px;
}

.stat small,.muted {color:var(--muted)}

.main-grid {
 display:grid;
 grid-template-columns:1.1fr .9fr;
 gap:18px;
 margin-top:22px;
}

.panel {
 padding:20px;
 min-width:0;
}

.panel h2 {margin-top:0}

.uploadbox {
 margin-top:16px;
 border:1px dashed #e5aab0;
 border-radius:14px;
 padding:17px;
 background:#fffafb;
}

.uploadbox input[type=file] {
 max-width:100%;
 margin-bottom:12px;
}

.searchrow {
 display:flex;
 gap:9px;
 margin:16px 0 12px;
 flex-wrap:wrap;
}

.searchrow input {
 flex:1;
 min-width:150px;
 border:1px solid var(--line);
 border-radius:10px;
 padding:11px;
}

.searchrow select {
 border:1px solid var(--line);
 border-radius:10px;
 padding:11px;
}

.filelist {
 max-height:360px;
 overflow:auto;
}

.file {
 display:flex;
 align-items:center;
 gap:12px;
 padding:13px 0;
 border-bottom:1px solid #f5e7e9;
}

.fileicon {
 width:40px;
 height:40px;
 display:grid;
 place-items:center;
 border-radius:12px;
 background:#fff0f1;
 font-size:20px;
 flex-shrink:0;
}

.filename {
 font-weight:bold;
 overflow-wrap:anywhere;
}

.filemeta {
 color:var(--muted);
 font-size:12px;
 margin-top:4px;
}

.fileactions {
 margin-left:auto;
 display:flex;
 gap:7px;
 align-items:center;
}

.smallbtn {
 border:1px solid var(--line);
 border-radius:9px;
 background:#fff;
 padding:8px 10px;
 color:var(--red);
 cursor:pointer;
}

.delete-form {display:inline}

.quickgrid {
 display:grid;
 grid-template-columns:repeat(4,1fr);
 gap:13px;
}

.quick {
 padding:17px;
 transition:.18s;
}

.quick:hover {
 transform:translateY(-3px);
 border-color:#e8a3aa;
}

.qicon {font-size:24px}
.quick strong {
 display:block;
 margin:9px 0 5px;
}

.quick small {
 color:var(--muted);
 line-height:1.5;
}

.notice {
 padding:12px 14px;
 border-radius:12px;
 background:#fff0f1;
 color:#8f0610;
 margin:12px 0;
}

.empty {
 padding:24px 8px;
 color:var(--muted);
 text-align:center;
}

.footer {
 margin-top:34px;
 background:linear-gradient(120deg,#160307,#350008);
 border-top:4px solid #e90d22;
 color:white;
 padding:24px 4%;
 display:flex;
 justify-content:space-between;
 align-items:center;
 gap:16px;
 flex-wrap:wrap;
}

.footer small {color:#eacdd0}

.dark {
 --ink:#f4f4f5;
 --muted:#b7bbc5;
 --card:#19191f;
 --line:#383039;
 background:#101014;
 color:var(--ink);
}

.dark .topbar {background:#15151bee}
.dark .stat,.dark .panel,.dark .quick {background:#19191f}
.dark .searchrow input,.dark .searchrow select,
.dark .smallbtn,.dark .uploadbox {
 background:#202027;
 color:#eee;
 border-color:#383039;
}

@media(max-width:900px) {
 .welcome,.main-grid {grid-template-columns:1fr}
 .stats {grid-template-columns:repeat(2,1fr)}
 .quickgrid {grid-template-columns:repeat(2,1fr)}
}

@media(max-width:520px) {
 .topbar {align-items:flex-start;flex-direction:column}
 .nav {width:100%;gap:3px}
 .nav a,.nav button {padding:8px}
 .stats {gap:8px}
 .stat {padding:12px}
 .panel {padding:15px}
 .file {align-items:flex-start;flex-wrap:wrap}
 .fileactions {margin-left:52px}
 .quickgrid {gap:9px}
 .quick {padding:13px}
 .footer {justify-content:center;text-align:center}
}
</style>
</head>

<body id="top">

<header class="topbar">
 <a class="brand" href="{{ url_for('home') }}">Tr!<span>5</span>h@</a>
 <nav class="nav">
  <a href="{{ url_for('home') }}">⌂ Home</a>
  <a href="#files">▣ Files</a>
  <a href="{{ url_for('boxing_game') }}">🎮 Game</a>
  <a href="#tools">✦ Tools</a>
  <a href="{{ url_for('login') if not admin else url_for('logout') }}" class="login">
   {{ 'Admin Login' if not admin else 'Logout' }}
  </a>
  <button type="button" id="themeBtn">☼ Theme</button>
 </nav>
</header>

<div class="wrap">

{% with messages = get_flashed_messages() %}
{% for msg in messages %}
<div class="notice">{{ msg }}</div>
{% endfor %}
{% endwith %}

{% if message %}
<div class="notice">{{ message }}</div>
{% endif %}

<section class="welcome">
 <div class="intro">
  <div class="eyebrow">SHARE · PLAY · GROW</div>
  <h1>Your files.<br>Your <span>space.</span></h1>
  <p>Welcome to Tr!5h@ — upload, find and download files, and take a break in the game zone.</p>
  <div class="pills">
   <span class="pill">🔒 Protected uploads</span>
   <span class="pill">⚡ Quick file access</span>
   <span class="pill">☁️ Cloud storage</span>
  </div>
 </div>

 <div class="arena">
  <div>YOUR BREAK TIME</div>
  <h2>Game Zone</h2>
  <p>Take a break and jump into the arena.</p>
  <a class="btn" href="{{ url_for('boxing_game') }}">🎮 PLAY GAME ➜</a>
 </div>
</section>

<section class="stats">
 <div class="stat"><span class="icon">📁</span><strong>{{ files|length }}</strong><small>Available files</small></div>
 <div class="stat"><span class="icon">☁️</span><strong>Cloud</strong><small>File storage</small></div>
 <div class="stat"><span class="icon">🛡️</span><strong>{{ 'Admin' if admin else 'Visitor' }}</strong><small>Current access</small></div>
 <div class="stat"><span class="icon">🎮</span><strong>Game</strong><small>Ready to play</small></div>
</section>

<section class="main-grid">

<div class="panel" id="files">
 <h2>📤 File Manager</h2>
 <div class="muted">Upload and manage files from one place.</div>

 {% if admin %}
 <form class="uploadbox" action="{{ url_for('upload') }}" method="post" enctype="multipart/form-data">
  <strong>Upload a new file</strong>
  <p class="muted">Maximum file size: 100 MB</p>
  <input type="file" name="file" required>
  <br><button class="btn" type="submit">⬆ Upload File</button>
 </form>
 {% else %}
 <div class="uploadbox">
  <strong>Want to upload files?</strong>
  <p class="muted">Admin login is required to upload or delete files.</p>
  <a class="btn" href="{{ url_for('login') }}">🔑 Admin Login</a>
 </div>
 {% endif %}

 <div class="searchrow">
  <input id="fileSearch" type="search" placeholder="🔍 Search files...">
  <select id="fileCategory">
   <option value="all">All types</option>
   <option value="image">Images</option>
   <option value="video">Videos</option>
   <option value="document">Documents</option>
   <option value="other">Others</option>
  </select>
 </div>

 <div class="filelist" id="fileList">
 {% for item in files %}
 {% set ext = item.name.rsplit('.', 1)[-1].lower() if '.' in item.name else '' %}
 {% set kind = 'image' if ext in ['jpg','jpeg','png','gif','webp','svg','bmp'] else 'video' if ext in ['mp4','mov','avi','mkv','webm'] else 'document' if ext in ['pdf','doc','docx','txt','xls','xlsx','ppt','pptx','csv'] else 'other' %}
 <div class="file" data-name="{{ item.name|lower }}" data-kind="{{ kind }}">
  <div class="fileicon">{{ '🖼️' if kind == 'image' else '🎬' if kind == 'video' else '📄' if kind == 'document' else '📦' }}</div>
  <div><div class="filename">{{ item.name }}</div><div class="filemeta">{{ kind|title }}</div></div>
  <div class="fileactions">
   <a class="smallbtn" href="{{ url_for('download', file_id=item.id) }}">Download</a>
   {% if admin %}
   <form class="delete-form" action="{{ url_for('delete', file_id=item.id) }}" method="post" onsubmit="return confirm('Delete this file?')">
    <button class="smallbtn" type="submit">Delete</button>
   </form>
   {% endif %}
  </div>
 </div>
 {% endfor %}
 </div>
 <div class="empty" id="noMatches" {% if files %}hidden{% endif %}>No files found.</div>
</div>

<div class="panel" id="tools">
 <h2>✨ Quick Access</h2>
 <p class="muted">Jump straight to the section you need.</p>
 <div class="quickgrid" style="grid-template-columns:repeat(2,1fr);margin-top:15px">
  <a class="quick" href="#files"><div class="qicon">🔎</div><strong>Find Files</strong><small>Search uploaded files</small></a>
  <a class="quick" href="{{ url_for('boxing_game') }}"><div class="qicon">🎮</div><strong>Game</strong><small>Open the game zone</small></a>
  <a class="quick" href="{{ url_for('login') if not admin else url_for('logout') }}"><div class="qicon">👤</div><strong>{{ 'Admin Access' if not admin else 'Sign Out' }}</strong><small>Manage file access</small></a>
  <a class="quick" href="#top"><div class="qicon">⬆️</div><strong>Back to Top</strong><small>Return to homepage</small></a>
 </div>
 <div class="uploadbox">
  <strong>💡 Quick tip</strong>
  <p class="muted">Search by file name or filter by type.</p>
 </div>
</div>
</section>

<section class="section-title">
 <div><h2>Explore Tr!5h@</h2><p class="muted">Your files and game in one place.</p></div>
</section>

<section class="quickgrid">
 <a class="quick" href="#files"><div class="qicon">📚</div><strong>Browse Files</strong><small>See available uploads</small></a>
 <a class="quick" href="#fileSearch"><div class="qicon">🔍</div><strong>Search</strong><small>Find a file quickly</small></a>
 <a class="quick" href="{{ url_for('boxing_game') }}"><div class="qicon">🕹️</div><strong>Game</strong><small>Open the game zone</small></a>
 <a class="quick" href="{{ url_for('login') if not admin else url_for('logout') }}"><div class="qicon">⚙️</div><strong>Admin Panel</strong><small>Manage site access</small></a>
</section>
</div>

<footer class="footer">
 <div><div class="brand">Tr!<span>5</span>h@</div><small>Share · Play · Grow</small></div>
 <div>Made bye Harsh Sharma</div>
 <small>Tr!5h@ · File Sharing + Game</small>
</footer>

<script>
const search = document.getElementById('fileSearch');
const category = document.getElementById('fileCategory');

function filterFiles() {
 const q = (search.value || '').toLowerCase().trim();
 const kind = category.value;
 let visible = 0;

 document.querySelectorAll('#fileList .file').forEach(row => {
  const okName = (row.dataset.name || '').includes(q);
  const okKind = kind === 'all' || row.dataset.kind === kind;
  row.hidden = !(okName && okKind);
  if (!row.hidden) visible++;
 });

 document.getElementById('noMatches').hidden = visible !== 0;
}

search.addEventListener('input', filterFiles);
category.addEventListener('change', filterFiles);

document.getElementById('themeBtn').addEventListener('click', () => {
 document.body.classList.toggle('dark');
 try {
  localStorage.setItem('trisha-dark', document.body.classList.contains('dark') ? '1' : '0');
 } catch(e) {}
});

try {
 if (localStorage.getItem('trisha-dark') === '1') {
  document.body.classList.add('dark');
 }
} catch(e) {}
</script>
</body>
</html>
"""

LOGIN_PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tr!5h@ Admin Login</title>
<style>
body{font-family:Arial,sans-serif;background:#fff7f8;margin:0;min-height:100vh;display:grid;place-items:center;color:#20232a}
.card{background:white;border:1px solid #f1d5d8;border-radius:18px;padding:28px;width:min(90%,400px);box-shadow:0 10px 30px #8f061018}
h1{color:#c1121f;margin-top:0}
input{width:100%;padding:12px;border:1px solid #e5bfc3;border-radius:9px;margin:10px 0 16px;box-sizing:border-box}
button{background:#c1121f;color:white;border:0;border-radius:9px;padding:12px 18px;font-weight:bold;cursor:pointer}
a{color:#c1121f;text-decoration:none}
</style>
</head>
<body>
<main class="card">
<h1>Tr!5h@ Admin</h1>
<p>Sign in to upload and manage cloud files.</p>
<form method="post">
<input type="password" name="password" placeholder="Admin password" required autofocus>
<button type="submit">Login</button>
</form>
<p><a href="/">← Back to Home</a></p>
</main>
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
        abort(503, description="Render Environment Variables check karein.")


def _list_cloud_files():
    _require_cloud()
    response = imagekit.assets.list(path=IMAGEKIT_FOLDER, limit=100)
    data = _to_dict(response)
    assets = data.get("assets") or data.get("files") or data.get("results")

    if assets is None and isinstance(response, list):
        assets = response
    if assets is None:
        assets = getattr(response, "assets", None) or getattr(response, "files", None) or []

    result = []
    for asset in assets:
        file_id = _field(asset, "file_id", "id")
        name = _field(asset, "name", "file_name", "filename", default="Unnamed file")
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
        message = "Cloud files load nahi ho paayi. ImageKit credentials ya SDK logs check karein."

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
        return "Render Environment mein HARSHSHARE_ADMIN_PASSWORD aur HARSHSHARE_SECRET_KEY set karein.", 503

    if request.method == "POST":
        password = request.form.get("password", "")
        if hmac.compare_digest(password, ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("home"))

        return "Password galat hai. <a href='/login'>Dobara try karein</a>", 401

    return LOGIN_PAGE


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
            logger.error("ImageKit upload response incomplete: %s", _to_dict(response))
            abort(502, description="ImageKit upload response incomplete.")

        flash("File cloud par upload ho gayi.")

    except Exception:
        logger.exception("ImageKit upload failed")
        abort(502, description="Upload fail ho gaya. Render logs check karein.")

    return redirect(url_for("home"))


@app.route("/download/<path:file_id>")
def download(file_id):
    _require_cloud()

    try:
        files = _list_cloud_files()
        asset = next((item for item in files if item["id"] == file_id), None)

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
        asset = next((item for item in files if item["id"] == file_id), None)

        if not asset:
            abort(404)

        imagekit.files.delete(file_id)
        def _to_dict(obj):
    """Convert SDK objects to dictionaries."""
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
    """Fetch files from the HarshShare folder in ImageKit."""
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
    # Existing game page ko preserve karega.
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

    return LOGIN_PAGE


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
                "ImageKit upload response incomplete: %s",
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
