import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, abort
import json
from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

ALLOWED_IP = "192.168.123.114"

LICENSES = {
    "ABC-123-XYZ": {
        "expires": datetime(2026, 12, 31),
        "active": True
    }
}

def get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)
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

def check_ip():
    if get_ip() != ALLOWED_IP:
        abort(403)
def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 🚫 접속 차단 페이지
@app.route("/")
def index():
    if get_ip() != ALLOWED_IP:
        return render_template_string("""
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ko">
<html>
<head>
<meta charset="UTF-8">
<title>Access Denied</title>
<title>Login</title>
<style>
body {
    background: radial-gradient(circle at top, #1a1a1a, #000);
    color: #fff;
    font-family: 'Segoe UI', sans-serif;
    height: 100vh;
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}
.card {
    background: #111;
    padding: 40px;
    border-radius: 14px;
    text-align: center;
    box-shadow: 0 0 40px rgba(255,0,0,0.2);
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
.toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #ff3b3b;
    padding: 14px 18px;
    border-radius: 10px;
    font-weight: bold;
    animation: fade 4s forwards;
input {
    width:100%;
    padding:10px;
    margin-top:10px;
    border:none;
    border-radius:6px;
}
@keyframes fade {
    0% {opacity: 0; transform: translateY(20px);}
    10% {opacity: 1; transform: translateY(0);}
    90% {opacity: 1;}
    100% {opacity: 0;}
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
</style>
</head>
<body>
<div class="card">
    <h2>🚫 접근 권한 없음</h2>
    <p>이 웹사이트에 접속할 권한이 없습니다.</p>
<div class="box">
<h2>Secure Access</h2>
<form method="post">
<input name="id" placeholder="ID" required>
<input name="pw" type="password" placeholder="Password" required>
<button>LOGIN</button>
{% if error %}<div class="error">{{error}}</div>{% endif %}
</form>
</div>
<div class="toast">접근이 차단되었습니다</div>
</body>
</html>
"""), 403
    return redirect("/admin")

# 🔑 라이선스 API
@app.route("/check_license", methods=["POST"])
def check_license():
    data = request.get_json(silent=True) or {}
    key = data.get("license")

    lic = LICENSES.get(key)
    if not lic or not lic["active"]:
        return jsonify({"valid": False}), 403

    if lic["expires"] < datetime.utcnow():
        return jsonify({"valid": False, "reason": "expired"}), 403

    return jsonify({"valid": True, "expires": lic["expires"].isoformat()})

# 🛠 관리자 페이지
@app.route("/admin", methods=["GET", "POST"])
def admin():
    check_ip()

    if request.method == "POST":
        key = request.form["key"]
        days = int(request.form["days"])

        if key not in LICENSES:
            LICENSES[key] = {
                "expires": datetime.utcnow() + timedelta(days=days),
                "active": True
            }
        else:
            LICENSES[key]["expires"] += timedelta(days=days)

        return redirect(url_for("admin"))
"""

    return render_template_string("""
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ko">
<html>
<head>
<meta charset="UTF-8">
<title>License Admin</title>
<title>Dashboard</title>
<style>
body {
    background: linear-gradient(135deg, #0f0f0f, #1a1a1a);
    color: #fff;
    font-family: 'Segoe UI', sans-serif;
    margin: 0;
    padding: 40px;
}
.container {
    max-width: 900px;
    margin: auto;
    background:#111;
    color:white;
    font-family:Arial;
    padding:40px;
}
.card {
    background: #111;
    padding: 30px;
    border-radius: 16px;
    box-shadow: 0 0 30px rgba(0,0,0,0.6);
    margin-bottom: 30px;
}
h1 {
    margin-top: 0;
}
input, button {
    padding: 12px;
    border-radius: 8px;
    border: none;
    outline: none;
    font-size: 14px;
}
input {
    background: #222;
    color: #fff;
    margin-right: 10px;
}
button {
    background: #4caf50;
    color: #fff;
    cursor: pointer;
}
button:hover {
    background: #43a047;
}
table {
    width: 100%;
    border-collapse: collapse;
    background:#1f1f1f;
    padding:30px;
    border-radius:12px;
    width:350px;
}
th, td {
    padding: 14px;
    border-bottom: 1px solid #222;
    text-align: left;
}
th {
    color: #aaa;
}
.status {
    padding: 6px 10px;
    border-radius: 20px;
    font-size: 12px;
}
.active {
    background: #2e7d32;
}
.expired {
    background: #c62828;
.ok {
    color:#4cd137;
}
</style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>🔐 License Manager</h1>
        <form method="post">
            <input name="key" placeholder="LICENSE-KEY" required>
            <input name="days" type="number" value="30">
            <button type="submit">생성 / 연장</button>
        </form>
    </div>

    <div class="card">
        <h2>📋 라이선스 목록</h2>
        <table>
            <tr>
                <th>KEY</th>
                <th>만료일</th>
                <th>상태</th>
            </tr>
            {% for k, v in licenses.items() %}
            <tr>
                <td>{{k}}</td>
                <td>{{v.expires}}</td>
                <td>
                    {% if v.expires > now %}
                        <span class="status active">ACTIVE</span>
                    {% else %}
                        <span class="status expired">EXPIRED</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
<div class="card">
<h2>License Status</h2>
<p>Status: <span class="ok">{{status}}</span></p>
<p>Expire: {{expire}}</p>
</div>
</body>
</html>
""", licenses=LICENSES, now=datetime.utcnow())
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
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

@app.route("/dashboard")
def dashboard():
    data = load_data()
    return render_template_string(
        DASHBOARD_HTML,
        status=data["license"]["status"],
        expire=data["license"]["expire"]
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
