"""FastAPI API routes for extraction, intelligence, and official Meta messaging."""

import json
import uuid
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Header, Query, Response

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
    InstagramSendMessageRequest,
    InstagramSendMessageResponse,
    ColdOutreachPrepareRequest,
    ColdOutreachPrepareResponse,
    RecipientStatusResponse,
    InstagramEligibilityRequest,
    InstagramEligibilityResponse,
    MessageRecord,
    OutreachGenerateRequest,
    OutreachGenerateResponse,
)
from app.graph.workflow import run_extraction_pipeline
from app.services.instagram_service import instagram_service, resolve_recipient_for_creator
from app.services.ai_outreach import ai_outreach_service

router = APIRouter(prefix="/api", tags=["Intelligence"])

# In-memory background jobs registry
JOBS_STORE: Dict[str, Dict[str, Any]] = {}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns system health status and configuration diagnostics without revealing secrets."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        youtube_api_configured=settings.has_youtube_api_key,
        gemini_api_configured=settings.has_gemini_api_key,
        meta_api_configured=settings.has_meta_configured,
        meta_access_token_present=bool(settings.INSTAGRAM_ACCESS_TOKEN),
        instagram_account_id_present=bool(settings.INSTAGRAM_ACCOUNT_ID),
        meta_graph_api_version=settings.META_GRAPH_API_VERSION or "v21.0",
        environment=settings.ENVIRONMENT,
        supported_modes=["real", "simulation"],
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
    Evaluates messaging eligibility under official Meta Graph API specifications.
    Distinguishes public discovery, recipient identity (IGSID), and messaging capability.
    """
    return await instagram_service.check_eligibility(
        username=request.instagram_username,
        instagram_user_id=request.instagram_user_id,
        mode=request.mode,
    )


@router.post("/social/instagram/send", response_model=InstagramSendResponse)
async def send_instagram_message(request: InstagramSendRequest, response: Response):
    """
    Dispatches a message via official Meta Graph API (or local simulation).
    Enforces recipient eligibility, server-side idempotency, and never mocks success.
    """
    clean_user = request.instagram_username or request.creator_username
    target_id = request.instagram_user_id or request.recipient_igsid
    logger.info(
        f"POST /api/social/instagram/send mode='{request.mode}' "
        f"username='{clean_user}', user_id='{target_id}'"
    )
    result = await instagram_service.send_message(request)
    if not result.success:
        response.status_code = 400
    return result


@router.post("/instagram/outreach/prepare", response_model=ColdOutreachPrepareResponse)
async def prepare_cold_instagram_outreach(request: ColdOutreachPrepareRequest):
    """
    Prepares a cold Instagram outreach action without calling Meta API.
    Normalizes the Instagram profile URL, records an auditable record as 'prepared',
    and returns verified URL + message payload for manual completion on Instagram.
    """
    raw_msg = (request.message or "").strip()
    if not raw_msg:
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    clean_user = request.creator_username.lstrip("@").strip() if request.creator_username else None
    
    if not clean_user and not request.creator_url:
        raise HTTPException(
            status_code=400,
            detail="Either creator_username or creator_url is required to prepare Instagram outreach."
        )

    # Normalize canonical Instagram URL
    canonical_url = request.creator_url
    if not canonical_url and clean_user:
        canonical_url = f"https://www.instagram.com/{clean_user}/"
    elif canonical_url and not canonical_url.endswith("/"):
        canonical_url = f"{canonical_url}/"

    # Record audit log without falsely claiming 'sent'
    record = instagram_service.record_cold_outreach(
        creator_id=request.creator_id,
        instagram_username=clean_user,
        instagram_url=canonical_url,
        message=raw_msg,
        action=request.action or "profile_opened_copied",
    )

    return ColdOutreachPrepareResponse(
        success=True,
        status="prepared",
        action=request.action or "profile_opened_copied",
        instagram_username=f"@{clean_user}" if clean_user else None,
        instagram_url=canonical_url,
        message=raw_msg,
        prepared_at=record.created_at,
        details="Cold outreach prepared. Message copied and Instagram profile ready."
    )


@router.get("/instagram/recipient-status", response_model=RecipientStatusResponse)
async def get_instagram_recipient_status(
    creator_id: Optional[str] = Query(None),
    instagram_username: Optional[str] = Query(None),
    instagram_url: Optional[str] = Query(None),
    mode: str = Query("real"),
):
    """
    Retrieves the recipient messaging status for the frontend composer.
    Automatically determines if a legitimate Meta messaging identity is stored.
    Does NOT require or leak raw IGSIDs to the browser.
    """
    return instagram_service.get_recipient_status(
        creator_id=creator_id,
        instagram_username=instagram_username,
        instagram_url=instagram_url,
        mode=mode,
    )


@router.post("/instagram/send-message", response_model=InstagramSendResponse)
async def send_official_instagram_message_alias(request: InstagramSendRequest, response: Response):
    """
    Alias route for /api/social/instagram/send for backward compatibility.
    """
    return await send_instagram_message(request, response)



@router.get("/social/instagram/history")
async def get_instagram_message_history():
    """Returns persistent audit log of all Instagram message send attempts."""
    return instagram_service.get_message_history()



# ==========================================
# Meta Webhook Ingestion Routes
# ==========================================

@router.get("/webhook/instagram")
async def meta_webhook_verification(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Meta Webhook Verification Endpoint.
    Responds to Meta's subscription challenge if verify token matches.
    """
    expected_token = settings.META_WEBHOOK_VERIFY_TOKEN or "creator_outreach_verify_token"
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("Meta Webhook verification challenge passed successfully.")
        return Response(content=hub_challenge or "", media_type="text/plain")
    logger.warning("Meta Webhook verification challenge failed: token mismatch.")
    raise HTTPException(status_code=403, detail="Webhook verification token mismatch")


@router.post("/webhook/instagram")
async def meta_webhook_handler(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    """
    Meta Webhook Event Ingestion.
    Validates X-Hub-Signature-256, parses messaging/change events, and registers verified IGSIDs.
    """
    body_bytes = await request.body()
    
    # If app secret is configured, verify HMAC signature
    if settings.META_APP_SECRET:
        if not instagram_service.verify_webhook_signature(body_bytes, x_hub_signature_256):
            logger.warning("Meta Webhook rejected: Invalid HMAC SHA-256 signature.")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        data = await request.json()
        updated = instagram_service.ingest_webhook_event(data)
        logger.info(f"Meta Webhook processed event successfully. Updated {updated} recipient mapping(s).")
        return {"status": "success", "recipients_updated": updated}
    except Exception as e:
        logger.error(f"Error parsing webhook body: {e}")
        return {"status": "error", "message": str(e)}


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
