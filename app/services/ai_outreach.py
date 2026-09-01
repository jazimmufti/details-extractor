"""AI-powered Creator Outreach Message Generator.

Generates highly personalized, grounded outreach DMs and emails based strictly on discovered evidence.
"""

from typing import Optional, List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.core.logging import logger
from app.models.messaging_models import OutreachGenerateRequest, OutreachGenerateResponse

OUTREACH_SYSTEM_PROMPT = """You are an expert creator partnerships manager.
Your task is to write a concise, genuine, and highly personalized outreach message to a content creator.

STRICT RULES:
1. Ground the message ONLY on information provided in the input (creator name, channel topics, video titles).
2. NEVER invent fake mutual friends, fake products they reviewed, or fake statistics.
3. Keep the tone warm, authentic, respectful, and concise (under 75 words).
4. Clearly state admiration for their specific content and suggest a collaboration.
5. End with a polite sign-off.

Output ONLY the message body text without any preamble or conversational filler."""


class AIOutreachService:
    """Service to generate grounded creator outreach messages."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._llm = None

        if self.api_key:
            try:
                self._llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    temperature=0.4,
                )
            except Exception as e:
                logger.error(f"Failed to initialize Gemini for outreach generation: {e}")

    @property
    def is_configured(self) -> bool:
        return bool(self._llm is not None)

    async def generate_message(self, request: OutreachGenerateRequest) -> OutreachGenerateResponse:
        """
        Generates a personalized outreach message. Uses Gemini if available,
        or grounded template fallback if unconfigured.
        """
        name = request.creator_name or request.channel_name or "there"
        # Clean up name if it has handles
        clean_name = name.split("@")[-1].strip() if "@" in name else name
        sender = request.sender_name or "Outreach Team"
        platform = request.platform or "YouTube"
        video_title = request.recent_video_title or ""
        desc_snippet = request.description_snippet or ""

        grounded_points = []
        if request.creator_name or request.channel_name:
            grounded_points.append(f"Creator: {request.creator_name or request.channel_name}")
        if video_title:
            grounded_points.append(f"Content: '{video_title}'")
        if platform:
            grounded_points.append(f"Platform: {platform}")

        if self.is_configured:
            try:
                prompt_text = f"""Creator / Channel: {clean_name}
Platform: {platform}
Recent Video / Content: {video_title if video_title else 'N/A'}
About / Bio snippet: {desc_snippet[:400] if desc_snippet else 'N/A'}
Sender Name: {sender}

Write a concise outreach message to {clean_name}:"""

                prompt = ChatPromptTemplate.from_messages([
                    ("system", OUTREACH_SYSTEM_PROMPT),
                    ("user", prompt_text),
                ])

                chain = prompt | self._llm
                response = await chain.ainvoke({})
                generated_text = response.content.strip()

                return OutreachGenerateResponse(
                    success=True,
                    message=generated_text,
                    subject=f"Collaboration with {clean_name}",
                    grounded_evidence=grounded_points,
                )
            except Exception as e:
                logger.warning(f"Gemini outreach generation failed: {e}. Using grounded template fallback.")

        # Grounded template fallback
        if video_title:
            msg = (
                f"Hi {clean_name},\n\n"
                f"I came across your content on {platform} (especially '{video_title}') and really enjoyed it. "
                f"I'd love to connect and discuss a potential collaboration.\n\n"
                f"Best,\n{sender}"
            )
        else:
            msg = (
                f"Hi {clean_name},\n\n"
                f"I came across your channel on {platform} and really admire your work. "
                f"I'd love to connect and discuss a potential collaboration.\n\n"
                f"Best,\n{sender}"
            )

        return OutreachGenerateResponse(
            success=True,
            message=msg,
            subject=f"Collaboration with {clean_name}",
            grounded_evidence=grounded_points,
        )


ai_outreach_service = AIOutreachService()
