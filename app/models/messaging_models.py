"""Pydantic data models for Instagram Messaging & AI Outreach."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class InstagramSendRequest(BaseModel):
    """Payload to send an Instagram Direct Message via official Meta API."""
    creator_id: Optional[str] = Field(default=None, description="Internal or external creator identifier")
    instagram_user_id: Optional[str] = Field(default=None, description="Meta Instagram-Scoped User ID (IGSID) or Page-Scoped ID (PSID)")
    instagram_username: Optional[str] = Field(default=None, description="Discovered Instagram handle/username")
    message: str = Field(..., description="Message text content to send to the recipient")
    message_type: str = Field(default="test", description="Message type: 'test' or 'outreach'")


class InstagramSendResponse(BaseModel):
    """Response returned after attempting an official Meta Instagram DM send."""
    success: bool = Field(..., description="Whether Meta API confirmed message delivery")
    status: str = Field(..., description="Send status: 'sent', 'failed', 'not_eligible', 'not_configured'")
    message_id: Optional[str] = Field(default=None, description="Meta message identifier if send succeeded")
    recipient_id: Optional[str] = Field(default=None, description="Meta recipient ID if available")
    error: Optional[str] = Field(default=None, description="Human-readable error description")
    details: Optional[str] = Field(default=None, description="Detailed technical or policy context")
    provider: str = Field(default="meta", description="Messaging infrastructure provider ('meta')")
    sent_at: Optional[str] = Field(default=None, description="ISO timestamp when Meta acknowledged the send")


class InstagramEligibilityRequest(BaseModel):
    """Request to evaluate if a discovered creator is eligible for Meta API messaging."""
    instagram_username: Optional[str] = Field(default=None, description="Discovered Instagram handle")
    instagram_user_id: Optional[str] = Field(default=None, description="Known Instagram Scoped User ID (IGSID)")


class InstagramEligibilityResponse(BaseModel):
    """Detailed messaging eligibility status under Meta's current API rules."""
    configured: bool = Field(..., description="Whether Meta API credentials are active in backend")
    discovered: bool = Field(..., description="Whether an Instagram account was discovered")
    username: Optional[str] = Field(default=None, description="Discovered Instagram username")
    instagram_user_id: Optional[str] = Field(default=None, description="Resolved or provided Instagram Scoped ID")
    is_eligible: bool = Field(..., description="Whether a message can be delivered through Meta API now")
    status: str = Field(..., description="Eligibility status: 'eligible', 'not_eligible', 'not_configured', 'not_discovered'")
    reason: str = Field(..., description="Human-readable explanation of messaging status")
    requirements: List[str] = Field(default_factory=list, description="Meta API policy/technical requirements")


class MessageRecord(BaseModel):
    """Auditable log entry for recorded message attempts."""
    id: str
    creator_id: Optional[str] = None
    instagram_username: Optional[str] = None
    instagram_user_id: Optional[str] = None
    message: str
    message_type: str = "test"
    status: str
    provider: str = "meta"
    meta_message_id: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    sent_at: Optional[str] = None


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
