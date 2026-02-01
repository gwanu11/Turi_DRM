import json, uuid, hashlib, os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, render_template, session

# ===============================
# 설정
# ===============================
LICENSE_FILE = "licenses.json"
SECRET_KEY = "MY_SUPER_SECRET_KEY"
ADMIN_ID = "adonis"
ADMIN_PW = "adonis2023"

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ===============================
# 유틸
# ===============================
def now():
    return datetime.utcnow()

def hash_key(key: str) -> str:
    return hashlib.sha256((key + SECRET_KEY).encode()).hexdigest()

def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    with open(LICENSE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_licenses(data):
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ===============================
# 라이센스 로직
# ===============================
def create_license(days: int):
    licenses = load_licenses()
    raw_key = str(uuid.uuid4()).upper()
    hashed = hash_key(raw_key)

    licenses[hashed] = {
        "created_at": now().isoformat(),
        "expires_at": (now() + timedelta(days=days)).isoformat(),
        "active": False,
        "disabled": False,
        "ip": ""
    }

    save_licenses(licenses)
    return raw_key

def activate_license(key: str, ip=None):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "라이센스 없음"

    lic = licenses[hashed]

    if lic["disabled"]:
        return False, "비활성화된 라이센스"

    if ip:
        if lic.get("ip") and lic["ip"] != ip:
            # 다른 IP에서 사용 시 자동 비활성화
            lic["disabled"] = True
            save_licenses(licenses)
            return False, f"허용되지 않은 IP에서 사용됨 ({ip}) - 자동 비활성화"

        lic["ip"] = ip  # IP 기록

    lic["active"] = True
    save_licenses(licenses)
    return True, "활성화 완료"

def deactivate_license(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "라이센스 없음"

    licenses[hashed]["disabled"] = True
    licenses[hashed]["active"] = False
    save_licenses(licenses)
    return True, "비활성화 완료"

def extend_license(key: str, days: int):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "라이센스 없음"

    expires = datetime.fromisoformat(licenses[hashed]["expires_at"])
    licenses[hashed]["expires_at"] = (expires + timedelta(days=days)).isoformat()
    save_licenses(licenses)
    return True, f"{days}일 연장 완료"

def check_drm_logic(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "INVALID_LICENSE"

    lic = licenses[hashed]

    if lic["disabled"]:
        return False, "DISABLED"

    if not lic["active"]:
        return False, "NOT_ACTIVATED"

    if now() > datetime.fromisoformat(lic["expires_at"]):
        return False, "EXPIRED"

    return True, "OK"

# ===============================
# 🔐 DRM API
# ===============================
@app.route("/api/drm/check", methods=["POST"])
def api_drm_check():
    data = request.json
    key = data.get("license")
    ip = data.get("ip")

    if not key:
        return jsonify({"valid": False, "message": "NO_LICENSE"}), 400

    valid, msg = activate_license(key, ip=ip)  # IP 포함 체크 및 활성화
    return jsonify({"valid": valid, "message": msg})

@app.route("/api/drm/lock", methods=["POST"])
def api_drm_lock():
    data = request.json
    key = data.get("license")
    if not key:
        return jsonify({"ok": False, "message": "NO_LICENSE"}), 400
    ok, msg = deactivate_license(key)
    return jsonify({"ok": ok, "message": msg})

# ===============================
# 웹 UI
# ===============================
@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u == ADMIN_ID and p == ADMIN_PW:
            session["admin"] = True
            return redirect("/dashboard")
        return render_template("login.html", error="로그인 실패")
    return render_template("login.html")

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if not session.get("admin"):
        return redirect("/login")
    licenses = load_licenses()
    msg = ""
    if request.method == "POST":
        action = request.form.get("action")
        key = request.form.get("key")
        days = request.form.get("days", 0)
        if action == "create":
            msg = "생성된 라이센스: " + create_license(int(days))
        elif action == "activate":
            msg = activate_license(key)[1]
        elif action == "deactivate":
            msg = deactivate_license(key)[1]
        elif action == "extend":
            msg = extend_license(key, int(days))[1]
    return render_template("dashboard.html", licenses=licenses, message=msg, now=now().isoformat())

# ===============================
# 실행
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
