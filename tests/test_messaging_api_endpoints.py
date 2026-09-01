"""Integration tests for FastAPI Instagram Messaging & Webhook endpoints."""

import hmac
import hashlib
import json
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_api_health_endpoint():
    """GET /api/health returns detailed non-secret diagnostics."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "youtube_api_configured" in data
        assert "gemini_api_configured" in data
        assert "meta_api_configured" in data
        assert "supported_modes" in data
        assert data["supported_modes"] == ["real", "simulation"]
        # Ensure secrets are NOT leaked in response
        assert "INSTAGRAM_ACCESS_TOKEN" not in data
        assert "META_APP_SECRET" not in data


@pytest.mark.asyncio
async def test_api_eligibility_real_vs_simulation(monkeypatch):
    """POST /api/social/instagram/eligibility distinguishes Real vs Simulation mode."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Real Mode with username only -> cannot send
        res_real = await client.post("/api/social/instagram/eligibility", json={
            "instagram_username": "mrbeast",
            "mode": "real"
        })
        assert res_real.status_code == 200
        data_real = res_real.json()
        assert data_real["can_send"] is False
        assert data_real["discovery"]["status"] == "discovered"
        assert data_real["recipient"]["status"] == "unresolved"
        assert data_real["capability"]["status"] == "requires_interaction"

        # 2. Simulation Mode with username -> can send in simulation
        res_sim = await client.post("/api/social/instagram/eligibility", json={
            "instagram_username": "mrbeast",
            "mode": "simulation"
        })
        assert res_sim.status_code == 200
        data_sim = res_sim.json()
        assert data_sim["can_send"] is True
        assert data_sim["mode"] == "simulation"
        assert data_sim["capability"]["provider"] == "local"


@pytest.mark.asyncio
async def test_api_send_simulation_flow():
    """POST /api/social/instagram/send in simulation mode succeeds without calling Meta."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/social/instagram/send", json={
            "instagram_username": "mkbhd",
            "message": "Testing simulation dispatch",
            "mode": "simulation",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["status"] == "simulated"
        assert data["mode"] == "simulation"
        assert data["message_id"] is None
        assert data["provider"] == "local"


@pytest.mark.asyncio
async def test_api_send_real_mode_rejects_unresolved_recipient(monkeypatch):
    """POST /api/social/instagram/send in real mode rejects when IGSID is missing."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/social/instagram/send", json={
            "instagram_username": "mrbeast",
            "instagram_user_id": None,
            "message": "Cold DM attempt",
            "mode": "real",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is False
        assert data["status"] == "rejected"
        assert data["mode"] == "real"
        assert "cannot receive messages via username alone" in data["error"]


@pytest.mark.asyncio
async def test_api_webhook_verification(monkeypatch):
    """GET /api/webhook/instagram verifies Meta subscription challenge."""
    monkeypatch.setattr(settings, "META_WEBHOOK_VERIFY_TOKEN", "test_verify_token_123")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Valid verification
        res_valid = await client.get("/api/webhook/instagram", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test_verify_token_123",
            "hub.challenge": "1158201444"
        })
        assert res_valid.status_code == 200
        assert res_valid.text == "1158201444"

        # Invalid token
        res_invalid = await client.get("/api/webhook/instagram", params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "1158201444"
        })
        assert res_invalid.status_code == 403


@pytest.mark.asyncio
async def test_get_recipient_status_endpoint(monkeypatch):
    """GET /api/instagram/recipient-status returns messaging eligibility without exposing raw IGSID."""
    from app.services.instagram_service import _save_recipient_to_registry

    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    # 1. Unregistered creator -> interaction required
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/instagram/recipient-status", params={
            "instagram_username": "@unregistered_creator",
            "mode": "real"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["instagram_username"] == "@unregistered_creator"
        assert data["messaging"]["eligible"] is False
        assert data["messaging"]["status"] == "interaction_required"

        # 2. Registered creator via webhook interaction -> eligible
        _save_recipient_to_registry(
            username="registered_creator",
            igsid="17841499887766554",
            creator_id="UC_reg_creator_123",
            source="meta_webhook"
        )

        res2 = await client.get("/api/instagram/recipient-status", params={
            "instagram_username": "registered_creator",
            "creator_id": "UC_reg_creator_123",
            "mode": "real"
        })
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["success"] is True
        assert data2["messaging"]["eligible"] is True
        assert data2["messaging"]["status"] == "eligible"
        # Raw IGSID is not leaked directly in messaging dict
        assert "17841499887766554" not in json.dumps(data2["messaging"])


