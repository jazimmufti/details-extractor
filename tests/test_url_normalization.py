"""Unit tests for URL normalization and deduplication."""

import pytest
from app.services.url_normalizer import normalize_url, get_canonical_dedup_key, extract_raw_urls


def test_normalize_url_removes_tracking_and_www():
    url = "http://www.instagram.com/mkbhd/?utm_source=yt&utm_medium=desc&igshid=12345"
    normalized = normalize_url(url)
    assert normalized == "https://instagram.com/mkbhd"


def test_dedup_key_matching():
    url1 = "https://instagram.com/creator"
    url2 = "http://www.instagram.com/creator/"
    url3 = "https://www.instagram.com/creator?igshid=xyz"
    
    key1 = get_canonical_dedup_key(url1)
    key2 = get_canonical_dedup_key(url2)
    key3 = get_canonical_dedup_key(url3)
    
    assert key1 == key2 == key3 == "instagram.com/creator"


def test_extract_raw_urls_from_text():
    text = """
    Check out my gear:
    Camera: https://amazon.com/dp/B08XYZ?tag=affiliate
    Instagram: instagram.com/techcreator
    Twitter: https://twitter.com/creator
    Portfolio: http://myportfolio.design/
    """
    extracted = extract_raw_urls(text)
    assert any("instagram.com/techcreator" in u for u in extracted)
    assert any("twitter.com/creator" in u for u in extracted)
    assert any("myportfolio.design" in u for u in extracted)
