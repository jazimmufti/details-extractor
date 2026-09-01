"""Comprehensive Unit tests for Meta Instagram Messaging Integration,
Separation of Concerns, Recipient Identity Resolution, and Simulation Mode.
"""

import hmac
import hashlib
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from app.core.config import settings
from app.models.messaging_models import (
    DiscoveryStatus,
    RecipientIdentityStatus,
    MessagingStatus,
    SendStatus,
    DiscoveredInstagramProfile,
    MetaRecipient,
    MessagingCapability,
    InstagramEligibilityRequest,
    InstagramEligibilityResponse,
    InstagramSendRequest,
    InstagramSendResponse,
)
from app.services.instagram_service import (
    InstagramMessagingService,
    _save_message_record,
    _load_message_records,
    _save_recipient_to_registry,
    _load_recipients_registry,
)


@pytest.mark.asyncio
async def test_eligibility_not_discovered():
    """1. When no Instagram handle or ID is present, status is not_discovered."""
    service = InstagramMessagingService()
    res = await service.check_eligibility(username=None, instagram_user_id=None, mode="real")
    assert res.discovery.status == DiscoveryStatus.NOT_DISCOVERED
    assert res.recipient.status == RecipientIdentityStatus.UNRESOLVED
    assert res.can_send is False
    assert res.capability.status == MessagingStatus.NOT_MESSAGEABLE


@pytest.mark.asyncio
async def test_eligibility_username_only_unresolved(monkeypatch):
    """2 & 3. Username alone is DISCOVERED, but Recipient Identity is UNRESOLVED.
    Invariant: Username must NEVER be converted into an IGSID.
    """
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    res = await service.check_eligibility(username="@mrbeast", instagram_user_id=None, mode="real")
    
    # Discovery is present
    assert res.discovery.status == DiscoveryStatus.DISCOVERED
    assert res.discovery.username == "mrbeast"
    
    # Recipient identity is UNRESOLVED
    assert res.recipient.status == RecipientIdentityStatus.UNRESOLVED
    assert res.recipient.recipient_id is None
    
    # Capability is NOT_MESSAGEABLE / REQUIRES_INTERACTION
    assert res.capability.status == MessagingStatus.REQUIRES_INTERACTION
    assert res.can_send is False
    assert "prohibits cold direct messages" in res.capability.reason


@pytest.mark.asyncio
async def test_eligibility_not_configured(monkeypatch):
    """4. When Meta credentials are not present, status is not_configured."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "")
    
    service = InstagramMessagingService()
    res = await service.check_eligibility(username="mkbhd", mode="real")
    assert res.capability.status == MessagingStatus.NOT_CONFIGURED
    assert res.can_send is False
    assert "not configured" in res.capability.reason.lower()


@pytest.mark.asyncio
async def test_eligibility_with_legitimate_igsid(monkeypatch):
    """5 & 6. When a legitimate IGSID is resolved/provided, status is MESSAGEABLE and can_send=True."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    res = await service.check_eligibility(username="mkbhd", instagram_user_id="17841401234567890", mode="real")
    
    assert res.discovery.status == DiscoveryStatus.DISCOVERED
    assert res.recipient.status == RecipientIdentityStatus.RESOLVED
    assert res.recipient.recipient_id == "17841401234567890"
    assert res.capability.status == MessagingStatus.MESSAGEABLE
    assert res.can_send is True


@pytest.mark.asyncio
async def test_eligibility_simulation_mode():
    """7. Local simulation mode allows testing without Meta credentials."""
    service = InstagramMessagingService()
    res = await service.check_eligibility(username="testcreator", mode="simulation")
    
    assert res.mode == "simulation"
    assert res.can_send is True
    assert res.capability.status == MessagingStatus.MESSAGEABLE
    assert res.capability.provider == "local"


@pytest.mark.asyncio
async def test_send_simulation_never_calls_meta(monkeypatch):
    """8 & 15. Simulation mode executes locally and makes ZERO external Meta API requests."""
    service = InstagramMessagingService()
    req = InstagramSendRequest(
        instagram_username="mkbhd",
        message="Simulated test outreach",
        mode="simulation",
    )
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        res = await service.send_message(req)
        
        # Zero HTTP calls made!
        mock_post.assert_not_called()
        assert res.success is True
        assert res.status == "simulated"
        assert res.mode == "simulation"
        assert res.provider == "local"
        assert res.message_id is None  # Never fakes a Meta message ID!


