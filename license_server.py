import os
import json
from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

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

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

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
</style>
</head>
<body>
<div class="box">
<h2>Secure Access</h2>
<form method="post">
<input name="id" placeholder="ID" required>
<input name="pw" type="password" placeholder="Password" required>
<button>LOGIN</button>
{% if error %}<div class="error">{{error}}</div>{% endif %}
</form>
</div>
</body>
</html>
"""

DASHBOARD_HTML = """
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
</style>
</head>
<body>
<div class="card">
<h2>License Status</h2>
<p>Status: <span class="ok">{{status}}</span></p>
<p>Expire: {{expire}}</p>
</div>
</body>
</html>
"""

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
