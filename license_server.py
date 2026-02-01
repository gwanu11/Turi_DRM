import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, abort

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

def check_ip():
    if get_ip() != ALLOWED_IP:
        abort(403)

# 🚫 접속 차단 페이지
@app.route("/")
def index():
    if get_ip() != ALLOWED_IP:
        return render_template_string("""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>Access Denied</title>
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
}
@keyframes fade {
    0% {opacity: 0; transform: translateY(20px);}
    10% {opacity: 1; transform: translateY(0);}
    90% {opacity: 1;}
    100% {opacity: 0;}
}
</style>
</head>
<body>
<div class="card">
    <h2>🚫 접근 권한 없음</h2>
    <p>이 웹사이트에 접속할 권한이 없습니다.</p>
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

    return render_template_string("""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>License Admin</title>
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
</div>
</body>
</html>
""", licenses=LICENSES, now=datetime.utcnow())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

