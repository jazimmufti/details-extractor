"""Evidence compilation and auditing service."""

from typing import List, Dict, Any
from app.models.extraction_models import EvidenceItem, ContactEmail, SocialAccount, WebsiteInfo, YouTubeInfo


def compile_evidence(
    youtube_info: YouTubeInfo,
    emails: List[ContactEmail],
    social_media: Dict[str, SocialAccount],
    websites: List[WebsiteInfo],
) -> List[EvidenceItem]:
    """
    Assembles a comprehensive, auditable list of EvidenceItem objects
    linking every extracted entity to its source and textual proof.
    """
    evidence_list: List[EvidenceItem] = []

    # 1. YouTube Channel / Video Evidence
    if youtube_info.channel_id:
        evidence_list.append(
            EvidenceItem(
                field="youtube:channel",
                source="youtube_api",
                raw_match=youtube_info.channel_id,
                context=f"Channel Name: '{youtube_info.channel_name}', Channel ID: '{youtube_info.channel_id}', URL: '{youtube_info.channel_url}'",
                confidence="High",
            )
        )
    if youtube_info.video_title:
        evidence_list.append(
            EvidenceItem(
                field="youtube:video",
                source="youtube_api",
                raw_match=youtube_info.video_title,
                context=f"Video Title: '{youtube_info.video_title}', URL: '{youtube_info.video_url}'",
                confidence="High",
            )
        )

    # 2. Emails Evidence
    for em in emails:
        evidence_list.append(
            EvidenceItem(
                field="email",
                source=em.source,
                raw_match=em.email,
                context=em.evidence,
                confidence=em.confidence,
            )
        )

    # 3. Social Media Evidence
    for platform, account in social_media.items():
        evidence_list.append(
            EvidenceItem(
                field=f"social:{platform}",
                source=account.source,
                raw_match=account.username or account.url,
                context=account.evidence or account.url,
                confidence=account.confidence,
            )
        )

    # 4. Websites Evidence
    for site in websites:
        evidence_list.append(
            EvidenceItem(
                field="website",
                source=site.source,
                raw_match=site.url,
                context=site.evidence or site.url,
                confidence=site.confidence,
            )
        )

    return evidence_list
