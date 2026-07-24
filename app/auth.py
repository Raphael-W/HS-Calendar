import jwt
import json
import requests
from .extensions import fernet
from flask import abort

# === Logic ===
def calculate_pay(rate, hours):
    return rate * hours


# === JWT ===
def decode_jwt(jwt_token):
    full_jwt = jwt.decode(jwt_token, options={"verify_signature": False})
    return {"username": full_jwt["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"],
            "expiry": full_jwt["exp"]}


# === CALENDAR TOKEN ===
def make_token(username: str, password: str, kid: int) -> str:
    payload = json.dumps({"u": username, "p": password, "kid": kid}).encode()
    return fernet.encrypt(payload).decode()


def decode_token(token: str) -> tuple[str, str, int]:
    payload = json.loads(fernet.decrypt(token.encode()))
    return payload["u"], payload["p"], payload["kid"]


# === REQUESTS ===
def make_hs_request(endpoint, auth=None, method="GET", params=None, json_params=None):
    if auth:
        headers = {"Authorization": f"Bearer {auth}"}
    else:
        headers = {}

    if params is None: params = {}
    if json_params is None: json_params = {}

    url = f"https://hsstaffapi65.high-society.co.uk/api/{endpoint}"
    r = requests.request(method, url, params=params, headers=headers, json=json_params)
    return r


def authenticate_user(username, password):
    response = make_hs_request("Authentication/Authenticate", method="POST", json_params = {"userName": username, "password": password})

    if response.status_code == 401:
        abort(401, description = "Invalid credentials")
    elif not response.ok:
        abort(500, description = "Upstream request failed")

    return response.text
