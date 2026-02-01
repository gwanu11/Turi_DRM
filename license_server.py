from flask import Flask, request, jsonify, redirect, session, render_template_string
import json
from datetime import datetime
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = "adonis-secret-key"
@@ -25,15 +26,15 @@ def save_data(data):
<title>Login</title>
<style>
body{background:#0f1220;color:white;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;}
.box{background:#1c2038;padding:40px;border-radius:12px;width:300px;}
.box{background:#1c2038;padding:40px;border-radius:12px;width:320px;}
input,button{width:100%;padding:10px;margin-top:10px;border-radius:6px;border:none;}
button{background:#6c63ff;color:white;cursor:pointer;}
.error{color:#ff6b6b;margin-top:10px;}
</style>
</head>
<body>
<div class="box">
<h2>🔐 LOGIN</h2>
<h2>🔐 ADMIN LOGIN</h2>
<form method="post">
<input name="id" placeholder="ID" required>
<input name="pw" type="password" placeholder="Password" required>
@@ -49,27 +50,55 @@ def save_data(data):
<!DOCTYPE html>
<html>
<head>
<title>Dashboard</title>
<title>DRM Dashboard</title>
<style>
body{background:#0f1220;color:white;font-family:sans-serif;padding:40px;}
.card{background:#1c2038;padding:20px;border-radius:12px;max-width:500px;}
input,button{padding:8px;border:none;border-radius:6px;margin-top:8px;}
button{background:#6c63ff;color:white;cursor:pointer;}
.danger{background:#ff4d4f;}
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
<h2>✅ DRM 관리자</h2>
<h2>🛡 DRM 라이센스 관리</h2>

<form method="post" action="/add_license">
<input name="key" placeholder="라이센스 키" required>
<input name="date" placeholder="만료일 (YYYY-MM-DD)" required>
<button>라이센스 추가</button>
<form method="post" action="/create">
<button class="create">➕ 라이센스 생성 (30일)</button>
</form>

<br>
<a href="/logout"><button class="danger">로그아웃</button></a>
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
@@ -106,7 +135,7 @@ def save_data(data):

# ================= ROUTES =================

@app.route("/", methods=["GET", "POST"])
@app.route("/", methods=["GET","POST"])
def login():
data = load_data()
if request.method == "POST":
@@ -120,24 +149,46 @@ def login():
def dashboard():
if not session.get("login"):
return redirect("/denied")
    return render_template_string(DASHBOARD_HTML)
    data = load_data()
    return render_template_string(DASHBOARD_HTML, licenses=data["licenses"])

@app.route("/add_license", methods=["POST"])
def add_license():
@app.route("/create", methods=["POST"])
def create():
if not session.get("login"):
return redirect("/denied")

data = load_data()
    key = request.form["key"]
    date = request.form["date"]
    key = str(uuid.uuid4()).upper()
    expires = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

data["licenses"][key] = {
"active": True,
        "expires": date
        "expires": expires
}
save_data(data)
return redirect("/dashboard")

@app.route("/toggle/<key>", methods=["POST"])
def toggle(key):
    if not session.get("login"):
        return redirect("/denied")

    data = load_data()
    data["licenses"][key]["active"] = not data["licenses"][key]["active"]
    save_data(data)
    return redirect("/dashboard")

@app.route("/extend/<key>", methods=["POST"])
def extend(key):
    if not session.get("login"):
        return redirect("/denied")

    data = load_data()
    old = datetime.strptime(data["licenses"][key]["expires"], "%Y-%m-%d")
    data["licenses"][key]["expires"] = (old + timedelta(days=30)).strftime("%Y-%m-%d")
    save_data(data)
    return redirect("/dashboard")

@app.route("/logout")
def logout():
session.clear()
@@ -152,9 +203,9 @@ def denied():
@app.route("/check_license", methods=["POST"])
def check_license():
data = load_data()
    license_key = request.json.get("license")
    key = request.json.get("license")

    lic = data["licenses"].get(license_key)
    lic = data["licenses"].get(key)
if not lic or not lic["active"]:
return jsonify({"valid": False}), 403
