"""Unit tests for Meta Instagram Messaging Integration and Eligibility logic."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from app.core.config import settings
from app.models.messaging_models import (
    InstagramSendRequest,
    InstagramSendResponse,
    InstagramEligibilityRequest,
)
from app.services.instagram_service import InstagramMessagingService, _save_message_record, _load_message_records


@pytest.mark.asyncio
async def test_eligibility_not_discovered():
    """When no Instagram handle or ID is discovered, eligibility is not_discovered."""
    service = InstagramMessagingService()
    res = await service.check_eligibility(username=None, instagram_user_id=None)
    assert res.discovered is False
    assert res.is_eligible is False
    assert res.status == "not_discovered"


@pytest.mark.asyncio
async def test_eligibility_not_configured(monkeypatch):
    """When Meta credentials are not present, status is not_configured."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "")
    
    service = InstagramMessagingService()
    res = await service.check_eligibility(username="@mkbhd")
    assert res.configured is False
    assert res.discovered is True
    assert res.is_eligible is False
    assert res.status == "not_configured"
    assert "not configured" in res.reason


@pytest.mark.asyncio
async def test_eligibility_username_only_without_igsid(monkeypatch):
    """When Meta credentials exist but only username is found without IGSID, status is not_eligible."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    res = await service.check_eligibility(username="mkbhd")
    assert res.configured is True
    assert res.discovered is True
    assert res.is_eligible is False
    assert res.status == "not_eligible"
    assert "Instagram-Scoped User ID (IGSID)" in res.reason


@pytest.mark.asyncio
async def test_eligibility_with_valid_igsid(monkeypatch):
    """When IGSID is provided, status is eligible."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    res = await service.check_eligibility(username="mkbhd", instagram_user_id="17841401234567890")
    assert res.configured is True
    assert res.is_eligible is True
    assert res.status == "eligible"
    assert res.instagram_user_id == "17841401234567890"


@pytest.mark.asyncio
async def test_send_message_unconfigured(monkeypatch):
    """Send fails gracefully without faking success when unconfigured."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "")
    
    service = InstagramMessagingService()
    req = InstagramSendRequest(
        creator_id="creator_123",
        instagram_username="testuser",
        message="Hi! Test message",
    )
    res = await service.send_message(req)
    assert res.success is False
    assert res.status == "not_configured"
    assert "not configured" in res.error.lower()


@pytest.mark.asyncio
async def test_send_message_username_only_rejects_without_igsid(monkeypatch):
    """Send rejects with not_eligible when recipient has no IGSID under Meta rules."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    req = InstagramSendRequest(
        creator_id="creator_123",
        instagram_username="mkbhd",
        message="Hi! Test message",
    )
    
    # Mock conversation lookup returning None
    with patch.object(service, "_try_lookup_conversation_recipient", return_value=None):
        res = await service.send_message(req)
        assert res.success is False
        assert res.status == "not_eligible"
        assert "not currently eligible" in res.error


@pytest.mark.asyncio
async def test_send_message_meta_api_success(monkeypatch):
    """When Meta Graph API responds with 200 OK, returns genuine success with message_id."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_valid_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    req = InstagramSendRequest(
        creator_id="creator_123",
        instagram_user_id="17841401234567890",
        instagram_username="mkbhd",
        message="Hi! Test message from AI creator outreach application.",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "recipient_id": "17841401234567890",
        "message_id": "aWdfbWVzc2FnZToxNz",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        res = await service.send_message(req)

        assert res.success is True
        assert res.status == "sent"
        assert res.message_id == "aWdfbWVzc2FnZToxNz"
        assert res.recipient_id == "17841401234567890"
        assert res.sent_at is not None


@pytest.mark.asyncio
async def test_send_message_meta_api_error_translation(monkeypatch):
    """When Meta returns an API error code, maps to a human-readable explanation."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_valid_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    req = InstagramSendRequest(
        creator_id="creator_123",
        instagram_user_id="17841401234567890",
        instagram_username="mkbhd",
        message="Hi! Test message",
    )

    # 1. Token error (190)
    mock_res_190 = MagicMock()
    mock_res_190.status_code = 400
    mock_res_190.json.return_value = {
        "error": {
            "message": "Error validating access token: Session has expired.",
            "type": "OAuthException",
            "code": 190,
            "error_subcode": 463
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_res_190
        res = await service.send_message(req)
        assert res.success is False
        assert res.status == "failed"
        assert "Access token is invalid or expired" in res.error

    # 2. Recipient eligibility error (100 / 2018001)
    mock_res_elig = MagicMock()
    mock_res_elig.status_code = 400
    mock_res_elig.json.return_value = {
        "error": {
            "message": "Cannot message user outside 24-hour window.",
            "type": "IGApiException",
            "code": 100,
            "error_subcode": 2018001
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_res_elig
        res = await service.send_message(req)
        assert res.success is False
        assert res.status == "not_eligible"
        assert "The recipient is not eligible" in res.error
