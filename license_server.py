from flask import Flask, request, jsonify
import uuid, json, os
from datetime import datetime, timedelta
import hashlib

# ------------------
# 설정
# ------------------
LICENSE_FILE = "licenses.json"
SECRET_KEY = "MY_SUPER_SECRET_KEY"

app = Flask(__name__)

# ------------------
# 유틸
# ------------------
def now():
    return datetime.utcnow()

def hash_key(key: str) -> str:
    return hashlib.sha256((key + SECRET_KEY).encode()).hexdigest()

def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        return {}
    with open(LICENSE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_licenses(data):
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ------------------
# 라이센스 로직
# ------------------


def create_license(days):
    licenses = load_licenses()
    raw_key = str(uuid.uuid4()).upper()
    hashed = hash_key(raw_key)
    licenses[hashed] = {
        "created_at": now().isoformat(),
        "expires_at": (now()+timedelta(days=days)).isoformat(),
        "active": False,
        "disabled": False
    }
    save_licenses(licenses)
    return raw_key

def activate_license(key):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return False, "라이센스 없음"
    if licenses[hashed]["disabled"]: return False, "비활성화됨"
    licenses[hashed]["active"] = True
    save_licenses(licenses)
    return True, "활성화 완료"

def deactivate_license(key):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return False, "라이센스 없음"
    licenses[hashed]["active"] = False
    licenses[hashed]["disabled"] = True
    save_licenses(licenses)
    return True, "비활성화 완료"

def extend_license(key, days):
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses: return False, "라이센스 없음"
    licenses[hashed]["expires_at"] = (datetime.fromisoformat(licenses[hashed]["expires_at"])+timedelta(days=days)).isoformat()
    save_licenses(licenses)
    return True, f"{days}일 연장 완료"

def check_drm_logic(key):
    licenses = load_licenses()  # JSON 파일 로드
    hashed = hash_key(key)      # 클라이언트에서 보내는 키 해시화
    if hashed not in licenses:
        return False, "라이센스 없음"
    lic = licenses[hashed]
    if lic["disabled"]:
        return False, "비활성화됨"
    if not lic["active"]:
        return False, "활성화되지 않음"
    if datetime.now() > datetime.fromisoformat(lic["expires_at"]):
        return False, "만료됨"
    return True, "정상"


# ------------------
# API 엔드포인트
# ------------------

@app.route("/api/drm/create", methods=["POST"])
def api_create():
    data = request.json
    days = data.get("days")
    if not days:
        return jsonify({"success": False, "message": "기간(days) 필요"}), 400
    
    key = create_license(days)  # 기존 로직 그대로 사용
    return jsonify({"success": True, "license": key, "days": days})

@app.route("/api/drm/activate", methods=["POST"])
def api_activate():
    data = request.json
    key = data.get("license")
    if not key:
        return jsonify({"success": False, "message": "라이센스 필요"}), 400
    success, msg = activate_license(key)
    return jsonify({"success": success, "message": msg})

@app.route("/api/drm/deactivate", methods=["POST"])
def api_deactivate():
    data = request.json
    key = data.get("license")
    if not key:
        return jsonify({"success": False, "message": "라이센스 필요"}), 400
    success, msg = deactivate_license(key)
    return jsonify({"success": success, "message": msg})

@app.route("/api/drm/extend", methods=["POST"])
def api_extend():
    data = request.json
    key = data.get("license")
    days = data.get("days")
    if not key or not days:
        return jsonify({"success": False, "message": "라이센스 및 연장 기간 필요"}), 400
    success, msg = extend_license(key, days)
    return jsonify({"success": success, "message": msg})

@app.route("/api/drm/list", methods=["POST"])
def api_list():
    licenses = load_licenses()
    # 필요 없는 HTML 페이지가 아니라 JSON으로 반환
    return jsonify({"success": True, "licenses": licenses})

    
@app.route("/api/drm/check", methods=["POST"])
def api_check():
    data = request.json
    key = data.get("license")
    if not key:
        return jsonify({"valid": False, "message": "라이센스 필요"}), 400
    valid, msg = check_drm_logic(key)
    return jsonify({"valid": valid, "message": msg})

@app.route("/api/drm/lock", methods=["POST"])
def api_lock():
    data = request.json
    key = data.get("license")
    if not key:
        return jsonify({"success": False, "message": "라이센스 필요"}), 400
    licenses = load_licenses()
    hashed = hash_key(key)
    if hashed not in licenses:
        return jsonify({"success": False, "message": "라이센스 없음"}), 404
    licenses[hashed]["active"] = False
    licenses[hashed]["disabled"] = True
    save_licenses(licenses)
    return jsonify({"success": True, "message": "비활성화 완료"})

# ------------------
# 서버 실행
# ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)



