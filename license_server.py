import json, os, uuid, hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session

# ===============================
# 설정
# ===============================
app = Flask(__name__)
app.secret_key = "SUPER_SECRET_SESSION_KEY"

LICENSE_FILE = "licenses.json"
SECRET_KEY = "MY_SUPER_SECRET_KEY"

ADMIN_ID = "adonis"
ADMIN_PW = "adonis2023"

# ===============================
# 유틸
# ===============================
def now(): return datetime.utcnow()

def hash_key(key: str) -> str:
    return hashlib.sha256((key + SECRET_KEY).encode()).hexdigest()

def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
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
# HTML 템플릿
# ===============================
LOGIN_HTML = """
<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>로그인 - TURI DRM</title>
<style>
body {background:#0f172a;color:white;font-family:'Segoe UI',Arial,sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
.box {background:#1e293b;padding:50px;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,0.5);text-align:center;width:320px;}
h2 {margin-bottom:30px;color:#facc15;}
input {padding:12px;margin:10px 0;width:100%;border-radius:8px;border:none;background:#0f172a;color:white;}
input::placeholder {color:#94a3b8;}
button {padding:12px 20px;width:100%;border:none;border-radius:8px;background:#2563eb;color:white;font-weight:bold;cursor:pointer;transition:0.3s;}
button:hover {background:#1d4ed8;}
.error {color:#f87171;margin-bottom:10px;}
</style></head><body>
<div class="box">
<h2>🔐 로그인</h2>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="post">
<input type="text" name="id" placeholder="아이디" required><br>
<input type="password" name="pw" placeholder="비밀번호" required><br>
<button type="submit">로그인</button>
</form>
</div></body></html>
"""

DASH_HTML = """
<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>대시보드 - TURI DRM</title>
<style>
body {background:#0f172a;color:white;font-family:'Segoe UI',Arial,sans-serif;padding:20px;margin:0;}
h1 {color:#facc15;text-align:center;}
.table-container {overflow-x:auto;background:#1e293b;padding:20px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.5);}
table {width:100%;border-collapse:collapse;}
th,td {padding:12px;border-bottom:1px solid #334155;text-align:center;}
th {background:#2563eb;color:white;}
tr:hover {background:#334155;}
button {padding:5px 12px;border:none;border-radius:8px;background:#ef4444;color:white;cursor:pointer;transition:0.3s;}
button:hover {background:#dc2626;}
</style>
<script>
function deactivateLicense(key){
    if(!confirm("정말로 비활성화하시겠습니까?")) return;
    fetch("/api/drm/lock",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({license:key})})
    .then(res=>res.json()).then(data=>{
        alert(data.message);
        location.reload();
    }).catch(e=>alert("오류 발생"));
}
function activateLicense(key){
    fetch("/api/drm/activate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({license:key})})
    .then(res=>res.json()).then(data=>{
        alert(data.message);
        location.reload();
    }).catch(e=>alert("오류 발생"));
}
</script>
</head><body>
<h1>📊 TURI DRM Dashboard</h1>
<div class="table-container">
<table>
<tr><th>라이센스</th><th>생성일</th><th>만료일</th><th>활성</th><th>상태</th><th>액션</th></tr>
{% for key,lic in licenses.items() %}
<tr>
<td>{{ key }}</td>
<td>{{ lic.created_at }}</td>
<td>{{ lic.expires_at }}</td>
<td>{{ "✅" if lic.active else "❌" }}</td>
<td>{{ "🚫 비활성" if lic.disabled else "🟢 활성" }}</td>
<td>
<button onclick='activateLicense("{{ key }}")'>활성화</button>
<button onclick='deactivateLicense("{{ key }}")'>비활성화</button>
</td>
</tr>
{% endfor %}
</table>
</div>
</body></html>
"""

# ===============================
# Flask 라우트
# ===============================
@app.route("/", methods=["GET"])
def home():
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        id_=request.form.get("id")
        pw=request.form.get("pw")
        if id_==ADMIN_ID and pw==ADMIN_PW:
            session["logged_in"]=True
            return redirect("/dashboard")
        else:
            return render_template_string(LOGIN_HTML,error="아이디 또는 비밀번호 오류")
    return render_template_string(LOGIN_HTML)

@app.route("/dashboard", methods=["GET"])
def dashboard():
    if not session.get("logged_in"):
        return redirect("/login")
    licenses = load_licenses()
    return render_template_string(DASH_HTML,licenses=licenses)

# ===============================
# DRM API
# ===============================
@app.route("/api/drm/activate", methods=["POST"])
def api_activate():
    key=request.json.get("license")
    success,msg=activate_license(key)
    return jsonify({"success":success,"message":msg})

@app.route("/api/drm/lock", methods=["POST"])
def api_lock():
    key=request.json.get("license")
    success,msg=deactivate_license(key)
    return jsonify({"success":success,"message":msg})

# ===============================
# 실행
# ===============================
if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000,debug=True)
