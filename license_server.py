# license_server.py
from flask import Flask, request, jsonify
import os, json, uuid
from datetime import datetime, timedelta

LICENSE_FILE = "licenses.json"

app = Flask(__name__)

# ------------------
# 유틸리티
# ------------------
def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        return {}
    with open(LICENSE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_licenses(data):
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def check_drm_logic(key):
    licenses = load_licenses()
    if key not in licenses:
        return False, "라이센스 없음"
    lic = licenses[key]
    now = datetime.utcnow()
    if lic["disabled"]:
        return False, "비활성화됨"
    if not lic["active"]:
        return False, "활성화되지 않음"
    if now > datetime.fromisoformat(lic["expires_at"]):
        return False, "만료됨"
    remaining = (datetime.fromisoformat(lic["expires_at"]) - now).days
    return True, f"정상, 남은 기간: {remaining}일"

# ------------------
# 모든 API 정의
# ------------------
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
    licenses = load_licenses()
    if key not in licenses:
        return jsonify({"success": False, "message": "라이센스 없음"}), 404
    licenses[key]["disabled"] = True
    licenses[key]["active"] = False
    save_licenses(licenses)
    return jsonify({"success": True, "message": "라이센스 잠금 완료"})

@app.route("/api/drm/list", methods=["POST"])
def api_list():
    licenses = load_licenses()
    return jsonify({"success": True, "licenses": licenses})

@app.route("/api/drm/create", methods=["POST"])
def api_create():
    data = request.json
    days = data.get("days")
    if not days:
        return jsonify({"success": False, "message": "기간(days) 필요"}), 400
    licenses = load_licenses()
    key = str(uuid.uuid4()).upper()
    now_str = datetime.utcnow().isoformat()
    exp_str = (datetime.utcnow() + timedelta(days=int(days))).isoformat()
    licenses[key] = {"created_at": now_str, "expires_at": exp_str, "active": False, "disabled": False}
    save_licenses(licenses)
    return jsonify({"success": True, "license": key, "remaining": days})

@app.route("/api/drm/activate", methods=["POST"])
def api_activate():
    data = request.json
    key = data.get("license")
    licenses = load_licenses()
    if key not in licenses:
        return jsonify({"success": False, "message": "라이센스 없음"}), 404
    licenses[key]["active"] = True
    save_licenses(licenses)
    return jsonify({"success": True, "message": "활성화 완료"})

@app.route("/api/drm/deactivate", methods=["POST"])
def api_deactivate():
    data = request.json
    key = data.get("license")
    licenses = load_licenses()
    if key not in licenses:
        return jsonify({"success": False, "message": "라이센스 없음"}), 404
    licenses[key]["disabled"] = True
    licenses[key]["active"] = False
    save_licenses(licenses)
    return jsonify({"success": True, "message": "비활성화 완료"})

@app.route("/api/drm/extend", methods=["POST"])
def api_extend():
    data = request.json
    key = data.get("license")
    days = data.get("days")
    licenses = load_licenses()
    if key not in licenses:
        return jsonify({"success": False, "message": "라이센스 없음"}), 404
    exp = datetime.fromisoformat(licenses[key]["expires_at"])
    licenses[key]["expires_at"] = (exp + timedelta(days=int(days))).isoformat()
    save_licenses(licenses)
    return jsonify({"success": True, "message": f"{days}일 연장 완료"})

# ------------------
# Render 환경용 서버 실행
# ------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
