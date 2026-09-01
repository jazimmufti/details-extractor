"""Pydantic models for extracted data and results."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class YouTubeInfo(BaseModel):
    """Structured official YouTube details."""
    channel_name: str = Field(default="", description="Name of the YouTube channel")
    channel_url: str = Field(default="", description="Canonical URL to the YouTube channel")
    channel_id: str = Field(default="", description="Unique YouTube channel ID (e.g., UC...)")
    video_title: Optional[str] = Field(default=None, description="Title of the video if applicable")
    video_url: Optional[str] = Field(default=None, description="URL of the video if applicable")
    description: str = Field(default="", description="Retrieved description text (video or channel)")
    subscriber_count: Optional[int] = Field(default=None, description="Number of channel subscribers")
    view_count: Optional[int] = Field(default=None, description="View count if applicable")
    avatar_url: Optional[str] = Field(default=None, description="Channel profile thumbnail")
    banner_url: Optional[str] = Field(default=None, description="Channel banner image")


class SocialAccount(BaseModel):
    """Individual extracted social media account."""
    platform: str = Field(..., description="Normalized social platform name (e.g. instagram, twitter, tiktok)")
    url: str = Field(..., description="Canonical normalized URL to the profile")
    username: Optional[str] = Field(default=None, description="Extracted handle/username")
    source: str = Field(default="youtube_description", description="Origin source of the link")
    evidence: str = Field(default="", description="Verbatim text context snippet containing the link")
    confidence: str = Field(default="High", description="Evidence-based confidence: High, Medium, Low")


class ContactEmail(BaseModel):
    """Extracted contact email address."""
    email: str = Field(..., description="Cleaned email address")
    source: str = Field(default="youtube_description", description="Origin source of the email")
    evidence: str = Field(default="", description="Verbatim sentence or text context containing the email")
    confidence: str = Field(default="High", description="Evidence-based confidence: High, Medium, Low")


class WebsiteInfo(BaseModel):
    """Generic or personal website link."""
    url: str = Field(..., description="Normalized website URL")
    domain: str = Field(default="", description="Extracted root domain")
    title: Optional[str] = Field(default=None, description="Optional descriptive label or domain title")
    source: str = Field(default="youtube_description", description="Origin source")
    evidence: str = Field(default="", description="Verbatim context snippet")
    confidence: str = Field(default="High", description="High, Medium, Low")


class EvidenceItem(BaseModel):
    """Auditable evidence record for any extracted piece of information."""
    field: str = Field(..., description="Target field/type (email, social:platform, website, etc.)")
    source: str = Field(..., description="Source location (video_description, channel_about, etc.)")
    raw_match: str = Field(..., description="Exact string or token matched")
    context: str = Field(..., description="Surrounding sentence or text context")
    confidence: str = Field(default="High", description="Confidence rating based on evidence")


class GeminiStructuredOutput(BaseModel):
    """Schema for structured output from Gemini classification."""
    social_accounts: List[SocialAccount] = Field(default_factory=list, description="Classified social accounts from ambiguous text")
    emails: List[ContactEmail] = Field(default_factory=list, description="Verified emails with evidence")
    websites: List[WebsiteInfo] = Field(default_factory=list, description="Verified websites")


class ExtractionData(BaseModel):
    """Complete extraction payload."""
    youtube: YouTubeInfo
    social_media: Dict[str, SocialAccount] = Field(default_factory=dict)
    emails: List[ContactEmail] = Field(default_factory=list)
    websites: List[WebsiteInfo] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[ExtractionData] = None
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
