"""Google Gemini AI integration using LangChain for semantic classification."""

from typing import Optional, Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.core.logging import logger
from app.models.extraction_models import (
    GeminiStructuredOutput,
    SocialAccount,
    ContactEmail,
    WebsiteInfo,
)

SYSTEM_PROMPT = """You are a rigorous, evidence-based social & contact information extraction system.

Given publicly retrieved YouTube text, descriptions, and URLs:

1. Extract ONLY information explicitly supported by the provided input text.
2. NEVER invent, hallucinate, or guess an email address or username.
3. NEVER fabricate a social media URL.
4. Do NOT assume an account exists merely because a person's name or brand appears without a handle or link.
5. For every extracted item, include verbatim evidence showing exactly where in the text it was found.
6. Classify URLs into their appropriate platform (e.g., instagram, twitter, tiktok, facebook, linkedin, threads, discord, telegram, twitch, reddit, snapchat, pinterest).
7. If an item is ambiguous or unsure, assign Low or Medium confidence.
8. If no information is found for a field, return an empty list for that field.

Strictly adhere to the provided JSON schema output."""

USER_PROMPT_TEMPLATE = """Please analyze the following retrieved YouTube description and raw URLs to extract and normalize any verified social accounts, contact emails, and personal/brand websites.

[Raw Unstructured Text / Descriptions]:
\"\"\"
{raw_text}
\"\"\"

[Extracted URLs]:
{raw_urls}

Extract only verified information with direct textual evidence. Do not guess or invent any contacts."""


class GeminiService:
    """Service wrapping Google Gemini via LangChain for semantic structuring."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._llm = None
        
        if self.api_key:
            try:
                self._llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    temperature=0.0,  # Deterministic / lowest hallucination
                )
            except Exception as e:
                logger.error(f"Failed to initialize Gemini LLM client: {e}")

    @property
    def is_configured(self) -> bool:
        return bool(self._llm is not None)

    async def extract_and_structure(
        self, raw_text: str, raw_urls: List[str]
    ) -> Optional[GeminiStructuredOutput]:
        """
        Uses Gemini to semantically classify ambiguous links and extract structured social/contact data.
        Returns None gracefully if not configured or on failure.
        """
        if not self.is_configured:
            logger.info("Gemini API key not configured; skipping AI semantic enrichment.")
            return None

        if not raw_text.strip() and not raw_urls:
            return GeminiStructuredOutput()

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("user", USER_PROMPT_TEMPLATE)
            ])

            structured_llm = self._llm.with_structured_output(GeminiStructuredOutput)
            chain = prompt | structured_llm

            logger.info("Executing Gemini semantic extraction chain...")
            result: GeminiStructuredOutput = await chain.ainvoke({
                "raw_text": raw_text[:8000],  # Guard against excessive tokens
                "raw_urls": "\n".join(raw_urls) if raw_urls else "None"
            })
            return result
        except Exception as e:
            logger.warning(f"Gemini semantic structuring failed or timed out: {e}. Falling back to deterministic results.")
            return None


gemini_service = GeminiService()
