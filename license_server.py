from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)

# 메모리 DB
licenses = {}  # license_key: {"active": bool, "expire": "YYYY-MM-DD HH:MM:SS", "created": "YYYY-MM-DD HH:MM:SS"}

# 라이센스 생성
def generate_license():
    def rand4():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TURI-DRM-{rand4()}-{rand4()}"

# 현재 시간 문자열
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 만료 시간 문자열
def expire_str(days):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

# --- 라이센스 생성 ---
@app.route("/api/license/create", methods=["POST"])
def create_license():
    data = request.get_json()
    days = data.get("days")
    if not isinstance(days, int):
        return jsonify({"error": "days는 숫자여야 합니다."}), 400

    key = generate_license()
    licenses[key] = {
        "active": True,
        "created": now_str(),
        "expire": expire_str(days)
    }
    return jsonify({"license": key, **licenses[key]})

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
    return jsonify({"licenses": licenses})

# --- 라이센스 검증 ---
@app.route("/api/license/verify", methods=["POST"])
def verify_license():
    data = request.get_json()
    key = data.get("license")
    lic = licenses.get(key)
    if not lic:
        return jsonify({"valid": False, "reason": "not_found"})

    if not lic["active"]:
        return jsonify({"valid": False, "reason": "disabled"})

    expire_time = datetime.strptime(lic["expire"], "%Y-%m-%d %H:%M:%S")
    if expire_time < datetime.now():
        return jsonify({"valid": False, "reason": "expired"})

    return jsonify({"valid": True, **lic})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