@pytest.mark.asyncio
async def test_send_message_automatic_igsid_resolution(monkeypatch):
    """POST /api/instagram/send-message automatically resolves stored legitimate IGSID without user input."""
    from app.services.instagram_service import _save_recipient_to_registry

    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_super_secret_token_123")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    # Save verified recipient to persistent registry
    _save_recipient_to_registry(
        username="auto_resolved_creator",
        igsid="17841477777777777",
        creator_id="UC_auto_123",
        source="meta_webhook"
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "recipient_id": "17841477777777777",
        "message_id": "mid.auto_resolved_success_001"
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.services.instagram_service.httpx.AsyncClient", mock_client_cls):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Client sends only creator_username and message (NO recipient_igsid provided by frontend)
            res = await client.post("/api/instagram/send-message", json={
                "creator_id": "UC_auto_123",
                "creator_username": "auto_resolved_creator",
                "message": "Outreach message with automatic IGSID resolution!",
            })

            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["status"] == "sent"
            assert data["message_id"] == "mid.auto_resolved_success_001"

            # Check that backend dispatched with the correct auto-resolved IGSID
            assert mock_client.post.called
            call_kwargs = mock_client.post.call_args
            assert call_kwargs[1]["json"]["recipient"]["id"] == "17841477777777777"
            assert call_kwargs[1]["json"]["message"]["text"] == "Outreach message with automatic IGSID resolution!"


@pytest.mark.asyncio
async def test_send_message_unregistered_creator_rejected():
    """POST /api/instagram/send-message returns HTTP 400 when no legitimate IGSID is stored."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/instagram/send-message", json={
            "creator_username": "non_stored_creator_xyz",
            "message": "Hello creator without stored IGSID",
        })
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["status"] == "not_messageable"
        assert data["error_code"] == "RECIPIENT_NOT_ELIGIBLE"
        assert "Unable to send automatically: recipient is not eligible for Meta messaging." in data["message"]


@pytest.mark.asyncio
async def test_send_message_missing_igsid_and_username():
    """POST /api/instagram/send-message returns HTTP 400 when no identifier can resolve IGSID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/instagram/send-message", json={
            "message": "Hello creator",
        })
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["error_code"] == "RECIPIENT_NOT_ELIGIBLE"
        assert "Unable to send automatically: recipient is not eligible for Meta messaging." in data["message"]


@pytest.mark.asyncio
async def test_send_message_username_substituted_as_igsid():
    """POST /api/instagram/send-message rejects @username as substitute for IGSID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/instagram/send-message", json={
            "recipient_igsid": "@mrbeast",
            "message": "Hello creator",
        })
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["error_code"] == "IGSID_REQUIRED"


@pytest.mark.asyncio
async def test_send_message_empty_message():
    """POST /api/instagram/send-message returns HTTP 400 when message is empty."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/instagram/send-message", json={
            "recipient_igsid": "17841412345678901",
            "message": "   ",
        })
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["error_code"] == "MESSAGE_REQUIRED"


@pytest.mark.asyncio
async def test_send_message_too_long():
    """POST /api/instagram/send-message returns HTTP 400 when message exceeds 1000 characters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/instagram/send-message", json={
            "recipient_igsid": "17841412345678901",
            "message": "a" * 1005,
        })
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["error_code"] == "MESSAGE_TOO_LONG"


@pytest.mark.asyncio
async def test_send_message_real_meta_success(monkeypatch):
    """POST /api/instagram/send-message sends real Meta API request and returns success payload."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_super_secret_token_123")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "recipient_id": "17841499999999999",
        "message_id": "aWdfbWVzc2FnZToxNzgz"
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.services.instagram_service.httpx.AsyncClient", mock_client_cls):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/instagram/send-message", json={
                "recipient_igsid": "17841499999999999",
                "message": "Hello from creator discovery app!",
                "creator_username": "tested_creator",
                "creator_url": "https://instagram.com/tested_creator"
            })

            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["status"] == "sent"
            assert data["provider"] == "meta_instagram"
            assert data["message_id"] == "aWdfbWVzc2FnZToxNzgz"
            assert "sent_at" in data

            # Verify Meta API call structure
            assert mock_client.post.called
            call_kwargs = mock_client.post.call_args
            assert "https://graph.facebook.com/v21.0/17841400000000000/messages" in call_kwargs[0][0]
            assert call_kwargs[1]["json"] == {
                "recipient": {"id": "17841499999999999"},
                "message": {"text": "Hello from creator discovery app!"}
            }
            assert "Bearer EAA_super_secret_token_123" in call_kwargs[1]["headers"]["Authorization"]

            # Verify token NEVER leaks in response
            assert "EAA_super_secret_token_123" not in json.dumps(data)


