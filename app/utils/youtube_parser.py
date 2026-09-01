"""YouTube URL parser and validator."""

import re
from enum import Enum
from typing import Optional, NamedTuple
from urllib.parse import urlparse, parse_qs, unquote


class YouTubeURLType(str, Enum):
    VIDEO = "VIDEO"
    SHORT = "SHORT"
    CHANNEL_HANDLE = "CHANNEL_HANDLE"
    CHANNEL_ID = "CHANNEL_ID"
    CUSTOM_CHANNEL = "CUSTOM_CHANNEL"
    USER_CHANNEL = "USER_CHANNEL"
    UNKNOWN = "UNKNOWN"


class ParsedYouTubeTarget(NamedTuple):
    url_type: YouTubeURLType
    identifier: str  # video_id, channel_id, @handle, or custom_name
    canonical_url: str
    original_url: str


# Regex patterns
VIDEO_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{11}$")
CHANNEL_ID_REGEX = re.compile(r"^UC[a-zA-Z0-9_-]{22}$")
HANDLE_REGEX = re.compile(r"^@[a-zA-Z0-9_.-]{3,30}$")


def parse_youtube_url(url: str) -> Optional[ParsedYouTubeTarget]:
    """
    Parses and validates any YouTube URL variant.
    Returns ParsedYouTubeTarget with URL type and core identifier or None if invalid.
    """
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # Handle direct handle input like "@mrbeast"
    if url.startswith("@"):
        clean_handle = url.split("/")[0].split("?")[0].strip()
        if HANDLE_REGEX.match(clean_handle):
            return ParsedYouTubeTarget(
                url_type=YouTubeURLType.CHANNEL_HANDLE,
                identifier=clean_handle,
                canonical_url=f"https://www.youtube.com/{clean_handle}",
                original_url=url,
            )

    # Ensure URL has protocol for urlparse
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return None

    hostname = (parsed.hostname or "").lower()
    
    # Valid YouTube domains
    valid_domains = (
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
    )
    
    if not any(hostname == d or hostname.endswith("." + d) for d in valid_domains):
        return None

    path = unquote(parsed.path or "").strip()
    query_params = parse_qs(parsed.query)

    # 1. youtu.be/VIDEO_ID
    if hostname == "youtu.be" or hostname.endswith(".youtu.be"):
        parts = [p for p in path.split("/") if p]
        if parts:
            video_id = parts[0]
            if VIDEO_ID_REGEX.match(video_id):
                return ParsedYouTubeTarget(
                    url_type=YouTubeURLType.VIDEO,
                    identifier=video_id,
                    canonical_url=f"https://www.youtube.com/watch?v={video_id}",
                    original_url=url,
                )

    # 2. youtube.com/watch?v=VIDEO_ID
    if path == "/watch" or path.startswith("/watch/"):
        v_list = query_params.get("v")
        if v_list and v_list[0]:
            video_id = v_list[0]
            if VIDEO_ID_REGEX.match(video_id):
                return ParsedYouTubeTarget(
                    url_type=YouTubeURLType.VIDEO,
                    identifier=video_id,
                    canonical_url=f"https://www.youtube.com/watch?v={video_id}",
                    original_url=url,
                )

    # 3. youtube.com/shorts/SHORTS_ID
    if path.startswith("/shorts/"):
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            shorts_id = parts[1]
            if VIDEO_ID_REGEX.match(shorts_id):
                return ParsedYouTubeTarget(
                    url_type=YouTubeURLType.SHORT,
                    identifier=shorts_id,
                    canonical_url=f"https://www.youtube.com/shorts/{shorts_id}",
                    original_url=url,
                )

    # 4. youtube.com/embed/VIDEO_ID or youtube.com/v/VIDEO_ID
    if path.startswith("/embed/") or path.startswith("/v/"):
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            vid = parts[1]
            if VIDEO_ID_REGEX.match(vid):
                return ParsedYouTubeTarget(
                    url_type=YouTubeURLType.VIDEO,
                    identifier=vid,
                    canonical_url=f"https://www.youtube.com/watch?v={vid}",
                    original_url=url,
                )

    # 5. youtube.com/@handle
    if path.startswith("/@"):
        handle_match = re.match(r"^(/@[a-zA-Z0-9_.-]+)", path)
        if handle_match:
            handle = handle_match.group(1).lstrip("/")
            return ParsedYouTubeTarget(
                url_type=YouTubeURLType.CHANNEL_HANDLE,
                identifier=handle,
                canonical_url=f"https://www.youtube.com/{handle}",
                original_url=url,
            )

    # 6. youtube.com/channel/CHANNEL_ID (UC...)
    if path.startswith("/channel/"):
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            chan_id = parts[1]
            if chan_id.startswith("UC"):
                return ParsedYouTubeTarget(
                    url_type=YouTubeURLType.CHANNEL_ID,
                    identifier=chan_id,
                    canonical_url=f"https://www.youtube.com/channel/{chan_id}",
                    original_url=url,
                )

    # 7. youtube.com/c/CustomName
    if path.startswith("/c/"):
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            custom_name = parts[1]
            return ParsedYouTubeTarget(
                url_type=YouTubeURLType.CUSTOM_CHANNEL,
                identifier=custom_name,
                canonical_url=f"https://www.youtube.com/c/{custom_name}",
                original_url=url,
            )

    # 8. youtube.com/user/UserName
    if path.startswith("/user/"):
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            user_name = parts[1]
            return ParsedYouTubeTarget(
                url_type=YouTubeURLType.USER_CHANNEL,
                identifier=user_name,
                canonical_url=f"https://www.youtube.com/user/{user_name}",
                original_url=url,
            )

    # 9. Direct path handle or custom name (e.g., youtube.com/pewdiepie)
    parts = [p for p in path.split("/") if p]
    if len(parts) == 1 and parts[0] not in ("watch", "shorts", "feed", "results", "playlist", "gaming", "live"):
        identifier = parts[0]
        if identifier.startswith("@"):
            return ParsedYouTubeTarget(
                url_type=YouTubeURLType.CHANNEL_HANDLE,
                identifier=identifier,
                canonical_url=f"https://www.youtube.com/{identifier}",
                original_url=url,
            )
        return ParsedYouTubeTarget(
            url_type=YouTubeURLType.CUSTOM_CHANNEL,
            identifier=identifier,
            canonical_url=f"https://www.youtube.com/{identifier}",
            original_url=url,
        )

    return None
