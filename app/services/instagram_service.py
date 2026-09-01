"""Official Meta Instagram Messaging Service Integration.

Follows official Meta Graph API specifications for Instagram Messaging.
Enforces strict separation between:
1. Public Instagram Profile Discovery
2. Meta Recipient Identity (IGSID)
3. Messaging Capability & Sendability
4. Real Meta Mode vs Local Simulation Mode
"""

import hmac
import hashlib
import json
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.models.messaging_models import (
    DiscoveryStatus,
    RecipientIdentityStatus,
    MessagingStatus,
    SendStatus,
    MessagingMode,
    DiscoveredInstagramProfile,
    MetaRecipient,
    MessagingCapability,
    InstagramEligibilityRequest,
    InstagramEligibilityResponse,
    InstagramSendRequest,
    InstagramSendResponse,
    MetaErrorDiagnostics,
    MessageRecord,
)

# Persistent storage paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
MESSAGES_FILE = DATA_DIR / "messages.json"
RECIPIENTS_FILE = DATA_DIR / "recipients.json"


def _ensure_data_files():
    """Ensure data directory and persistent json files exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not MESSAGES_FILE.exists():
        MESSAGES_FILE.write_text("[]", encoding="utf-8")
    if not RECIPIENTS_FILE.exists():
        RECIPIENTS_FILE.write_text("{}", encoding="utf-8")


def _save_message_record(record: MessageRecord):
    """Appends an auditable message record to local persistent store."""
    try:
        _ensure_data_files()
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
        _ensure_data_files()
        if MESSAGES_FILE.exists():
            raw = json.loads(MESSAGES_FILE.read_text(encoding="utf-8"))
            return [MessageRecord(**item) for item in raw]
    except Exception as e:
        logger.error(f"Failed to load message records: {e}")
    return []


def _load_recipients_registry() -> Dict[str, Dict[str, Any]]:
    """Loads verified webhook/interaction recipient mapping: username/id -> recipient_info."""
    try:
        _ensure_data_files()
        if RECIPIENTS_FILE.exists():
            return json.loads(RECIPIENTS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load recipients registry: {e}")
    return {}


def _save_recipient_to_registry(
    username: Optional[str],
    igsid: str,
    creator_id: Optional[str] = None,
    instagram_url: Optional[str] = None,
    source: str = "webhook",
):
    """Saves a verified creator IGSID mapping established from legitimate inbound interaction or webhook."""
    try:
        _ensure_data_files()
        registry = _load_recipients_registry()
        clean_user = username.lstrip("@").lower().strip() if username else None
        now_str = datetime.now(timezone.utc).isoformat()
        
        record = {
            "igsid": igsid.strip(),
            "username": clean_user,
            "creator_id": creator_id,
            "instagram_url": instagram_url or (f"https://instagram.com/{clean_user}" if clean_user else None),
            "messaging_eligible": True,
            "status": "eligible",
            "source": source,
            "resolved_via": source,
            "last_interaction_at": now_str,
            "updated_at": now_str,
        }
        
        if clean_user:
            existing = registry.get(clean_user, {})
            record["first_interaction_at"] = existing.get("first_interaction_at", now_str)
            registry[clean_user] = record

        if creator_id:
            registry[f"cid:{creator_id}"] = record

        RECIPIENTS_FILE.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to save recipient to registry: {e}")


def resolve_recipient_for_creator(
    creator_id: Optional[str] = None,
    instagram_username: Optional[str] = None,
    instagram_url: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Resolves the legitimate stored Meta messaging identity (IGSID) for a creator.
    
    Strict Invariant:
    Never generates, scrapes, or guesses an IGSID from a username.
    Returns the stored identity if a legitimate interaction exists, or None.
    """
    registry = _load_recipients_registry()
    if not registry:
        return None

    # 1. Search by creator_id
    if creator_id:
        cid_key = f"cid:{creator_id}"
        if cid_key in registry and registry[cid_key].get("igsid"):
            return registry[cid_key]
        if creator_id in registry and registry[creator_id].get("igsid"):
            return registry[creator_id]

    # 2. Search by normalized username
    if instagram_username:
        clean_user = instagram_username.lstrip("@").lower().strip()
        if clean_user in registry and registry[clean_user].get("igsid"):
            return registry[clean_user]
        
        # Scan registry records
        for val in registry.values():
            if isinstance(val, dict) and val.get("username") == clean_user and val.get("igsid"):
                return val

    # 3. Search by instagram_url
    if instagram_url:
        clean_url = instagram_url.lower().rstrip("/")
        for val in registry.values():
            if isinstance(val, dict):
                rec_url = (val.get("instagram_url") or "").lower().rstrip("/")
                if rec_url and rec_url == clean_url and val.get("igsid"):
                    return val

    return None


