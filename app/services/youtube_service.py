"""Official YouTube Data API v3 integration service with public channel fallback."""

import re
import json
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import urlparse, parse_qs, unquote
import httpx
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.core.logging import logger
from app.models.extraction_models import YouTubeInfo
from app.utils.youtube_parser import ParsedYouTubeTarget, YouTubeURLType


DEFAULT_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def extract_url_from_youtube_redirect(raw_url: str) -> str:
    """Extracts actual destination URL from a YouTube redirect URL."""
    if not raw_url:
        return ""
    if "q=" in raw_url:
        try:
            parsed = urlparse(raw_url)
            qs = parse_qs(parsed.query)
            if "q" in qs and qs["q"]:
                return qs["q"][0]
        except Exception:
            pass
    return raw_url


def parse_channel_profile_data_from_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts profile links, metadata, and continuation tokens from parsed ytInitialData.
    """
    discovered_links: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    def add_link(raw_u: str, title: str = ""):
        clean_u = extract_url_from_youtube_redirect(raw_u).strip()
        if clean_u and clean_u not in seen_urls:
            seen_urls.add(clean_u)
            discovered_links.append({
                "url": clean_u,
                "title": title or "",
                "source": "youtube_channel_profile",
                "evidence": f"Channel profile link ({title}): {clean_u}" if title else f"Channel profile link: {clean_u}",
            })

    # 1. Microformat sameAs schema links
    microformat = data.get("microformat", {}).get("microformatDataRenderer", {})
    same_as = (
        microformat.get("channelProfileMicroformatDetails", {})
        .get("profilePage", {})
        .get("mainEntity", {})
        .get("sameAs", [])
    )
    for u in same_as:
        add_link(u, "Profile Link")

    # 2. Header pageHeaderViewModel attribution links
    page_header = (
        data.get("header", {})
        .get("pageHeaderRenderer", {})
        .get("content", {})
        .get("pageHeaderViewModel", {})
    )
    attribution = page_header.get("attribution", {}).get("attributionViewModel", {})
    text_content = attribution.get("text", {}).get("content", "").strip()
    text_runs = attribution.get("text", {}).get("commandRuns", [])
    for run in text_runs:
        endpoint = run.get("onTap", {}).get("innertubeCommand", {}).get("urlEndpoint", {})
        u = endpoint.get("url", "")
        if u:
            add_link(u, text_content or "Header Link")

    # 3. Continuation token for full about links dialog
    continuation_token = None
    suffix_runs = attribution.get("suffix", {}).get("commandRuns", [])
    for run in suffix_runs:
        panel = run.get("onTap", {}).get("innertubeCommand", {}).get("showEngagementPanelEndpoint", {}).get("engagementPanel", {})
        contents = panel.get("engagementPanelSectionListRenderer", {}).get("content", {}).get("sectionListRenderer", {}).get("contents", [])
        for c in contents:
            item_contents = c.get("itemSectionRenderer", {}).get("contents", [])
            for ic in item_contents:
                token = ic.get("continuationItemRenderer", {}).get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")
                if token:
                    continuation_token = token
                    break

    # 4. Check for embedded aboutChannelViewModel or channelExternalLinkViewModel anywhere in ytInitialData
    def scan_for_view_models(obj):
        if isinstance(obj, dict):
            if "channelExternalLinkViewModel" in obj:
                vm = obj["channelExternalLinkViewModel"]
                title = vm.get("title", {}).get("content", "")
                link_data = vm.get("link", {})
                runs = link_data.get("commandRuns", [])
                u = ""
                if runs:
                    u = runs[0].get("onTap", {}).get("innertubeCommand", {}).get("urlEndpoint", {}).get("url", "")
                if not u:
                    u = link_data.get("content", "")
                if u:
                    add_link(u, title)
            if "channelHeaderLinksRenderer" in obj:
                links_renderer = obj["channelHeaderLinksRenderer"]
                all_header_links = links_renderer.get("primaryLinks", []) + links_renderer.get("secondaryLinks", [])
                for hl in all_header_links:
                    title = hl.get("title", {}).get("simpleText", "")
                    endpoint = hl.get("navigationEndpoint", {}).get("urlEndpoint", {})
                    u = endpoint.get("url", "")
                    if u:
                        add_link(u, title)
            for v in obj.values():
                scan_for_view_models(v)
        elif isinstance(obj, list):
            for it in obj:
                scan_for_view_models(it)

    scan_for_view_models(data)

    # 5. Extract metadata from microformat & metadata renderers
    channel_name = microformat.get("title", "")
    channel_url = microformat.get("urlCanonical", "")
    description = microformat.get("description", "")
    avatar_url = None
    thumbnails = microformat.get("thumbnail", {}).get("thumbnails", [])
    if thumbnails:
        avatar_url = thumbnails[-1].get("url")

    return {
        "links": discovered_links,
        "continuation_token": continuation_token,
        "channel_name": channel_name,
        "channel_url": channel_url,
        "description": description,
        "avatar_url": avatar_url,
    }


def parse_continuation_about_response(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extracts links from Innertube continuation browse response."""
    discovered_links: List[Dict[str, Any]] = []
    seen = set()

    endpoints = data.get("onResponseReceivedEndpoints", [])
    for ep in endpoints:
        items = ep.get("appendContinuationItemsAction", {}).get("continuationItems", [])
        for it in items:
            about_vm = it.get("aboutChannelRenderer", {}).get("metadata", {}).get("aboutChannelViewModel", {})
            for l in about_vm.get("links", []):
                vm = l.get("channelExternalLinkViewModel", {})
                title = vm.get("title", {}).get("content", "")
                runs = vm.get("link", {}).get("commandRuns", [])
                raw_u = ""
                if runs:
                    raw_u = runs[0].get("onTap", {}).get("innertubeCommand", {}).get("urlEndpoint", {}).get("url", "")
                if not raw_u:
                    raw_u = vm.get("link", {}).get("content", "")

                clean_u = extract_url_from_youtube_redirect(raw_u).strip()
                if clean_u and clean_u not in seen:
                    seen.add(clean_u)
                    discovered_links.append({
                        "url": clean_u,
                        "title": title or "",
                        "source": "youtube_channel_profile",
                        "evidence": f"Channel profile link ({title}): {clean_u}" if title else f"Channel profile link: {clean_u}",
                    })
    return discovered_links


