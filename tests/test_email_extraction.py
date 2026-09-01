"""Unit tests for email extraction and context parsing."""

import pytest
from app.services.email_extractor import extract_emails


def test_standard_email_extraction():
    text = """
    Thanks for watching!
    For business inquiries: business@example.com
    Press contact: press@example.org
    """
    emails = extract_emails(text)
    email_addrs = [e.email for e in emails]
    assert "business@example.com" in email_addrs
    assert "press@example.org" in email_addrs
    
    biz_item = next(e for e in emails if e.email == "business@example.com")
    assert biz_item.confidence == "High"
    assert "business@example.com" in biz_item.evidence


def test_complex_and_uk_domains():
    text = "Reach our UK team at hello@agency.co.uk and our dev at contact+yt@sub.domain.tech"
    emails = extract_emails(text)
    email_addrs = [e.email for e in emails]
    assert "hello@agency.co.uk" in email_addrs
    assert "contact+yt@sub.domain.tech" in email_addrs


def test_obfuscated_emails():
    text = "Send business offers to sponsor [at] creator [dot] com or partner(at)studio.io"
    emails = extract_emails(text)
    email_addrs = [e.email for e in emails]
    assert "sponsor@creator.com" in email_addrs
    assert "partner@studio.io" in email_addrs


def test_no_email_returns_empty():
    text = """
    Check out my latest vlog!
    Follow me on Twitter: https://twitter.com/creator
    Subscribe for more videos every week!
    """
    emails = extract_emails(text)
    assert emails == []


def test_reject_false_positives():
    text = "Check our logo assets at logo@2x.png and background@4x.jpg"
    emails = extract_emails(text)
    assert emails == []
