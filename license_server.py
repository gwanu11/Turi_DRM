from flask import Flask, request, jsonify, redirect, session, render_template_string
import json
from datetime import datetime, timedelta
import uuid
import hashlib
import os
from datetime import datetime, timedelta

LICENSE_FILE = "licenses.json"
SECRET_KEY = "MY_SUPER_SECRET_KEY"


# -------------------------------
# 유틸
# -------------------------------
def now():
    return datetime.utcnow()

app = Flask(__name__)
app.secret_key = "adonis-secret-key"
DATA_FILE = "data.json"

# ================= JSON =================
def hash_key(key: str) -> str:
    return hashlib.sha256((key + SECRET_KEY).encode()).hexdigest()

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:

def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        return {}
    with open(LICENSE_FILE, "r", encoding="utf-8") as f:
return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ================= HTML =================

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Login</title>
<style>
body{background:#0f1220;color:white;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;}
.box{background:#1c2038;padding:40px;border-radius:12px;width:320px;}
input,button{width:100%;padding:10px;margin-top:10px;border-radius:6px;border:none;}
button{background:#6c63ff;color:white;cursor:pointer;}
.error{color:#ff6b6b;margin-top:10px;}
</style>
</head>
<body>
<div class="box">
<h2>🔐 ADMIN LOGIN</h2>
<form method="post">
<input name="id" placeholder="ID" required>
<input name="pw" type="password" placeholder="Password" required>
<button>Login</button>
</form>
<div class="error">{{error}}</div>
</div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>DRM Dashboard</title>
<style>
body{background:#0f1220;color:white;font-family:sans-serif;padding:40px;}
.card{background:#1c2038;padding:20px;border-radius:12px;max-width:900px;}
table{width:100%;border-collapse:collapse;margin-top:20px;}
th,td{border-bottom:1px solid #333;padding:10px;text-align:center;}
button{padding:6px 10px;border:none;border-radius:6px;cursor:pointer;}
.create{background:#6c63ff;color:white;}
.on{background:#4caf50;color:white;}
.off{background:#ff4d4f;color:white;}
.extend{background:#ffa502;color:black;}
.logout{background:#ff4d4f;color:white;margin-top:20px;}
</style>
</head>
<body>
<div class="card">
<h2>🛡 DRM 라이센스 관리</h2>

<form method="post" action="/create">
<button class="create">➕ 라이센스 생성 (30일)</button>
</form>

<table>
<tr>
<th>라이센스 키</th>
<th>상태</th>
<th>만료일</th>
<th>관리</th>
</tr>
{% for k,v in licenses.items() %}
<tr>
<td>{{k}}</td>
<td>{{"활성" if v.active else "비활성"}}</td>
<td>{{v.expires}}</td>
<td>
<form style="display:inline" method="post" action="/toggle/{{k}}">
<button class="{{'off' if v.active else 'on'}}">
{{"비활성화" if v.active else "활성화"}}
</button>
</form>
<form style="display:inline" method="post" action="/extend/{{k}}">
<button class="extend">연장(+30일)</button>
</form>
</td>
</tr>
{% endfor %}
</table>

<a href="/logout"><button class="logout">로그아웃</button></a>
</div>
</body>
</html>
"""

DENIED_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Access Denied</title>
<style>
body{background:#0f1220;}
.toast{
position:fixed;
bottom:20px;
right:20px;
background:#ff4d4f;
color:white;
padding:16px 24px;
border-radius:8px;
animation:fadein .5s;
}
@keyframes fadein{
from{opacity:0;transform:translateY(20px);}
to{opacity:1;transform:translateY(0);}
}
</style>
</head>
<body>
<div class="toast">🚫 이 웹사이트에 접속할 권한이 없습니다</div>
</body>
</html>
"""

# ================= ROUTES =================

@app.route("/", methods=["GET","POST"])
def login():
    data = load_data()
    if request.method == "POST":
        if request.form["id"] == data["account"]["id"] and request.form["pw"] == data["account"]["password"]:
            session["login"] = True
            return redirect("/dashboard")
        return render_template_string(LOGIN_HTML, error="❌ 로그인 실패")
    return render_template_string(LOGIN_HTML, error="")

@app.route("/dashboard")
def dashboard():
    if not session.get("login"):
        return redirect("/denied")
    data = load_data()
    return render_template_string(DASHBOARD_HTML, licenses=data["licenses"])

@app.route("/create", methods=["POST"])
def create():
    if not session.get("login"):
        return redirect("/denied")

    data = load_data()
    key = str(uuid.uuid4()).upper()
    expires = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    data["licenses"][key] = {
        "active": True,
        "expires": expires

def save_licenses(data):
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# -------------------------------
# 라이센스 생성
# -------------------------------
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
    save_data(data)
    return redirect("/dashboard")

@app.route("/toggle/<key>", methods=["POST"])
def toggle(key):
    if not session.get("login"):
        return redirect("/denied")
    save_licenses(licenses)
    return raw_key


# -------------------------------
# 활성화
# -------------------------------
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


# -------------------------------
# 비활성화
# -------------------------------
def deactivate_license(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "라이센스 없음"

    licenses[hashed]["disabled"] = True
    licenses[hashed]["active"] = False
    save_licenses(licenses)
    return True, "비활성화 완료"


# -------------------------------
# 기간 연장
# -------------------------------
def extend_license(key: str, days: int):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "라이센스 없음"

    expires = datetime.fromisoformat(licenses[hashed]["expires_at"])
    licenses[hashed]["expires_at"] = (expires + timedelta(days=days)).isoformat()

    save_licenses(licenses)
    return True, f"{days}일 연장 완료"


# -------------------------------
# DRM 체크 (프로그램 실행 시)
# -------------------------------
def check_drm(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "❌ 유효하지 않은 라이센스"

    lic = licenses[hashed]

    if lic["disabled"]:
        return False, "🚫 비활성화된 라이센스"

    if not lic["active"]:
        return False, "⚠ 활성화되지 않은 라이센스"

    if now() > datetime.fromisoformat(lic["expires_at"]):
        return False, "⌛ 라이센스 만료"

    return True, "✅ 라이센스 정상"

    data = load_data()
    data["licenses"][key]["active"] = not data["licenses"][key]["active"]
    save_data(data)
    return redirect("/dashboard")

@app.route("/extend/<key>", methods=["POST"])
def extend(key):
    if not session.get("login"):
        return redirect("/denied")
# -------------------------------
# 예제 CLI
# -------------------------------
def main():
    while True:
        print("\n1. 라이센스 생성")
        print("2. 라이센스 활성화")
        print("3. 라이센스 비활성화")
        print("4. 라이센스 기간 연장")
        print("5. DRM 체크")
        print("0. 종료")

    data = load_data()
    old = datetime.strptime(data["licenses"][key]["expires"], "%Y-%m-%d")
    data["licenses"][key]["expires"] = (old + timedelta(days=30)).strftime("%Y-%m-%d")
    save_data(data)
    return redirect("/dashboard")
        cmd = input("선택: ")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
        if cmd == "1":
            days = int(input("기간(일): "))
            key = create_license(days)
            print("생성된 라이센스 키:", key)

@app.route("/denied")
def denied():
    return render_template_string(DENIED_HTML)
        elif cmd == "2":
            key = input("라이센스 키: ")
            print(activate_license(key)[1])

# ================= DRM API =================
        elif cmd == "3":
            key = input("라이센스 키: ")
            print(deactivate_license(key)[1])

@app.route("/check_license", methods=["POST"])
def check_license():
    data = load_data()
    key = request.json.get("license")
        elif cmd == "4":
            key = input("라이센스 키: ")
            days = int(input("연장 일수: "))
            print(extend_license(key, days)[1])

    lic = data["licenses"].get(key)
    if not lic or not lic["active"]:
        return jsonify({"valid": False}), 403
        elif cmd == "5":
            key = input("라이센스 키: ")
            print(check_drm(key)[1])

    if datetime.now() > datetime.strptime(lic["expires"], "%Y-%m-%d"):
        return jsonify({"valid": False, "reason": "expired"}), 403
        elif cmd == "0":
            break

    return jsonify({"valid": True})
        else:
            print("잘못된 입력")

# ================= START =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    main()
