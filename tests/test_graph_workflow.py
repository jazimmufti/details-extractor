"""Integration test for the LangGraph extraction pipeline."""

import pytest
from app.graph.workflow import run_extraction_pipeline
from app.utils.youtube_parser import YouTubeURLType


@pytest.mark.asyncio
async def test_pipeline_with_invalid_url():
    result = await run_extraction_pipeline("https://notayoutubeorinstagramurl.com/something")
    assert result.get("success") is False
    assert len(result.get("errors", [])) > 0
    assert "Invalid or unsupported URL" in result["errors"][0]


@pytest.mark.asyncio
async def test_pipeline_with_empty_url():
    result = await run_extraction_pipeline("")
    assert result.get("success") is False
    assert len(result.get("errors", [])) > 0


@pytest.mark.asyncio
async def test_pipeline_with_instagram_profile_url():
    from unittest.mock import patch, AsyncMock
    with patch("app.graph.nodes.gemini_service.extract_and_structure", new_callable=AsyncMock) as mock_gem:
        mock_gem.return_value = None
        url = "https://www.instagram.com/rajshamani/?igsh=ZDNlZDc0MzIxNw=="
        result = await run_extraction_pipeline(url)
        
        assert result.get("url_type") == YouTubeURLType.INSTAGRAM_PROFILE.value
        assert result.get("identifier") == "@rajshamani"
        assert "final_data" in result
        assert result["final_data"] is not None
        assert result["final_data"].social_links is not None
        assert "instagram" in result["final_data"].social_links
        assert result["final_data"].social_links["instagram"].username == "@rajshamani"
        assert "instagram.com/rajshamani" in result["final_data"].social_links["instagram"].url
