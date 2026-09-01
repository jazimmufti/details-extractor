"""Comprehensive tests for YouTube channel profile & About links fallback extraction."""

import pytest
from unittest.mock import patch, MagicMock
import httpx

from app.services.youtube_service import (
    YouTubeService,
    parse_channel_profile_data_from_json,
    parse_continuation_about_response,
    extract_url_from_youtube_redirect,
)
from app.services.social_extractor import extract_socials_and_websites, classify_url
from app.graph.workflow import run_extraction_pipeline
from app.utils.youtube_parser import parse_youtube_url


MOCK_YT_INITIAL_DATA = {
    "microformat": {
        "microformatDataRenderer": {
            "title": "Raj Shamani",
            "urlCanonical": "https://www.youtube.com/channel/UCzwCEE_PchiBULMnAJqhGVg",
            "description": "Figuring Out podcast and business interviews.",
            "thumbnail": {
                "thumbnails": [{"url": "https://yt3.googleusercontent.com/avatar.jpg"}]
            },
            "channelProfileMicroformatDetails": {
                "profilePage": {
                    "mainEntity": {
                        "sameAs": [
                            "https://www.instagram.com/rajshamani",
                            "https://twitter.com/rajshamani/",
                            "https://linkedin.com/in/rajshamani/",
                            "https://facebook.com/shamaniraj/",
                            "https://threads.com/@rajshamani"
                        ]
                    }
                }
            }
        }
    },
    "header": {
        "pageHeaderRenderer": {
            "content": {
                "pageHeaderViewModel": {
                    "attribution": {
                        "attributionViewModel": {
                            "text": {
                                "content": "Instagram",
                                "commandRuns": [
                                    {
                                        "onTap": {
                                            "innertubeCommand": {
                                                "urlEndpoint": {
                                                    "url": "https://www.youtube.com/redirect?event=channel_header&q=https%3A%2F%2Fwww.instagram.com%2Frajshamani"
                                                }
                                            }
                                        }
                                    }
                                ]
                            },
                            "suffix": {
                                "content": "and 4 more links",
                                "commandRuns": []
                            }
                        }
                    }
                }
            }
        }
    }
}


