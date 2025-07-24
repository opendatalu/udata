from flask import current_app, abort, request
import requests
from typing import Optional

def validate_captcha_token(token: Optional[str] = None) -> bool:

    mcaptcha_url = current_app.config.get("MCAPTCHA_URL")
    mcaptcha_site_key = current_app.config.get("MCAPTCHA_SITE_KEY")
    mcaptcha_backend_url = current_app.config.get(
        "MCAPTCHA_BACKEND_URL", mcaptcha_url
    )  # Differentiated from mcaptcha_url because requests from the container need host.docker.internal

    # Start mCaptcha verification
    if mcaptcha_backend_url and mcaptcha_site_key:
        mcaptcha_token = token if token else request.form.get("mcaptcha__token")

        mcaptcha_secret_key = current_app.config.get("MCAPTCHA_SECRET_KEY")
        if not mcaptcha_secret_key:
            raise ValueError("Missing MCAPTCHA_SECRET_KEY in configuration")

        if not mcaptcha_token:
            abort(400, "Missing mCaptcha token")

        payload = {
            "token": mcaptcha_token,
            "key": mcaptcha_site_key,
            "secret": mcaptcha_secret_key,
        }
        resp = requests.post(
            f"{mcaptcha_backend_url}/api/v1/pow/siteverify", json=payload
        )
        resp = resp.json()

        return resp.get("valid")

    return True
