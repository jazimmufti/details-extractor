"""LangGraph extraction state definition."""

from typing import TypedDict, List, Dict, Any, Optional
from app.models.extraction_models import (
    YouTubeInfo,
    SocialAccount,
    ContactEmail,
    WebsiteInfo,
    EvidenceItem,
    ExtractionData
)
from app.utils.youtube_parser import ParsedYouTubeTarget


class ExtractionState(TypedDict, total=False):
    # Input & routing
    input_url: str
    parsed_target: Optional[ParsedYouTubeTarget]
    url_type: str
    identifier: str
    video_id: Optional[str]
    channel_id: Optional[str]

    # Retrieved YouTube data
    youtube_info: Optional[YouTubeInfo]
    raw_texts: List[str]
    raw_urls: List[str]
    profile_links: List[Dict[str, Any]]

    # Deterministically extracted entities
    deterministic_emails: List[ContactEmail]
    deterministic_socials: Dict[str, SocialAccount]
    deterministic_websites: List[WebsiteInfo]

    # AI structured output
    ai_structured: Optional[Dict[str, Any]]

    # Merged, deduplicated & verified entities
    final_emails: List[ContactEmail]
    final_socials: Dict[str, SocialAccount]
    final_websites: List[WebsiteInfo]
    final_evidence: List[EvidenceItem]

    # Final result payload
    final_data: Optional[ExtractionData]
    
    # Progress stage tracking for UI
    current_stage: str
    
    # Status & Error tracking
    success: bool
    errors: List[str]
    warnings: List[str]
