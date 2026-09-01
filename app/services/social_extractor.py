"""Deterministic social media link identification and username extractor."""

import re
from typing import Dict, Optional, Tuple, List, Any, Union
from urllib.parse import urlparse
from app.models.extraction_models import SocialAccount, WebsiteInfo
from app.services.url_normalizer import normalize_url, extract_domain, extract_raw_urls

# Social platform regex and parser definitions
PLATFORM_RULES = [
    {
        "platform": "instagram",
        "domains": ["instagram.com", "instagr.am"],
        "regex": re.compile(r"^/([a-zA-Z0-9_.-]+)", re.I),
        "invalid_paths": {"p", "reel", "stories", "explore", "direct", "accounts", "legal", "about"}
    },
    {
        "platform": "twitter",
        "domains": ["twitter.com", "x.com"],
        "regex": re.compile(r"^/([a-zA-Z0-9_]{1,15})", re.I),
        "invalid_paths": {"home", "explore", "search", "notifications", "messages", "i", "intent", "tos", "privacy"}
    },
    {
        "platform": "tiktok",
        "domains": ["tiktok.com"],
        "regex": re.compile(r"^/(@[a-zA-Z0-9_.-]+)", re.I),
        "invalid_paths": {"discover", "upload", "foryou", "live", "legal", "tag"}
    },
    {
        "platform": "facebook",
        "domains": ["facebook.com", "fb.com", "fb.me"],
        "regex": re.compile(r"^/([a-zA-Z0-9_.-]+)", re.I),
        "invalid_paths": {"pages", "groups", "watch", "events", "gaming", "marketplace", "share", "sharer", "photo", "story"}
    },
    {
        "platform": "linkedin",
        "domains": ["linkedin.com"],
        "regex": re.compile(r"^/(?:in|company)/([a-zA-Z0-9_-]+)", re.I),
        "invalid_paths": {"feed", "jobs", "mynetwork", "messaging", "notifications", "pulse"}
    },
    {
        "platform": "threads",
        "domains": ["threads.net", "threads.com"],
        "regex": re.compile(r"^/(@[a-zA-Z0-9_.-]+)", re.I),
        "invalid_paths": {"terms", "privacy"}
    },
    {
        "platform": "discord",
        "domains": ["discord.gg", "discord.com"],
        "regex": re.compile(r"^/(?:invite/)?([a-zA-Z0-9_-]+)", re.I),
        "invalid_paths": {"channels", "app", "login", "register", "download"}
    },
    {
        "platform": "telegram",
        "domains": ["t.me", "telegram.me"],
        "regex": re.compile(r"^/([a-zA-Z0-9_]{5,32})", re.I),
        "invalid_paths": {"s", "joinchat", "share"}
    },
    {
        "platform": "twitch",
        "domains": ["twitch.tv"],
        "regex": re.compile(r"^/([a-zA-Z0-9_]{4,25})", re.I),
        "invalid_paths": {"directory", "downloads", "prime", "videos", "p"}
    },
    {
        "platform": "reddit",
        "domains": ["reddit.com"],
        "regex": re.compile(r"^/(?:user|u)/([a-zA-Z0-9_-]+)", re.I),
        "invalid_paths": {"r", "all", "popular", "submit"}
    },
    {
        "platform": "snapchat",
        "domains": ["snapchat.com"],
        "regex": re.compile(r"^/add/([a-zA-Z0-9_.-]+)", re.I),
        "invalid_paths": {"discover", "lens", "spotlight"}
    },
    {
        "platform": "pinterest",
        "domains": ["pinterest.com", "pin.it"],
        "regex": re.compile(r"^/([a-zA-Z0-9_-]+)", re.I),
        "invalid_paths": {"pin", "today", "ideas", "business"}
    },
    {
        "platform": "patreon",
        "domains": ["patreon.com"],
        "regex": re.compile(r"^/([a-zA-Z0-9_-]+)", re.I),
        "invalid_paths": {"home", "login", "signup", "explore"}
    },
    {
        "platform": "github",
        "domains": ["github.com"],
        "regex": re.compile(r"^/([a-zA-Z0-9_-]+)", re.I),
        "invalid_paths": {"features", "pricing", "explore", "topics", "trending", "collections", "events"}
    },
    {
        "platform": "spotify",
        "domains": ["spotify.com", "open.spotify.com"],
        "regex": re.compile(r"^/(?:artist|user|show)/([a-zA-Z0-9]+)", re.I),
        "invalid_paths": {"download", "premium", "search", "genre"}
    },
    {
        "platform": "linktree",
        "domains": ["linktr.ee", "beacons.ai", "bio.link", "campsite.bio", "hoo.be"],
        "regex": re.compile(r"^/([a-zA-Z0-9_.-]+)", re.I),
        "invalid_paths": {"s", "admin", "login", "register"}
    }
]

