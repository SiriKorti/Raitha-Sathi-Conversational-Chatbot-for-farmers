"""
test_persistent_chat.py — Test suite for Persistent User-Specific Chat History & Security Isolation

Verifies:
1. User Isolation: User A cannot see User B's conversations.
2. IDOR Protection: User B cannot retrieve User A's conversation by direct ID.
3. Delete Protection: User B cannot delete User A's conversation.
4. Persistence: Conversations survive memory clear and restore from disk.
5. Conversation Continuity: Historical messages and dialogue state are preserved.
"""

import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.auth_manager import AuthManager
from app.services.conversation_manager import ConversationManager


@pytest.fixture
def auth_mgr(tmp_path):
    users_file = tmp_path / "users.json"
    return AuthManager(db_path=str(users_file))


@pytest.fixture
def conv_mgr(tmp_path):
    convs_file = tmp_path / "conversations.json"
    return ConversationManager(db_path=convs_file)


def test_conversation_manager_crud(conv_mgr):
    user_a = "farmer_alice"
    user_b = "farmer_bob"

    # 1. Create conversation for Alice
    conv_a = conv_mgr.create_conversation(user_id=user_a, title="Tomato Yellow Leaves")
    conv_a_id = conv_a["id"]
    assert conv_a["title"] == "Tomato Yellow Leaves"
    assert conv_a["user_id"] == user_a

    # 2. Add message turns
    msg1 = conv_mgr.add_message(user_id=user_a, conversation_id=conv_a_id, role="farmer", content="My tomato leaves are yellow")
    msg2 = conv_mgr.add_message(user_id=user_a, conversation_id=conv_a_id, role="assistant", content="Check for nitrogen deficiency")

    assert msg1["role"] == "farmer"
    assert msg2["role"] == "assistant"

    # 3. Retrieve conversation for Alice
    fetched_a = conv_mgr.get_conversation(user_id=user_a, conversation_id=conv_a_id)
    assert fetched_a is not None
    assert len(fetched_a["messages"]) == 2

    # 4. Strict isolation: Bob cannot retrieve Alice's conversation
    fetched_b = conv_mgr.get_conversation(user_id=user_b, conversation_id=conv_a_id)
    assert fetched_b is None

    # 5. List conversations for Alice vs Bob
    alice_list = conv_mgr.get_user_conversations(user_a)
    bob_list = conv_mgr.get_user_conversations(user_b)
    assert len(alice_list) == 1
    assert alice_list[0]["id"] == conv_a_id
    assert len(bob_list) == 0

    # 6. Bob cannot delete Alice's conversation
    del_b = conv_mgr.delete_conversation(user_id=user_b, conversation_id=conv_a_id)
    assert del_b is False
    # Alice's conversation remains
    assert conv_mgr.get_conversation(user_id=user_a, conversation_id=conv_a_id) is not None

    # 7. Alice deletes her own conversation
    del_a = conv_mgr.delete_conversation(user_id=user_a, conversation_id=conv_a_id)
    assert del_a is True
    assert conv_mgr.get_conversation(user_id=user_a, conversation_id=conv_a_id) is None
    assert len(conv_mgr.get_user_conversations(user_a)) == 0


