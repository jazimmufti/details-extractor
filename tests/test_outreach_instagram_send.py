"""Comprehensive tests for the dedicated POST /api/outreach/instagram/send endpoint.

Tests:
1. Eligible recipient (stored IGSID) -> Dispatches to Meta -> returns HTTP 200 with verified message_id.
2. Ineligible recipient (public handle only) -> Rejection with HTTP 400 RECIPIENT_NOT_ELIGIBLE; Meta is NEVER called.
3. Meta API error -> HTTP 400 rejected with Meta diagnostics; never marked as sent.
4. Missing Meta configuration -> HTTP 400 not_configured.
5. Successful send audit trail -> Records creator, handle, timestamp, message, message_id, status.
6. No fake success when Meta rejects the request.
7. Unresolved Instagram account -> HTTP 400 ACCOUNT_UNRESOLVED.
8. Simulation mode -> Succeeds locally without external network requests.
"""

import json
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.core.config import settings
from app.services.instagram_service import _save_recipient_to_registry, instagram_service


@pytest.mark.asyncio
async def test_outreach_send_eligible_recipient(monkeypatch):
    """1 & 5. Eligible recipient with stored IGSID dispatches to Meta and returns success."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_valid_outreach_token_123")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    # Store legitimate recipient mapping
    _save_recipient_to_registry(
        username="eligible_creator",
        igsid="17841499998888111",
        creator_id="UC_eligible_001",
        source="meta_webhook",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "recipient_id": "17841499998888111",
        "message_id": "mid.meta_official_outreach_12345",
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.services.instagram_service.httpx.AsyncClient", mock_client_cls):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/outreach/instagram/send", json={
                "creator_name": "Eligible Creator Channel",
                "creator_id": "UC_eligible_001",
                "instagram_username": "@eligible_creator",
                "instagram_url": "https://www.instagram.com/eligible_creator/",
                "message": "Hi, loved your recent video and would love to partner on our upcoming campaign!",
                "mode": "real",
            })

            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["status"] == "sent"
            assert data["message_id"] == "mid.meta_official_outreach_12345"
            assert data["recipient_id"] == "17841499998888111"
            assert data["provider"] == "meta"
            assert "sent_at" in data

            # Verify Meta API call structure
            assert mock_client.post.called
            call_kwargs = mock_client.post.call_args
            assert "17841400000000000/messages" in call_kwargs[0][0]
            assert call_kwargs[1]["json"]["recipient"]["id"] == "17841499998888111"
            assert "loved your recent video" in call_kwargs[1]["json"]["message"]["text"]

            # Verify audit trail
            hist = instagram_service.get_message_history()
            assert len(hist) > 0
            latest = hist[-1]
            assert latest.status == "sent"
            assert latest.meta_message_id == "mid.meta_official_outreach_12345"
            assert latest.meta_recipient_id == "17841499998888111"
            assert latest.creator_id == "UC_eligible_001"


@pytest.mark.asyncio
async def test_outreach_send_ineligible_recipient(monkeypatch):
    """2. Ineligible recipient (public handle only, no stored IGSID) is rejected without calling Meta."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_valid_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    mock_client = AsyncMock()
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.services.instagram_service.httpx.AsyncClient", mock_client_cls):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/outreach/instagram/send", json={
                "creator_name": "Cold Discovered Creator",
                "creator_id": "UC_cold_creator_999",
                "instagram_username": "@cold_discovered_creator",
                "instagram_url": "https://www.instagram.com/cold_discovered_creator/",
                "message": "Cold outreach attempt",
                "mode": "real",
            })

            assert res.status_code == 400
            data = res.json()
            assert data["success"] is False
            assert data["status"] in ("not_eligible", "not_messageable")
            assert data["error_code"] == "RECIPIENT_NOT_ELIGIBLE"
            assert "This Instagram account was found, but Meta does not currently allow this account" in data["error"]
            assert data["message_id"] is None

            # CRITICAL: Meta API was NEVER called
            assert not mock_client.post.called

            # Verify audit trail records rejection without fake message ID
            hist = instagram_service.get_message_history()
            latest = hist[-1]
            assert latest.status in ("not_messageable", "not_eligible")
            assert latest.meta_message_id is None
            assert latest.error_code == "RECIPIENT_NOT_ELIGIBLE"


@pytest.mark.asyncio
async def test_outreach_send_meta_api_error(monkeypatch):
    """3 & 6. Meta API error (e.g. 24h window closed) returns structured rejection and no fake success."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_valid_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")

    _save_recipient_to_registry(
        username="expired_window_creator",
        igsid="17841455555555555",
        creator_id="UC_expired_001",
        source="meta_webhook",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        "error": {
            "message": "(#10) Message failed to send because 24 hour window has expired.",
            "type": "OAuthException",
            "code": 10,
            "error_subcode": 2018001,
            "fbtrace_id": "trace_err_400_abc",
        }
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    with patch("app.services.instagram_service.httpx.AsyncClient", mock_client_cls):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/outreach/instagram/send", json={
                "creator_name": "Expired Window Creator",
                "creator_id": "UC_expired_001",
                "instagram_username": "@expired_window_creator",
                "message": "Outreach message after window expired",
                "mode": "real",
            })

            assert res.status_code == 400
            data = res.json()
            assert data["success"] is False
            assert data["status"] == "rejected"
            assert data["error_code"] == "META_10"
            assert data["message_id"] is None
            assert data["meta_diagnostics"]["code"] == 10
            assert data["meta_diagnostics"]["error_subcode"] == 2018001
            assert data["meta_diagnostics"]["fbtrace_id"] == "trace_err_400_abc"

            # Verify audit trail records rejection and NO fake message ID
            hist = instagram_service.get_message_history()
            latest = hist[-1]
            assert latest.status == "rejected"
            assert latest.meta_message_id is None
            assert latest.meta_error_code == 10


@pytest.mark.asyncio
async def test_outreach_send_missing_meta_configuration(monkeypatch):
    """4. Missing Meta configuration returns HTTP 400 not_configured."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/outreach/instagram/send", json={
            "creator_name": "Any Creator",
            "instagram_username": "@any_creator",
            "message": "Hello creator",
            "mode": "real",
        })

        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["status"] == "not_configured"
        assert data["error_code"] == "META_NOT_CONFIGURED"
        assert "not configured" in data["error"].lower()


@pytest.mark.asyncio
async def test_outreach_send_unresolved_account():
    """7. Completely unresolved account (no handle, URL, or IGSID) returns HTTP 400 ACCOUNT_UNRESOLVED."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/outreach/instagram/send", json={
            "message": "Hello with no recipient identifiers",
            "mode": "real",
        })

        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["status"] == "account_unresolved"
        assert data["error_code"] == "ACCOUNT_UNRESOLVED"
        assert "could not be resolved" in data["error"].lower()


@pytest.mark.asyncio
async def test_outreach_send_simulation_mode():
    """8. Simulation mode succeeds locally and labels output as simulated."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/outreach/instagram/send", json={
            "creator_name": "Simulated Creator",
            "creator_id": "UC_sim_001",
            "instagram_username": "@simulated_creator",
            "message": "Test simulated outreach message",
            "mode": "simulation",
        })

        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["status"] == "simulated"
        assert data["mode"] == "simulation"
        assert data["provider"] == "local"
        assert data["message_id"] is None
        assert "Simulated successfully" in data["details"]
