import json, uuid, hashlib, os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from functools import wraps

# ===============================
# 설정
# ===============================
LICENSE_FILE = "licenses.json"
SECRET_KEY = "MY_SUPER_SECRET_KEY"
ADMIN_ID = "adonis"
ADMIN_PW = "adonis2023"

app = Flask(__name__)
app.secret_key = "SUPER_SECRET_SESSION_KEY"

# ===============================
# 유틸
# ===============================
def now(): return datetime.utcnow()
def hash_key(key: str) -> str: return hashlib.sha256((key+SECRET_KEY).encode()).hexdigest()
def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE,"w",encoding="utf-8") as f: json.dump({},f)
    with open(LICENSE_FILE,"r",encoding="utf-8") as f: return json.load(f)
def save_licenses(data):
    with open(LICENSE_FILE,"w",encoding="utf-8") as f: json.dump(data,f,indent=4,ensure_ascii=False)
def check_drm_logic(key: str):
    licenses=load_licenses();hashed=hash_key(key)
    if hashed not in licenses: return False,"INVALID_LICENSE"
    lic=licenses[hashed]
    if lic["disabled"]: return False,"DISABLED"
    if not lic["active"]: return False,"NOT_ACTIVATED"
    if now()>datetime.fromisoformat(lic["expires_at"]): return False,"EXPIRED"
    return True,"OK"
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"): return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ===============================
# 라이센스 로직
# ===============================
def create_license(days:int):
    licenses=load_licenses();raw_key=str(uuid.uuid4()).upper();hashed=hash_key(raw_key)
    licenses[hashed]={"created_at":now().isoformat(),"expires_at":(now()+timedelta(days=days)).isoformat(),"active":False,"disabled":False}
    save_licenses(licenses)
    return raw_key
def activate_license(key:str):
    licenses=load_licenses();hashed=hash_key(key)
    if hashed not in licenses: return False,"라이센스 없음"
    if licenses[hashed]["disabled"]: return False,"비활성화된 라이센스"
    licenses[hashed]["active"]=True; save_licenses(licenses)
    return True,"활성화 완료"
def deactivate_license(key:str):
    licenses=load_licenses();hashed=hash_key(key)
    if hashed not in licenses: return False,"라이센스 없음"
    licenses[hashed]["active"]=False; licenses[hashed]["disabled"]=True
    save_licenses(licenses); return True,"비활성화 완료"
def extend_license(key:str,days:int):
    licenses=load_licenses();hashed=hash_key(key)
    if hashed not in licenses: return False,"라이센스 없음"
    expires=datetime.fromisoformat(licenses[hashed]["expires_at"])
    licenses[hashed]["expires_at"]=(expires+timedelta(days=days)).isoformat()
    save_licenses(licenses)
    return True,f"{days}일 연장 완료"

# ===============================
# 🔐 웹 로그인
# ===============================
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        id_=request.form.get("id");pw=request.form.get("pw")
        if id_==ADMIN_ID and pw==ADMIN_PW: session["logged_in"]=True; return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_PAGE,error="아이디 또는 비밀번호 오류")
    return render_template_string(LOGIN_PAGE,error="")

LOGIN_PAGE="""
<html><head><title>관리자 로그인</title><style>
body{background:#0f172a;color:white;font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh}
.box{background:#020617;padding:40px;border-radius:12px;box-shadow:0 0 20px rgba(0,0,0,0.6);text-align:center;width:400px}
input{width:90%;padding:10px;margin:5px;border-radius:6px;border:none}
button{padding:10px 20px;border-radius:6px;border:none;background:#2563eb;color:white;cursor:pointer;margin-top:10px}
.error{color:red;margin:10px 0}
</style></head><body>
<div class="box"><h1>🔐 관리자 로그인</h1>
<form method="post">
<input type="text" name="id" placeholder="아이디"><br>
<input type="password" name="pw" placeholder="비밀번호"><br>
<button type="submit">로그인</button></form>
<div class="error">{{ error }}</div></div></body></html>
"""