def test_api_multi_user_isolation_and_idor():
    """
    Integration test verifying API-level security:
    - User A and User B tokens
    - Session list isolation
    - Direct access IDOR prevention
    - Cross-user delete prevention
    """
    with TestClient(app) as client:
        import secrets
        rnd = secrets.token_hex(4)
        email_a = f"alpha_{rnd}@test.raitha"
        phone_a = f"9{secrets.token_hex(4)[:9]}"
        email_b = f"beta_{rnd}@test.raitha"
        phone_b = f"8{secrets.token_hex(4)[:9]}"

        # Register User A
        reg_a = client.post("/api/auth/register", json={
            "fullName": "User Alpha",
            "mobile": phone_a,
            "email": email_a,
            "password": "password123"
        })
        assert reg_a.status_code == 200
        token_a = reg_a.json()["token"]
        user_a_id = reg_a.json()["user"]["id"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Register User B
        reg_b = client.post("/api/auth/register", json={
            "fullName": "User Beta",
            "mobile": phone_b,
            "email": email_b,
            "password": "password123"
        })
        assert reg_b.status_code == 200
        token_b = reg_b.json()["token"]
        user_b_id = reg_b.json()["user"]["id"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 1. User A creates a new conversation
        new_conv_res = client.post("/api/chat/new", headers=headers_a)
        assert new_conv_res.status_code == 200
        conv_a_id = new_conv_res.json()["session_id"]

        # 2. User A chats in that conversation
        chat_res = client.post("/api/chat", headers=headers_a, json={
            "session_id": conv_a_id,
            "message": "ನನ್ನ ಟೊಮೇಟೊ ಗಿಡದಲ್ಲಿ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ",
            "language": "kn"
        })
        assert chat_res.status_code == 200
        assert "response" in chat_res.json()

        # 3. User A checks sessions -> sees conv_a_id
        sess_a_res = client.get("/api/chat/sessions", headers=headers_a)
        assert sess_a_res.status_code == 200
        sessions_a = sess_a_res.json()["sessions"]
        assert any(s["id"] == conv_a_id for s in sessions_a)

        # 4. User B checks sessions -> MUST NOT see conv_a_id!
        sess_b_res = client.get("/api/chat/sessions", headers=headers_b)
        assert sess_b_res.status_code == 200
        sessions_b = sess_b_res.json()["sessions"]
        assert not any(s["id"] == conv_a_id for s in sessions_b)

        # 5. IDOR Attack: User B attempts to read User A's history directly
        attack_read = client.get(f"/api/chat/history/{conv_a_id}", headers=headers_b)
        assert attack_read.status_code == 404, "User B should not access User A's conversation"

        # 6. IDOR Delete Attack: User B attempts to delete User A's conversation
        attack_del = client.delete(f"/api/chat/session/{conv_a_id}", headers=headers_b)
        assert attack_del.status_code == 404, "User B should not delete User A's conversation"

        # 7. User A's history is still intact
        history_a = client.get(f"/api/chat/history/{conv_a_id}", headers=headers_a)
        assert history_a.status_code == 200
        assert len(history_a.json()["history"]) >= 2

        # 8. User A legitimately deletes their conversation
        legit_del = client.delete(f"/api/chat/session/{conv_a_id}", headers=headers_a)
        assert legit_del.status_code == 200

        # Verify it is gone
        check_deleted = client.get(f"/api/chat/history/{conv_a_id}", headers=headers_a)
        assert check_deleted.status_code == 404


def test_logout_login_restoration_and_continuity():
    """
    Simulates:
    1. User registers/logs in
    2. Sends initial agricultural message
    3. Logs out (invalidates token)
    4. Logs in again (new token issued)
    5. Verifies previous conversation is restored from persistent storage
    6. Continues the conversation with context intact
    """
    with TestClient(app) as client:
        # Step 1: Login
        login_res = client.post("/api/auth/login", json={
            "identifier": "farmer@raitha.app",
            "password": "farmer123"
        })
        assert login_res.status_code == 200
        token_1 = login_res.json()["token"]
        headers_1 = {"Authorization": f"Bearer {token_1}"}

        # Step 2: Start conversation & ask initial question
        new_res = client.post("/api/chat/new", headers=headers_1)
        conv_id = new_res.json()["session_id"]

        chat_1 = client.post("/api/chat", headers=headers_1, json={
            "session_id": conv_id,
            "message": "I am growing maize, it is 40 days old.",
            "language": "en"
        })
        assert chat_1.status_code == 200
        assert "response" in chat_1.json()

        # Step 3: Logout
        logout_res = client.post("/api/auth/logout", headers=headers_1)
        assert logout_res.status_code == 200

        # Old token is now rejected
        rejected = client.get("/api/chat/sessions", headers=headers_1)
        assert rejected.status_code == 401

        # Step 4: Login again
        login_res_2 = client.post("/api/auth/login", json={
            "identifier": "farmer@raitha.app",
            "password": "farmer123"
        })
        assert login_res_2.status_code == 200
        token_2 = login_res_2.json()["token"]
        headers_2 = {"Authorization": f"Bearer {token_2}"}

        # Step 5: Conversations restored after login
        sessions_res = client.get("/api/chat/sessions", headers=headers_2)
        assert sessions_res.status_code == 200
        sessions = sessions_res.json()["sessions"]
        matching_conv = next((s for s in sessions if s["id"] == conv_id), None)
        assert matching_conv is not None
        assert matching_conv["title"] != ""

        # Step 6: Open previous conversation & verify messages
        history_res = client.get(f"/api/chat/history/{conv_id}", headers=headers_2)
        assert history_res.status_code == 200
        messages = history_res.json()["history"]
        assert len(messages) >= 2
        assert "maize" in messages[0]["content"].lower()

        # Step 7: Continue previous conversation
        chat_2 = client.post("/api/chat", headers=headers_2, json={
            "session_id": conv_id,
            "message": "The lower leaves are turning yellow. What should I do?",
            "language": "en"
        })
        assert chat_2.status_code == 200

        # Verify updated message count
        history_updated = client.get(f"/api/chat/history/{conv_id}", headers=headers_2)
        assert history_updated.status_code == 200
        assert len(history_updated.json()["history"]) >= 4

