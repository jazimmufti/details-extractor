"""URL normalization and canonicalization service."""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, unquote

# Tracking query parameters to strip
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "igshid", "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid",
    "si", "feature", "ref", "ref_src", "source", "s", "t", "tab",
    "hl", "lang", "sub_confirmation"
}

# Regex to find URLs in raw text
RAW_URL_REGEX = re.compile(
    r"""(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))""",
    re.VERBOSE
)


def extract_raw_urls(text: str) -> list[str]:
    """Extracts all raw URL strings from unstructured text."""
    if not text:
        return []
    matches = RAW_URL_REGEX.findall(text)
    urls = []
    for match in matches:
        raw_url = match[0] if isinstance(match, tuple) else match
        if raw_url:
            urls.append(raw_url.strip().rstrip(".,;:!?)'\""))
    return urls


def normalize_url(url: str) -> str:
    """
    Normalizes a URL:
    - Prepends https:// if scheme is missing
    - Lowercases hostname
    - Strips www.
    - Removes tracking query parameters
    - Removes trailing slashes (except root)
    """
    if not url or not isinstance(url, str):
        return ""
    
    clean_url = url.strip().rstrip(".,;:!?)'\"")
    
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url
        
    try:
        parsed = urlparse(clean_url)
    except Exception:
        return clean_url

    scheme = "https"  # Standardize to https
    netloc = (parsed.netloc or "").lower()
    
    # Strip www.
    if netloc.startswith("www."):
        netloc = netloc[4:]
        
    path = parsed.path or ""
    # Normalize duplicate slashes
    path = re.sub(r"/+", "/", path)
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]

    # Clean query parameters
    query_dict = parse_qs(parsed.query, keep_blank_values=False)
    filtered_query = {k: v for k, v in query_dict.items() if k.lower() not in TRACKING_PARAMS}
    
    new_query = urlencode(filtered_query, doseq=True) if filtered_query else ""
    
    # Do not keep useless fragments like #
    fragment = parsed.fragment if parsed.fragment not in ("", "top", "main") else ""

    normalized = urlunparse((scheme, netloc, path, parsed.params, new_query, fragment))
    return normalized


def extract_domain(url: str) -> str:
    """Extracts base domain from URL (e.g., instagram.com)."""
    try:
        norm = normalize_url(url)
        parsed = urlparse(norm)
        return parsed.netloc.lower()
    except Exception:
        return ""


def get_canonical_dedup_key(url: str) -> str:
    """Produces a string key for deduplicating URLs."""
    norm = normalize_url(url)
    try:
        parsed = urlparse(norm)
        path = (parsed.path or "").lower().rstrip("/")
        return f"{parsed.netloc.lower()}{path}"
    except Exception:
        return norm.lower()
