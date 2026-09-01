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
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["status"] == "not_messageable"
        assert data["error_code"] == "RECIPIENT_NOT_ELIGIBLE"
        assert "Unable to send automatically: recipient is not eligible for Meta messaging." in data["error"]


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
        assert data["messaging"]["status"] in ("manual_send_required", "interaction_required", "manual_instagram_required")
        assert data["delivery"]["method"] == "manual_instagram"

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
    """POST /api/social/instagram/send automatically resolves stored legitimate IGSID without user input."""
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
            # Client sends only instagram_username and message (NO instagram_user_id provided by frontend)
            res = await client.post("/api/social/instagram/send", json={
                "creator_id": "UC_auto_123",
                "instagram_username": "auto_resolved_creator",
                "message": "Outreach message with automatic IGSID resolution!",
                "mode": "real"
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
    """POST /api/social/instagram/send returns HTTP 400 when no legitimate IGSID is stored."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/social/instagram/send", json={
            "instagram_username": "non_stored_creator_xyz",
            "message": "Hello creator without stored IGSID",
            "mode": "real"
        })
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["status"] == "not_messageable"
        assert data["error_code"] == "RECIPIENT_NOT_ELIGIBLE"
        assert "Unable to send automatically: recipient is not eligible for Meta messaging." in data["error"]


@pytest.mark.asyncio
async def test_send_message_missing_igsid_and_username():
    """POST /api/social/instagram/send returns HTTP 400 when no identifier can resolve IGSID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/social/instagram/send", json={
            "message": "Hello creator",
            "mode": "real"
        })
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["error_code"] == "RECIPIENT_NOT_ELIGIBLE"
        assert "Unable to send automatically: recipient is not eligible for Meta messaging." in data["error"]


