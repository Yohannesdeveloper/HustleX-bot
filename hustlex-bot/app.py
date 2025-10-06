from flask import Flask, render_template, request, redirect, url_for
import sqlite3, os, requests, html
from urllib.parse import urlparse
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

BOT_TOKEN = os.getenv("BOT_TOKEN", "8034250378:AAH9wK5c10AC69BerzHz7zriXs3eI6X9B5A")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003194542999")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://hustlexeth.netlify.app/")

# Allowed extensions
ALLOWED_EXTENSIONS = {"pdf", "docx", "png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Save job to DB including file paths
def save_job(job_data):
    conn = sqlite3.connect("jobs.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT, job_type TEXT, work_location TEXT,
            salary TEXT, deadline TEXT, description TEXT,
            client_type TEXT, company_name TEXT, verified TEXT,
            previous_jobs TEXT, job_link TEXT,
            cv_file TEXT, profile_image TEXT
        )
    """)
    cur.execute("""
        INSERT INTO jobs (job_title, job_type, work_location, salary, deadline, description,
            client_type, company_name, verified, previous_jobs, job_link, cv_file, profile_image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_data["job_title"], job_data["job_type"], job_data["work_location"],
        job_data["salary"], job_data["deadline"], job_data["description"],
        job_data["client_type"], job_data["company_name"], job_data["verified"],
        job_data["previous_jobs"], job_data["job_link"],
        job_data.get("cv_file"), job_data.get("profile_image")
    ))
    conn.commit()
    conn.close()

def _ensure_uploads_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"[WARN] Could not ensure uploads directory '{path}': {e}")


# Send job to Telegram channel (basic info only)
def post_to_telegram(job_data):
    if not BOT_TOKEN:
        return False, "BOT_TOKEN environment variable is not set."
    if not CHANNEL_ID:
        return False, "CHANNEL_ID environment variable is not set."

    # Safely build HTML message to avoid Markdown parsing issues
    def esc(v):
        return html.escape(str(v or "")).replace("\n", "<br>")

    # Guard: Telegram message length limit ~4096 chars. Trim description if needed.
    desc = (job_data.get('description') or '').strip()
    if len(desc) > 1500:
        desc = desc[:1500] + '…'

    job_text = (
        f"<b>📢 New Job Posted!</b><br><br>"
        f"<b>Job Title:</b> {esc(job_data.get('job_title'))}<br>"
        f"<b>Job Type:</b> {esc(job_data.get('job_type'))}<br>"
        f"<b>Location:</b> {esc(job_data.get('work_location'))}<br>"
        f"<b>Salary:</b> {esc(job_data.get('salary'))}<br>"
        f"<b>Deadline:</b> {esc(job_data.get('deadline'))}<br>"
        f"<b>Description:</b> {esc(desc)}<br>"
        f"<b>Client Type:</b> {esc(job_data.get('client_type'))}<br>"
        f"<b>Company Name:</b> {esc(job_data.get('company_name'))}<br>"
        f"<b>Verified:</b> {esc(job_data.get('verified'))}<br>"
        f"<b>Previous Jobs:</b> {esc(job_data.get('previous_jobs'))}<br><br>"
        f"From: {esc(WEBSITE_URL)}"
    )
    def normalize_url(u: str) -> str:
        u = (u or "").strip()
        if not u:
            return WEBSITE_URL
        if not (u.startswith("http://") or u.startswith("https://")):
            u = "https://" + u
        try:
            parsed = urlparse(u)
            if not parsed.scheme or not parsed.netloc:
                return WEBSITE_URL
        except Exception:
            return WEBSITE_URL
        return u
    def verify_reachable(u: str) -> str:
        try:
            r = requests.head(u, allow_redirects=True, timeout=8)
            if r.status_code >= 400:
                # Some servers don't support HEAD well; try GET quickly
                r = requests.get(u, allow_redirects=True, timeout=8)
            return u if r.status_code < 400 else WEBSITE_URL
        except Exception:
            return WEBSITE_URL
    safe_url = verify_reachable(normalize_url(job_data.get("job_link")))
    keyboard = {"inline_keyboard": [[{"text": "View Details", "url": safe_url}]]}
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": CHANNEL_ID,
            "text": job_text,
            "parse_mode": "HTML",
            "reply_markup": keyboard,
            "disable_web_page_preview": True
        }, timeout=15)
        # Telegram returns JSON with ok:true/false
        ok = False
        details = f"HTTP {resp.status_code}"
        try:
            data = resp.json()
            ok = bool(data.get("ok"))
            if not ok:
                details = data.get("description") or details
        except Exception:
            details = resp.text or details
        return ok, details if not ok else "Posted to Telegram"
    except Exception as e:
        return False, str(e)


@app.route("/telegram-test")
def telegram_test():
    """Smoke-test Telegram configuration. Optional query: ?chat_id=@name or -100..."""
    if not BOT_TOKEN:
        return {"ok": False, "error": "BOT_TOKEN not set"}, 500
    test_chat_id = request.args.get("chat_id") or CHANNEL_ID
    if not test_chat_id:
        return {"ok": False, "error": "No chat id provided and CHANNEL_ID not set"}, 500
    # Try getChat for clearer error (e.g., bot not a member / channel not found)
    try:
        info = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getChat",
            params={"chat_id": test_chat_id}, timeout=15
        )
        data = info.json()
        if not data.get("ok"):
            return {"ok": False, "stage": "getChat", "chat_id": test_chat_id, "error": data.get("description")}, 500
    except Exception as e:
        return {"ok": False, "stage": "getChat", "chat_id": test_chat_id, "error": str(e)}, 500

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": test_chat_id,
                "text": "HustleX test message ✅",
                "parse_mode": "HTML"
            }, timeout=15
        )
        j = r.json()
        return j, (200 if j.get("ok") else 500)
    except Exception as e:
        return {"ok": False, "stage": "sendMessage", "chat_id": test_chat_id, "error": str(e)}, 500


@app.route("/telegram-whoami")
def telegram_whoami():
    if not BOT_TOKEN:
        return {"ok": False, "error": "BOT_TOKEN not set"}, 500
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=15)
        j = r.json()
        return j, (200 if j.get("ok") else 500)
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500

@app.route("/post-job", methods=["GET", "POST"])
def post_job():
    if request.method == "POST":
        job_data = {k: request.form[k] for k in request.form}

        # Handle file uploads
        cv_file = request.files.get("cv_file")
        profile_image = request.files.get("profile_image")

        _ensure_uploads_dir(app.config["UPLOAD_FOLDER"])

        if cv_file and allowed_file(cv_file.filename):
            filename = secure_filename(cv_file.filename)
            cv_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            cv_file.save(cv_path)
            job_data["cv_file"] = cv_path

        if profile_image and allowed_file(profile_image.filename):
            filename = secure_filename(profile_image.filename)
            img_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            profile_image.save(img_path)
            job_data["profile_image"] = img_path

        save_job(job_data)
        ok, details = post_to_telegram(job_data)
        if not ok:
            print(f"[ERROR] Telegram post failed: {details}")
        return render_template("success.html", posted=ok, details=details)
    return render_template("post_job.html")
if __name__ == "__main__":
    app.run(debug=True)  # or use host='0.0.0.0' if needed
