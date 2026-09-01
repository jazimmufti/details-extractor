"""Official Meta Instagram Messaging Service Integration.

Follows official Meta Graph API specifications for Instagram Messaging.
Never fakes success, enforces recipient eligibility rules, and logs all attempts.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.models.messaging_models import (
    InstagramSendRequest,
    InstagramSendResponse,
    InstagramEligibilityResponse,
    MessageRecord,
)

# Persistent audit log file
DATA_DIR = Path(__file__).parent.parent.parent / "data"
MESSAGES_FILE = DATA_DIR / "messages.json"


def _ensure_data_dir():
    """Ensure data directory and messages audit file exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not MESSAGES_FILE.exists():
        MESSAGES_FILE.write_text("[]", encoding="utf-8")


def _save_message_record(record: MessageRecord):
    """Appends an auditable message record to local persistent store."""
    try:
        _ensure_data_dir()
        existing = []
        if MESSAGES_FILE.exists():
            try:
                existing = json.loads(MESSAGES_FILE.read_text(encoding="utf-8"))
            except Exception:
                existing = []
        existing.append(record.model_dump())
        MESSAGES_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to persist message audit log: {e}")


def _load_message_records() -> List[MessageRecord]:
    """Loads all message records from audit store."""
    try:
        _ensure_data_dir()
        if MESSAGES_FILE.exists():
            raw = json.loads(MESSAGES_FILE.read_text(encoding="utf-8"))
            return [MessageRecord(**item) for item in raw]
    except Exception as e:
        logger.error(f"Failed to load message records: {e}")
    return []


