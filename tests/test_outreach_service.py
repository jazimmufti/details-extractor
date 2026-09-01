"""Unit tests for AI Outreach generation service."""

import pytest
from app.models.messaging_models import OutreachGenerateRequest
from app.services.ai_outreach import AIOutreachService


@pytest.mark.asyncio
async def test_ai_outreach_fallback_generation():
    """Verify grounded fallback generation when Gemini is not invoked."""
    service = AIOutreachService()
    # Force fallback
    service._llm = None

    req = OutreachGenerateRequest(
        creator_name="Marques Brownlee",
        channel_name="MKBHD",
        platform="YouTube",
        recent_video_title="Smartphone Awards 2026",
        sender_name="Alex from Partnership Team",
    )

    res = await service.generate_message(req)
    assert res.success is True
    assert "Marques Brownlee" in res.message or "MKBHD" in res.message
    assert "Smartphone Awards 2026" in res.message
    assert "Alex from Partnership Team" in res.message
    assert len(res.grounded_evidence) >= 2