@pytest.mark.asyncio
async def test_send_message_username_substituted_as_igsid():
    """POST /api/social/instagram/send rejects @username as substitute for IGSID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/social/instagram/send", json={
            "instagram_user_id": "@mrbeast",
            "message": "Hello creator",
            "mode": "real"
        })
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["error_code"] == "IGSID_REQUIRED"


@pytest.mark.asyncio
async def test_send_message_empty_message():
    """POST /api/social/instagram/send returns validation error when message is empty."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/social/instagram/send", json={
            "instagram_user_id": "17841412345678901",
            "message": "",
            "mode": "real"
        })
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_send_message_too_long():
    """POST /api/social/instagram/send returns validation error when message exceeds 1000 characters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/social/instagram/send", json={
            "instagram_user_id": "17841412345678901",
            "message": "a" * 1005,
            "mode": "real"
        })
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_send_message_real_meta_success(monkeypatch):
    """POST /api/social/instagram/send sends real Meta API request and returns success payload."""
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
            res = await client.post("/api/social/instagram/send", json={
                "instagram_user_id": "17841499999999999",
                "message": "Hello from creator discovery app!",
                "instagram_username": "tested_creator",
                "mode": "real"
            })

            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["status"] == "sent"
            assert data["provider"] == "meta"
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
    """POST /api/social/instagram/send returns HTTP 400 with structured error when Meta rejects."""
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
            res = await client.post("/api/social/instagram/send", json={
                "instagram_user_id": "17841499999999999",
                "message": "Hello from creator discovery app!",
                "mode": "real"
            })

            assert res.status_code == 400
            data = res.json()
            assert data["success"] is False
            assert data["status"] == "rejected"
            assert data["provider"] == "meta"
            assert data["meta_diagnostics"]["code"] == 10
            assert "permissions" in data["error"].lower() or "unauthorized" in data["error"].lower()
            assert "EAA_super_secret_token_123" not in json.dumps(data)


@pytest.mark.asyncio
async def test_send_message_audit_trail_recorded(monkeypatch):
    """Verifies that POST /api/social/instagram/send logs all attempts into audit storage."""
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
            res = await client.post("/api/social/instagram/send", json={
                "instagram_user_id": "17841488888888888",
                "message": "Audit trail verification text",
                "instagram_username": "audit_creator",
                "mode": "real"
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


@pytest.mark.asyncio
async def test_webhook_ingest_and_subsequent_send_flow(monkeypatch):
    """
    End-to-End flow:
    1. Meta webhook event arrives from an interacting creator.
    2. Recipient IGSID & username/creator_id are registered in persistence.
    3. Recipient status confirms messaging eligibility.
    4. Send endpoint automatically resolves the stored IGSID and dispatches to Meta.
    5. Mocked Meta API returns HTTP 200 with mid.xxx.
    6. Audit log records 'sent' with real Meta message ID.
    """
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token_full_flow")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    monkeypatch.setattr(settings, "META_APP_SECRET", "")  # Skip HMAC signature check for unit test

    webhook_payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400000000000",
                "time": 1700000000,
                "messaging": [
                    {
                        "sender": {
                            "id": "17841499112233445",
                            "username": "real_collaborator"
                        },
                        "recipient": {
                            "id": "17841400000000000"
                        },
                        "timestamp": 1700000000,
                        "message": {
                            "mid": "m_inbound_123",
                            "text": "Hello, I want to partner with your brand!"
                        },
                        "optin": {
                            "ref": "UC_collab_999"
                        }
                    }
                ]
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "recipient_id": "17841499112233445",
        "message_id": "mid.meta_delivery_success_777"
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Deliver Webhook Event
        wh_res = await client.post("/api/webhook/instagram", json=webhook_payload)
        assert wh_res.status_code == 200
        wh_data = wh_res.json()
        assert wh_data["status"] == "success"
        assert wh_data["recipients_updated"] >= 1

        # 2. Check Recipient Status
        status_res = await client.get("/api/instagram/recipient-status", params={
            "instagram_username": "real_collaborator",
            "creator_id": "UC_collab_999",
            "mode": "real"
        })
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["messaging"]["eligible"] is True
        assert status_data["messaging"]["status"] == "eligible"
        assert "17841499112233445" not in json.dumps(status_data["messaging"])  # Raw IGSID not leaked

        # 3. Dispatch Message via POST /api/social/instagram/send (only username/creator_id provided)
        with patch("app.services.instagram_service.httpx.AsyncClient", mock_client_cls):
            send_res = await client.post("/api/social/instagram/send", json={
                "creator_id": "UC_collab_999",
                "instagram_username": "real_collaborator",
                "message": "Hi, let's collaborate on a sponsor deal!",
                "mode": "real"
            })

            assert send_res.status_code == 200
            send_data = send_res.json()
            assert send_data["success"] is True
            assert send_data["status"] == "sent"
            assert send_data["message_id"] == "mid.meta_delivery_success_777"
            assert send_data["provider"] == "meta"

            # 4. Verify Meta API call parameters
            assert mock_client.post.called
            call_args = mock_client.post.call_args
            assert "https://graph.facebook.com/v21.0/17841400000000000/messages" in call_args[0][0]
            assert call_args[1]["headers"]["Authorization"] == "Bearer EAA_test_token_full_flow"
            assert call_args[1]["json"] == {
                "recipient": {"id": "17841499112233445"},
                "message": {"text": "Hi, let's collaborate on a sponsor deal!"}
            }

            # 5. Check Audit Log
            hist_res = await client.get("/api/social/instagram/history")
            assert hist_res.status_code == 200
            hist = hist_res.json()
            latest = hist[-1]
            assert latest["status"] == "sent"
            assert latest["meta_message_id"] == "mid.meta_delivery_success_777"
            assert latest["meta_recipient_id"] == "17841499112233445"
            assert latest["provider"] == "meta"


@pytest.mark.asyncio
async def test_negative_public_username_meta_not_called(monkeypatch):
    """Strict negative test: Discovered public username without stored IGSID NEVER triggers Meta API."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    mock_client = AsyncMock()
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.services.instagram_service.httpx.AsyncClient", mock_client_cls):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/social/instagram/send", json={
                "instagram_username": "some_completely_uncontacted_creator_12345",
                "message": "Cold message attempt",
                "mode": "real"
            })

            assert res.status_code == 400
            data = res.json()
            assert data["success"] is False
            assert data["status"] == "not_messageable"
            assert data["error_code"] == "RECIPIENT_NOT_ELIGIBLE"
            assert "Unable to send automatically: recipient is not eligible for Meta messaging." in data["error"]

            # CRITICAL: External Meta API was NEVER called
            assert not mock_client.post.called


