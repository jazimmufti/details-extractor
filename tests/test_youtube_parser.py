"""Unit tests for YouTube URL parser."""

import pytest
from app.utils.youtube_parser import parse_youtube_url, YouTubeURLType


def test_parse_standard_video_url():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    target = parse_youtube_url(url)
    assert target is not None
    assert target.url_type == YouTubeURLType.VIDEO
    assert target.identifier == "dQw4w9WgXcQ"
    assert target.canonical_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_parse_video_url_with_tracking_and_timestamp():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&feature=shared&ab_channel=RickAstley"
    target = parse_youtube_url(url)
    assert target is not None
    assert target.url_type == YouTubeURLType.VIDEO
    assert target.identifier == "dQw4w9WgXcQ"


def test_parse_short_domain_video():
    url = "https://youtu.be/dQw4w9WgXcQ?si=abcdef12345"
    target = parse_youtube_url(url)
    assert target is not None
    assert target.url_type == YouTubeURLType.VIDEO
    assert target.identifier == "dQw4w9WgXcQ"


def test_parse_shorts_url():
    url = "https://www.youtube.com/shorts/3f5t3g4e_rM"
    target = parse_youtube_url(url)
    assert target is not None
    assert target.url_type == YouTubeURLType.SHORT
    assert target.identifier == "3f5t3g4e_rM"
    assert target.canonical_url == "https://www.youtube.com/shorts/3f5t3g4e_rM"


def test_parse_channel_handle():
    url = "https://www.youtube.com/@mkbhd"
    target = parse_youtube_url(url)
    assert target is not None
    assert target.url_type == YouTubeURLType.CHANNEL_HANDLE
    assert target.identifier == "@mkbhd"
    assert target.canonical_url == "https://www.youtube.com/@mkbhd"


def test_parse_raw_handle():
    url = "@MrBeast"
    target = parse_youtube_url(url)
    assert target is not None
    assert target.url_type == YouTubeURLType.CHANNEL_HANDLE
    assert target.identifier == "@MrBeast"


def test_parse_channel_id():
    url = "https://www.youtube.com/channel/UCBJycsmduvYEL83R_U4JriQ"
    target = parse_youtube_url(url)
    assert target is not None
    assert target.url_type == YouTubeURLType.CHANNEL_ID
    assert target.identifier == "UCBJycsmduvYEL83R_U4JriQ"


def test_parse_custom_channel():
    url = "https://www.youtube.com/c/Veritasium"
    target = parse_youtube_url(url)
    assert target is not None
    assert target.url_type == YouTubeURLType.CUSTOM_CHANNEL
    assert target.identifier == "Veritasium"


def test_parse_user_channel():
    url = "https://www.youtube.com/user/TEDtalksDirector"
    target = parse_youtube_url(url)
    assert target is not None
    assert target.url_type == YouTubeURLType.USER_CHANNEL
    assert target.identifier == "TEDtalksDirector"


def test_invalid_urls():
    assert parse_youtube_url("") is None
    assert parse_youtube_url("https://google.com") is None
    assert parse_youtube_url("https://vimeo.com/12345678") is None
    assert parse_youtube_url("not a url") is None
