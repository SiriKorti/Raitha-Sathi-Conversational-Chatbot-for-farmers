"""
test_chat_regression.py — Regression verification for existing chat endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_chat_new_session_auth_required():
    with TestClient(app) as client:
        # Unauthenticated request must return 401
        res_unauth = client.post("/api/chat/new")
        assert res_unauth.status_code == 401

        # Authenticate
        login_res = client.post("/api/auth/login", json={
            "identifier": "farmer@raitha.app",
            "password": "farmer123"
        })
        assert login_res.status_code == 200
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Authenticated request succeeds
        res = client.post("/api/chat/new", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "session_id" in data


def test_chat_sessions_list_auth_required():
    with TestClient(app) as client:
        # Unauthenticated request must return 401
        res_unauth = client.get("/api/chat/sessions")
        assert res_unauth.status_code == 401

        # Authenticate
        login_res = client.post("/api/auth/login", json={
            "identifier": "farmer@raitha.app",
            "password": "farmer123"
        })
        assert login_res.status_code == 200
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Authenticated request succeeds
        res = client.get("/api/chat/sessions", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "sessions" in data

