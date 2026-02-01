from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# --------------------
# 라이센스 저장
# --------------------
licenses = {}  
# 구조 예시: {"TURI-DRM-20260201120000": {"expire": "2026-02-03 12:00:00", "active": True, "ip": None}}

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
# 몰라인마
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

    # IP 체크
    if lic["ip"] is None:
        # 첫 사용 시 IP 기록
        lic["ip"] = ip
    elif lic["ip"] != ip:
        # 다른 IP에서 접근 시 허용 안됨
        return jsonify({"valid": False, "message": "허용되지 않은 IP에서 라이센스 사용"}), 200

    return jsonify({"valid": True, "message": "정상 라이센스"}), 200


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
# 라이센스 비활성화
# --------------------
@app.route("/api/drm/lock", methods=["POST"])
def deactivate_license():
    data = request.json
    key = data.get("license")
    if key in licenses:
        licenses[key]["active"] = False
        return jsonify({"success": True})
    return jsonify({"success": False, "reason": "라이센스 없음"})

# --------------------
# 라이센스 체크 (DRM 프로그램용)
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
    # IP 기록
    lic["ip"] = ip
    return jsonify({"valid": True, "message": "정상 라이센스"}), 200

# --------------------
# 서버 실행
# --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