@pytest.mark.asyncio
async def test_send_real_mode_rejects_username_only_before_http(monkeypatch):
    """9. Real mode refuses username-only recipient without making an invalid HTTP request."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_test_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    req = InstagramSendRequest(
        instagram_username="mrbeast",
        instagram_user_id=None,
        message="Test message",
        mode="real",
    )
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        res = await service.send_message(req)
        
        # Refused before external dispatch
        mock_post.assert_not_called()
        assert res.success is False
        assert res.status == "rejected"
        assert "cannot receive messages via username alone" in res.error


@pytest.mark.asyncio
async def test_send_real_mode_success(monkeypatch):
    """10 & 16. Real mode sends to legitimate IGSID and records actual Meta message ID."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_valid_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    req = InstagramSendRequest(
        instagram_user_id="17841401234567890",
        instagram_username="mkbhd",
        message="Hi Marques, partnership opportunity.",
        mode="real",
    )
    
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "recipient_id": "17841401234567890",
        "message_id": "meta_msg_987654321",
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_res
        res = await service.send_message(req)
        
        mock_post.assert_called_once()
        assert res.success is True
        assert res.status == "sent"
        assert res.mode == "real"
        assert res.message_id == "meta_msg_987654321"
        assert res.recipient_id == "17841401234567890"


@pytest.mark.asyncio
async def test_send_real_mode_meta_error_diagnostics(monkeypatch):
    """11. Real mode captures full Meta error diagnostics without guessing."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_expired_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    req = InstagramSendRequest(
        instagram_user_id="17841401234567890",
        message="Hello",
        mode="real",
    )
    
    mock_res = MagicMock()
    mock_res.status_code = 400
    mock_res.json.return_value = {
        "error": {
            "message": "Error validating access token: Session has expired.",
            "type": "OAuthException",
            "code": 190,
            "error_subcode": 463,
            "fbtrace_id": "Az123456789",
        }
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_res
        res = await service.send_message(req)
        
        assert res.success is False
        assert res.status == "rejected"
        assert res.meta_diagnostics is not None
        assert res.meta_diagnostics.code == 190
        assert res.meta_diagnostics.fbtrace_id == "Az123456789"
        assert "invalid or expired" in res.error


@pytest.mark.asyncio
async def test_idempotency_prevents_duplicate_sends(monkeypatch):
    """12 & 19. Server-side idempotency returns cached response for duplicate requests."""
    monkeypatch.setattr(settings, "INSTAGRAM_ACCESS_TOKEN", "EAA_valid_token")
    monkeypatch.setattr(settings, "INSTAGRAM_ACCOUNT_ID", "17841400000000000")
    
    service = InstagramMessagingService()
    req = InstagramSendRequest(
        idempotency_key="key_duplicate_test_123",
        instagram_user_id="17841401234567890",
        message="Test message",
        mode="real",
    )
    
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "recipient_id": "17841401234567890",
        "message_id": "meta_msg_idempotent_1",
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_res
        # First send
        res1 = await service.send_message(req)
        assert res1.success is True
        assert mock_post.call_count == 1
        
        # Second send with identical idempotency key
        res2 = await service.send_message(req)
        assert res2.success is True
        assert res2.message_id == "meta_msg_idempotent_1"
        # Mock post was NOT called a second time!
        assert mock_post.call_count == 1


def test_webhook_signature_verification(monkeypatch):
    """20 & 21. Webhook HMAC SHA-256 signature verification."""
    monkeypatch.setattr(settings, "META_APP_SECRET", "super_secret_app_key")
    
    service = InstagramMessagingService()
    payload = b'{"object": "instagram", "entry": []}'
    
    # Generate valid signature
    valid_sig = "sha256=" + hmac.new(b"super_secret_app_key", payload, hashlib.sha256).hexdigest()
    assert service.verify_webhook_signature(payload, valid_sig) is True
    
    # Invalid signature
    invalid_sig = "sha256=invalid_hex_signature"
    assert service.verify_webhook_signature(payload, invalid_sig) is False


def test_webhook_ingest_event_resolves_recipient():
    """22. Inbound webhook messaging event registers verified sender IGSID."""
    service = InstagramMessagingService()
    event_payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "17841400000000000",
                "time": 1700000000,
                "messaging": [
                    {
                        "sender": {"id": "17841409999999999", "username": "verified_creator"},
                        "recipient": {"id": "17841400000000000"},
                        "message": {"text": "Hi, let's connect!"}
                    }
                ]
            }
        ]
    }
    
    updated = service.ingest_webhook_event(event_payload)
    assert updated == 1
    
    # Verify registry contains mapping
    registry = _load_recipients_registry()
    assert "verified_creator" in registry
    assert registry["verified_creator"]["igsid"] == "17841409999999999"
