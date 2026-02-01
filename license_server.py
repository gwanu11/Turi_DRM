from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

licenses = {}  # {"TURI-DRM-XXXX": {"expire": "2026-02-03 12:00:00", "active": True, "ip": None}}

# --------------------
# 라이센스 생성
# --------------------
@app.route("/api/drm/create", methods=["POST"])
def create_license():
    data = request.json
    days = int(data.get("days", 30))
    key = f"TURI-DRM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    expire = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    licenses[key] = {"expire": expire, "active": True, "ip": None}
    return jsonify({"license": key, "expire": expire})

# --------------------
# 라이센스 목록
# --------------------
@app.route("/api/drm/list", methods=["GET"])
def list_licenses():
    return jsonify({"licenses": licenses})

# --------------------
# 라이센스 활성화
# --------------------
@app.route("/api/drm/activate", methods=["POST"])
def activate_license():
    data = request.json
    key = data.get("license")
    if key in licenses:
        licenses[key]["active"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "reason": "라이센스 없음"})

# --------------------
# 새 Lock API
# --------------------
@app.route("/api/drm/lock", methods=["POST"])
def lock_license():
    data = request.json
    key = data.get("license")
    if key in licenses:
        licenses[key]["active"] = False
        return jsonify({"success": True})
    return jsonify({"success": False, "reason": "라이센스 없음"})

# --------------------
# 라이센스 체크 (IP 제한 포함)
# --------------------
@app.route("/api/drm/check", methods=["POST"])
def check_license():
    data = request.json
    key = data.get("license")
    ip = data.get("ip")

    if key not in licenses:
        return jsonify({"valid": False, "message": "잘못된 라이센스"}), 200

    lic = licenses[key]

    if not lic["active"]:
        return jsonify({"valid": False, "message": "비활성화된 라이센스"}), 200

    # IP 제한: 첫 사용이면 기록, 다른 IP 사용 시 오류
    if lic["ip"] is None:
        lic["ip"] = ip
    elif lic["ip"] != ip:
        return jsonify({"valid": False, "message": "허용되지 않은 IP에서 라이센스 사용"}), 200

    return jsonify({"valid": True, "message": "정상 라이센스"}), 200

# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
