from flask import Flask, jsonify, request

from syntax_checker.main import analyze_code


app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.get("/")
def index():
    return jsonify({"status": "ok", "service": "syntax-analyser-api"})


@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"syntax_valid": False, "errors": ["Code must be a string"]}), 400

    return jsonify(analyze_code(code))


if __name__ == "__main__":
    app.run(debug=True)
