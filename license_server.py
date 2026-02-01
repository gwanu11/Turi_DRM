from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
licenses = {}  # {license_key: {"active": True, "expire_at": datetime, "created_at": datetime}}

def generate_license():
    def rand4():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TURI-DRM-{rand4()}-{rand4()}"

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
    # 반환 시점에서 datetime -> 문자열 변환
    return jsonify({
        "license": license_key,
        "expire_at": expire_at.isoformat(),
        "created_at": created_at.isoformat()
    })

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
    # 모든 expire_at, created_at 문자열 처리
    result = []
    for key, val in licenses.items():
        result.append({
            "license": key,
            "active": val["active"],
            "expire_at": val["expire_at"].isoformat(),
            "created_at": val["created_at"].isoformat()
        })
    return jsonify({"licenses": result})

# --- 라이센스 검증 (프로그램용) ---
@app.route("/api/license/verify", methods=["POST"])
def verify_license():
    data = request.get_json()
    key = data.get("license")
    lic = licenses.get(key)
    if not lic:
        return jsonify({"valid": False, "reason": "not_found"})
    if not lic["active"]:
        return jsonify({"valid": False, "reason": "disabled"})
    if lic["expire_at"] < datetime.now():
        return jsonify({"valid": False, "reason": "expired"})
    return jsonify({
        "valid": True,
        "expire_at": lic["expire_at"].isoformat(),
        "created_at": lic["created_at"].isoformat()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
