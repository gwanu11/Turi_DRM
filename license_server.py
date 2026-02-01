import os
import json
import uuid
import hashlib
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

# ===============================
# 설정
# ===============================
LICENSE_FILE = "licenses.json"
SECRET_KEY = "MY_SUPER_SECRET_KEY"
ADMIN_ID = "adonis"
ADMIN_PW = "adonis2023"

app = Flask(__name__)

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
        "disabled": False
    }
    save_licenses(licenses)
    return raw_key

def activate_license(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses:
        return False, "라이센스 없음"
    if licenses[hashed]["disabled"]:
        return False, "비활성화된 라이센스"
    licenses[hashed]["active"] = True
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

def lock_license(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses:
        return False, "라이센스 없음"
    licenses[hashed]["disabled"] = True
    licenses[hashed]["active"] = False
    save_licenses(licenses)
    return True, "잠금 완료"

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
    if not key:
        return jsonify({"valid": False, "message": "NO_LICENSE"}), 400
    valid, msg = check_drm_logic(key)
    return jsonify({"valid": valid, "message": msg})

@app.route("/api/drm/create", methods=["POST"])
def api_drm_create():
    data = request.json
    days = int(data.get("days", 30))
    key = create_license(days)
    return jsonify({"license": key})

@app.route("/api/drm/activate", methods=["POST"])
def api_drm_activate():
    data = request.json
    key = data.get("license")
    success, msg = activate_license(key)
    return jsonify({"success": success, "message": msg})

@app.route("/api/drm/deactivate", methods=["POST"])
def api_drm_deactivate():
    data = request.json
    key = data.get("license")
    success, msg = deactivate_license(key)
    return jsonify({"success": success, "message": msg})

@app.route("/api/drm/extend", methods=["POST"])
def api_drm_extend():
    data = request.json
    key = data.get("license")
    days = int(data.get("days", 0))
    success, msg = extend_license(key, days)
    return jsonify({"success": success, "message": msg})

@app.route("/api/drm/lock", methods=["POST"])
def api_drm_lock():
    data = request.json
    key = data.get("license")
    success, msg = lock_license(key)
    return jsonify({"success": success, "message": msg})

# ===============================
# 🌐 로그인/대시보드 페이지
# ===============================
LOGIN_PAGE = """
<html>
<head>
<title>로그인 - TURI DRM</title>
<style>
body {background:#0f172a;color:white;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;}
.box {background:#020617;padding:40px;border-radius:12px;box-shadow:0 0 20px rgba(0,0,0,0.6);text-align:center;width:400px;}
input {width:90%;padding:10px;margin:10px 0;border-radius:6px;border:none;}
button {padding:10px 20px;border:none;border-radius:6px;background:#6366f1;color:white;cursor:pointer;font-weight:bold;}
</style>
</head>
<body>
<div class="box">
<h2>로그인</h2>
<form method="POST" action="/login">
<input type="text" name="username" placeholder="아이디" required><br>
<input type="password" name="password" placeholder="비밀번호" required><br>
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
body {background:#0f172a;color:white;font-family:Arial;padding:20px;}
h1 {color:#6366f1;}
table {width:100%;border-collapse:collapse;margin-top:20px;}
th, td {border:1px solid #333;padding:8px;text-align:center;}
th {background:#1e293b;}
button {padding:6px 12px;border:none;border-radius:6px;background:#6366f1;color:white;cursor:pointer;}
</style>
</head>
<body>
<h1>DRM 관리자 대시보드</h1>
<p>총 라이센스: {{ total }}</p>
<table>
<tr><th>라이센스</th><th>활성</th><th>비활성</th><th>만료</th><th>생성일</th><th>행동</th></tr>
{% for k,v in licenses.items() %}
<tr>
<td>{{ v.raw }}</td>
<td>{{ "✅" if v.active else "❌" }}</td>
<td>{{ "✅" if v.disabled else "❌" }}</td>
<td>{{ v.expires_at }}</td>
<td>{{ v.created_at }}</td>
<td>
<form method="POST" action="/dashboard/action">
<input type="hidden" name="license" value="{{ v.raw }}">
<button name="action" value="activate">활성화</button>
<button name="action" value="deactivate">비활성화</button>
</form>
</td>
</tr>
{% endfor %}
</table>
</body>
</html>
"""

# ===============================
# 로그인
# ===============================
from flask import session
app.secret_key = os.urandom(24)

@app.route("/", methods=["GET"])
def home():
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form.get("username")
        p=request.form.get("password")
        if u==ADMIN_ID and p==ADMIN_PW:
            session["logged_in"]=True
            return redirect("/dashboard")
        else:
            return "<h3 style='color:red;text-align:center;'>로그인 실패</h3>"+LOGIN_PAGE
    return LOGIN_PAGE

@app.route("/dashboard", methods=["GET"])
def dashboard():
    if not session.get("logged_in"):
        return redirect("/login")
    raw_licenses={}
    for h, v in load_licenses().items():
        raw_licenses[h] = {**v, "raw": h}  # 실제 키 표시
    return render_template_string(DASHBOARD_PAGE, licenses=raw_licenses, total=len(raw_licenses))

@app.route("/dashboard/action", methods=["POST"])
def dashboard_action():
    if not session.get("logged_in"):
        return redirect("/login")
    key=request.form.get("license")
    action=request.form.get("action")
    msg=""
    if action=="activate":
        _, msg=activate_license(key)
    elif action=="deactivate":
        _, msg=deactivate_license(key)
    return f"<h3 style='color:#6366f1;text-align:center;'>{msg}</h3><a href='/dashboard'>대시보드로 돌아가기</a>"

# ===============================
# CLI 관리자
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
        if cmd=="1":
            days=int(input("기간(일): "))
            print("라이센스:", create_license(days))
        elif cmd=="2":
            print(activate_license(input("키: "))[1])
        elif cmd=="3":
            print(deactivate_license(input("키: "))[1])
        elif cmd=="4":
            key=input("키: ")
            days=int(input("연장 일수: "))
            print(extend_license(key, days)[1])
        elif cmd=="5":
            print(check_drm_logic(input("키: "))[1])
        elif cmd=="0":
            break
        else:
            print("잘못된 입력")

# ===============================
# 실행
# ===============================
if __name__=="__main__":
    threading.Thread(target=admin_cli, daemon=True).start()
    app.run(host="0.0.0.0", p