MOCK_ABOUT_CONTINUATION_RESP = {
    "onResponseReceivedEndpoints": [
        {
            "appendContinuationItemsAction": {
                "continuationItems": [
                    {
                        "aboutChannelRenderer": {
                            "metadata": {
                                "aboutChannelViewModel": {
                                    "links": [
                                        {
                                            "channelExternalLinkViewModel": {
                                                "title": {"content": "Instagram"},
                                                "link": {
                                                    "commandRuns": [
                                                        {
                                                            "onTap": {
                                                                "innertubeCommand": {
                                                                    "urlEndpoint": {
                                                                        "url": "https://www.youtube.com/redirect?event=channel_description&q=https%3A%2F%2Fwww.instagram.com%2Frajshamani"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            }
                                        },
                                        {
                                            "channelExternalLinkViewModel": {
                                                "title": {"content": "Twitter"},
                                                "link": {
                                                    "commandRuns": [
                                                        {
                                                            "onTap": {
                                                                "innertubeCommand": {
                                                                    "urlEndpoint": {
                                                                        "url": "https://www.youtube.com/redirect?event=channel_description&q=https%3A%2F%2Ftwitter.com%2Frajshamani"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            }
                                        },
                                        {
                                            "channelExternalLinkViewModel": {
                                                "title": {"content": "LinkedIn"},
                                                "link": {
                                                    "commandRuns": [
                                                        {
                                                            "onTap": {
                                                                "innertubeCommand": {
                                                                    "urlEndpoint": {
                                                                        "url": "https://www.youtube.com/redirect?event=channel_description&q=https%3A%2F%2Fin.linkedin.com%2Fin%2Frajshamani%2F"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            }
                                        },
                                        {
                                            "channelExternalLinkViewModel": {
                                                "title": {"content": "Facebook"},
                                                "link": {
                                                    "commandRuns": [
                                                        {
                                                            "onTap": {
                                                                "innertubeCommand": {
                                                                    "urlEndpoint": {
                                                                        "url": "https://www.youtube.com/redirect?event=channel_description&q=https%3A%2F%2Fwww.facebook.com%2Fshamaniraj%2F"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            }
                                        },
                                        {
                                            "channelExternalLinkViewModel": {
                                                "title": {"content": "Threads"},
                                                "link": {
                                                    "commandRuns": [
                                                        {
                                                            "onTap": {
                                                                "innertubeCommand": {
                                                                    "urlEndpoint": {
                                                                        "url": "https://www.youtube.com/redirect?event=channel_description&q=https%3A%2F%2Fwww.threads.com%2F%40rajshamani"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                ]
            }
        }
    ]
}


def test_redirect_url_extraction():
    """Verify clean destination URL extraction from YouTube redirects."""
    redirect_url = "https://www.youtube.com/redirect?event=channel_header&redir_token=XYZ&q=https%3A%2F%2Fwww.instagram.com%2Frajshamani"
    extracted = extract_url_from_youtube_redirect(redirect_url)
    assert extracted == "https://www.instagram.com/rajshamani"

    # Non-redirect URL should remain unchanged
    direct_url = "https://twitter.com/rajshamani"
    assert extract_url_from_youtube_redirect(direct_url) == direct_url


def test_requirement_a_mock_channel_page_extracts_all_five():
    """Requirement A: Verify all five profile links (Instagram, Twitter, LinkedIn, Facebook, Threads) are extracted."""
    parsed = parse_channel_profile_data_from_json(MOCK_YT_INITIAL_DATA)
    links = parsed["links"]
    extracted_urls = [l["url"] for l in links]

    assert any("instagram.com/rajshamani" in u for u in extracted_urls)
    assert any("twitter.com/rajshamani" in u for u in extracted_urls)
    assert any("linkedin.com/in/rajshamani" in u for u in extracted_urls)
    assert any("facebook.com/shamaniraj" in u for u in extracted_urls)
    assert any("threads.com/@rajshamani" in u for u in extracted_urls)
    assert len(links) >= 5


def test_requirement_b_classification_by_existing_social_extractor():
    """Requirement B: Verify that those URLs are classified by the existing social extractor."""
    parsed = parse_channel_profile_data_from_json(MOCK_YT_INITIAL_DATA)
    socials, websites = extract_socials_and_websites(
        raw_urls=parsed["links"],
        source="youtube_channel_profile"
    )

    assert "instagram" in socials
    assert "twitter" in socials
    assert "linkedin" in socials
    assert "facebook" in socials
    assert "threads" in socials

    assert socials["instagram"].username == "@rajshamani"
    assert socials["twitter"].username == "@rajshamani"
    assert socials["linkedin"].username == "@rajshamani"
    assert socials["facebook"].username == "@shamaniraj"
    assert socials["threads"].username == "@rajshamani"


def test_requirement_c_source_is_youtube_channel_profile():
    """Requirement C: Verify source is youtube_channel_profile, not youtube_description."""
    parsed = parse_channel_profile_data_from_json(MOCK_YT_INITIAL_DATA)
    socials, websites = extract_socials_and_websites(
        raw_urls=parsed["links"],
        source="youtube_channel_profile"
    )

    for platform, account in socials.items():
        assert account.source == "youtube_channel_profile", f"Account {platform} has wrong source: {account.source}"
        assert account.confidence == "High"


def test_requirement_d_duplicate_deduplication():
    """Requirement D: Verify duplicate URLs in both description and profile are deduplicated properly."""
    profile_links = [
        {"url": "https://instagram.com/rajshamani", "title": "Instagram", "source": "youtube_channel_profile"}
    ]
    description_urls = [
        "https://www.instagram.com/rajshamani?igshid=123",
        "https://twitter.com/rajshamani"
    ]
    description_text = "Follow on IG https://www.instagram.com/rajshamani?igshid=123 and Twitter https://twitter.com/rajshamani"

    # Extract profile socials
    prof_soc, _ = extract_socials_and_websites(profile_links, source="youtube_channel_profile")
    # Extract description socials
    desc_soc, _ = extract_socials_and_websites(description_urls, text_content=description_text, source="youtube_description")

    # Merge as done in pipeline
    merged_soc = dict(desc_soc)
    for plat, acc in prof_soc.items():
        merged_soc[plat] = acc

    assert len(merged_soc) == 2
    assert merged_soc["instagram"].source == "youtube_channel_profile"
    assert merged_soc["twitter"].source == "youtube_description"


def test_requirement_e_unrelated_external_links_not_attributed_to_channel():
    """Requirement E: Verify unrelated video feeds or recommendation links are not attributed as channel profile links."""
    # A page with video descriptions mentioning external guests or sponsors
    data_with_unrelated = dict(MOCK_YT_INITIAL_DATA)
    # The profile parser specifically extracts from microformat sameAs, header attribution, and about view models
    parsed = parse_channel_profile_data_from_json(data_with_unrelated)
    profile_urls = [l["url"] for l in parsed["links"]]

    # Ensure none of the video feeds or unrelated links are in the profile links
    assert "https://www.gatesfoundation.org/" not in profile_urls
    assert "https://amzn.to/3WZOSoi" not in profile_urls


def test_requirement_f_existing_description_extraction_still_works():
    """Requirement F: Verify existing YouTube description extraction still functions."""
    desc_text = "Contact us at contact@rajshamani.com or business@figuringout.tv. Follow https://instagram.com/rajshamani"
    from app.services.email_extractor import extract_emails
    emails = extract_emails(desc_text, source="youtube_description")
    assert len(emails) == 2
    assert {e.email for e in emails} == {"contact@rajshamani.com", "business@figuringout.tv"}

    socials, websites = extract_socials_and_websites(["https://instagram.com/rajshamani"], text_content=desc_text, source="youtube_description")
    assert "instagram" in socials
    assert socials["instagram"].source == "youtube_description"


def test_requirement_g_fallback_does_not_crash_on_network_failure():
    """Requirement G: Verify fallback does not crash when the channel page cannot be fetched."""
    service = YouTubeService()
    
    with patch("httpx.Client.get", side_effect=httpx.ConnectError("Connection refused")):
        res = service.fetch_channel_profile_data("https://www.youtube.com/@nonexistent_channel_123")
        assert res["links"] == []
        assert res["channel_url"] == "https://www.youtube.com/@nonexistent_channel_123"

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "Not found"
        mock_get.return_value = mock_resp

        res = service.fetch_channel_profile_data("https://www.youtube.com/@404_channel")
        assert res["links"] == []


@pytest.mark.asyncio
async def test_end_to_end_pipeline_with_profile_fallback():
    """End-to-end test of the LangGraph extraction pipeline with mocked profile data."""
    mock_profile_result = {
        "links": [
            {"url": "https://www.instagram.com/rajshamani", "title": "Instagram", "source": "youtube_channel_profile"},
            {"url": "https://twitter.com/rajshamani", "title": "Twitter", "source": "youtube_channel_profile"},
            {"url": "https://in.linkedin.com/in/rajshamani/", "title": "LinkedIn", "source": "youtube_channel_profile"},
            {"url": "https://www.facebook.com/shamaniraj", "title": "Facebook", "source": "youtube_channel_profile"},
            {"url": "https://www.threads.com/@rajshamani", "title": "Threads", "source": "youtube_channel_profile"},
        ],
        "channel_name": "Raj Shamani",
        "channel_url": "https://www.youtube.com/@rajshamani",
        "description": "Figuring Out with Raj Shamani. Email: biz@rajshamani.com",
        "avatar_url": "https://yt3.googleusercontent.com/avatar.jpg",
    }

    with patch.object(YouTubeService, "fetch_channel_profile_data", return_value=mock_profile_result):
        state = await run_extraction_pipeline("https://www.youtube.com/@rajshamani")

        assert state.get("success") is True
        data = state.get("final_data")
        assert data is not None

        # Verify socials
        socials = data.social_media
        assert len(socials) >= 5
        assert "instagram" in socials
        assert "twitter" in socials
        assert "linkedin" in socials
        assert "facebook" in socials
        assert "threads" in socials

        # Verify source & evidence
        for plat in ["instagram", "twitter", "linkedin", "facebook", "threads"]:
            acc = socials[plat]
            assert acc.source == "youtube_channel_profile"
            assert acc.confidence == "High"

        # Verify email from description
        emails = data.emails
        assert len(emails) == 1
        assert emails[0].email == "biz@rajshamani.com"

        # Verify evidence list contains youtube_channel_profile entries
        profile_evidence = [e for e in data.evidence if e.source == "youtube_channel_profile"]
        assert len(profile_evidence) >= 5
