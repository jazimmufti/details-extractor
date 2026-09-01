"""FastAPI API routes for extraction and intelligence."""

import uuid
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.core.config import settings
from app.core.logging import logger
from app.api.schemas import (
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    JobStartResponse,
    JobStatusResponse,
    InstagramSendRequest,
    InstagramSendResponse,
    InstagramEligibilityRequest,
    InstagramEligibilityResponse,
    MessageRecord,
    OutreachGenerateRequest,
    OutreachGenerateResponse,
)
from app.graph.workflow import run_extraction_pipeline
from app.services.instagram_service import instagram_service
from app.services.ai_outreach import ai_outreach_service

router = APIRouter(prefix="/api", tags=["Intelligence"])

# In-memory background jobs registry
JOBS_STORE: Dict[str, Dict[str, Any]] = {}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns health status and API configuration flags."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        youtube_api_configured=settings.has_youtube_api_key,
        gemini_api_configured=settings.has_gemini_api_key,
        meta_api_configured=settings.has_meta_configured,
        environment=settings.ENVIRONMENT,
    )



@router.post("/extract", response_model=ExtractResponse)
async def extract_youtube_intelligence(request: ExtractRequest):
    """
    Synchronously extracts social media and contact intelligence
    from a given YouTube video, Short, @handle, or channel URL.
    """
    logger.info(f"POST /api/extract received URL: {request.url}")
    try:
        final_state = await run_extraction_pipeline(request.url)
        
        errors = final_state.get("errors", [])
        if errors:
            return ExtractResponse(
                success=False,
                error="; ".join(errors),
                warnings=final_state.get("warnings", []),
            )

        data = final_state.get("final_data")
        return ExtractResponse(
            success=True,
            data=data,
            warnings=final_state.get("warnings", []),
        )
    except Exception as e:
        logger.error(f"Error during extraction request: {e}", exc_info=True)
        return ExtractResponse(
            success=False,
            error=f"Internal extraction error: {str(e)}",
        )


async def _run_job_worker(job_id: str, url: str):
    """Background worker to run extraction and update job state stages."""
    try:
        JOBS_STORE[job_id]["status"] = "processing"
        JOBS_STORE[job_id]["stage"] = "Validating URL"
        
        final_state = await run_extraction_pipeline(url)
        
        errors = final_state.get("errors", [])
        if errors:
            JOBS_STORE[job_id]["status"] = "failed"
            JOBS_STORE[job_id]["error"] = "; ".join(errors)
            JOBS_STORE[job_id]["stage"] = "Failed"
        else:
            JOBS_STORE[job_id]["status"] = "completed"
            JOBS_STORE[job_id]["stage"] = "Extraction completed"
            JOBS_STORE[job_id]["data"] = final_state.get("final_data")
    except Exception as e:
        logger.error(f"Background job {job_id} failed: {e}")
        JOBS_STORE[job_id]["status"] = "failed"
        JOBS_STORE[job_id]["error"] = str(e)
        JOBS_STORE[job_id]["stage"] = "Failed"


@router.post("/research", response_model=JobStartResponse)
async def start_research_job(request: ExtractRequest, background_tasks: BackgroundTasks):
    """Initiates an asynchronous background intelligence research job."""
    job_id = str(uuid.uuid4())
    JOBS_STORE[job_id] = {
        "job_id": job_id,
        "url": request.url,
        "status": "pending",
        "stage": "Job queued",
        "data": None,
        "error": None,
    }
    background_tasks.add_task(_run_job_worker, job_id, request.url)
    return JobStartResponse(
        success=True,
        job_id=job_id,
        message="Research job successfully initiated",
    )


@router.get("/research/{job_id}", response_model=JobStatusResponse)
async def get_research_job(job_id: str):
    """Retrieves status and results for a background research job."""
    job = JOBS_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        stage=job["stage"],
        data=job.get("data"),
        error=job.get("error"),
    )


# ==========================================
# Instagram Official Messaging API Routes
# ==========================================

@router.get("/social/instagram/status")
async def get_instagram_messaging_status():
    """Returns Meta Instagram API configuration diagnostics and capability status."""
    return instagram_service.get_configuration_status()


@router.post("/social/instagram/eligibility", response_model=InstagramEligibilityResponse)
async def check_instagram_messaging_eligibility(request: InstagramEligibilityRequest):
    """
    Evaluates whether a discovered creator is eligible for Meta API messaging.
    Enforces Meta recipient rules (IGSID requirements, 24h window, tester roles).
    """
    return await instagram_service.check_eligibility(
        username=request.instagram_username,
        instagram_user_id=request.instagram_user_id,
    )


@router.post("/social/instagram/send", response_model=InstagramSendResponse)
async def send_instagram_message(request: InstagramSendRequest):
    """
    Dispatches a real Instagram Direct Message via official Meta Graph API.
    Enforces recipient eligibility, validates credentials, and never mocks success.
    """
    logger.info(f"POST /api/social/instagram/send requested for username='{request.instagram_username}', user_id='{request.instagram_user_id}'")
    return await instagram_service.send_message(request)


@router.get("/social/instagram/history")
async def get_instagram_message_history():
    """Returns persistent audit log of all Instagram message send attempts."""
    return instagram_service.get_message_history()


# ==========================================
# AI Outreach Generator Routes
# ==========================================

@router.post("/outreach/generate", response_model=OutreachGenerateResponse)
async def generate_outreach_message(request: OutreachGenerateRequest):
    """
    Generates a personalized creator outreach message strictly grounded
    in discovered evidence (channel niche, video titles, creator name).
    """
    logger.info(f"POST /api/outreach/generate for creator='{request.creator_name or request.channel_name}'")
    return await ai_outreach_service.generate_message(request)

