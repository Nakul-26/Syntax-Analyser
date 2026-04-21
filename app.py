from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from syntax_checker.main import analyze_code


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "web"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.post("/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"syntax_valid": False, "errors": ["Code must be a string"]}), 400

    return jsonify(analyze_code(code))


if __name__ == "__main__":
    app.run(debug=True)
