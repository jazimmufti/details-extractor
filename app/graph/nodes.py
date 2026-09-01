"""Atomic LangGraph processing nodes for YouTube Intelligence pipeline."""

from typing import Dict, Any, List
from app.core.logging import logger
from app.graph.state import ExtractionState
from app.utils.youtube_parser import parse_youtube_url, YouTubeURLType
from app.services.youtube_service import youtube_service
from app.services.url_normalizer import extract_raw_urls, normalize_url, get_canonical_dedup_key
from app.services.email_extractor import extract_emails
from app.services.social_extractor import extract_socials_and_websites
from app.services.evidence_service import compile_evidence
from app.services.gemini_service import gemini_service
from app.models.extraction_models import (
    YouTubeInfo,
    SocialAccount,
    ContactEmail,
    WebsiteInfo,
    ExtractionData
)


async def validate_input_node(state: ExtractionState) -> Dict[str, Any]:
    """Node 1: Validates incoming URL parameter."""
    logger.info("LangGraph Node [1/10]: Validating user input URL...")
    url = state.get("input_url", "").strip()
    
    if not url:
        return {
            "errors": ["Input URL cannot be empty"],
            "success": False,
            "current_stage": "validation_failed",
        }

    return {
        "input_url": url,
        "current_stage": "Validating URL",
        "errors": [],
        "warnings": [],
    }


async def resolve_youtube_url_node(state: ExtractionState) -> Dict[str, Any]:
    """Node 2: Parses and classifies YouTube URL format."""
    logger.info("LangGraph Node [2/10]: Parsing and resolving YouTube URL structure...")
    url = state.get("input_url", "")
    parsed = parse_youtube_url(url)

    if not parsed:
        msg = f"Invalid or unsupported YouTube URL: '{url}'. Please provide a valid YouTube video, Short, @handle, or channel URL."
        logger.warning(msg)
        return {
            "errors": state.get("errors", []) + [msg],
            "success": False,
            "current_stage": "resolution_failed",
        }

    logger.info(f"Detected URL type: {parsed.url_type.value} | Identifier: {parsed.identifier}")
    return {
        "parsed_target": parsed,
        "url_type": parsed.url_type.value,
        "identifier": parsed.identifier,
        "video_id": parsed.identifier if parsed.url_type in (YouTubeURLType.VIDEO, YouTubeURLType.SHORT) else None,
        "channel_id": parsed.identifier if parsed.url_type == YouTubeURLType.CHANNEL_ID else None,
        "current_stage": "Resolving YouTube identifier",
    }


async def fetch_youtube_data_node(state: ExtractionState) -> Dict[str, Any]:
    """Node 3: Retrieves official YouTube metadata via API and public channel profile."""
    logger.info("LangGraph Node [3/10]: Fetching metadata from YouTube Data API and channel profile...")
    parsed = state.get("parsed_target")
    if not parsed:
        return {"current_stage": "fetch_failed", "success": False}

    try:
        yt_info, raw_texts, profile_links = youtube_service.fetch_target_data(parsed)
        logger.info(f"Retrieved {len(raw_texts)} text block(s) and {len(profile_links)} profile link(s).")
        return {
            "youtube_info": yt_info,
            "raw_texts": raw_texts,
            "profile_links": profile_links,
            "channel_id": yt_info.channel_id,
            "current_stage": "Fetching YouTube data",
        }
    except Exception as e:
        logger.error(f"Error in fetch_youtube_data: {e}")
        return {
            "errors": state.get("errors", []) + [str(e)],
            "success": False,
            "current_stage": "fetch_failed",
        }


async def collect_text_and_links_node(state: ExtractionState) -> Dict[str, Any]:
    """Node 4: Consolidates all text blocks and descriptions."""
    logger.info("LangGraph Node [4/10]: Consolidating description and text blocks...")
    raw_texts = state.get("raw_texts", [])
    yt_info = state.get("youtube_info")

    combined_text_list = list(raw_texts)
    if yt_info:
        if yt_info.description and yt_info.description not in combined_text_list:
            combined_text_list.append(yt_info.description)

    return {
        "raw_texts": combined_text_list,
        "current_stage": "Extracting text and links",
    }


async def extract_emails_node(state: ExtractionState) -> Dict[str, Any]:
    """Node 5: High precision regex email extraction with contextual evidence."""
    logger.info("LangGraph Node [5/10]: Performing deterministic regex email extraction...")
    raw_texts = state.get("raw_texts", [])
    all_emails: List[ContactEmail] = []
    seen_emails = set()

    for idx, text in enumerate(raw_texts):
        source = "youtube_video_description" if idx == 0 and state.get("video_id") else "channel_description"
        found = extract_emails(text, source=source)
        for em in found:
            if em.email not in seen_emails:
                seen_emails.add(em.email)
                all_emails.append(em)

    logger.info(f"Extracted {len(all_emails)} deterministic email(s).")
    return {
        "deterministic_emails": all_emails,
        "current_stage": "Extracting emails",
    }


