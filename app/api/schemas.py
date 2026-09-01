"""API Request and Response schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.extraction_models import ExtractionData
from app.models.messaging_models import (
    InstagramSendRequest,
    InstagramSendResponse,
    InstagramEligibilityRequest,
    InstagramEligibilityResponse,
    MessageRecord,
    OutreachGenerateRequest,
    OutreachGenerateResponse,
)


class ExtractRequest(BaseModel):
    """Payload to trigger extraction."""
    url: str = Field(..., description="YouTube video, Short, or Channel URL", example="https://www.youtube.com/@mkbhd")


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
    """System health and configuration status."""
    status: str
    version: str
    youtube_api_configured: bool
    gemini_api_configured: bool
    meta_api_configured: bool
    environment: str

