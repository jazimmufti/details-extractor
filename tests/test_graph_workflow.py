"""Integration test for the LangGraph extraction pipeline."""

import pytest
from app.graph.workflow import run_extraction_pipeline
from app.utils.youtube_parser import YouTubeURLType


@pytest.mark.asyncio
async def test_pipeline_with_invalid_url():
    result = await run_extraction_pipeline("https://notayoutubeurl.com/something")
    assert result.get("success") is False
    assert len(result.get("errors", [])) > 0
    assert "Invalid or unsupported YouTube URL" in result["errors"][0]


@pytest.mark.asyncio
async def test_pipeline_with_empty_url():
    result = await run_extraction_pipeline("")
    assert result.get("success") is False
    assert len(result.get("errors", [])) > 0


@pytest.mark.asyncio
async def test_pipeline_with_valid_youtube_handle():
    url = "https://www.youtube.com/@mkbhd"
    result = await run_extraction_pipeline(url)
    
    # Should resolve correctly
    assert result.get("url_type") == YouTubeURLType.CHANNEL_HANDLE.value
    assert result.get("identifier") == "@mkbhd"
    assert "final_data" in result
    assert result["final_data"] is not None
    assert result["final_data"].youtube is not None
