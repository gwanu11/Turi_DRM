import os
from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_LICENSES = {
    "ABC-123-XYZ": True,
    "TEST-456-KEY": True
}

@app.route("/check_license", methods=["POST"])
def check_license():
    data = request.get_json(silent=True) or {}
    license_key = data.get("license")

    if VALID_LICENSES.get(license_key):
        return jsonify({"valid": True})

    return jsonify({"valid": False}), 403


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # ⭐ Render 필수
    app.run(host="0.0.0.0", port=port)
