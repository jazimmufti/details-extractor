# Creator Discovery & AI Outreach System • Official Meta Instagram Messaging

A production-grade creator discovery and AI outreach application that accepts any **YouTube video, YouTube Short, @handle, or channel URL**, extracts publicly verified contacts and reliable Instagram accounts, generates personalized AI outreach messages, and executes **real test messaging through Meta's official Instagram Graph API**.

Built with **Python, FastAPI, LangGraph, Google Gemini, and Meta Graph API**, featuring a modern dark-mode glassmorphic web UI inspired by top creator collaboration tools.

---

## 🌟 Key Features

* **Universal Creator Discovery**: Extracts creator profile, verified public business emails, and reliable Instagram handles from any YouTube video, Short, @handle, or channel link.
* **Evidence-Based Contact Extraction**: Strictly extracts publicly available and evidenced emails with source attribution. Never guesses or fabricates emails.
* **Grounded AI Outreach Messages**: Generates personalized creator outreach messages with Google Gemini, grounded strictly on discovered channel topics and recent content.
* **Official Meta Instagram Messaging**: Real integration with Meta's official Graph API for Instagram Direct Messaging (`/messages`).
* **Strict Eligibility Validation**: Distinguishes between discovered handles and Meta API messaging eligibility (IGSID / conversation window rules). Never mocks success or simulates message delivery.
* **Auditable Message History**: Records all message attempts with timestamps, recipient IDs, provider status, and Meta message identifiers in persistent audit storage.
* **Modern Web Interface**: Responsive dark glassmorphism layout with live status indicators, inline outreach editor, test message dispatcher, and evidence inspection drawer.


---

## 🏛 Architecture & Data Flow

```text
User enters YouTube URL
        ↓
[1. validate_input]
        ↓
[2. resolve_youtube_url] (Detects Video / Short / @Handle / Channel ID)
        ↓
[3. fetch_youtube_data] (Calls official YouTube Data API v3)
        ↓
[4. collect_text_and_links] (Aggregates descriptions & text blocks)
        ↓
[5. extract_emails] (High-precision RFC regex + anti-obfuscation)
        ↓
[6. extract_urls] (Discovers & extracts raw links)
        ↓
[7. classify_social_links] (Deterministic matcher for 12+ platforms)
        ↓
[8. gemini_structuring] (LangChain + Gemini structured schema extraction)
        ↓
[9. deduplicate_and_validate] (Canonicalizes URLs, deduplicates entities)
        ↓
[10. build_final_result] (Assembles ExtractionData + auditable evidence)
        ↓
FastAPI JSON Response / Frontend Dashboard
```

---

## 📁 Project Structure

```text
details extractor/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point & static mounting
│   ├── api/
│   │   ├── routes.py               # REST API endpoints (/api/extract, /api/health, /api/research)
│   │   └── schemas.py              # Pydantic request/response schemas
│   ├── core/
│   │   ├── config.py               # Pydantic Settings (.env configuration)
│   │   └── logging.py              # Structured logging configuration
│   ├── graph/
│   │   ├── state.py                # LangGraph ExtractionState TypedDict
│   │   ├── nodes.py                # 10 atomic pipeline execution nodes
│   │   └── workflow.py             # Compiled LangGraph StateGraph
│   ├── models/
│   │   └── extraction_models.py    # Core Pydantic data models & evidence structures
│   ├── services/
│   │   ├── youtube_service.py      # Google YouTube Data API v3 client & resolution
│   │   ├── gemini_service.py       # LangChain + Google Gemini structured output
│   │   ├── email_extractor.py      # Regex & anti-obfuscation email engine
│   │   ├── social_extractor.py     # 12+ social platform detector & handle extractor
│   │   ├── url_normalizer.py       # Canonicalizer & tracking parameter stripper
│   │   └── evidence_service.py     # Auditable evidence compiler
│   └── utils/
│       └── youtube_parser.py       # Robust YouTube URL parser & validator
├── frontend/
│   ├── index.html                  # Responsive modern Web UI
│   ├── style.css                   # Glassmorphic dark theme & animations
│   └── app.js                      # Client logic, live progress, & rendering
├── tests/
│   ├── __init__.py
│   ├── test_youtube_parser.py      # URL parser test suite
│   ├── test_email_extraction.py    # Email regex & obfuscation tests
│   ├── test_social_extraction.py   # Social platform & username tests
│   ├── test_url_normalization.py   # Canonicalization & tracking removal tests
│   └── test_graph_workflow.py      # End-to-end LangGraph pipeline tests
├── .env                            # Active environment configuration
├── .env.example                    # Sample environment template
├── .gitignore                      # Git ignore file
├── requirements.txt                # Python backend dependencies
└── README.md                       # Comprehensive documentation
```

---

## 🔑 Required API Keys

Create a `.env` file (copied from `.env.example`) in the root directory:

```env
# Google YouTube Data API v3 Key (Obtain from Google Cloud Console)
YOUTUBE_API_KEY=your_youtube_api_key_here

# Google Gemini API Key (Obtain from Google AI Studio)
GEMINI_API_KEY=your_gemini_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=*
```

