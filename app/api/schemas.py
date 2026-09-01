"""API Request and Response schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.extraction_models import ExtractionData
from app.models.messaging_models import (
    InstagramSendRequest,
    InstagramSendResponse,
    InstagramEligibilityRequest,
    InstagramEligibilityResponse,
    OutreachDeliveryInfo,
    OutreachStatus,
    DeliveryMethod,
    MessageRecord,
    OutreachGenerateRequest,
    OutreachGenerateResponse,
)


class MessagingRecipientStatus(BaseModel):
    eligible: bool
    status: str  # "eligible", "interaction_required", "not_configured"
    reason: Optional[str] = None
    source: Optional[str] = None
    last_interaction_at: Optional[str] = None


class RecipientStatusResponse(BaseModel):
    """Response for GET /api/instagram/recipient-status and /api/instagram/outreach/status."""
    success: bool
    creator_id: Optional[str] = None
    instagram_username: Optional[str] = None
    instagram_url: Optional[str] = None
    outreach_status: str = "ready_for_outreach"
    delivery: OutreachDeliveryInfo
    meta_recipient_id_available: bool = False
    messaging: MessagingRecipientStatus


class OutreachStatusResponse(RecipientStatusResponse):
    """Aliased schema for /api/instagram/outreach/status."""
    pass


class InstagramSendMessageRequest(BaseModel):
    """Payload to send an official Instagram message via Meta Send API."""
    creator_id: Optional[str] = Field(default=None, description="Creator ID or YouTube Channel ID")
    creator_username: Optional[str] = Field(default=None, description="Discovered creator username")
    creator_url: Optional[str] = Field(default=None, description="Creator profile URL")
    message: Optional[str] = Field(default=None, description="Message text content")
    recipient_igsid: Optional[str] = Field(default=None, description="Direct IGSID (optional internal/developer test override)")


class InstagramSendMessageResponse(BaseModel):
    """Response returned from POST /api/instagram/send-message."""
    success: bool
    status: str  # "sent", "failed", "rejected", "not_messageable"
    provider: str = "meta_instagram"
    recipient_igsid: Optional[str] = None
    message_id: Optional[str] = None
    sent_at: Optional[str] = None
    error_code: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class ColdOutreachPrepareRequest(BaseModel):
    """Payload to prepare cold Instagram outreach."""
    creator_id: Optional[str] = Field(default=None, description="Creator ID or channel ID")
    creator_username: Optional[str] = Field(default=None, description="Discovered Instagram handle")
    creator_url: Optional[str] = Field(default=None, description="Discovered Instagram URL")
    message: str = Field(..., min_length=1, max_length=1000, description="Personalized outreach message")
    action: Optional[str] = Field(default="profile_opened_copied", description="Action taken: profile_opened_copied, message_copied")


class ColdOutreachPrepareResponse(BaseModel):
    """Response returned when preparing cold Instagram outreach."""
    success: bool
    status: str = "prepared"
    action: str = "profile_opened_copied"
    instagram_username: Optional[str] = None
    instagram_url: Optional[str] = None
    message: str
    prepared_at: str
    details: str = "Cold outreach prepared. Message copied and Instagram profile ready."





class ExtractRequest(BaseModel):
    """Payload to trigger extraction."""
    url: str = Field(..., description="YouTube video, Short, or Channel URL", json_schema_extra={"example": "https://www.youtube.com/@mkbhd"})


class ExtractResponse(BaseModel):
    """Immediate synchronous extraction response."""
    success: bool
    data: Optional[ExtractionData] = None
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class JobStartResponse(BaseModel):
    """Response when initiating background research job."""
    success: bool
    job_id: str
    message: str


class JobStatusResponse(BaseModel):
    """Job status check response."""
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    stage: str  # Current execution stage description
    data: Optional[ExtractionData] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """System health and configuration status (non-secret diagnostics only)."""
    status: str
    version: str
    youtube_api_configured: bool
    gemini_api_configured: bool
    meta_api_configured: bool
    meta_access_token_present: bool
    instagram_account_id_present: bool
    meta_graph_api_version: str
    environment: str
    supported_modes: List[str] = Field(default_factory=lambda: ["real", "simulation"])