async def extract_urls_node(state: ExtractionState) -> Dict[str, Any]:
    """Node 6: Extracts all raw URLs from text blocks and channel profile."""
    logger.info("LangGraph Node [6/10]: Extracting raw URLs from descriptions and channel profile...")
    raw_texts = state.get("raw_texts", [])
    profile_links = state.get("profile_links", [])
    
    discovered_urls: List[str] = []
    seen = set()

    # 1. Profile links
    for pl in profile_links:
        u = pl.get("url") if isinstance(pl, dict) else str(pl)
        if u and u not in seen:
            seen.add(u)
            discovered_urls.append(u)

    # 2. Description URLs
    for text in raw_texts:
        for u in extract_raw_urls(text):
            if u and u not in seen:
                seen.add(u)
                discovered_urls.append(u)

    logger.info(f"Discovered {len(discovered_urls)} unique raw URL(s) ({len(profile_links)} from profile).")
    return {
        "raw_urls": discovered_urls,
        "current_stage": "Extracting URLs",
    }


async def classify_social_links_node(state: ExtractionState) -> Dict[str, Any]:
    """Node 7: Deterministically maps URLs to 12+ social platforms and websites with source attribution."""
    logger.info("LangGraph Node [7/10]: Classifying URLs into social platforms and websites...")
    profile_links = state.get("profile_links", [])
    raw_urls = state.get("raw_urls", [])
    raw_texts = state.get("raw_texts", [])
    combined_text = "\n".join(raw_texts)

    # 1. Extract from channel profile links (source: youtube_channel_profile)
    profile_socials, profile_websites = extract_socials_and_websites(
        raw_urls=profile_links,
        text_content="",
        source="youtube_channel_profile"
    )

    # 2. Extract from raw description URLs (source: youtube_description)
    desc_socials, desc_websites = extract_socials_and_websites(
        raw_urls=raw_urls,
        text_content=combined_text,
        source="youtube_description"
    )

    # 3. Merge socials prioritizing channel profile links
    merged_socials: Dict[str, SocialAccount] = dict(desc_socials)
    for platform, profile_acc in profile_socials.items():
        merged_socials[platform] = profile_acc

    # 4. Merge websites prioritizing channel profile links
    seen_domains = {w.domain.lower() for w in profile_websites if w.domain}
    merged_websites: List[WebsiteInfo] = list(profile_websites)
    for desc_web in desc_websites:
        if desc_web.domain and desc_web.domain.lower() not in seen_domains:
            seen_domains.add(desc_web.domain.lower())
            merged_websites.append(desc_web)

    logger.info(
        f"Classified {len(merged_socials)} social account(s) ({len(profile_socials)} profile, "
        f"{len(desc_socials)} description) and {len(merged_websites)} website(s)."
    )
    return {
        "deterministic_socials": merged_socials,
        "deterministic_websites": merged_websites,
        "current_stage": "Analyzing social accounts",
    }


async def gemini_structuring_node(state: ExtractionState) -> Dict[str, Any]:
    """Node 8: AI-powered semantic classification and entity structuring via Gemini."""
    logger.info("LangGraph Node [8/10]: Running Gemini semantic classification & structuring...")
    raw_texts = state.get("raw_texts", [])
    raw_urls = state.get("raw_urls", [])
    combined_text = "\n\n".join(raw_texts)

    ai_output = None
    warnings = list(state.get("warnings", []))

    if gemini_service.is_configured:
        try:
            ai_output = await gemini_service.extract_and_structure(combined_text, raw_urls)
        except Exception as e:
            logger.warning(f"Gemini execution skipped due to error: {e}")
            warnings.append(f"Gemini enrichment unavailable: {str(e)}")
    else:
        logger.info("Gemini API key omitted; relying on 100% deterministic extraction.")

    return {
        "ai_structured": ai_output.model_dump() if ai_output else None,
        "warnings": warnings,
        "current_stage": "Structuring data",
    }


