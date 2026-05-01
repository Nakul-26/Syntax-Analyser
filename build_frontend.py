"""
This file writes the front-end API config file.
It helps the web page know which backend URL to call.
"""

from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT_DIR / "web"
ENV_FILE = ROOT_DIR / ".env"
OUTPUT_FILE = WEB_DIR / "env.js"


def load_dotenv(path: Path) -> dict[str, str]:
    # Read simple key=value lines from the env file.
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def main() -> None:
    # Pick the API URL from the environment or use the default one.
    file_env = load_dotenv(ENV_FILE)
    api_base_url = (
        os.environ.get("FRONTEND_API_BASE_URL")
        or os.environ.get("API_BASE_URL")
        or file_env.get("FRONTEND_API_BASE_URL")
        or file_env.get("API_BASE_URL")
        or "https://YOUR-VERCEL-APP.vercel.app"
    )

    OUTPUT_FILE.write_text(
        # Write a tiny config file for the browser page.
        "window.APP_CONFIG = {\n"
        f'  API_BASE_URL: "{api_base_url.rstrip("/")}"\n'
        "};\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