class InstagramMessagingService:
    """Official Meta Instagram Graph API Messaging Client."""

    def __init__(self):
        self.api_version = settings.META_GRAPH_API_VERSION or "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    @property
    def is_configured(self) -> bool:
        """Returns True if required Meta credentials are present."""
        return settings.has_meta_configured

    def get_configuration_status(self) -> Dict[str, Any]:
        """Returns non-sensitive configuration diagnostics."""
        return {
            "configured": self.is_configured,
            "has_access_token": bool(settings.INSTAGRAM_ACCESS_TOKEN),
            "account_id": settings.INSTAGRAM_ACCOUNT_ID or None,
            "api_version": self.api_version,
            "provider": "meta",
            "test_mode": True,
        }

    async def check_eligibility(
        self, username: Optional[str] = None, instagram_user_id: Optional[str] = None
    ) -> InstagramEligibilityResponse:
        """
        Evaluates whether a discovered Instagram account can receive a message
        via the official Meta Graph API.
        
        Meta API Rules:
        1. Meta does NOT permit unsolicited cold messaging by username alone.
        2. A recipient must have an Instagram-Scoped ID (IGSID) or Page-Scoped ID (PSID).
        3. A messaging conversation must be initiated by the user or within the 24h standard window.
        4. In Development Mode, the recipient must be an approved app tester.
        """
        clean_username = username.lstrip("@").strip() if username else None
        discovered = bool(clean_username or instagram_user_id)

        if not discovered:
            return InstagramEligibilityResponse(
                configured=self.is_configured,
                discovered=False,
                username=None,
                instagram_user_id=None,
                is_eligible=False,
                status="not_discovered",
                reason="No Instagram account was discovered for this creator.",
                requirements=[
                    "A valid Instagram profile must be identified first.",
                ]
            )

        if not self.is_configured:
            return InstagramEligibilityResponse(
                configured=False,
                discovered=True,
                username=clean_username,
                instagram_user_id=instagram_user_id,
                is_eligible=False,
                status="not_configured",
                reason="Meta Instagram API credentials (INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID) are not configured in the server environment.",
                requirements=[
                    "Configure INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in .env.",
                    "Meta app must have 'instagram_manage_messages' permission enabled."
                ]
            )

        # If user provided or system resolved a recipient IGSID
        if instagram_user_id and instagram_user_id.strip():
            return InstagramEligibilityResponse(
                configured=True,
                discovered=True,
                username=clean_username,
                instagram_user_id=instagram_user_id.strip(),
                is_eligible=True,
                status="eligible",
                reason="Instagram Scoped ID (IGSID) is available. Eligible for Meta Graph API messaging attempt.",
                requirements=[
                    "Message will be sent directly through Meta Graph API.",
                    "Subject to Meta's 24-hour customer service window and platform policies."
                ]
            )

        # When only a public username is discovered from YouTube/socials
        return InstagramEligibilityResponse(
            configured=True,
            discovered=True,
            username=clean_username,
            instagram_user_id=None,
            is_eligible=False,
            status="not_eligible",
            reason=(
                f"Discovered @{clean_username} cannot receive unsolicited messages via username alone. "
                "Meta's official Graph API requires a recipient Instagram-Scoped User ID (IGSID) "
                "established when a user interacts with your business account."
            ),
            requirements=[
                "Meta Graph API prohibits direct username-based cold DMs.",
                "Recipient must send a DM or comment to your Instagram Professional account to generate an IGSID.",
                "Alternatively, specify the recipient's IGSID if already known from previous interactions."
            ]
        )

    async def _try_lookup_conversation_recipient(self, username: str) -> Optional[str]:
        """
        Attempts to query active business inbox conversations to see if
        a recipient matching the username already has an established IGSID.
        """
        if not self.is_configured:
            return None

        clean_username = username.lstrip("@").lower().strip()
        account_id = settings.INSTAGRAM_ACCOUNT_ID
        token = settings.INSTAGRAM_ACCESS_TOKEN

        try:
            url = f"{self.base_url}/{account_id}/conversations"
            params = {
                "fields": "participants,updated_time",
                "access_token": token,
                "platform": "instagram",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    for conv in data.get("data", []):
                        for p in conv.get("participants", {}).get("data", []):
                            if p.get("username", "").lower() == clean_username:
                                return p.get("id")
        except Exception as e:
            logger.warning(f"Failed to lookup conversation for username '{username}': {e}")
        return None

    def _map_meta_error(self, status_code: int, error_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Maps raw Meta Graph API error codes into human-readable messages.
        """
        code = error_data.get("code")
        subcode = error_data.get("error_subcode")
        meta_msg = error_data.get("message", "Unknown Meta API error")
        error_type = error_data.get("type", "")

        logger.error(f"Meta Graph API Error: code={code}, subcode={subcode}, type={error_type}, msg={meta_msg}")

        # Expired or invalid token
        if code == 190:
            return (
                "Access token is invalid or expired. Please generate a new Meta User or Page Access Token.",
                "status: 401 / code: 190 (OAuthException)"
            )
        # Permission missing
        if code in (10, 200) or "capability" in meta_msg.lower() or "permission" in meta_msg.lower():
            return (
                "Instagram account authorization or 'instagram_manage_messages' permission is required.",
                f"code: {code} / {meta_msg}"
            )
        # Recipient eligibility / 24 hour window / not reachable
        if code == 100 and subcode in (2018001, 2018074, 2018028) or "recipient" in meta_msg.lower():
            return (
                "The recipient is not eligible for this messaging flow. Meta requires recipient interaction or active messaging window.",
                f"code: {code} / subcode: {subcode} ({meta_msg})"
            )
        # Rate limit
        if code in (4, 17, 32, 613):
            return (
                "Meta messaging rate limit exceeded. Please wait before retrying.",
                f"code: {code} ({meta_msg})"
            )

        return (
            f"Meta rejected the message: {meta_msg}",
            f"HTTP {status_code} / code: {code}"
        )

    async def send_message(self, request: InstagramSendRequest) -> InstagramSendResponse:
        """
        Executes a real message dispatch through Meta's official Graph API.
        
        Strictly returns genuine Meta API results. Never mocks success.
        """
        rec_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        clean_username = request.instagram_username.lstrip("@").strip() if request.instagram_username else None

        # 1. Validate Meta Credentials Configuration
        if not self.is_configured:
            err_msg = "Instagram messaging is not configured yet."
            details_msg = "INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID must be configured on the server."
            record = MessageRecord(
                id=rec_id,
                creator_id=request.creator_id,
                instagram_username=clean_username,
                instagram_user_id=request.instagram_user_id,
                message=request.message,
                message_type=request.message_type,
                status="not_configured",
                provider="meta",
                error=err_msg,
                created_at=now_str,
            )
            _save_message_record(record)
            return InstagramSendResponse(
                success=False,
                status="not_configured",
                error=err_msg,
                details=details_msg,
                provider="meta",
            )

        # 2. Check and Resolve Recipient ID
        target_user_id = request.instagram_user_id
        if not target_user_id and clean_username:
            # Try looking up in existing business conversations
            target_user_id = await self._try_lookup_conversation_recipient(clean_username)

        # 3. If recipient ID is still missing, reject based on Meta API eligibility rules
        if not target_user_id:
            err_msg = (
                f"Discovered Instagram account @{clean_username or 'creator'} is not currently eligible "
                "to receive direct messages through Meta's official API."
            )
            details_msg = (
                "Meta Graph API requires an Instagram-Scoped User ID (IGSID). Public handles cannot be "
                "messaged cold without prior user interaction or an established conversation."
            )
            record = MessageRecord(
                id=rec_id,
                creator_id=request.creator_id,
                instagram_username=clean_username,
                instagram_user_id=None,
                message=request.message,
                message_type=request.message_type,
                status="not_eligible",
                provider="meta",
                error=err_msg,
                created_at=now_str,
            )
            _save_message_record(record)
            return InstagramSendResponse(
                success=False,
                status="not_eligible",
                error=err_msg,
                details=details_msg,
                provider="meta",
            )

        # 4. Dispatch Official Meta Graph API Request
        account_id = settings.INSTAGRAM_ACCOUNT_ID
        token = settings.INSTAGRAM_ACCESS_TOKEN
        endpoint = f"{self.base_url}/{account_id}/messages"

        payload = {
            "recipient": {"id": target_user_id.strip()},
            "message": {"text": request.message.strip()},
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        logger.info(f"Dispatching real Meta Instagram DM to recipient ID: {target_user_id} via {endpoint}")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                status_code = response.status_code
                sent_timestamp = datetime.now(timezone.utc).isoformat()

                if status_code in (200, 201):
                    res_json = response.json()
                    meta_msg_id = res_json.get("message_id")
                    meta_recipient_id = res_json.get("recipient_id", target_user_id)

                    logger.info(f"Meta Graph API confirmed DM delivery! Message ID: {meta_msg_id}")

                    record = MessageRecord(
                        id=rec_id,
                        creator_id=request.creator_id,
                        instagram_username=clean_username,
                        instagram_user_id=meta_recipient_id,
                        message=request.message,
                        message_type=request.message_type,
                        status="sent",
                        provider="meta",
                        meta_message_id=meta_msg_id,
                        created_at=now_str,
                        sent_at=sent_timestamp,
                    )
                    _save_message_record(record)

                    return InstagramSendResponse(
                        success=True,
                        status="sent",
                        message_id=meta_msg_id,
                        recipient_id=meta_recipient_id,
                        sent_at=sent_timestamp,
                        provider="meta",
                    )
                else:
                    # Meta returned an error status
                    try:
                        err_body = response.json().get("error", {})
                    except Exception:
                        err_body = {"message": response.text}

                    user_error, technical_details = self._map_meta_error(status_code, err_body)
                    
                    # Determine whether this is an eligibility rejection or server/auth failure
                    subcode = err_body.get("error_subcode")
                    is_eligibility_error = (
                        err_body.get("code") == 100
                        and subcode in (2018001, 2018074, 2018028)
                    )
                    final_status = "not_eligible" if is_eligibility_error else "failed"

                    record = MessageRecord(
                        id=rec_id,
                        creator_id=request.creator_id,
                        instagram_username=clean_username,
                        instagram_user_id=target_user_id,
                        message=request.message,
                        message_type=request.message_type,
                        status=final_status,
                        provider="meta",
                        error=user_error,
                        created_at=now_str,
                    )
                    _save_message_record(record)

                    return InstagramSendResponse(
                        success=False,
                        status=final_status,
                        recipient_id=target_user_id,
                        error=user_error,
                        details=technical_details,
                        provider="meta",
                    )

        except httpx.TimeoutException:
            logger.error("Meta Graph API request timed out after 15 seconds.")
            err_msg = "Meta API request timed out. Please try again."
            record = MessageRecord(
                id=rec_id,
                creator_id=request.creator_id,
                instagram_username=clean_username,
                instagram_user_id=target_user_id,
                message=request.message,
                message_type=request.message_type,
                status="failed",
                provider="meta",
                error=err_msg,
                created_at=now_str,
            )
            _save_message_record(record)
            return InstagramSendResponse(
                success=False,
                status="failed",
                recipient_id=target_user_id,
                error=err_msg,
                details="HTTP Connection Timeout",
                provider="meta",
            )
        except Exception as e:
            logger.error(f"Unexpected exception during Meta Instagram messaging: {e}", exc_info=True)
            err_msg = f"Network or connection error when contacting Meta API: {str(e)}"
            record = MessageRecord(
                id=rec_id,
                creator_id=request.creator_id,
                instagram_username=clean_username,
                instagram_user_id=target_user_id,
                message=request.message,
                message_type=request.message_type,
                status="failed",
                provider="meta",
                error=err_msg,
                created_at=now_str,
            )
            _save_message_record(record)
            return InstagramSendResponse(
                success=False,
                status="failed",
                recipient_id=target_user_id,
                error=err_msg,
                details=str(e),
                provider="meta",
            )

    def get_message_history(self) -> List[MessageRecord]:
        """Returns all recorded message attempts."""
        return _load_message_records()


# Singleton service instance
instagram_service = InstagramMessagingService()
