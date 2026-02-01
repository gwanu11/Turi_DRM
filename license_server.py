import json
import uuid
import hashlib
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect
import threading

# ===============================
# 설정
# ===============================
LICENSE_FILE = "licenses.json"
SECRET_KEY = "MY_SUPER_SECRET_KEY"
ADMIN_ID = "adonis"
ADMIN_PW = "adonis2023"

app = Flask(__name__)

# ===============================
# 유틸
# ===============================
def now():
    return datetime.utcnow()

def hash_key(key: str) -> str:
    return hashlib.sha256((key + SECRET_KEY).encode()).hexdigest()

def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
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
        "disabled": False,
        "bound_ip": None
    }
    save_licenses(licenses)
    return raw_key

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

def deactivate_license(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses:
        return False, "라이센스 없음"
    licenses[hashed]["disabled"] = True
    licenses[hashed]["active"] = False
    save_licenses(licenses)
    return True, "비활성화 완료"

def extend_license(key: str, days: int):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses:
        return False, "라이센스 없음"
    expires = datetime.fromisoformat(licenses[hashed]["expires_at"])
    licenses[hashed]["expires_at"] = (expires + timedelta(days=days)).isoformat()
    save_licenses(licenses)
    return True, f"{days}일 연장 완료"

def check_drm_logic(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses:
        return False, "INVALID_LICENSE"
    lic = licenses[hashed]
    if lic["disabled"]:
        return False, "DISABLED"
    if not lic["active"]:
        return False, "NOT_ACTIVATED"
    if now() > datetime.fromisoformat(lic["expires_at"]):
        return False, "EXPIRED"
    return True, "OK"

# ===============================
# 🔐 DRM API
# ===============================
@app.route("/api/drm/check", methods=["POST"])
def api_drm_check():
    data = request.json
    key = data.get("license")
    if not key:
        return jsonify({"valid": False, "message": "NO_LICENSE"}), 400
    valid, msg = check_drm_logic(key)
    return jsonify({"valid": valid, "message": msg})

@app.route("/api/drm/lock", methods=["POST"])
def api_drm_lock():
    data = request.json
    key = data.get("license")
    if not key:
        return jsonify({"ok": False, "message": "NO_LICENSE"}), 400
    ok, msg = deactivate_license(key)
    if not ok:
        return jsonify({"ok": False, "message": msg}), 400
    return jsonify({"ok": True, "message": "LICENSE_LOCKED"})

# ===============================
# 🌐 웹 페이지
# ===============================
@app.route("/", methods=["GET"])
def home():
    # "/" 접속 시 자동으로 로그인 페이지로 리다이렉트
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")
        if user == ADMIN_ID and pw == ADMIN_PW:
            return """
            <html><body>
            <h1>관리자 로그인 성공</h1>
            <p>CLI 또는 API를 사용하세요.</p>
            </body></html>
            """
        return "<h1>로그인 실패</h1>"
    return """
    <form method="post" style="margin:100px;">
        <label>아이디: <input name="username"></label><br><br>
        <label>비밀번호: <input name="password" type="password"></label><br><br>
        <input type="submit" value="로그인">
    </form>
    """

# ===============================
# CLI 관리자
# ===============================
def admin_cli():
    while True:
        print("\n1. 라이센스 생성")
        print("2. 라이센스 활성화")
        print("3. 라이센스 비활성화")
        print("4. 라이센스 기간 연장")
        print("5. DRM 체크")
        print("0. 종료")
        cmd = input("선택: ")
        if cmd=="1":
            days=int(input("기간(일): "))
            print("라이센스:",create_license(days))
        elif cmd=="2":
            print(activate_license(input("키: "))[1])
        elif cmd=="3":
            print(deactivate_license(input("키: "))[1])
        elif cmd=="4":
            key=input("키: ")
            days=int(input("연장 일수: "))
            print(extend_license(key,days)[1])
        elif cmd=="5":
            print(check_drm_logic(input("키: "))[1])
        elif cmd=="0":
            break

# ===============================
# 실행
# ===============================
if __name__=="__main__":
    threading.Thread(target=admin_cli, daemon=True).start()
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)
