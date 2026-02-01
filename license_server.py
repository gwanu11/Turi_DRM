from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_LICENSES = {
    "ABC-123-XYZ": True,
    "TEST-456-KEY": True
}

@app.route("/check_license", methods=["POST"])
def check_license():
    data = request.json
    license_key = data.get("license")

    if VALID_LICENSES.get(license_key):
        return jsonify({"valid": True})
    return jsonify({"valid": False}), 403

app.run(host="0.0.0.0", port=5000)
