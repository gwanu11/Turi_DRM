import json, uuid, hashlib, os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session, render_template_string
import threading

# ===============================
# 설정
# ===============================
LICENSE_FILE = "licenses.json"
SECRET_KEY = "MY_SUPER_SECRET_KEY"
ADMIN_ID = "adonis"
ADMIN_PW = "adonis2023"

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ===============================
# 유틸
# ===============================
def now(): return datetime.utcnow()
def hash_key(key: str) -> str:
    return hashlib.sha256((key + SECRET_KEY).encode()).hexdigest()
def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "w", encoding="utf-8") as f: json.dump({}, f)
        return {}
    with open(LICENSE_FILE, "r", encoding="utf-8") as f: return json.load(f)
def save_licenses(data):
    with open(LICENSE_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

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
    if hashed not in licenses: return False,"라이센스 없음"
    if licenses[hashed]["disabled"]: return False,"비활성화된 라이센스"
    licenses[hashed]["active"]=True
    save_licenses(licenses)
    return True,"활성화 완료"
def deactivate_license(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return False,"라이센스 없음"
    licenses[hashed]["disabled"]=True
    licenses[hashed]["active"]=False
    save_licenses(licenses)
    return True,"비활성화 완료"
def extend_license(key: str, days:int):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return False,"라이센스 없음"
    expires = datetime.fromisoformat(licenses[hashed]["expires_at"])
    licenses[hashed]["expires_at"] = (expires + timedelta(days=days)).isoformat()
    save_licenses(licenses)
    return True,f"{days}일 연장 완료"
def check_drm_logic(key:str):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return False,"INVALID_LICENSE"
    lic = licenses[hashed]
    if lic["disabled"]: return False,"DISABLED"
    if not lic["active"]: return False,"NOT_ACTIVATED"
    if now() > datetime.fromisoformat(lic["expires_at"]): return False,"EXPIRED"
    return True,"OK"

# ===============================
# 🔐 DRM API
# ===============================
@app.route("/api/drm/check", methods=["POST"])
def api_drm_check():
    data = request.json
    key = data.get("license")
    if not key: return jsonify({"valid": False, "message":"NO_LICENSE"}),400
    valid,msg = check_drm_logic(key)
    return jsonify({"valid":valid,"message":msg})

@app.route("/api/drm/lock", methods=["POST"])
def api_drm_lock():
    data = request.json
    key = data.get("license")
    if not key: return jsonify({"ok":False,"message":"NO_LICENSE"}),400
    ok,msg = deactivate_license(key)
    return jsonify({"ok":ok,"message":msg})

# ===============================
# 🌐 웹 페이지
# ===============================
@app.route("/")
def home(): return redirect("/login")

# 로그인
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        user=request.form.get("username")
        pw=request.form.get("password")
        if user==ADMIN_ID and pw==ADMIN_PW:
            session["admin"]=True
            return redirect("/dashboard")
        return render_template_string("<h2>로그인 실패</h2><a href='/login'>다시</a>")
    return render_template_string("""
    <html>
    <head>
    <title>로그인</title>
    <style>
    body{background:#0f172a;color:white;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;}
    .box{background:#020617;padding:40px;border-radius:12px;box-shadow:0 0 20px rgba(0,0,0,0.6);}
    input{padding:10px;margin:5px;width:200px;border-radius:6px;border:none;}
    input[type=submit]{background:#3b82f6;color:white;cursor:pointer;width:220px;}
    </style>
    </head>
    <body>
        <div class="box">
        <h1>관리자 로그인</h1>
        <form method="post">
            <input name="username" placeholder="아이디"><br>
            <input name="password" type="password" placeholder="비밀번호"><br>
            <input type="submit" value="로그인">
        </form>
        </div>
    </body>
    </html>
    """)

# 대시보드
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if not session.get("admin"): return redirect("/login")
    licenses = load_licenses()
    message=""
    if request.method=="POST":
        action = request.form.get("action")
        key = request.form.get("key")
        days = request.form.get("days",0)
        if action=="create":
            message="생성된 라이센스: "+create_license(int(days))
        elif action=="activate":
            message=activate_license(key)[1]
        elif action=="deactivate":
            message=deactivate_license(key)[1]
        elif action=="extend":
            message=extend_license(key,int(days))[1]
    return render_template_string("""
    <html>
    <head>
    <title>대시보드</title>
    <style>
    body{background:#0f172a;color:white;font-family:Arial;padding:20px;}
    table{border-collapse:collapse;width:100%;margin-top:20px;}
    th,td{border:1px solid #333;padding:8px;text-align:center;}
    th{background:#1e293b;}
    input,select{padding:5px;margin:2px;}
    .msg{color:#3b82f6;font-weight:bold;}
    </style>
    </head>
    <body>
    <h1>관리자 대시보드</h1>
    <div class="msg">{{message}}</div>
    <form method="post">
        <select name="action">
            <option value="create">라이센스 생성</option>
            <option value="activate">라이센스 활성화</option>
            <option value="deactivate">라이센스 비활성화</option>
            <option value="extend">라이센스 기간 연장</option>
        </select>
        <input name="key" placeholder="키 (생성 제외)">
        <input name="days" placeholder="기간/연장(일)">
        <input type="submit" value="실행">
    </form>
    <table>
        <tr><th>라이센스</th><th>활성</th><th>비활성</th><th>생성일</th><th>만료일</th></tr>
        {% for k,v in licenses.items() %}
        <tr>
            <td>{{k}}</td>
            <td>{{v.active}}</td>
            <td>{{v.disabled}}</td>
            <td>{{v.created_at}}</td>
            <td>{{v.expires_at}}</td>
        </tr>
        {% endfor %}
    </table>
    </body>
    </html>
    """, licenses=licenses, message=message)

# ===============================
# CLI 관리자 (선택)
# ===============================
def admin_cli():
    while True:
        print("\n1. 라이센스 생성\n2. 활성화\n3. 비활성화\n4. 기간 연장\n5. DRM 체크\n0. 종료")
        cmd=input("선택: ")
        if cmd=="1": print("키:",create_license(int(input("기간:"))))
        elif cmd=="2": print(activate_license(input("키:"))[1])
        elif cmd=="3": print(deactivate_license(input("키:"))[1])
        elif cmd=="4": print(extend_license(input("키:"),int(input("연장일수:")))[1])
        elif cmd=="5": print(check_drm_logic(input("키:"))[1])
        elif cmd=="0": break

# ===============================
# 실행
# ===============================
if __name__=="__main__":
    threading.Thread(target=admin_cli, daemon=True).start()
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