# ===============================
# 🌐 웹 대시보드
# ===============================
@app.route("/dashboard")
@login_required
def dashboard():
    licenses=load_licenses();display=[]
    for k,v in licenses.items(): display.append({"key":k,"created":v["created_at"],"expires":v["expires_at"],"active":v["active"],"disabled":v["disabled"]})
    return render_template_string(DASHBOARD_PAGE,licenses=display)

DASHBOARD_PAGE="""
<html><head><title>라이센스 대시보드</title><style>
body{background:#0f172a;color:white;font-family:Arial;padding:20px}
table{width:100%;border-collapse:collapse;margin-top:20px}
th,td{border:1px solid #444;padding:10px;text-align:center}
th{background:#2563eb;color:white}
button{padding:5px 10px;border-radius:6px;border:none;background:#2563eb;color:white;cursor:pointer}
</style></head><body>
<h1>📋 라이센스 대시보드</h1>
<table>
<tr><th>라이센스</th><th>생성일</th><th>만료일</th><th>활성화</th><th>비활성화</th><th>연장</th></tr>
{% for lic in licenses %}
<tr>
<td>{{ lic.key }}</td>
<td>{{ lic.created }}</td>
<td>{{ lic.expires }}</td>
<td>
<form method="post" action="/activate"><input type="hidden" name="key" value="{{ lic.key }}"><button type="submit">활성화</button></form>
</td>
<td>
<form method="post" action="/deactivate"><input type="hidden" name="key" value="{{ lic.key }}"><button type="submit">비활성화</button></form>
</td>
<td>
<form method="post" action="/extend"><input type="hidden" name="key" value="{{ lic.key }}"><input type="number" name="days" value="30" style="width:50px"><button type="submit">연장</button></form>
</td>
</tr>
{% endfor %}
</table>
<form method="post" action="/create"><h3>새 라이센스 생성</h3>기간(일): <input type="number" name="days" value="30"><button type="submit">생성</button></form>
</body></html>
"""

# ===============================
# 웹 대시보드 액션
# ===============================
@app.route("/create",methods=["POST"]);@login_required
def web_create(): days=int(request.form.get("days",30));create_license(days);return redirect(url_for("dashboard"))
@app.route("/activate",methods=["POST"]);@login_required
def web_activate(): key=request.form.get("key");activate_license(key);return redirect(url_for("dashboard"))
@app.route("/deactivate",methods=["POST"]);@login_required
def web_deactivate(): key=request.form.get("key");deactivate_license(key);return redirect(url_for("dashboard"))
@app.route("/extend",methods=["POST"]);@login_required
def web_extend(): key=request.form.get("key");days=int(request.form.get("days",30));extend_license(key,days);return redirect(url_for("dashboard"))

# ===============================
# 🔥 프로그램용 DRM API
# ===============================
@app.route("/api/drm/check",methods=["POST"])
def api_check():
    data=request.json;key=data.get("license")
    valid,msg=check_drm_logic(key) if key else (False,"NO_LICENSE")
    return jsonify({"valid":valid,"message":msg})
@app.route("/api/drm/create",methods=["POST"])
def api_create(): days=int(request.json.get("days",30));key=create_license(days);return jsonify({"key":key})
@app.route("/api/drm/activate",methods=["POST"])
def api_activate(): key=request.json.get("license");ok,msg=activate_license(key);return jsonify({"success":ok,"message":msg})
@app.route("/api/drm/deactivate",methods=["POST"])
def api_deactivate(): key=request.json.get("license");ok,msg=deactivate_license(key);return jsonify({"success":ok,"message":msg})
@app.route("/api/drm/extend",methods=["POST"])
def api_extend(): data=request.json;key=data.get("license");days=int(data.get("days",30));ok,msg=extend_license(key,days);return jsonify({"success":ok,"message":msg})
@app.route("/api/drm/lock",methods=["POST"])
def api_lock(): key=request.json.get("license");ok,msg=deactivate_license(key);return jsonify({"success":ok,"message":msg})

# ===============================
# 실행
# ===============================
if __name__=="__main__": app.run(host="0.0.0.0",port=10000)
