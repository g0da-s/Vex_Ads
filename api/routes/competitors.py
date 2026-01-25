"""
Competitor analysis routes.
Handles fetching and processing competitor ads from Meta Ad Library.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from supabase import Client

from api.dependencies import get_supabase
from services.storage import get_storage_service
from services.meta_api import (
    extract_page_id_or_query,
    fetch_ads_from_searchapi,
    process_ad_data,
    download_image,
)
from models.database import get_database_service
from models.schemas import (
    CompetitorAnalyzeRequest,
    CompetitorAnalyzeResponse,
    CompetitorAdResponse,
)
from config import get_settings


def calculate_days_running(ad_delivery_start) -> int:
    """Calculate how many days an ad has been running."""
    if not ad_delivery_start:
        return 0

    # Handle string dates
    if isinstance(ad_delivery_start, str):
        try:
            ad_delivery_start = datetime.fromisoformat(ad_delivery_start.replace("Z", "+00:00"))
        except ValueError:
            return 0

    now = datetime.now(timezone.utc)
    if ad_delivery_start.tzinfo is None:
        ad_delivery_start = ad_delivery_start.replace(tzinfo=timezone.utc)
    return max(0, (now - ad_delivery_start).days)

settings = get_settings()
router = APIRouter(prefix="/competitors", tags=["Competitors"])


@router.post("/analyze", response_model=CompetitorAnalyzeResponse)
async def analyze_competitor(
    request: CompetitorAnalyzeRequest,
    supabase: Client = Depends(get_supabase),
):
    """
    Analyze competitor ads from Meta Ad Library.

    **Process:**
    1. Extract page_id from the provided Ad Library URL
    2. Fetch ad metadata from Meta Graph API
    3. Download ad images (direct URLs - no scraping needed!)
    4. Store images in Supabase Storage
    5. Save ad records to database

    **URL Format:**
    ```
    https://www.facebook.com/ads/library/?view_all_page_id=123456789
    ```
    """
    # Initialize services
    storage = get_storage_service(supabase)
    db = get_database_service(supabase)

    # Validate session exists
    session = db.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload assets first.",
        )

    # Extract page_id from URL
    page_id, _ = extract_page_id_or_query(request.ad_library_url)

    if not page_id:
        raise HTTPException(
            status_code=400,
            detail="Could not extract page_id from URL. "
            "Please provide a valid Ad Library URL with view_all_page_id parameter.",
        )

    try:
        # Fetch more ads to find the best winners (we'll filter to top 5)
        # SearchAPI charges per request, not per result, so fetching more is free
        # Note: active_status="all" returns more ads, we'll filter by duration
        raw_response = await fetch_ads_from_searchapi(
            page_id=page_id,
            limit=50,
            active_status="all",
        )
        raw_ads = raw_response.get("ads", [])

        if not raw_ads:
            raise HTTPException(
                status_code=404,
                detail="No ads found for this page. "
                "The page may not have active ads or may be in a restricted region.",
            )

        # Process and download each ad
        competitor_ads = []
        download_count = 0

        for raw_ad in raw_ads:
            # Process ad metadata
            ad_data = process_ad_data(raw_ad)

            # Skip if this ad already exists for this session (prevent duplicates)
            existing_ad = db.get_competitor_ad_by_meta_id(
                session_id=request.session_id,
                meta_ad_id=ad_data["ad_id"],
            )
            if existing_ad:
                # Return existing ad instead of creating duplicate
                image_signed_url = None
                if existing_ad.get("storage_path"):
                    image_signed_url = storage.get_signed_url(
                        bucket=settings.bucket_competitor_ads,
                        path=existing_ad["storage_path"],
                    )
                days = calculate_days_running(existing_ad.get("ad_delivery_start"))
                competitor_ads.append(
                    CompetitorAdResponse(
                        id=existing_ad["id"],
                        page_id=existing_ad["page_id"],
                        page_name=existing_ad.get("page_name"),
                        ad_id=existing_ad["ad_id"],
                        ad_text=existing_ad.get("ad_text"),
                        image_url=image_signed_url or existing_ad.get("original_image_url") or "",
                        impressions_lower=existing_ad.get("impressions_lower"),
                        impressions_upper=existing_ad.get("impressions_upper"),
                        ad_delivery_start=existing_ad.get("ad_delivery_start"),
                        is_active=ad_data.get("is_active", False),
                        days_running=days,
                        winner_score=ad_data.get("winner_score", 0.0),
                    )
                )
                continue

            # Try to download the ad image
            # Prefer resized_image_url (faster), fall back to original_image_url
            image_url = ad_data.get("resized_image_url") or ad_data.get(
                "original_image_url"
            )
            storage_path = None

            if image_url:
                image_bytes = await download_image(image_url)
                if image_bytes:
                    # Upload to Supabase Storage
                    upload_result = storage.upload_file(
                        bucket=settings.bucket_competitor_ads,
                        file_bytes=image_bytes,
                        original_filename=f"{ad_data['ad_id']}.jpg",
                        folder=request.session_id,
                    )
                    storage_path = upload_result["path"]
                    download_count += 1

            # Save to database
            db_ad = db.create_competitor_ad(
                session_id=request.session_id,
                page_id=ad_data["page_id"],
                ad_id=ad_data["ad_id"],
                page_name=ad_data.get("page_name"),
                ad_text=ad_data.get("ad_text"),
                original_image_url=image_url,
                storage_path=storage_path,
                impressions_lower=ad_data.get("impressions_lower"),
                impressions_upper=ad_data.get("impressions_upper"),
                ad_delivery_start=ad_data.get("ad_delivery_start"),
                is_active=ad_data.get("is_active", False),
                winner_score=ad_data.get("winner_score", 0.0),
            )

            # Generate signed URL if image was downloaded
            image_signed_url = None
            if storage_path:
                image_signed_url = storage.get_signed_url(
                    bucket=settings.bucket_competitor_ads,
                    path=storage_path,
                )

            # Build response object
            days = calculate_days_running(ad_data.get("ad_delivery_start"))
            competitor_ads.append(
                CompetitorAdResponse(
                    id=db_ad["id"],
                    page_id=ad_data["page_id"],
                    page_name=ad_data.get("page_name"),
                    ad_id=ad_data["ad_id"],
                    ad_text=ad_data.get("ad_text"),
                    image_url=image_signed_url or image_url or "",
                    impressions_lower=ad_data.get("impressions_lower"),
                    impressions_upper=ad_data.get("impressions_upper"),
                    ad_delivery_start=ad_data.get("ad_delivery_start"),
                    is_active=ad_data.get("is_active", False),
                    days_running=days,
                    winner_score=ad_data.get("winner_score", 0.0),
                )
            )

        # Sort by winner_score (highest first) and take top 5
        competitor_ads.sort(key=lambda x: x.winner_score, reverse=True)
        top_winners = competitor_ads[:5]

        return CompetitorAnalyzeResponse(
            session_id=request.session_id,
            page_id=page_id or "unknown",
            ads_found=len(raw_ads),
            ads_downloaded=download_count,
            competitor_ads=top_winners,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze competitor ads: {str(e)}",
        )


@router.get("/{session_id}", response_model=list[CompetitorAdResponse])
async def get_competitor_ads(
    session_id: str,
    supabase: Client = Depends(get_supabase),
):
    """
    Get all competitor ads for a session.

    Returns previously analyzed ads with refreshed signed URLs.
    """
    storage = get_storage_service(supabase)
    db = get_database_service(supabase)

    # Validate session exists
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get competitor ads from database
    ads = db.get_competitor_ads(session_id)

    # Build response with fresh signed URLs
    result = []
    for ad in ads:
        image_url = ""
        if ad.get("storage_path"):
            image_url = storage.get_signed_url(
                bucket=settings.bucket_competitor_ads,
                path=ad["storage_path"],
            )
        elif ad.get("original_image_url"):
            image_url = ad["original_image_url"]

        days = calculate_days_running(ad.get("ad_delivery_start"))
        result.append(
            CompetitorAdResponse(
                id=ad["id"],
                page_id=ad["page_id"],
                page_name=ad.get("page_name"),
                ad_id=ad["ad_id"],
                ad_text=ad.get("ad_text"),
                image_url=image_url,
                impressions_lower=ad.get("impressions_lower"),
                impressions_upper=ad.get("impressions_upper"),
                ad_delivery_start=ad.get("ad_delivery_start"),
                is_active=ad.get("is_active", False),
                days_running=days,
                winner_score=ad.get("winner_score", 0.0),
            )
        )

    # Sort by winner_score (highest first)
    result.sort(key=lambda x: x.winner_score, reverse=True)

    return result