# Excluded generic domains (video links, google search, etc.)
EXCLUDED_DOMAINS = {
    "youtube.com", "youtu.be", "google.com", "goo.gl", "bit.ly", "tinyurl.com",
    "amazon.com", "amzn.to", "apple.com", "play.google.com"
}


def classify_url(url: str, text_context: str = "", source: str = "youtube_description") -> Optional[Tuple[str, SocialAccount]]:
    """
    Determines if a URL is a social profile and extracts the username.
    Returns (platform_name, SocialAccount) or None if it's not a known social profile.
    """
    clean_url = normalize_url(url)
    if not clean_url:
        return None

    try:
        parsed = urlparse(clean_url)
        domain = parsed.netloc.lower()
        path = parsed.path or ""
    except Exception:
        return None

    for rule in PLATFORM_RULES:
        if any(domain == d or domain.endswith("." + d) for d in rule["domains"]):
            platform = rule["platform"]
            match = rule["regex"].match(path)
            username = None
            
            if match:
                raw_handle = match.group(1).lstrip("@")
                if raw_handle.lower() not in rule["invalid_paths"]:
                    username = f"@{raw_handle}" if not raw_handle.startswith("@") else raw_handle

            # Evidence snippet
            evidence = text_context if text_context else f"Found link: {clean_url}"
            confidence = "High" if (username or source == "youtube_channel_profile") else "Medium"

            account = SocialAccount(
                platform=platform,
                url=clean_url,
                username=username,
                source=source,
                evidence=evidence,
                confidence=confidence,
            )
            return platform, account

    return None


def extract_socials_and_websites(
    raw_urls: List[Any],
    text_content: str = "",
    source: str = "youtube_description"
) -> Tuple[Dict[str, SocialAccount], List[WebsiteInfo]]:
    """
    Classifies a list of URLs (strings or dicts with metadata) into structured SocialAccounts and WebsiteInfos.
    """
    socials: Dict[str, SocialAccount] = {}
    websites: List[WebsiteInfo] = []
    seen_websites: set[str] = set()

    for item in raw_urls:
        if not item:
            continue
        
        if isinstance(item, dict):
            url = item.get("url", "")
            item_source = item.get("source", source)
            item_title = item.get("title", "")
            item_evidence = item.get("evidence") or item.get("context") or ""
        else:
            url = str(item)
            item_source = source
            item_title = ""
            item_evidence = ""

        if not url:
            continue

        # Build context from text if available
        context = item_evidence
        if not context and item_title:
            context = f"Channel profile link ({item_title}): {url}"
        elif not context and text_content and url in text_content:
            idx = text_content.find(url)
            start = max(0, idx - 40)
            end = min(len(text_content), idx + len(url) + 40)
            context = text_content[start:end].replace("\n", " ").strip()
            if start > 0:
                context = "..." + context
            if end < len(text_content):
                context = context + "..."

        classified = classify_url(url, text_context=context, source=item_source)
        
        if classified:
            platform, account = classified
            # Deduplicate by platform (prefer profile links over description, or accounts with username)
            if platform not in socials:
                socials[platform] = account
            else:
                existing = socials[platform]
                # If existing is from description and new is from channel profile, replace
                if existing.source != "youtube_channel_profile" and account.source == "youtube_channel_profile":
                    socials[platform] = account
                elif not existing.username and account.username:
                    socials[platform] = account
        else:
            # Check if valid generic website
            norm_url = normalize_url(url)
            dom = extract_domain(norm_url)
            
            if dom and dom not in EXCLUDED_DOMAINS and dom not in seen_websites:
                seen_websites.add(dom)
                site_title = item_title or dom.split(".")[0].capitalize()
                site_evidence = context or (f"Channel profile website: {norm_url}" if item_source == "youtube_channel_profile" else f"Found website link: {norm_url}")
                confidence = "High" if (item_source == "youtube_channel_profile" or not any(x in dom for x in ("t.co", "short"))) else "Medium"
                
                websites.append(
                    WebsiteInfo(
                        url=norm_url,
                        domain=dom,
                        title=site_title,
                        source=item_source,
                        evidence=site_evidence,
                        confidence=confidence,
                    )
                )

    return socials, websites
