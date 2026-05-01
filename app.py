"""
This file starts the web API for the syntax analyzer.
It accepts code from the front end and sends back parse results.
"""

import os

from flask import Flask, jsonify, request

from syntax_checker.main import analyze_code


app = Flask(__name__)
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*").rstrip("/")


@app.after_request
def add_cors_headers(response):
    # Allow the browser page to call this API.
    response.headers["Access-Control-Allow-Origin"] = FRONTEND_ORIGIN
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.get("/")
def index():
    # Simple health check for the API.
    return jsonify({"status": "ok", "service": "syntax-analyser-api"})


@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    # Handle browser preflight requests.
    if request.method == "OPTIONS":
        return ("", 204)

    # Read the code sent by the front end.
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    if not isinstance(code, str):
        return jsonify({"syntax_valid": False, "errors": ["Code must be a string"]}), 400

    # Run the parser and return the result as JSON.
    return jsonify(analyze_code(code))


if __name__ == "__main__":
    # Start the local server when this file is run directly.
    app.run(debug=True)