@pytest.mark.asyncio
async def test_outreach_resolution_no_prior_conversation_rajshamani(monkeypatch):
    """Scenario 1: Discovered creator (e.g. @rajshamani) with no prior conversation is outreach-ready via manual send."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/instagram/outreach/status", params={
            "instagram_username": "rajshamani",
            "creator_id": "UC_raj_shamani_channel",
            "mode": "real"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["outreach_status"] == "ready_for_outreach"
        assert data["delivery"]["method"] == "manual_instagram"
        assert data["delivery"]["messageable"] is False
        assert data["delivery"]["can_attempt_api_send"] is False
        assert "manual" in data["delivery"]["label"].lower()
        assert data["meta_recipient_id_available"] is False


@pytest.mark.asyncio
async def test_outreach_resolution_legitimate_meta_recipient(monkeypatch):
    """Scenario 2: Creator with legitimate Meta recipient ID resolves to meta_api delivery."""
    from app.services.instagram_service import _save_recipient_to_registry

    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    _save_recipient_to_registry(
        username="verified_partner",
        igsid="17841499998888777",
        creator_id="UC_verified_partner_99",
        source="meta_webhook"
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/instagram/outreach/status", params={
            "instagram_username": "verified_partner",
            "creator_id": "UC_verified_partner_99",
            "mode": "real"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["outreach_status"] == "api_messageable"
        assert data["delivery"]["method"] == "meta_api"
        assert data["delivery"]["messageable"] is True
        assert data["delivery"]["can_attempt_api_send"] is True
        assert data["meta_recipient_id_available"] is True


@pytest.mark.asyncio
async def test_outreach_meta_api_failure_handling(monkeypatch):
    """Scenario 3: Meta API returns error -> status is recorded as rejected/failed without claiming sent."""
    from app.services.instagram_service import _save_recipient_to_registry

    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    _save_recipient_to_registry(
        username="failing_recipient",
        igsid="17841488888888888",
        creator_id="UC_fail_creator_01",
        source="meta_webhook"
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        "error": {
            "message": "(#10) Message failed to send because 24 hour window has expired.",
            "type": "OAuthException",
            "code": 10,
            "fbtrace_id": "trace_xyz_123"
        }
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.services.instagram_service.httpx.AsyncClient", mock_client_cls):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/social/instagram/send", json={
                "creator_id": "UC_fail_creator_01",
                "instagram_username": "failing_recipient",
                "message": "Hello partner!",
                "mode": "real"
            })
            assert res.status_code == 400
            data = res.json()
            assert data["success"] is False
            assert data["status"] == "rejected"
            assert data["error"] is not None

            # Audit record is NOT marked as sent
            hist_res = await client.get("/api/social/instagram/history")
            assert hist_res.status_code == 200
            hist = hist_res.json()
            latest = hist[-1]
            assert latest["status"] == "rejected"
            assert latest["meta_message_id"] is None


@pytest.mark.asyncio
async def test_batch_creator_delivery_method_resolution(monkeypatch):
    """Scenario 6: Mixed outreach batch resolution correctly identifies independent delivery methods."""
    from app.services.instagram_service import instagram_service, _save_recipient_to_registry

    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    _save_recipient_to_registry(
        username="partner_with_igsid",
        igsid="17841411122233344",
        creator_id="UC_partner_01",
        source="meta_webhook"
    )

    # 1. Partner with IGSID -> meta_api
    deliv_a = instagram_service.resolve_delivery_method(
        creator_id="UC_partner_01",
        instagram_username="partner_with_igsid",
        mode="real"
    )
    assert deliv_a["method"] == "meta_api"
    assert deliv_a["messageable"] is True
    assert deliv_a["can_attempt_api_send"] is True

    # 2. Public creator without IGSID -> manual_instagram
    deliv_b = instagram_service.resolve_delivery_method(
        creator_id="UC_cold_creator_02",
        instagram_username="cold_creator_raj",
        mode="real"
    )
    assert deliv_b["method"] == "manual_instagram"
    assert deliv_b["messageable"] is False
    assert deliv_b["can_attempt_api_send"] is False

    # 3. Simulation mode -> simulation
    deliv_c = instagram_service.resolve_delivery_method(
        creator_id="UC_sim_creator_03",
        instagram_username="any_creator",
        mode="simulation"
    )
    assert deliv_c["method"] == "simulation"
    assert deliv_c["messageable"] is True




