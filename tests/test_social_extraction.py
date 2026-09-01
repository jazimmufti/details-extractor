"""Unit tests for social media link and handle extraction."""

import pytest
from app.services.social_extractor import classify_url, extract_socials_and_websites


def test_classify_instagram():
    platform, account = classify_url("https://www.instagram.com/mkbhd/?hl=en")
    assert platform == "instagram"
    assert account.username == "@mkbhd"
    assert account.url == "https://instagram.com/mkbhd"


def test_classify_twitter_and_x():
    platform, account1 = classify_url("https://twitter.com/elonmusk")
    assert platform == "twitter"
    assert account1.username == "@elonmusk"

    platform, account2 = classify_url("https://x.com/OpenAI?s=20")
    assert platform == "twitter"
    assert account2.username == "@OpenAI"
    assert "s=20" not in account2.url


def test_classify_tiktok():
    platform, account = classify_url("https://www.tiktok.com/@mrbeast?lang=en")
    assert platform == "tiktok"
    assert account.username == "@mrbeast"


def test_classify_linkedin():
    platform, account = classify_url("https://www.linkedin.com/in/satyanadella/")
    assert platform == "linkedin"
    assert account.username == "@satyanadella"


def test_classify_threads():
    platform, account = classify_url("https://www.threads.net/@zuck")
    assert platform == "threads"
    assert account.username == "@zuck"


def test_classify_discord_and_telegram():
    platform, account1 = classify_url("https://discord.gg/minecraft")
    assert platform == "discord"
    assert account1.username == "@minecraft"

    platform, account2 = classify_url("https://t.me/durov")
    assert platform == "telegram"
    assert account2.username == "@durov"


def test_classify_twitch_reddit_snapchat_pinterest():
    assert classify_url("https://twitch.tv/ninja")[0] == "twitch"
    assert classify_url("https://reddit.com/u/spez")[0] == "reddit"
    assert classify_url("https://snapchat.com/add/djkhaled305")[0] == "snapchat"
    assert classify_url("https://pinterest.com/tastemade")[0] == "pinterest"


def test_extract_socials_and_websites_combined():
    urls = [
        "https://instagram.com/techlead",
        "https://twitter.com/techlead",
        "https://techlead.org/merch",
        "https://youtube.com/watch?v=123"  # Should be excluded as generic YT
    ]
    text = "Follow on Instagram https://instagram.com/techlead or visit https://techlead.org/merch"
    
    socials, websites = extract_socials_and_websites(urls, text_content=text)
    
    assert "instagram" in socials
    assert "twitter" in socials
    assert len(websites) == 1
    assert websites[0].domain == "techlead.org"


def test_extract_socials_from_plain_text_mentions():
    text = """
    Thanks for watching!
    Instagram: @rajshamani
    Twitter: @rajshamani
    TikTok: @rajshamani
    """
    socials, websites = extract_socials_and_websites([], text_content=text)
    assert "instagram" in socials
    assert socials["instagram"].username == "@rajshamani"
    assert socials["instagram"].url == "https://instagram.com/rajshamani"
    assert "twitter" in socials
    assert "tiktok" in socials


def test_empty_socials():
    urls = []
    socials, websites = extract_socials_and_websites(urls, "No links in here!")
    assert socials == {}
    assert websites == []