class YouTubeService:
    """Service to interact with YouTube Data API v3 and public channel profile pages."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self._client = None
        if self.api_key:
            try:
                self._client = build("youtube", "v3", developerKey=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize YouTube API client: {e}")

    @property
    def is_configured(self) -> bool:
        return bool(self._client is not None)

    def fetch_channel_profile_data(self, channel_url: str) -> Dict[str, Any]:
        """
        Fetches the public YouTube channel page and extracts profile links and metadata.
        Falls back gracefully if the network request fails or format differs.
        """
        result = {
            "links": [],
            "channel_name": "",
            "channel_url": channel_url,
            "description": "",
            "avatar_url": None,
        }

        if not channel_url:
            return result

        try:
            logger.info(f"Fetching public channel profile page: {channel_url}")
            with httpx.Client(headers=DEFAULT_HTTP_HEADERS, timeout=8.0, follow_redirects=True) as client:
                resp = client.get(channel_url)
                if resp.status_code != 200:
                    logger.warning(f"Public channel fetch returned status code {resp.status_code} for {channel_url}")
                    return result

                html = resp.text
                match = re.search(r"var ytInitialData = ({.*?});</script>", html)
                if not match:
                    logger.warning(f"ytInitialData payload not found in channel HTML for {channel_url}")
                    return result

                data = json.loads(match.group(1))
                parsed_data = parse_channel_profile_data_from_json(data)
                result.update(parsed_data)

                # Fetch continuation links if token present
                continuation_token = parsed_data.get("continuation_token")
                if continuation_token:
                    try:
                        browse_payload = {
                            "context": {
                                "client": {
                                    "clientName": "WEB",
                                    "clientVersion": "2.20240101.00.00",
                                    "hl": "en",
                                    "gl": "US",
                                }
                            },
                            "continuation": continuation_token,
                        }
                        browse_resp = client.post("https://www.youtube.com/youtubei/v1/browse", json=browse_payload)
                        if browse_resp.status_code == 200:
                            extra_links = parse_continuation_about_response(browse_resp.json())
                            # Merge links without duplicating
                            existing_urls = {l["url"] for l in result["links"]}
                            for el in extra_links:
                                if el["url"] not in existing_urls:
                                    existing_urls.add(el["url"])
                                    result["links"].append(el)
                    except Exception as ce:
                        logger.warning(f"Error fetching about links continuation for {channel_url}: {ce}")

                logger.info(f"Discovered {len(result['links'])} public channel profile link(s) for {channel_url}")
                return result

        except Exception as e:
            logger.warning(f"Failed to fetch public channel profile data for {channel_url}: {e}")
            return result

    def fetch_target_data(self, target: ParsedYouTubeTarget) -> Tuple[YouTubeInfo, List[str], List[Dict[str, Any]]]:
        """
        Fetches official metadata for a parsed YouTube target along with public profile links.
        Returns:
            (YouTubeInfo, list_of_raw_text_blocks, list_of_profile_links)
        """
        if not self.is_configured:
            logger.warning("YouTube API Key is not configured. Using public page fallback.")
            return self._build_unconfigured_fallback(target)

        try:
            if target.url_type in (YouTubeURLType.VIDEO, YouTubeURLType.SHORT):
                return self._fetch_video_and_channel(target.identifier, target.canonical_url)
            elif target.url_type == YouTubeURLType.CHANNEL_ID:
                return self._fetch_channel_by_id(target.identifier, target.canonical_url)
            elif target.url_type == YouTubeURLType.CHANNEL_HANDLE:
                return self._fetch_channel_by_handle(target.identifier, target.canonical_url)
            elif target.url_type in (YouTubeURLType.CUSTOM_CHANNEL, YouTubeURLType.USER_CHANNEL):
                return self._fetch_channel_by_custom_query(target.identifier, target.canonical_url)
            else:
                return self._build_unconfigured_fallback(target)
        except HttpError as e:
            logger.error(f"YouTube API HttpError: {e}")
            error_reason = e.error_details[0].get("reason") if e.error_details else str(e)
            raise ValueError(f"YouTube API error: {error_reason}")
        except Exception as e:
            logger.error(f"Unexpected error fetching YouTube data: {e}")
            raise

    def _fetch_video_and_channel(self, video_id: str, video_url: str) -> Tuple[YouTubeInfo, List[str], List[Dict[str, Any]]]:
        """Fetches video details followed by the parent channel's details and profile links."""
        video_response = self._client.videos().list(
            part="snippet,statistics",
            id=video_id
        ).execute()

        items = video_response.get("items", [])
        if not items:
            raise ValueError(f"Video not found or is private/deleted (ID: {video_id})")

        video_item = items[0]
        snippet = video_item.get("snippet", {})
        statistics = video_item.get("statistics", {})

        video_title = snippet.get("title", "")
        video_description = snippet.get("description", "")
        channel_id = snippet.get("channelId", "")
        channel_name = snippet.get("channelTitle", "")
        view_count = int(statistics.get("viewCount", 0)) if "viewCount" in statistics else None

        # Now fetch channel details
        channel_canonical_url = f"https://www.youtube.com/channel/{channel_id}"
        channel_info, channel_texts, channel_links = self._fetch_channel_by_id(channel_id, channel_canonical_url)

        # Combine video & channel metadata
        combined_info = YouTubeInfo(
            channel_name=channel_info.channel_name or channel_name,
            channel_url=channel_info.channel_url or channel_canonical_url,
            channel_id=channel_id,
            video_title=video_title,
            video_url=video_url,
            description=video_description,  # Primary text is video description
            subscriber_count=channel_info.subscriber_count,
            view_count=view_count,
            avatar_url=channel_info.avatar_url,
            banner_url=channel_info.banner_url,
        )

        raw_texts = [video_description] + channel_texts
        return combined_info, raw_texts, channel_links

    def _fetch_channel_by_id(self, channel_id: str, channel_url: str) -> Tuple[YouTubeInfo, List[str], List[Dict[str, Any]]]:
        """Fetches channel details by Channel ID (UC...)."""
        response = self._client.channels().list(
            part="snippet,statistics,brandingSettings",
            id=channel_id
        ).execute()

        items = response.get("items", [])
        if not items:
            raise ValueError(f"Channel not found (ID: {channel_id})")

        return self._parse_channel_item(items[0], channel_url)

    def _fetch_channel_by_handle(self, handle: str, channel_url: str) -> Tuple[YouTubeInfo, List[str], List[Dict[str, Any]]]:
        """Fetches channel details using forHandle API parameter."""
        clean_handle = handle.lstrip("@")
        try:
            response = self._client.channels().list(
                part="snippet,statistics,brandingSettings",
                forHandle=clean_handle
            ).execute()
            items = response.get("items", [])
            if items:
                return self._parse_channel_item(items[0], channel_url)
        except HttpError:
            pass

        # Fallback to search query
        return self._fetch_channel_by_custom_query(handle, channel_url)

    def _fetch_channel_by_custom_query(self, query: str, canonical_url: str) -> Tuple[YouTubeInfo, List[str], List[Dict[str, Any]]]:
        """Fallback: uses search API to locate channel."""
        clean_query = query.lstrip("@")
        search_res = self._client.search().list(
            part="snippet",
            q=clean_query,
            type="channel",
            maxResults=1
        ).execute()

        items = search_res.get("items", [])
        if not items:
            raise ValueError(f"Channel not found for identifier '{query}'")

        channel_id = items[0]["snippet"]["channelId"]
        return self._fetch_channel_by_id(channel_id, canonical_url)

    def _parse_channel_item(self, item: Dict[str, Any], canonical_url: str) -> Tuple[YouTubeInfo, List[str], List[Dict[str, Any]]]:
        """Parses raw YouTube channel API response item and enriches with profile links."""
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        branding = item.get("brandingSettings", {})

        channel_id = item.get("id", "")
        channel_name = snippet.get("title", "")
        custom_url = snippet.get("customUrl", "")
        description = snippet.get("description", "")
        
        channel_canonical_url = f"https://www.youtube.com/{custom_url}" if custom_url else canonical_url

        sub_count = int(statistics.get("subscriberCount", 0)) if "subscriberCount" in statistics else None
        view_count = int(statistics.get("viewCount", 0)) if "viewCount" in statistics else None

        avatar_url = (
            snippet.get("thumbnails", {}).get("high", {}).get("url") or
            snippet.get("thumbnails", {}).get("default", {}).get("url")
        )
        banner_url = branding.get("image", {}).get("bannerExternalUrl")

        info = YouTubeInfo(
            channel_name=channel_name,
            channel_url=channel_canonical_url,
            channel_id=channel_id,
            description=description,
            subscriber_count=sub_count,
            view_count=view_count,
            avatar_url=avatar_url,
            banner_url=banner_url,
        )

        raw_texts = [description] if description else []
        
        # Fetch public channel profile links
        profile_data = self.fetch_channel_profile_data(channel_canonical_url)
        profile_links = profile_data.get("links", [])
        public_desc = profile_data.get("description", "")
        if public_desc and public_desc not in raw_texts:
            raw_texts.append(public_desc)

        return info, raw_texts, profile_links

    def _build_unconfigured_fallback(self, target: ParsedYouTubeTarget) -> Tuple[YouTubeInfo, List[str], List[Dict[str, Any]]]:
        """Builds a fallback from public channel page when YouTube API is unconfigured."""
        is_video = target.url_type in (YouTubeURLType.VIDEO, YouTubeURLType.SHORT)
        
        # For non-video targets, fetch public channel data directly
        profile_data = {}
        if not is_video:
            profile_data = self.fetch_channel_profile_data(target.canonical_url)

        profile_links = profile_data.get("links", [])
        channel_name = profile_data.get("channel_name") or f"Channel for {target.identifier}"
        channel_desc = profile_data.get("description") or ""

        info = YouTubeInfo(
            channel_name=channel_name,
            channel_url=target.canonical_url if not is_video else "",
            channel_id=profile_data.get("channel_id") or (target.identifier if not is_video else ""),
            video_title=f"Video ({target.identifier})" if is_video else None,
            video_url=target.canonical_url if is_video else None,
            description=channel_desc,
            avatar_url=profile_data.get("avatar_url"),
        )
        raw_texts = [channel_desc] if channel_desc else []
        return info, raw_texts, profile_links


youtube_service = YouTubeService()

