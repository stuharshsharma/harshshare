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

# Current ImageKit Python SDK uses the private key for server-side API calls.
IMAGEKIT_PRIVATE_KEY = os.environ.get("IMAGEKIT_PRIVATE_KEY", "")
IMAGEKIT_URL_ENDPOINT = os.environ.get("IMAGEKIT_URL_ENDPOINT", "").rstrip("/")
IMAGEKIT_FOLDER = "/harshshare"

imagekit = ImageKit(private_key=IMAGEKIT_PRIVATE_KEY) if IMAGEKIT_PRIVATE_KEY else None

app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB
ADMIN_PASSWORD = os.environ.get("HARSHSHARE_ADMIN_PASSWORD", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>HarshShare</title>
    <style>
        * { box-sizing: border-box; }
        body {
            background: #fffafa; color: #222; font-family: Arial, sans-serif;
            margin: 0; padding: 25px 15px;
        }
        main {
            max-width: 900px; margin: 30px auto; padding: 25px;
            background: #fff; border: 1px solid #f1d5d8; border-radius: 18px;
            box-shadow: 0 8px 30px rgba(180, 0, 30, .08);
        }
        h1, h2, h3 { color: #c1121f; }
        h1 { text-align: center; font-size: 36px; }
        p { color: #555; line-height: 1.6; }
        a { color: #c1121f; text-decoration: none; overflow-wrap: anywhere; }
        a:hover { color: #8b0000; }
        button {
            background: #c1121f; color: white; border: 0; border-radius: 8px;
            padding: 10px 18px; cursor: pointer;
        }
        button:hover { background: #8b0000; }
        input { margin: 10px 0; max-width: 100%; }
        input[type=password] {
            border: 1px solid #e5bfc3; border-radius: 8px; padding: 10px;
        }
        .file { padding: 14px 0; border-bottom: 1px solid #f1d5d8; overflow-wrap: anywhere; }
        .notice { background: #fff0f1; border-radius: 8px; padding: 10px; }
        .delete-form { display: inline; margin-left: 10px; }
    </style>
</head>
<body>
<main>
    <h1>Tr!5h@</h1>
    <p>Upload ki gayi files yahan dekho aur download karo.</p>

    {% with messages = get_flashed_messages() %}
      {% for message in messages %}
        <p class="notice">{{ message }}</p>
      {% endfor %}
    {% endwith %}

    {% if admin %}
        <h2>Admin: Upload file</h2>
        <form action="{{ url_for('upload') }}" method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <br><button type="submit">Upload</button>
        </form>
        <p><a href="{{ url_for('logout') }}">Admin logout</a></p>
    {% else %}
        <p><a href="{{ url_for('login') }}">Admin login</a></p>
    {% endif %}

    <h2>Available files</h2>
    {% for item in files %}
        <div class="file">
            {{ item.name }}
            — <a href="{{ url_for('download', file_id=item.id) }}">Download</a>
            {% if admin %}
                <form class="delete-form" action="{{ url_for('delete', file_id=item.id) }}" method="post"
                      onsubmit="return confirm('Delete this file?');">
                    <button type="submit">Delete</button>
                </form>
            {% endif %}
        </div>
    {% else %}
        <p>No files found yet.</p>
    {% endfor %}
</main>
</body>
</html>
"""

LOGIN_PAGE = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>HarshShare Admin Login</title></head>
<body style="font-family:Arial,sans-serif;max-width:500px;margin:40px auto;padding:20px">
<h2>Admin Login</h2>
<form method="post">
  <input type="password" name="password" placeholder="Admin password" required>
  <button type="submit">Login</button>
</form>
<p><a href="/">Back to HarshShare</a></p>
</body></html>
"""


def _to_dict(obj):
    """Convert SDK/Pydantic objects to dictionaries without assuming SDK version."""
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
        # Also try common camelCase aliases.
        camel = name.split("_")[0] + "".join(part.title() for part in name.split("_")[1:])
        if camel in data and data[camel] is not None:
            return data[camel]
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def _require_cloud():
    if not imagekit or not IMAGEKIT_PRIVATE_KEY or not IMAGEKIT_URL_ENDPOINT:
        abort(503, description="ImageKit configure nahi hai. Render Environment Variables check karein.")


def _list_cloud_files():
    """Fetch files from the HarshShare folder in ImageKit."""
    _require_cloud()
    response = imagekit.assets.list(path=IMAGEKIT_FOLDER, limit=100)
    data = _to_dict(response)
    assets = data.get("assets") or data.get("files") or data.get("results")
    if assets is None and isinstance(response, list):
        assets = response
    if assets is None:
        # Some SDK versions expose the list under a typed attribute.
        assets = getattr(response, "assets", None) or getattr(response, "files", None) or []
    result = []
    for asset in assets:
        file_id = _field(asset, "file_id", "id")
        name = _field(asset, "name", "file_name", "filename", default="Unnamed file")
        url = _field(asset, "url", "file_url")
        if file_id and name:
            result.append({"id": str(file_id), "name": str(name), "url": url or ""})
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
        PAGE, files=files, admin=session.get("admin", False), message=message
    )


@app.route("/game")
def boxing_game():
    # Keep the existing game route/template.
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
        # Read the selected file and upload it directly to ImageKit.
        file_bytes = uploaded.read()
        response = imagekit.files.upload(
            file=file_bytes,
            file_name=filename,
            folder=IMAGEKIT_FOLDER,
            use_unique_file_name=True,
        )
        uploaded_id = _field(response, "file_id", "id")
        if not uploaded_id:
            logger.error("ImageKit upload response did not contain file_id: %s", _to_dict(response))
            abort(502, description="ImageKit upload response incomplete.")
        flash("File cloud par upload ho gayi.")
    except Exception:
        logger.exception("ImageKit upload failed")
        abort(502, description="Upload fail ho gaya. ImageKit dashboard aur Render logs check karein.")
    return redirect(url_for("home"))


@app.route("/download/<path:file_id>")
def download(file_id):
    _require_cloud()
    # Only accept a file ID found inside the HarshShare folder, not arbitrary URLs.
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
        flash("File cloud se delete kar di gayi.")
    except Exception:
        logger.exception("ImageKit delete failed")
        abort(502, description="Delete fail ho gaya. ImageKit dashboard aur Render logs check karein.")
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.errorhandler(413)
def file_too_large(_error):
    return "File 100 MB se badi hai. Chhoti file try karein.", 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=False)
