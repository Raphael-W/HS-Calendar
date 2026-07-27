from pathlib import Path
import json

import pytest
from flask import current_app as app
from app.auth import decode_token, make_token

# === PUBLIC PAGES ===
def test_main_page(client):
    resp = client.get("/")
    assert resp.status_code == 200


# === TOKEN ===
def test_token_creation_400(client):
    resp = client.post("/token", json={"username": "", "password": ""})
    assert resp.status_code == 400


def test_token_creation_401(client):
    resp = client.post("/token", json={"username": "invalid@email.com", "password": "incorrect"})
    assert resp.status_code == 401
    

def test_token_creation_200(client, credentials):
    username, password = credentials

    # Testing that token can be generated multiple times
    for i in range(2):
        resp = client.post("/token", json={"username": username, "password": password})
        assert resp.status_code == 200

        decoded_token = decode_token(resp.text)
        assert decoded_token["u"] == username
        assert decoded_token["p"] == password
        assert len(decoded_token) == 3


# === CALENDAR ===
def test_calendar_401(client, credentials):
    username, password = credentials
    token = make_token(username, "incorrect", 1)

    resp = client.get(f"/calendar?token={token}")
    assert resp.status_code == 401


def test_calendar_200(client, credentials):
    username, password = credentials
    token = client.post("/token", json={"username": username, "password": password}).text

    resp = client.get(f"/calendar?token={token}")
    assert resp.status_code == 200