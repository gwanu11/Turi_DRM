import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import requests

# ===============================
# 설정
# ===============================
LICENSE_FILE = "licenses.json"
SECRET_KEY = "MY_SUPER_SECRET_KEY"

ADMIN_ID = "adonis"
ADMIN_PW = "adonis2023"

WEBHOOK_URL = "https://discord.com/api/webhooks/1467163104306663612/SXhdRKXIctM4AqVnmOfkFytCiJXAZK9dcc6LjS4xEYTJG5bIx-kBnPvTDp-d1YQV3Ko1"

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

def send_webhook(title, reason, key, ip, color):
    payload = {
        "username": "TURI DRM",
        "embeds": [{
            "title": title,
            "description": "DRM 보안 이벤트 감지",
            "color": color,
            "fields": [
                {"name": "📌 사유", "value": f"```{reason}```", "inline": False},
                {"name": "🔑 라이센스", "value": f"```{key}```", "inline": False},
                {"name": "🌐 IP", "value": f"```{ip}```", "inline": True},
                {"name": "🕒 시간", "value": f"```{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}```", "inline": True}
            ],
            "footer": {"text": "TURI DRM SYSTEM"},
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=3)
    except:
        pass

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
        "disabled": False
    }
    save_licenses(licenses)
    return raw_key

def activate_license(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return False, "라이센스 없음"
    if licenses[hashed]["disabled"]: return False, "비활성화된 라이센스"
    licenses[hashed]["active"] = True
    save_licenses(licenses)
    return True, "활성화 완료"

def deactivate_license(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return False, "라이센스 없음"
    licenses[hashed]["active"] = False
    licenses[hashed]["disabled"] = True
    save_licenses(licenses)
    return True, "비활성화 완료"

def extend_license(key: str, days: int):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return False, "라이센스 없음"
    expires = datetime.fromisoformat(licenses[hashed]["expires_at"])
    licenses[hashed]["expires_at"] = (expires + timedelta(days=days)).isoformat()
    save_licenses(licenses)
    return True, f"{days}일 연장 완료"

def check_drm_logic(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return False, "INVALID_LICENSE"
    lic = licenses[hashed]
    if lic["disabled"]: return False, "DISABLED"
    if not lic["active"]: return False, "NOT_ACTIVATED"
    if now() > datetime.fromisoformat(lic["expires_at"]): return False, "EXPIRED"
    return True, "OK"

# ===============================
# Flask Routes
# ===============================

# 로그인 페이지
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        id_ = request.form.get("id")
        pw = request.form.get("pw")
        if id_==ADMIN_ID and pw==ADMIN_PW:
            session["logged_in"]=True
            return redirect("/dashboard")
        return render_template_string(LOGIN_HTML, error="아이디 또는 비밀번호 오류")
    return render_template_string(LOGIN_HTML, error="")

# 대시보드
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/login")
    licenses = load_licenses()
    return render_template_string(DASH_HTML, licenses=licenses)

# DRM 체크 API
@app.route("/api/drm/check", methods=["POST"])
def api_drm_check():
    data = request.json
    key = data.get("license")
    if not key:
        return jsonify({"valid": False, "message": "NO_LICENSE"}), 400
    valid, msg = check_drm_logic(key)
    return jsonify({"valid": valid, "message": msg})

# 라이센스 Lock API
@app.route("/api/drm/lock", methods=["POST"])
def api_drm_lock():
    data = request.json
    key = data.get("license")
    if not key:
        return jsonify({"success": False, "message": "NO_LICENSE"}), 400
    success, msg = deactivate_license(key)
    return jsonify({"success": success, "message": msg})

# 홈은 로그인 페이지로 리다이렉트
@app.route("/")
def home():
    return redirect("/login")

# ===============================
# HTML 템플릿
# ===============================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>로그인 - TURI DRM</title>
<style>
body {background:#0f172a;color:white;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
.box {background:#020617;padding:40px;border-radius:12px;box-shadow:0 0 20px rgba(0,0,0,0.6);text-align:center;}
input {padding:10px;margin:10px;width:200px;border-radius:5px;border:none;}
button {padding:10px 20px;border:none;border-radius:5px;background:#1e40af;color:white;cursor:pointer;}
.error {color:#f87171;margin-bottom:10px;}
</style>
</head>
<body>
<div class="box">
<h2>🔐 로그인</h2>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="post">
<input type="text" name="id" placeholder="아이디" required><br>
<input type="password" name="pw" placeholder="비밀번호" required><br>
<button type="submit">로그인</button>
</form>
</div>
</body>
</html>
"""

DASH_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>대시보드 - TURI DRM</title>
<style>
body {background:#0f172a;color:white;font-family:Arial;padding:20px;}
table {width:100%;border-collapse:collapse;margin-top:20px;}
th,td {padding:12px;border:1px solid #333;text-align:center;}
button {padding:5px 10px;border:none;border-radius:5px;background:#1e40af;color:white;cursor:pointer;}
</style>
<script>
function deactivateLicense(key){
    fetch("/api/drm/lock",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({license:key})})
    .then(res=>res.json()).then(data=>alert(data.message)).catch(e=>alert("오류 발생"));
}
</script>
</head>
<body>
<h1>📊 TURI DRM Dashboard</h1>
<table>
<tr><th>라이센스</th><th>생성일</th><th>만료일</th><th>활성</th><th>비활성화</th><th>액션</th></tr>
{% for key,lic in licenses.items() %}
<tr>
<td>{{ key }}</td>
<td>{{ lic.created_at }}</td>
<td>{{ lic.expires_at }}</td>
<td>{{ "✅" if lic.active else "❌" }}</td>
<td>{{ "🚫" if lic.disabled else "🟢" }}</td>
<td>
<button onclick='deactivateLicense("{{ key }}")'>비활성화</button>
</td>
</tr>
{% endfor %}
</table>
</body>
</html>
"""

# ===============================
# 실행
# ===============================
if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