### Obtaining API Keys:
1. **YouTube Data API v3**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a project, enable the **YouTube Data API v3**, and generate an **API Key** under Credentials.
2. **Google Gemini API Key**:
   - Visit [Google AI Studio](https://aistudio.google.com/) and create an API Key.

*(Note: The system gracefully handles cases where keys are omitted or quotas are exceeded by providing deterministic fallback extractions.)*

---

## 🚀 Installation & Running

### 1. Prerequisites
* Python 3.10+ installed.

### 2. Create Virtual Environment & Install Dependencies
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Run Backend & Frontend (Unified Server)
Start the FastAPI server:

```bash
uvicorn app.main:app --reload --port 8000
```

Open your browser and navigate to:
```text
http://localhost:8000
```

The interactive API documentation is available at:
```text
http://localhost:8000/docs
```

---

## 📡 API Endpoints

### 1. Health Check
`GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "youtube_api_configured": true,
  "gemini_api_configured": true,
  "environment": "development"
}
```

---

### 2. Synchronous Extraction
`POST /api/extract`

**Request:**
```json
{
  "url": "https://www.youtube.com/@mkbhd"
}
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "youtube": {
      "channel_name": "Marques Brownlee",
      "channel_url": "https://www.youtube.com/@mkbhd",
      "channel_id": "UCBJycsmduvYEL83R_U4JriQ",
      "video_title": null,
      "video_url": null,
      "description": "Quality Tech Videos | YouTuber | Geek...",
      "subscriber_count": 18500000,
      "view_count": 4150000000,
      "avatar_url": "https://yt3.googleusercontent.com/...",
      "banner_url": "https://yt3.googleusercontent.com/..."
    },
    "social_media": {
      "instagram": {
        "platform": "instagram",
        "url": "https://instagram.com/mkbhd",
        "username": "@mkbhd",
        "source": "youtube_description",
        "evidence": "Follow me on Instagram: https://instagram.com/mkbhd",
        "confidence": "High"
      },
      "twitter": {
        "platform": "twitter",
        "url": "https://twitter.com/mkbhd",
        "username": "@mkbhd",
        "source": "youtube_description",
        "evidence": "Twitter: https://twitter.com/mkbhd",
        "confidence": "High"
      },
      "tiktok": {
        "platform": "tiktok",
        "url": "https://tiktok.com/@mkbhd",
        "username": "@mkbhd",
        "source": "youtube_description",
        "evidence": "TikTok: https://tiktok.com/@mkbhd",
        "confidence": "High"
      }
    },
    "emails": [
      {
        "email": "marques@mkbhd.com",
        "source": "channel_description",
        "evidence": "Business inquiries: marques@mkbhd.com",
        "confidence": "High"
      }
    ],
    "websites": [
      {
        "url": "https://mkbhd.com",
        "domain": "mkbhd.com",
        "title": "Mkbhd",
        "source": "youtube_description",
        "evidence": "Merch & Website: https://mkbhd.com",
        "confidence": "High"
      }
    ],
    "evidence": [
      {
        "field": "youtube:channel",
        "source": "youtube_api",
        "raw_match": "UCBJycsmduvYEL83R_U4JriQ",
        "context": "Channel Name: 'Marques Brownlee', Channel ID: 'UCBJycsmduvYEL83R_U4JriQ', URL: 'https://www.youtube.com/@mkbhd'",
        "confidence": "High"
      },
      {
        "field": "email",
        "source": "channel_description",
        "raw_match": "marques@mkbhd.com",
        "context": "Business inquiries: marques@mkbhd.com",
        "confidence": "High"
      }
    ],
    "metadata": {
      "input_url": "https://www.youtube.com/@mkbhd",
      "url_type": "CHANNEL_HANDLE",
      "video_id": null,
      "channel_id": "UCBJycsmduvYEL83R_U4JriQ",
      "emails_count": 1,
      "socials_count": 3,
      "websites_count": 1
    }
  },
  "error": null,
  "warnings": []
}
```

---

### 3. Asynchronous Research Job
`POST /api/research` (Start Job) & `GET /api/research/{job_id}` (Poll Status)

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:

```bash
python -m pytest -v
```

Tests cover:
* Video, Shorts, Handle, Channel ID, and Custom URL variations.
* Email regex with obfuscation matching and false positive protection.
* Social URL parsing across 12+ platforms (Instagram, Twitter/X, TikTok, LinkedIn, Discord, Telegram, Twitch, Reddit, Snapchat, Pinterest, etc.).
* URL normalizer (protocol normalization, tracking tag removal).
* Full LangGraph pipeline workflow execution and error handling.

---

## 🛡 Security & Best Practices

* **Zero API Key Leaks**: All API credentials are read strictly from `.env` on the backend and are never sent to or visible from the frontend.
* **Anti-Hallucination Constraints**: Gemini prompts enforce strict extraction rules—never guessing or fabricating contact information without direct evidence.
* **Deterministic Priority**: Extractions are anchored in deterministic parsers first; AI assists only in semantic categorization.
