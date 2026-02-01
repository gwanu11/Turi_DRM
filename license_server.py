import os
from flask import Flask, request, jsonify, redirect, session, render_template_string
import json
from flask import Flask, request, redirect, url_for, render_template_string
from datetime import datetime

app = Flask(__name__)

app.secret_key = "adonis-secret-key"
DATA_FILE = "data.json"

# 최초 실행 시 JSON 생성
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "account": {
                "id": "adonis",
                "password": "adonis2023"
            },
            "license": {
                "status": "active",
                "expire": "2026-12-31"
            }
        }, f, indent=4, ensure_ascii=False)
# ================= JSON =================

def load_data():
with open(DATA_FILE, "r", encoding="utf-8") as f:
return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ================= HTML =================

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Login</title>
<style>
body {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
    font-family:Arial;
    color:white;
}
.box {
    background:rgba(255,255,255,0.1);
    padding:40px;
    border-radius:12px;
    box-shadow:0 0 30px rgba(0,0,0,.4);
}
input {
    width:100%;
    padding:10px;
    margin-top:10px;
    border:none;
    border-radius:6px;
}
button {
    margin-top:15px;
    width:100%;
    padding:10px;
    border:none;
    border-radius:6px;
    background:#00c6ff;
    color:black;
    font-weight:bold;
    cursor:pointer;
}
.error {
    margin-top:10px;
    color:#ff6b6b;
}
body{background:#0f1220;color:white;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;}
.box{background:#1c2038;padding:40px;border-radius:12px;width:300px;}
input,button{width:100%;padding:10px;margin-top:10px;border-radius:6px;border:none;}
button{background:#6c63ff;color:white;cursor:pointer;}
.error{color:#ff6b6b;margin-top:10px;}
</style>
</head>
<body>
<div class="box">
<h2>Secure Access</h2>
<h2>🔐 LOGIN</h2>
<form method="post">
<input name="id" placeholder="ID" required>
<input name="pw" type="password" placeholder="Password" required>
<button>LOGIN</button>
{% if error %}<div class="error">{{error}}</div>{% endif %}
<button>Login</button>
</form>
<div class="error">{{error}}</div>
</div>
</body>
</html>
@@ -88,56 +49,121 @@ def load_data():
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Dashboard</title>
<style>
body {
    background:#111;
    color:white;
    font-family:Arial;
    padding:40px;
}
.card {
    background:#1f1f1f;
    padding:30px;
    border-radius:12px;
    width:350px;
}
.ok {
    color:#4cd137;
}
body{background:#0f1220;color:white;font-family:sans-serif;padding:40px;}
.card{background:#1c2038;padding:20px;border-radius:12px;max-width:500px;}
input,button{padding:8px;border:none;border-radius:6px;margin-top:8px;}
button{background:#6c63ff;color:white;cursor:pointer;}
.danger{background:#ff4d4f;}
</style>
</head>
<body>
<div class="card">
<h2>License Status</h2>
<p>Status: <span class="ok">{{status}}</span></p>
<p>Expire: {{expire}}</p>
<h2>✅ DRM 관리자</h2>

<form method="post" action="/add_license">
<input name="key" placeholder="라이센스 키" required>
<input name="date" placeholder="만료일 (YYYY-MM-DD)" required>
<button>라이센스 추가</button>
</form>

<br>
<a href="/logout"><button class="danger">로그아웃</button></a>
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

@app.route("/", methods=["GET", "POST"])
def login():
data = load_data()
if request.method == "POST":
        if (
            request.form["id"] == data["account"]["id"]
            and request.form["pw"] == data["account"]["password"]
        ):
            return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_HTML, error="아이디 또는 비밀번호가 틀렸습니다")
    return render_template_string(LOGIN_HTML, error=None)
        if request.form["id"] == data["account"]["id"] and request.form["pw"] == data["account"]["password"]:
            session["login"] = True
            return redirect("/dashboard")
        return render_template_string(LOGIN_HTML, error="❌ 로그인 실패")
    return render_template_string(LOGIN_HTML, error="")

@app.route("/dashboard")
def dashboard():
    if not session.get("login"):
        return redirect("/denied")
    return render_template_string(DASHBOARD_HTML)

@app.route("/add_license", methods=["POST"])
def add_license():
    if not session.get("login"):
        return redirect("/denied")

data = load_data()
    return render_template_string(
        DASHBOARD_HTML,
        status=data["license"]["status"],
        expire=data["license"]["expire"]
    )
    key = request.form["key"]
    date = request.form["date"]

    data["licenses"][key] = {
        "active": True,
        "expires": date
    }
    save_data(data)
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/denied")
def denied():
    return render_template_string(DENIED_HTML)

# ================= DRM API =================

@app.route("/check_license", methods=["POST"])
def check_license():
    data = load_data()
    license_key = request.json.get("license")

    lic = data["licenses"].get(license_key)
    if not lic or not lic["active"]:
        return jsonify({"valid": False}), 403

    if datetime.now() > datetime.strptime(lic["expires"], "%Y-%m-%d"):
        return jsonify({"valid": False, "reason": "expired"}), 403

    return jsonify({"valid": True})

# ================= START =================

if __name__ == "__main__":
app.run(host="0.0.0.0", port=10000)
