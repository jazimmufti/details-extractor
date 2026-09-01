"""Pydantic data models for Instagram Messaging & AI Outreach.

Enforces strict separation between:
1. Public Instagram Discovery (username, URL, evidence)
2. Meta Recipient Identity (IGSID, conversation reference, resolution source)
3. Messaging Capability (sendability under official Meta API rules)
4. Message Attempt & Audit Records (real vs simulated dispatch logs)
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class DiscoveryStatus(str, Enum):
    NOT_DISCOVERED = "not_discovered"
    DISCOVERED = "discovered"


class OutreachStatus(str, Enum):
    DISCOVERED = "discovered"
    AI_MESSAGE_READY = "ai_message_ready"
    READY_FOR_OUTREACH = "ready_for_outreach"
    API_MESSAGEABLE = "api_messageable"
    API_SENT = "api_sent"
    MANUAL_INSTAGRAM_REQUIRED = "manual_instagram_required"
    FAILED = "failed"


class DeliveryMethod(str, Enum):
    META_API = "meta_api"
    MANUAL_INSTAGRAM = "manual_instagram"
    SIMULATION = "simulation"


class RecipientIdentityStatus(str, Enum):
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"


class MessagingStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    NOT_MESSAGEABLE = "not_messageable"
    REQUIRES_INTERACTION = "requires_interaction"
    MESSAGEABLE = "messageable"
    API_ERROR = "api_error"


class SendStatus(str, Enum):
    NOT_ATTEMPTED = "not_attempted"
    SIMULATED = "simulated"
    SENT = "sent"
    REJECTED = "rejected"
    FAILED = "failed"


class MessagingMode(str, Enum):
    REAL = "real"
    SIMULATION = "simulation"


class OutreachDeliveryInfo(BaseModel):
    """Delivery method capability evaluation for outreach."""
    method: str = "manual_instagram"  # "meta_api", "manual_instagram", "simulation"
    messageable: bool = False
    status: str = "manual_instagram_required"  # OutreachStatus
    label: str = "Instagram — manual send"
    details: str = "Automated Meta delivery unavailable for cold outreach. User-mediated Instagram DM handoff ready."
    can_attempt_api_send: bool = False


class DiscoveredInstagramProfile(BaseModel):
    """Public creator discovery info extracted from YouTube/social metadata."""
    status: DiscoveryStatus = DiscoveryStatus.NOT_DISCOVERED
    username: Optional[str] = None
    profile_url: Optional[str] = None
    source: Optional[str] = None
    evidence: Optional[str] = None
    confidence: Optional[str] = None
    discovered_at: Optional[str] = None


class MetaRecipient(BaseModel):
    """Meta-specific recipient identity. Never guessed or populated from username."""
    status: RecipientIdentityStatus = RecipientIdentityStatus.UNRESOLVED
    recipient_id: Optional[str] = None
    recipient_id_type: Optional[str] = None  # "igsid", "psid"
    conversation_id: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_via: Optional[str] = None  # "persisted_interaction", "webhook_event", "developer_test_input"


class MessagingCapability(BaseModel):
    """Evaluated capability to send an official message under Meta platform rules."""
    status: MessagingStatus = MessagingStatus.NOT_CONFIGURED
    reason: str
    can_attempt_send: bool = False
    checked_at: str
    provider: str = "meta"  # "meta" or "local"
    window_state: Optional[str] = None  # "active_24h", "requires_interaction", "unknown"
    permissions_state: Optional[str] = None  # "configured", "unconfigured", "missing_permission"
    requirements: List[str] = Field(default_factory=list)


class InstagramEligibilityRequest(BaseModel):
    """Request to evaluate if a discovered creator is eligible for Meta API messaging."""
    instagram_username: Optional[str] = Field(default=None, description="Discovered Instagram handle")
    instagram_user_id: Optional[str] = Field(default=None, description="Known Instagram Scoped User ID (IGSID)")
    mode: str = Field(default="real", description="Evaluation mode: 'real' or 'simulation'")


class InstagramEligibilityResponse(BaseModel):
    """Detailed messaging eligibility status with explicit separation of concerns."""
    mode: str = "real"
    can_send: bool = Field(..., description="Authoritative boolean: whether a message send can be initiated")
    discovery: DiscoveredInstagramProfile
    recipient: MetaRecipient
    capability: MessagingCapability

    # Backwards-compatible convenience getters for frontend consumption
    @property
    def configured(self) -> bool:
        return self.capability.status != MessagingStatus.NOT_CONFIGURED

    @property
    def is_eligible(self) -> bool:
        return self.can_send

    @property
    def status(self) -> str:
        return self.capability.status.value

    @property
    def reason(self) -> str:
        return self.capability.reason

    @property
    def username(self) -> Optional[str]:
        return self.discovery.username

    @property
    def instagram_user_id(self) -> Optional[str]:
        return self.recipient.recipient_id


class InstagramSendRequest(BaseModel):
    """Payload to send an Instagram Direct Message via official Meta API or simulation."""
    idempotency_key: Optional[str] = Field(default=None, description="Unique client key to prevent duplicate sends")
    creator_name: Optional[str] = Field(default=None, description="Discovered creator or channel name")
    creator_id: Optional[str] = Field(default=None, description="Internal or external creator identifier")
    instagram_user_id: Optional[str] = Field(default=None, description="Meta Instagram-Scoped User ID (IGSID)")
    instagram_username: Optional[str] = Field(default=None, description="Discovered Instagram handle/username")
    creator_username: Optional[str] = Field(default=None, description="Alias for instagram_username")
    recipient_igsid: Optional[str] = Field(default=None, description="Alias for instagram_user_id")
    instagram_url: Optional[str] = Field(default=None, description="Discovered Instagram or channel URL")
    creator_url: Optional[str] = Field(default=None, description="Alias for instagram_url")
    message: str = Field(..., min_length=1, max_length=1000, description="Message text content")
    message_type: str = Field(default="outreach", description="Message type: 'outreach' or 'test'")
    mode: str = Field(default="real", description="Dispatch mode: 'real' or 'simulation'")


class MetaErrorDiagnostics(BaseModel):
    """Structured diagnostics from raw Meta Graph API error body."""
    http_status: Optional[int] = None
    code: Optional[int] = None
    error_subcode: Optional[int] = None
    type: Optional[str] = None
    message: Optional[str] = None
    fbtrace_id: Optional[str] = None


class InstagramSendResponse(BaseModel):
    """Response returned after attempting a message send."""
    success: bool = Field(..., description="Whether Meta API confirmed delivery (or simulation succeeded)")
    status: str = Field(..., description="Send status: 'sent', 'simulated', 'rejected', 'failed', 'not_configured', 'not_messageable', 'not_eligible', 'meta_error', 'account_unresolved'")
    mode: str = Field(default="real", description="'real' or 'simulation'")
    message_id: Optional[str] = Field(default=None, description="Meta message ID (None in simulation)")
    recipient_id: Optional[str] = Field(default=None, description="Recipient identifier")
    error_code: Optional[str] = Field(default=None, description="Standardized error code (e.g. RECIPIENT_NOT_ELIGIBLE)")
    error: Optional[str] = Field(default=None, description="Human-readable error explanation")
    message: Optional[str] = Field(default=None, description="Convenience message text")
    reason: Optional[str] = Field(default=None, description="Detailed explanatory reason")
    details: Optional[str] = Field(default=None, description="Technical diagnostics")
    eligibility_result: Optional[str] = Field(default=None, description="Eligibility evaluation state")
    provider: str = Field(default="meta", description="'meta' or 'local'")
    sent_at: Optional[str] = Field(default=None, description="ISO timestamp")
    meta_diagnostics: Optional[MetaErrorDiagnostics] = None


class MessageRecord(BaseModel):
    """Auditable log entry for recorded message attempts."""
    id: str
    idempotency_key: Optional[str] = None
    creator: Optional[str] = None  # Creator display name / channel name
    creator_name: Optional[str] = None
    creator_id: Optional[str] = None
    instagram_username: Optional[str] = None
    instagram_url: Optional[str] = None
    meta_recipient_id: Optional[str] = None
    recipient_identifier: Optional[str] = None  # Meta-supported recipient identifier
    meta_recipient_id_available: bool = False
    message: str
    message_text: Optional[str] = None
    message_type: str = "outreach"
    mode: str = "real"  # "real", "simulation", "cold_outreach"
    delivery_method: str = "manual_instagram"  # "meta_api", "manual_instagram", "simulation"
    status: str  # "prepared", "opened", "manual_action_required", "sent", "simulated", "rejected", "failed", "not_configured", "not_messageable"
    final_status: Optional[str] = None
    eligibility_result: Optional[str] = None  # "eligible", "not_eligible", "interaction_required", "not_configured"
    provider: str = "instagram_direct"  # "instagram_direct", "meta", "local"
    meta_message_id: Optional[str] = None
    http_status: Optional[int] = None
    api_response_status: Optional[int] = None
    meta_error_code: Optional[int] = None
    error_code: Optional[str] = None
    meta_error_subcode: Optional[int] = None
    meta_error_type: Optional[str] = None
    meta_error_message: Optional[str] = None
    fbtrace_id: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    timestamp: Optional[str] = None
    prepared_at: Optional[str] = None
    sent_at: Optional[str] = None
    updated_at: Optional[str] = None


class OutreachGenerateRequest(BaseModel):
    """Payload to generate AI outreach grounded in discovered creator evidence."""
    creator_name: Optional[str] = Field(default=None, description="Creator or channel name")
    channel_name: Optional[str] = Field(default=None, description="Official channel name")
    platform: Optional[str] = Field(default="YouTube", description="Primary source platform")
    category: Optional[str] = Field(default=None, description="Detected category or niche")
    recent_video_title: Optional[str] = Field(default=None, description="Recent video/content title")
    description_snippet: Optional[str] = Field(default=None, description="Description snippet for context")
    sender_name: Optional[str] = Field(default="Creator Outreach Team", description="Name of sender/brand")


class OutreachGenerateResponse(BaseModel):
    """Personalized AI outreach message output."""
    success: bool
    message: str
    subject: Optional[str] = None
    grounded_evidence: List[str] = Field(default_factory=list)
    error: Optional[str] = None
