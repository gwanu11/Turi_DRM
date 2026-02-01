from flask import Flask, request, jsonify, redirect, session, render_template_string
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "adonis-secret-key"
DATA_FILE = "data.json"

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
<title>Login</title>
<style>
body{background:#0f1220;color:white;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;}
.box{background:#1c2038;padding:40px;border-radius:12px;width:300px;}
input,button{width:100%;padding:10px;margin-top:10px;border-radius:6px;border:none;}
button{background:#6c63ff;color:white;cursor:pointer;}
.error{color:#ff6b6b;margin-top:10px;}
</style>
</head>
<body>
<div class="box">
<h2>🔐 LOGIN</h2>
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
<title>Dashboard</title>
<style>
body{background:#0f1220;color:white;font-family:sans-serif;padding:40px;}
.card{background:#1c2038;padding:20px;border-radius:12px;max-width:500px;}
input,button{padding:8px;border:none;border-radius:6px;margin-top:8px;}
button{background:#6c63ff;color:white;cursor:pointer;}
.danger{background:#ff4d4f;}
</style>
</head>
<body>
<div class="card">
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