@pytest.mark.asyncio
async def test_send_message_real_meta_error(monkeypatch):
    """POST /api/instagram/send-message returns HTTP 400 with structured error when Meta rejects."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_super_secret_token_123")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        "error": {
            "message": "(#10) This recipient is not eligible for messages.",
            "type": "OAuthException",
            "code": 10,
            "error_subcode": 2534014,
            "fbtrace_id": "AbCdEfGh123"
        }
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.services.instagram_service.httpx.AsyncClient", mock_client_cls):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/instagram/send-message", json={
                "recipient_igsid": "17841499999999999",
                "message": "Hello from creator discovery app!",
            })

            assert res.status_code == 400
            data = res.json()
            assert data["success"] is False
            assert data["status"] == "failed"
            assert data["provider"] == "meta_instagram"
            assert data["error"]["code"] == "10"
            assert "permissions" in data["error"]["message"].lower() or "unauthorized" in data["error"]["message"].lower()
            assert "EAA_super_secret_token_123" not in json.dumps(data)


@pytest.mark.asyncio
async def test_send_message_audit_trail_recorded(monkeypatch):
    """Verifies that POST /api/instagram/send-message logs all attempts into audit storage."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "recipient_id": "17841488888888888",
        "message_id": "mid.audit_test_999"
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.services.instagram_service.httpx.AsyncClient", mock_client_cls):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/instagram/send-message", json={
                "recipient_igsid": "17841488888888888",
                "message": "Audit trail verification text",
                "creator_username": "audit_creator",
            })
            assert res.status_code == 200

            # Retrieve audit log
            hist_res = await client.get("/api/social/instagram/history")
            assert hist_res.status_code == 200
            hist = hist_res.json()
            assert len(hist) > 0
            latest = hist[-1]
            assert latest["meta_recipient_id"] == "17841488888888888"
            assert latest["instagram_username"] == "audit_creator"
            assert latest["meta_message_id"] == "mid.audit_test_999"
            assert latest["status"] == "sent"
            assert latest["provider"] == "meta"
            assert "EAA_test_token" not in json.dumps(hist)


@pytest.mark.asyncio
async def test_cold_outreach_prepare_success():
    """POST /api/instagram/outreach/prepare prepares cold outreach without calling Meta API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/instagram/outreach/prepare", json={
            "creator_id": "UCX6OQ3DkcsbYNE6H8uQQuVA",
            "creator_username": "@mrbeast",
            "message": "Hey MrBeast, loved the latest video and would love to collaborate!",
            "action": "profile_opened_copied"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["status"] == "prepared"
        assert data["action"] == "profile_opened_copied"
        assert data["instagram_username"] == "@mrbeast"
        assert data["instagram_url"] == "https://www.instagram.com/mrbeast/"
        assert "Hey MrBeast" in data["message"]
        assert "prepared_at" in data

        # Check that audit log records status as "prepared" and never "sent"
        hist_res = await client.get("/api/social/instagram/history")
        assert hist_res.status_code == 200
        hist = hist_res.json()
        latest = hist[-1]
        assert latest["status"] == "prepared"
        assert latest["mode"] == "cold_outreach"
        assert latest["provider"] == "instagram_direct"
        assert latest["instagram_username"] == "mrbeast"


@pytest.mark.asyncio
async def test_cold_outreach_prepare_validation():
    """POST /api/instagram/outreach/prepare validates empty message and missing handles."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Empty message
        res_empty = await client.post("/api/instagram/outreach/prepare", json={
            "creator_username": "testuser",
            "message": "   "
        })
        assert res_empty.status_code == 422 or res_empty.status_code == 400

        # Missing handle and URL
        res_no_handle = await client.post("/api/instagram/outreach/prepare", json={
            "message": "Hello creator!"
        })
        assert res_no_handle.status_code == 400