async def deduplicate_and_validate_node(state: ExtractionState) -> Dict[str, Any]:
    """Node 9: Merges deterministic extractions with AI classifications and canonicalizes records."""
    logger.info("LangGraph Node [9/10]: Deduplicating, canonicalizing, and validating extracted data...")
    
    det_emails = state.get("deterministic_emails", [])
    det_socials = dict(state.get("deterministic_socials", {}))
    det_websites = list(state.get("deterministic_websites", []))
    ai_structured = state.get("ai_structured")

    # 1. Merge Emails (Deterministic is primary; AI emails added ONLY if supported)
    final_emails: Dict[str, ContactEmail] = {em.email.lower(): em for em in det_emails}
    
    if ai_structured and "emails" in ai_structured:
        for ai_em in ai_structured["emails"]:
            email_addr = (ai_em.get("email") or "").strip().lower()
            if email_addr and email_addr not in final_emails:
                final_emails[email_addr] = ContactEmail(
                    email=email_addr,
                    source=ai_em.get("source", "gemini_semantic_extraction"),
                    evidence=ai_em.get("evidence", "Extracted via semantic context"),
                    confidence=ai_em.get("confidence", "Medium"),
                )

    # 2. Merge Socials (Preserving high-confidence profile accounts)
    final_socials: Dict[str, SocialAccount] = dict(det_socials)
    
    if ai_structured and "social_accounts" in ai_structured:
        for ai_acc in ai_structured["social_accounts"]:
            plat = (ai_acc.get("platform") or "").lower().strip()
            raw_url = ai_acc.get("url")
            username = ai_acc.get("username")
            if username and not username.startswith("@"):
                username = f"@{username}"

            if not raw_url and username:
                if plat == "instagram":
                    raw_url = f"https://instagram.com/{username.lstrip('@')}"
                elif plat == "twitter":
                    raw_url = f"https://twitter.com/{username.lstrip('@')}"
                elif plat == "tiktok":
                    raw_url = f"https://tiktok.com/@{username.lstrip('@')}"
                elif plat == "threads":
                    raw_url = f"https://threads.net/@{username.lstrip('@')}"
                elif plat == "linkedin":
                    raw_url = f"https://linkedin.com/in/{username.lstrip('@')}"

            if plat and raw_url:
                norm_u = normalize_url(raw_url)
                if plat not in final_socials:
                    final_socials[plat] = SocialAccount(
                        platform=plat,
                        url=norm_u,
                        username=username,
                        source=ai_acc.get("source", "gemini_semantic_extraction"),
                        evidence=ai_acc.get("evidence", "Identified via semantic classification"),
                        confidence=ai_acc.get("confidence", "Medium"),
                    )
                elif not final_socials[plat].username and username:
                    final_socials[plat].username = username

    # 3. Merge Websites
    seen_web_domains = {w.domain.lower() for w in det_websites if w.domain}
    final_websites = list(det_websites)

    if ai_structured and "websites" in ai_structured:
        for ai_web in ai_structured["websites"]:
            web_url = ai_web.get("url")
            if web_url:
                norm_w = normalize_url(web_url)
                dom = ai_web.get("domain") or norm_w
                if dom.lower() not in seen_web_domains:
                    seen_web_domains.add(dom.lower())
                    final_websites.append(
                        WebsiteInfo(
                            url=norm_w,
                            domain=dom,
                            title=ai_web.get("title") or dom.capitalize(),
                            source=ai_web.get("source", "gemini_semantic_extraction"),
                            evidence=ai_web.get("evidence", "Identified via semantic classification"),
                            confidence=ai_web.get("confidence", "Medium"),
                        )
                    )

    return {
        "final_emails": list(final_emails.values()),
        "final_socials": final_socials,
        "final_websites": final_websites,
        "current_stage": "Finalizing results",
    }


async def build_final_result_node(state: ExtractionState) -> Dict[str, Any]:
    """Node 10: Compiles complete auditable evidence and builds ExtractionData payload."""
    logger.info("LangGraph Node [10/10]: Compiling final extraction payload and auditable evidence...")
    
    yt_info = state.get("youtube_info") or YouTubeInfo()
    final_emails = state.get("final_emails", [])
    final_socials = state.get("final_socials", {})
    final_websites = state.get("final_websites", [])

    # Compile auditable evidence trail
    evidence_items = compile_evidence(
        youtube_info=yt_info,
        emails=final_emails,
        social_media=final_socials,
        websites=final_websites,
    )

    data = ExtractionData(
        youtube=yt_info,
        social_media=final_socials,
        social_links=final_socials,
        emails=final_emails,
        websites=final_websites,
        evidence=evidence_items,
        metadata={
            "input_url": state.get("input_url"),
            "url_type": state.get("url_type"),
            "video_id": state.get("video_id"),
            "channel_id": state.get("channel_id"),
            "emails_count": len(final_emails),
            "socials_count": len(final_socials),
            "websites_count": len(final_websites),
        }
    )

    logger.info(
        f"Extraction pipeline completed successfully! Found: {len(final_emails)} email(s), "
        f"{len(final_socials)} social account(s), {len(final_websites)} website(s)."
    )

    return {
        "final_data": data,
        "final_evidence": evidence_items,
        "success": True,
        "current_stage": "Completed",
    }
