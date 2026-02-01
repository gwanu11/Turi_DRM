from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)

# 메모리 DB
licenses = {}  # license_key: {"active": True, "expire_at": datetime, "created_at": datetime}

# 라이센스 생성 함수
def generate_license():
    def rand4():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TURI-DRM-{rand4()}-{rand4()}"

# --- 헬퍼: datetime -> 문자열 변환 ---
def serialize_license(key, data):
    return {
        "license": key,
        "active": data["active"],
        "expire_at": data["expire_at"].isoformat(),
        "created_at": data["created_at"].isoformat()
    }

# --- 라이센스 생성 ---
@app.route("/api/license/create", methods=["POST"])
def create_license():
    data = request.get_json()
    days = data.get("days")
    if not isinstance(days, int):
        return jsonify({"error": "days는 숫자여야 합니다."}), 400

    license_key = generate_license()
    expire_at = datetime.now() + timedelta(days=days)
    created_at = datetime.now()
    licenses[license_key] = {
        "active": True,
        "expire_at": expire_at,
        "created_at": created_at
    }
    return jsonify(serialize_license(license_key, licenses[license_key]))

# --- 라이센스 비활성화 ---
@app.route("/api/license/deactivate", methods=["POST"])
def deactivate_license():
    data = request.get_json()
    key = data.get("license")
    if key not in licenses:
        return jsonify({"success": False, "reason": "라이센스 없음"})
    licenses[key]["active"] = False
    return jsonify({"success": True})

# --- 라이센스 활성화 ---
@app.route("/api/license/activate", methods=["POST"])
def activate_license():
    data = request.get_json()
    key = data.get("license")
    if key not in licenses:
        return jsonify({"success": False, "reason": "라이센스 없음"})
    licenses[key]["active"] = True
    return jsonify({"success": True})

# --- 라이센스 목록 ---
@app.route("/api/license/list", methods=["GET"])
def list_licenses():
    result = [serialize_license(k, v) for k, v in licenses.items()]
    return jsonify({"licenses": result})

# --- 라이센스 검증 ---
@app.route("/api/license/verify", methods=["POST"])
def verify_license():
    data = request.get_json()
    key = data.get("lic
