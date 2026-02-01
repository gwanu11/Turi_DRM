import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import threading
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

# ===============================
# 유틸
# ===============================
def now(): return datetime.utcnow()
def hash_key(key: str) -> str: return hashlib.sha256((key + SECRET_KEY).encode()).hexdigest()

def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "w", encoding="utf-8") as f: json.dump({}, f)
        return {}
    with open(LICENSE_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_licenses(data):
    with open(LICENSE_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

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
    try: requests.post(WEBHOOK_URL, json=payload, timeout=3)
    except: pass

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
    licenses[hashed]["disabled"] = True
    licenses[hashed]["active"] = False
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
# DRM API
# ===============================
@app.route("/api/drm/check", methods=["POST"])
def api_drm_check():
    data = request.json
    key = data.get("license")
    if not key: return jsonify({"valid": False, "message": "NO_LICENSE"}), 400
    valid, msg = check_drm_logic(key)
    return jsonify({"valid": valid, "message": msg})

@app.route("/api/drm/lock", methods=["POST"])
def api_lock_license():
    data = request.json
    key = data.get("license")
    if not key: return jsonify({"success": False, "message": "NO_LICENSE"}), 400
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return jsonify({"success": False, "message": "LICENSE_NOT_FOUND"}), 404
    licenses[hashed]["disabled"] = True
    save_licenses(licenses)
    ip = request.remote_addr
    send_webhook("🚨 라이센스 강제 비활성화", "Lock API 호출됨", key, ip, 15158332)
    return jsonify({"success": True, "message": "LICENSE_DISABLED"})

# ===============================
# 로그인 & 대시보드
# ===============================
LOGIN_PAGE = """
<html>
<head>
<title>로그인 - TURI DRM</title>
<style>
body {background:#0f172a;color:white;font-family:Arial;text-align:center;padding-top:100px;}
input{padding:10px;margin:5px;border-radius:5px;border:none;}
button{padding:10px 20px;background:#6366f1;color:white;border:none;border-radius:5px;cursor:pointer;}
.box{background:#020617;padding:40px;border-radius:12px;display:inline-block;box-shadow:0 0 20px rgba(0,0,0,0.6);}
a{color:#6366f1;text-decoration:none;}
</style>
</head>
<body>
<div class="box">
<h1>🔐 로그인</h1>
<form method="POST">
<input name="id" placeholder="ID"><br>
<input name="pw" type="password" placeholder="비밀번호"><br>
<button type="submit">로그인</button>
</form>
</div>
</body>
</html>
"""

DASHBOARD_PAGE = """
<html>
<head>
<title>대시보드 - TURI DRM</title>
<style>
body {background:#0f172a;color:white;font-family:Arial;padding:50px;}
table{width:100%;border-collapse:collapse;margin-top:20px;}
th,td{padding:12px;border:1px solid #444;text-align:center;}
th{background:#6366f1;}
button{padding:5px 10px;background:#6366f1;color:white;border:none;border-radius:5px;cursor:pointer;}
</style>
</head>
<body>
<h1>💻 라이센스 대시보드</h1>
<p>로그인 ID: {{admin}}</p>
<table>
<tr><th>라이센스</th><th>활성</th><th>비활성</th><th>기간연장</th></tr>
{% for key, lic in licenses.items() %}
<tr>
<td>{{lic.raw_key}}</td>
<td>{{ "✅" if lic.active else "❌" }}</td>
<td>
<form method="POST" action="/deactivate">
<input type="hidden" name="key" value="{{lic.raw_key}}">
<button>비활성화</button>
</form>
</td>
<td>
<form method="POST" action="/extend">
<input type="hidden" name="key" value="{{lic.raw_key}}">
<input type="number" name="days" placeholder="일수" style="width:60px;">
<button>연장</button>
</form>
</td>
</tr>
{% endfor %}
</table>
<form method="POST" action="/create" style="margin-top:20px;">
<input type="number" name="days" placeholder="기간(일)">
<button>라이센스 생성</button>
</form>
</body>
</html>
"""

# ===============================
# 로그인 라우트
# ===============================
from flask import session
app.secret_key = "SUPER_SECRET_KEY"

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method=="POST":
        if request.form.get("id")==ADMIN_ID and request.form.get("pw")==ADMIN_PW:
            session["admin"]=ADMIN_ID
            return redirect(url_for("dashboard"))
    if "admin" in session: return redirect(url_for("dashboard"))
    return render_template_string(LOGIN_PAGE)

@app.route("/dashboard")
def dashboard():
    if "admin" not in session: return redirect(url_for("login"))
    raw_licenses = load_licenses()
    # 원래 키 복원
    licenses={}
    for hkey,data in raw_licenses.items():
        licenses[hkey] = data
        licenses[hkey]["raw_key"]=data.get("raw_key",hkey) # 표시용
    return render_template_string(DASHBOARD_PAGE, licenses=licenses, admin=session["admin"])

@app.route("/create", methods=["POST"])
def create():
    if "admin" not in session: return redirect(url_for("login"))
    days=int(request.form.get("days",30))
    key=create_license(days)
    # raw_key 저장
    licenses=load_licenses()
    hashed=hash_key(key)
    licenses[hashed]["raw_key"]=key
    save_licenses(licenses)
    return redirect(url_for("dashboard"))

@app.route("/deactivate", methods=["POST"])
def deactivate():
    if "admin" not in session: return redirect(url_for("login"))
    key=request.form.get("key")
    deactivate_license(key)
    return redirect(url_for("dashboard"))

@app.route("/extend", methods=["POST"])
def extend():
    if "admin" not in session: return redirect(url_for("login"))
    key=request.form.get("key")
    days=int(request.form.get("days",0))
    extend_license(key,days)
    return redirect(url_for("dashboard"))

# ===============================
# 실행
# ===============================
def admin_cli():
    while True:
        print("\n1. 라이센스 생성")
        print("2. 라이센스 활성화")
        print("3. 라이센스 비활성화")
        print("4. 라이센스 기간 연장")
        print("5. DRM 체크")
        print("0. 종료")
        cmd=input("선택: ")
        if cmd=="1": print("라이센스:",create_license(int(input("기간(일): ")) ))
        elif cmd=="2": print(activate_license(input("키: "))[1])
        elif cmd=="3": print(deactivate_license(input("키: "))[1])
        elif cmd=="4": print(extend_license(input("키: ")), int(input("연장 일수: ")) )[1]
        elif cmd=="5": print(check_drm_logic(input("키: "))[1])
        elif cmd=="0": break

if __name__=="__main__":
    threading.Thread(target=admin_cli, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
