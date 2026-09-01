"""Email extraction service with context and anti-obfuscation support."""

import re
from typing import List, Dict, Any, Tuple
from app.models.extraction_models import ContactEmail

# High precision RFC-compliant email regex
EMAIL_REGEX = re.compile(
    r"""(?i)\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+[a-zA-Z0-9])\b"""
)

# Obfuscated patterns like "contact [at] domain.com", "info (at) domain.com", "partner(at)studio.io", "name at domain dot com"
OBFUSCATED_PATTERNS = [
    re.compile(r"""(?i)\b([a-zA-Z0-9_.+-]+)\s*(?:\[at\]|\(at\)|\bat\b|@)\s*([a-zA-Z0-9-]+)\s*(?:\[dot\]|\(dot\)|\bdot\b|\.)\s*([a-zA-Z0-9-.]*[a-zA-Z]{2,})\b"""),
    re.compile(r"""(?i)\b([a-zA-Z0-9_.+-]+)\(at\)([a-zA-Z0-9-]+)\.([a-zA-Z0-9-.]*[a-zA-Z]{2,})\b"""),
    re.compile(r"""(?i)\b([a-zA-Z0-9_.+-]+)\[at\]([a-zA-Z0-9-]+)\.([a-zA-Z0-9-.]*[a-zA-Z]{2,})\b"""),
]

# File extensions to reject if mistakenly matched (e.g. image@2x.png)
INVALID_EMAIL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".mp3", ".zip"}

# Business context keywords that boost confidence
BUSINESS_KEYWORDS = {
    "business", "inquiries", "inquiry", "contact", "email", "mgmt", "management",
    "collab", "collaboration", "sponsor", "sponsorship", "booking", "press", "info", "hello"
}


def _extract_context(text: str, match_start: int, match_end: int, window: int = 70) -> str:
    """Extracts a readable surrounding text window around a match."""
    # Find full sentence or line boundaries if possible
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    
    snippet = text[start:end].replace("\r", " ").replace("\n", " ").strip()
    
    # Add ellipsis if truncated
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def extract_emails(text: str, source: str = "youtube_description") -> List[ContactEmail]:
    """
    Extracts all valid emails from text with verbatim evidence context and confidence rating.
    Deduplicates emails case-insensitively.
    """
    if not text or not isinstance(text, str):
        return []

    found_emails: Dict[str, ContactEmail] = {}

    # 1. Standard RFC Regex Matching
    for match in EMAIL_REGEX.finditer(text):
        raw_email = match.group(1).strip().lower()
        
        # Check invalid trailing extensions (e.g., test@2x.png)
        if any(raw_email.endswith(ext) for ext in INVALID_EMAIL_EXTENSIONS):
            continue

        # Skip common false positives
        if raw_email.endswith(".invalid") or raw_email.endswith(".local"):
            continue

        context = _extract_context(text, match.start(), match.end())
        
        # Determine confidence
        lower_context = context.lower()
        has_business_cue = any(kw in lower_context for kw in BUSINESS_KEYWORDS)
        confidence = "High" if has_business_cue or "@" in raw_email else "Medium"

        if raw_email not in found_emails:
            found_emails[raw_email] = ContactEmail(
                email=raw_email,
                source=source,
                evidence=context,
                confidence=confidence,
            )

    # 2. De-obfuscate patterns like "name [at] domain [dot] com"
    for pattern in OBFUSCATED_PATTERNS:
        for match in pattern.finditer(text):
            user, domain, tld = match.group(1), match.group(2), match.group(3)
            # Remove any internal dots in tld if redundant
            clean_email = f"{user}@{domain}.{tld}".strip().lower()
            
            if clean_email not in found_emails and not any(clean_email.endswith(ext) for ext in INVALID_EMAIL_EXTENSIONS):
                context = _extract_context(text, match.start(), match.end())
                found_emails[clean_email] = ContactEmail(
                    email=clean_email,
                    source=source,
                    evidence=f"De-obfuscated from: \"{context}\"",
                    confidence="Medium",
                )

    return list(found_emails.values())