class InstagramMessagingService:
    """Official Meta Instagram Graph API Client and Messaging Controller."""

    def __init__(self):
        self.api_version = settings.META_GRAPH_API_VERSION or "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        # In-memory TTL cache for server-side idempotency
        self._idempotency_cache: Dict[str, Tuple[float, InstagramSendResponse]] = {}

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
            "supported_modes": ["real", "simulation"],
            "webhook_configured": bool(settings.META_WEBHOOK_VERIFY_TOKEN),
        }

    def verify_webhook_signature(self, payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        """
        Validates X-Hub-Signature-256 from Meta using the configured META_APP_SECRET.
        """
        if not settings.META_APP_SECRET or not signature_header:
            return False
        
        try:
            expected_sig = signature_header.replace("sha256=", "").strip()
            mac = hmac.new(
                key=settings.META_APP_SECRET.encode("utf-8"),
                msg=payload_bytes,
                digestmod=hashlib.sha256
            )
            return hmac.compare_digest(mac.hexdigest(), expected_sig)
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False

    def ingest_webhook_event(self, event_data: Dict[str, Any]) -> int:
        """
        Parses Meta Instagram Webhook payload and persists any verified sender IGSIDs.
        Returns the number of recipients updated.
        """
        updated_count = 0
        try:
            for entry in event_data.get("entry", []):
                # 1. Check messaging events
                for messaging in entry.get("messaging", []):
                    sender_id = messaging.get("sender", {}).get("id")
                    # If sender profile/username is present in payload
                    sender_username = messaging.get("sender", {}).get("username")
                    if sender_id and sender_username:
                        _save_recipient_to_registry(sender_username, sender_id, source="webhook_messaging")
                        updated_count += 1
                # 2. Check changes events (comments, mentions)
                for change in entry.get("changes", []):
                    val = change.get("value", {})
                    user_info = val.get("from", {})
                    user_id = user_info.get("id")
                    username = user_info.get("username")
                    if user_id and username:
                        _save_recipient_to_registry(username, user_id, source="webhook_change")
                        updated_count += 1
        except Exception as e:
            logger.error(f"Error ingesting webhook event: {e}")
        return updated_count

    def record_cold_outreach(
        self,
        creator_id: Optional[str],
        instagram_username: Optional[str],
        instagram_url: Optional[str],
        message: str,
        action: str = "profile_opened_copied",
    ) -> MessageRecord:
        """
        Records an auditable entry for cold Instagram outreach.
        Strictly never claims the message was 'sent', as delivery is performed manually by the user.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        rec_id = str(uuid.uuid4())
        clean_user = instagram_username.lstrip("@").strip() if instagram_username else None

        record = MessageRecord(
            id=rec_id,
            creator_id=creator_id,
            instagram_username=clean_user,
            meta_recipient_id=None,
            message=message,
            message_type="outreach",
            mode="cold_outreach",
            status="prepared",
            provider="instagram_direct",
            meta_message_id=None,
            error=None,
            created_at=now_str,
            sent_at=None,
        )
        _save_message_record(record)
        return record

    def get_recipient_status(
        self,
        creator_id: Optional[str] = None,
        instagram_username: Optional[str] = None,
        instagram_url: Optional[str] = None,
        mode: str = "real",
    ) -> Dict[str, Any]:
        """
        Retrieves recipient messaging status for the frontend send composer.
        Does NOT expose raw IGSID to frontend JavaScript.
        """
        clean_user = instagram_username.lstrip("@").strip() if instagram_username else None
        canonical_url = instagram_url or (f"https://www.instagram.com/{clean_user}/" if clean_user else None)
        
        if mode == "simulation":
            return {
                "success": True,
                "creator_id": creator_id,
                "instagram_username": f"@{clean_user}" if clean_user else None,
                "instagram_url": canonical_url,
                "messaging": {
                    "eligible": True,
                    "status": "eligible",
                    "reason": "Local simulation mode active.",
                    "source": "simulation",
                }
            }

        # Resolve stored identity
        resolved = resolve_recipient_for_creator(
            creator_id=creator_id,
            instagram_username=clean_user,
            instagram_url=instagram_url,
        )

        if resolved and resolved.get("igsid") and self.is_configured:
            return {
                "success": True,
                "creator_id": creator_id or resolved.get("creator_id"),
                "instagram_username": f"@{clean_user}" if clean_user else (f"@{resolved.get('username')}" if resolved.get("username") else None),
                "instagram_url": canonical_url or resolved.get("instagram_url"),
                "messaging": {
                    "eligible": True,
                    "status": "eligible",
                    "reason": "Meta messaging available",
                    "source": resolved.get("source") or resolved.get("resolved_via") or "meta_webhook",
                    "last_interaction_at": resolved.get("last_interaction_at"),
                }
            }

        # Cold outreach ready (No established Meta conversation)
        return {
            "success": True,
            "creator_id": creator_id,
            "instagram_username": f"@{clean_user}" if clean_user else None,
            "instagram_url": canonical_url,
            "messaging": {
                "eligible": False,
                "status": "interaction_required",
                "reason": "Outreach ready",
            }
        }

    async def check_eligibility(
        self,
        username: Optional[str] = None,
        instagram_user_id: Optional[str] = None,
        creator_id: Optional[str] = None,
        mode: str = "real",
    ) -> InstagramEligibilityResponse:
        """
        Evaluates messaging eligibility under official Meta Graph API specifications.
        
        Strict Separation:
        1. Public Discovery: Is a public username or profile link present?
        2. Recipient Identity: Is a genuine Meta IGSID available/resolved?
        3. Messaging Capability: Can the system attempt a dispatch under current mode and rules?
        """
        now_str = datetime.now(timezone.utc).isoformat()
        clean_user = username.lstrip("@").strip() if username else None
        clean_id = instagram_user_id.strip() if instagram_user_id else None
        norm_mode = "simulation" if mode == "simulation" else "real"

        # 1. Build Discovered Profile
        if clean_user or clean_id:
            discovery = DiscoveredInstagramProfile(
                status=DiscoveryStatus.DISCOVERED,
                username=clean_user,
                profile_url=f"https://instagram.com/{clean_user}" if clean_user else None,
                source="YouTube metadata / profile link",
                confidence="High" if clean_user else "Manual Input",
                discovered_at=now_str,
            )
        else:
            discovery = DiscoveredInstagramProfile(
                status=DiscoveryStatus.NOT_DISCOVERED,
                discovered_at=now_str,
            )

        # 2. Check Local Simulation Mode
        if norm_mode == "simulation":
            if discovery.status == DiscoveryStatus.DISCOVERED:
                recipient = MetaRecipient(
                    status=RecipientIdentityStatus.RESOLVED if clean_id else RecipientIdentityStatus.UNRESOLVED,
                    recipient_id=clean_id or "sim_recipient_12345",
                    recipient_id_type="simulated_igsid",
                    resolved_at=now_str,
                    resolved_via="simulation_pipeline",
                )
                capability = MessagingCapability(
                    status=MessagingStatus.MESSAGEABLE,
                    reason="Local Simulation Mode: Pipeline can be tested locally without contacting Meta API.",
                    can_attempt_send=True,
                    checked_at=now_str,
                    provider="local",
                    window_state="simulated_active",
                    permissions_state="simulated",
                    requirements=[
                        "Simulated send will not make external HTTP requests.",
                        "Audit records will be clearly labeled as SIMULATED."
                    ],
                )
            else:
                recipient = MetaRecipient(status=RecipientIdentityStatus.UNRESOLVED)
                capability = MessagingCapability(
                    status=MessagingStatus.NOT_MESSAGEABLE,
                    reason="No Instagram account was discovered for this creator.",
                    can_attempt_send=False,
                    checked_at=now_str,
                    provider="local",
                )
            return InstagramEligibilityResponse(
                mode="simulation",
                can_send=capability.can_attempt_send,
                discovery=discovery,
                recipient=recipient,
                capability=capability,
            )

        # 3. Real Meta Mode: Validate Backend Credentials Configuration
        if not self.is_configured:
            recipient = MetaRecipient(
                status=RecipientIdentityStatus.RESOLVED if clean_id else RecipientIdentityStatus.UNRESOLVED,
                recipient_id=clean_id,
            )
            capability = MessagingCapability(
                status=MessagingStatus.NOT_CONFIGURED,
                reason="Meta Instagram API credentials (INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID) are not configured in the server environment.",
                can_attempt_send=False,
                checked_at=now_str,
                provider="meta",
                permissions_state="unconfigured",
                requirements=[
                    "Configure INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in .env.",
                    "Ensure connected Meta app has 'instagram_manage_messages' permission."
                ],
            )
            return InstagramEligibilityResponse(
                mode="real",
                can_send=False,
                discovery=discovery,
                recipient=recipient,
                capability=capability,
            )

        # 4. Real Meta Mode: If no Instagram account is discovered
        if discovery.status == DiscoveryStatus.NOT_DISCOVERED:
            recipient = MetaRecipient(status=RecipientIdentityStatus.UNRESOLVED)
            capability = MessagingCapability(
                status=MessagingStatus.NOT_MESSAGEABLE,
                reason="No Instagram profile was identified for this creator.",
                can_attempt_send=False,
                checked_at=now_str,
                provider="meta",
            )
            return InstagramEligibilityResponse(
                mode="real",
                can_send=False,
                discovery=discovery,
                recipient=recipient,
                capability=capability,
            )

        # 5. Real Meta Mode: Check for Legitimate Recipient Identity
        target_igsid = clean_id
        resolved_via = "developer_test_input" if clean_id else None

        if not target_igsid:
            resolved = resolve_recipient_for_creator(
                creator_id=creator_id,
                instagram_username=clean_user,
            )
            if resolved and resolved.get("igsid"):
                target_igsid = resolved["igsid"]
                resolved_via = resolved.get("source") or resolved.get("resolved_via") or "persisted_interaction"

        # 6. If IGSID is known / resolved
        if target_igsid:
            recipient = MetaRecipient(
                status=RecipientIdentityStatus.RESOLVED,
                recipient_id=target_igsid,
                recipient_id_type="igsid",
                resolved_at=now_str,
                resolved_via=resolved_via,
            )
            capability = MessagingCapability(
                status=MessagingStatus.MESSAGEABLE,
                reason="Valid Meta Instagram-Scoped ID (IGSID) is resolved. Ready for official Graph API dispatch.",
                can_attempt_send=True,
                checked_at=now_str,
                provider="meta",
                window_state="active_24h",
                permissions_state="configured",
                requirements=[
                    "Message will be delivered through official Meta Graph API.",
                    "Subject to Meta's 24-hour customer service window and developer app permissions."
                ],
            )
            return InstagramEligibilityResponse(
                mode="real",
                can_send=True,
                discovery=discovery,
                recipient=recipient,
                capability=capability,
            )

        # 7. When only a public username is discovered (No legitimate IGSID)
        recipient = MetaRecipient(
            status=RecipientIdentityStatus.UNRESOLVED,
            recipient_id=None,
        )
        capability = MessagingCapability(
            status=MessagingStatus.REQUIRES_INTERACTION,
            reason=(
                f"Discovered Instagram handle @{clean_user} is a public username. "
                "Meta's official Graph API prohibits cold direct messages by username alone. "
                "The creator must first interact with your connected Instagram account (e.g. DM or comment) "
                "to establish an Instagram-Scoped ID (IGSID), or a legitimate IGSID must be provided."
            ),
            can_attempt_send=False,
            checked_at=now_str,
            provider="meta",
            window_state="requires_interaction",
            permissions_state="configured",
            requirements=[
                "Meta Graph API does NOT support cold DMs to arbitrary usernames.",
                "Recipient must message or comment on your connected Professional Account to generate an IGSID.",
                "Or provide a registered Meta App Tester IGSID for development testing."
            ],
        )
        return InstagramEligibilityResponse(
            mode="real",
            can_send=False,
            discovery=discovery,
            recipient=recipient,
            capability=capability,
        )

    def _map_meta_error(self, status_code: int, error_data: Dict[str, Any]) -> Tuple[str, MetaErrorDiagnostics]:
        """
        Extracts structured diagnostics and maps verified Meta error codes without hallucination.
        """
        code = error_data.get("code")
        subcode = error_data.get("error_subcode")
        error_type = error_data.get("type")
        message = error_data.get("message", "Unknown Meta API error")
        fbtrace_id = error_data.get("fbtrace_id")

        diagnostics = MetaErrorDiagnostics(
            http_status=status_code,
            code=code,
            error_subcode=subcode,
            type=error_type,
            message=message,
            fbtrace_id=fbtrace_id,
        )

        logger.error(
            f"Meta Graph API Error: HTTP {status_code}, code={code}, subcode={subcode}, "
            f"type={error_type}, trace={fbtrace_id}, msg={message}"
        )

        # Map only verified standard Meta Graph API errors
        if code == 190:
            user_msg = "Meta Access Token is invalid or expired. Please refresh your token in .env."
        elif code in (10, 200) or (isinstance(message, str) and "permission" in message.lower()):
            user_msg = "Your Meta App lacks required permissions ('instagram_manage_messages') or account is unauthorized."
        elif code == 100 and subcode in (2018001, 2018074, 2018028):
            user_msg = "Recipient is outside the allowed 24-hour messaging window or not reachable under Meta API rules."
        elif code in (4, 17, 32, 613):
            user_msg = "Meta messaging rate limit reached. Please wait before retrying."
        else:
            user_msg = f"Meta API rejected the request: {message}"

        return user_msg, diagnostics

    async def send_message(self, request: InstagramSendRequest) -> InstagramSendResponse:
        """
        Dispatches message through official Meta Graph API or local simulation.
        
        Strict Invariants:
        1. Never converts username to guessed numeric ID.
        2. Never claims success without official Meta 200/201 acknowledgment.
        3. Enforces server-side idempotency against duplicate clicks.
        4. Simulation mode never calls external network and clearly labels output.
        """
        rec_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        
        # Support canonical and alias field names
        raw_username = request.instagram_username or request.creator_username
        clean_username = raw_username.lstrip("@").strip() if raw_username else None
        
        raw_user_id = request.instagram_user_id or request.recipient_igsid
        target_user_id = raw_user_id.strip() if raw_user_id else None
        
        norm_mode = "simulation" if (getattr(request, "mode", "real") == "simulation") else "real"
        idempotency_key = getattr(request, "idempotency_key", None)

        # 1. Idempotency Check
        if idempotency_key:
            cached = self._idempotency_cache.get(idempotency_key)
            if cached:
                cached_time, cached_response = cached
                if time.time() - cached_time < 60:  # 60 second duplicate guard
                    logger.info(f"Returning cached response for idempotency_key: {idempotency_key}")
                    return cached_response

        # 2. LOCAL SIMULATION MODE
        if norm_mode == "simulation":
            logger.info("Executing message dispatch in LOCAL SIMULATION mode (Zero Meta API calls)")
            sim_record = MessageRecord(
                id=rec_id,
                idempotency_key=idempotency_key,
                creator_id=request.creator_id,
                instagram_username=clean_username,
                meta_recipient_id=target_user_id or "sim_recipient_12345",
                message=request.message,
                message_type=request.message_type or "test",
                mode="simulation",
                status="simulated",
                provider="local",
                meta_message_id=None,
                created_at=now_str,
                sent_at=now_str,
            )
            _save_message_record(sim_record)

            response = InstagramSendResponse(
                success=True,
                status="simulated",
                mode="simulation",
                message_id=None,
                recipient_id=target_user_id or "sim_recipient_12345",
                message="Local simulation succeeded",
                provider="local",
                sent_at=now_str,
                details="[LOCAL SIMULATION] Simulated successfully. No external Meta API calls were made.",
            )
            if idempotency_key:
                self._idempotency_cache[idempotency_key] = (time.time(), response)
            return response

        # 3. REAL META MODE: Validate Configuration
        if not self.is_configured:
            err_msg = "Meta Instagram API is not configured on the server."
            record = MessageRecord(
                id=rec_id,
                idempotency_key=idempotency_key,
                creator_id=request.creator_id,
                instagram_username=clean_username,
                meta_recipient_id=target_user_id,
                message=request.message,
                message_type=request.message_type or "test",
                mode="real",
                status="not_configured",
                provider="meta",
                error=err_msg,
                created_at=now_str,
            )
            _save_message_record(record)
            response = InstagramSendResponse(
                success=False,
                status="not_configured",
                mode="real",
                error_code="META_NOT_CONFIGURED",
                error=err_msg,
                message=err_msg,
                details="INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID must be configured in .env.",
                provider="meta",
            )
            return response

        # 4. Reject invalid IGSID if explicitly provided as username or non-numeric
        if target_user_id and (target_user_id.startswith("@") or not target_user_id.isdigit()):
            err_msg = "A valid numeric Instagram-scoped recipient ID is required. Usernames cannot be used as IGSIDs."
            record = MessageRecord(
                id=rec_id,
                idempotency_key=idempotency_key,
                creator_id=request.creator_id,
                instagram_username=clean_username,
                meta_recipient_id=None,
                message=request.message,
                message_type=request.message_type or "test",
                mode="real",
                status="not_messageable",
                provider="meta",
                error=err_msg,
                created_at=now_str,
            )
            _save_message_record(record)
            return InstagramSendResponse(
                success=False,
                status="not_messageable",
                mode="real",
                error_code="IGSID_REQUIRED",
                error=err_msg,
                message=err_msg,
                details="Usernames or non-numeric strings are invalid as Meta recipient IDs.",
                provider="meta",
            )

        # 5. REAL META MODE: Check / Resolve legitimate IGSID from backend persistence
        if not target_user_id:
            resolved = resolve_recipient_for_creator(
                creator_id=request.creator_id,
                instagram_username=clean_username,
                instagram_url=request.creator_url,
            )
            if resolved and resolved.get("igsid"):
                target_user_id = resolved["igsid"]

        if not target_user_id:
            err_msg = "Unable to send automatically: recipient is not eligible for Meta messaging."
            details_msg = (
                f"Discovered Instagram handle @{clean_username or 'creator'} has not established an active messaging session "
                "with your connected Instagram Business account. Meta's official Graph API strictly requires a numeric "
                "Instagram-Scoped ID (IGSID) generated via recipient interaction before direct messages can be delivered."
            )
            record = MessageRecord(
                id=rec_id,
                idempotency_key=idempotency_key,
                creator_id=request.creator_id,
                instagram_username=clean_username,
                meta_recipient_id=None,
                message=request.message,
                message_type=request.message_type or "test",
                mode="real",
                status="not_messageable",
                provider="meta",
                error=err_msg,
                created_at=now_str,
            )
            _save_message_record(record)
            response = InstagramSendResponse(
                success=False,
                status="not_messageable",
                mode="real",
                error_code="RECIPIENT_NOT_ELIGIBLE",
                error=err_msg,
                message=err_msg,
                details=details_msg,
                provider="meta",
            )
            return response

        # 6. REAL META MODE: Dispatch Official Meta Graph API Request
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

        logger.info(f"Dispatching real Meta Instagram DM to IGSID: {target_user_id} via {endpoint}")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                http_res = await client.post(endpoint, json=payload, headers=headers)
                status_code = http_res.status_code
                sent_timestamp = datetime.now(timezone.utc).isoformat()

                if status_code in (200, 201):
                    res_json = http_res.json()
                    meta_msg_id = res_json.get("message_id")
                    meta_rec_id = res_json.get("recipient_id", target_user_id)

                    logger.info(f"Meta Graph API confirmed message delivery! Message ID: {meta_msg_id}")

                    record = MessageRecord(
                        id=rec_id,
                        idempotency_key=request.idempotency_key,
                        creator_id=request.creator_id,
                        instagram_username=clean_username,
                        meta_recipient_id=meta_rec_id,
                        message=request.message,
                        message_type=request.message_type,
                        mode="real",
                        status="sent",
                        provider="meta",
                        meta_message_id=meta_msg_id,
                        http_status=status_code,
                        created_at=now_str,
                        sent_at=sent_timestamp,
                    )
                    _save_message_record(record)

                    response = InstagramSendResponse(
                        success=True,
                        status="sent",
                        mode="real",
                        message_id=meta_msg_id,
                        recipient_id=meta_rec_id,
                        sent_at=sent_timestamp,
                        provider="meta",
                    )
                    if request.idempotency_key:
                        self._idempotency_cache[request.idempotency_key] = (time.time(), response)
                    return response
                else:
                    # Meta API returned an error payload
                    try:
                        err_body = http_res.json().get("error", {})
                    except Exception:
                        err_body = {"message": http_res.text}

                    user_error, diagnostics = self._map_meta_error(status_code, err_body)

                    record = MessageRecord(
                        id=rec_id,
                        idempotency_key=request.idempotency_key,
                        creator_id=request.creator_id,
                        instagram_username=clean_username,
                        meta_recipient_id=target_user_id,
                        message=request.message,
                        message_type=request.message_type,
                        mode="real",
                        status="rejected",
                        provider="meta",
                        http_status=status_code,
                        meta_error_code=diagnostics.code,
                        meta_error_subcode=diagnostics.error_subcode,
                        meta_error_type=diagnostics.type,
                        meta_error_message=diagnostics.message,
                        fbtrace_id=diagnostics.fbtrace_id,
                        error=user_error,
                        created_at=now_str,
                    )
                    _save_message_record(record)

                    response = InstagramSendResponse(
                        success=False,
                        status="rejected",
                        mode="real",
                        recipient_id=target_user_id,
                        error=user_error,
                        details=f"HTTP {status_code} | code: {diagnostics.code} | trace: {diagnostics.fbtrace_id or 'none'}",
                        provider="meta",
                        meta_diagnostics=diagnostics,
                    )
                    if request.idempotency_key:
                        self._idempotency_cache[request.idempotency_key] = (time.time(), response)
                    return response

        except httpx.TimeoutException:
            logger.error("Meta Graph API request timed out after 15 seconds.")
            err_msg = "Meta API request timed out. Please try again."
            record = MessageRecord(
                id=rec_id,
                idempotency_key=request.idempotency_key,
                creator_id=request.creator_id,
                instagram_username=clean_username,
                meta_recipient_id=target_user_id,
                message=request.message,
                message_type=request.message_type,
                mode="real",
                status="failed",
                provider="meta",
                error=err_msg,
                created_at=now_str,
            )
            _save_message_record(record)
            return InstagramSendResponse(
                success=False,
                status="failed",
                mode="real",
                recipient_id=target_user_id,
                error=err_msg,
                details="HTTP Connection Timeout",
                provider="meta",
            )
        except Exception as e:
            logger.error(f"Unexpected error during Meta Instagram send: {e}", exc_info=True)
            err_msg = f"Network or connection error: {str(e)}"
            record = MessageRecord(
                id=rec_id,
                idempotency_key=request.idempotency_key,
                creator_id=request.creator_id,
                instagram_username=clean_username,
                meta_recipient_id=target_user_id,
                message=request.message,
                message_type=request.message_type,
                mode="real",
                status="failed",
                provider="meta",
                error=err_msg,
                created_at=now_str,
            )
            _save_message_record(record)
            return InstagramSendResponse(
                success=False,
                status="failed",
                mode="real",
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
