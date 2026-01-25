"""
Ad generation routes.
Handles AI-powered ad generation using Gemini.
"""

from fastapi import APIRouter, HTTPException, Depends
from supabase import Client

from api.dependencies import get_supabase
from services.storage import get_storage_service
from services.ai_generator import generate_multiple_ads, build_generation_prompt, RateLimitError
from models.database import get_database_service
from models.schemas import (
    GenerateAdsRequest,
    GenerateAdsResponse,
    GeneratedAdResponse,
    AssetType,
)
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/generate", tags=["Generation"])


@router.post("", response_model=GenerateAdsResponse)
async def generate_ads(
    request: GenerateAdsRequest,
    supabase: Client = Depends(get_supabase),
):
    """
    Generate new ad images using Google Gemini AI.

    **Process:**
    1. Retrieve user's product image and logo from storage
    2. Retrieve selected competitor ad from storage
    3. Send all images to Gemini with generation prompt
    4. Save generated ads to Supabase Storage
    5. Return signed URLs for download

    **Requirements:**
    - Session must have uploaded assets (product image + logo)
    - Valid competitor_ad_id from previous analysis

    **Note:** Generation may fail if Gemini's image generation
    is unavailable or rate-limited. The service will return
    as many successful generations as possible.
    """
    # Initialize services
    storage = get_storage_service(supabase)
    db = get_database_service(supabase)

    # Validate session
    session = db.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload assets first.",
        )

    # Get user assets
    product_asset = db.get_user_asset_by_type(
        request.session_id, AssetType.PRODUCT_IMAGE.value
    )
    logo_asset = db.get_user_asset_by_type(request.session_id, AssetType.LOGO.value)

    if not product_asset or not logo_asset:
        raise HTTPException(
            status_code=400,
            detail="Missing required assets. Please upload product image and logo first.",
        )

    # Get competitor ads - either specific one or top winners
    if request.competitor_ad_id:
        # Use specific competitor ad
        competitor_ad = db.get_competitor_ad(request.competitor_ad_id)
        if not competitor_ad:
            raise HTTPException(
                status_code=404,
                detail="Competitor ad not found. Please analyze competitor first.",
            )
        if not competitor_ad.get("storage_path"):
            raise HTTPException(
                status_code=400,
                detail="Competitor ad image not available. Please select a different ad.",
            )
        competitor_ads_to_use = [competitor_ad]
    else:
        # Auto-select top winners based on winner_score
        all_competitor_ads = db.get_competitor_ads(request.session_id)
        if not all_competitor_ads:
            raise HTTPException(
                status_code=404,
                detail="No competitor ads found. Please analyze competitor first.",
            )

        # Filter ads with images and sort by winner_score
        ads_with_images = [ad for ad in all_competitor_ads if ad.get("storage_path")]
        if not ads_with_images:
            raise HTTPException(
                status_code=400,
                detail="No competitor ads with images available.",
            )

        # Sort by winner_score descending and take top N
        ads_with_images.sort(key=lambda x: x.get("winner_score", 0), reverse=True)
        competitor_ads_to_use = ads_with_images[:request.max_winners]

    try:
        # Download user assets once
        product_image = storage.download_file(
            bucket=settings.bucket_user_assets,
            path=product_asset["storage_path"],
        )
        logo_image = storage.download_file(
            bucket=settings.bucket_user_assets,
            path=logo_asset["storage_path"],
        )

        # Generate ads for each competitor ad
        generated_ads = []
        total_generated = 0

        for competitor_ad in competitor_ads_to_use:
            # Download competitor image
            competitor_image = storage.download_file(
                bucket=settings.bucket_competitor_ads,
                path=competitor_ad["storage_path"],
            )

            # Generate ads with Gemini
            generated_images = await generate_multiple_ads(
                competitor_image=competitor_image,
                product_image=product_image,
                logo_image=logo_image,
                competitor_ad_text=competitor_ad.get("ad_text"),
                product_description=request.product_description,
                num_variations=request.num_variations,
            )

            if not generated_images:
                continue  # Skip this winner, try next one

            # Save generated ads
            prompt_used = build_generation_prompt(
                competitor_ad_text=competitor_ad.get("ad_text"),
                product_description=request.product_description,
            )

            for i, image_bytes in enumerate(generated_images):
                # Upload to storage
                upload_result = storage.upload_file(
                    bucket=settings.bucket_generated_ads,
                    file_bytes=image_bytes,
                    original_filename=f"generated_{competitor_ad['id']}_{i}.png",
                    folder=request.session_id,
                )

                # Save to database
                db_ad = db.create_generated_ad(
                    session_id=request.session_id,
                    competitor_ad_id=competitor_ad["id"],
                    storage_path=upload_result["path"],
                    prompt_used=prompt_used,
                )

                # Generate signed URL for download
                download_url = storage.get_signed_url(
                    bucket=settings.bucket_generated_ads,
                    path=upload_result["path"],
                )

                generated_ads.append(
                    GeneratedAdResponse(
                        id=db_ad["id"],
                        download_url=download_url,
                        competitor_ad_id=competitor_ad["id"],
                        created_at=db_ad["created_at"],
                    )
                )
                total_generated += 1

        if not generated_ads:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate any ads. "
                "Gemini image generation may be unavailable. Please try again later.",
            )

        return GenerateAdsResponse(
            session_id=request.session_id,
            generated_count=total_generated,
            generated_ads=generated_ads,
        )

    except HTTPException:
        raise
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail=str(e),
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate ads: {str(e)}",
        )


@router.get("/{session_id}", response_model=list[GeneratedAdResponse])
async def get_generated_ads(
    session_id: str,
    supabase: Client = Depends(get_supabase),
):
    """
    Get all generated ads for a session.

    Returns previously generated ads with refreshed signed URLs.
    """
    storage = get_storage_service(supabase)
    db = get_database_service(supabase)

    # Validate session
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get generated ads from database
    ads = db.get_generated_ads(session_id)

    # Build response with fresh signed URLs
    result = []
    for ad in ads:
        download_url = storage.get_signed_url(
            bucket=settings.bucket_generated_ads,
            path=ad["storage_path"],
        )

        result.append(
            GeneratedAdResponse(
                id=ad["id"],
                download_url=download_url,
                competitor_ad_id=ad["competitor_ad_id"],
                created_at=ad["created_at"],
            )
        )

    return result


@router.get("/{session_id}/{ad_id}/download")
async def download_generated_ad(
    session_id: str,
    ad_id: str,
    supabase: Client = Depends(get_supabase),
):
    """
    Get a fresh download URL for a specific generated ad.

    Returns a signed URL that can be used to download the image.
    """
    storage = get_storage_service(supabase)
    db = get_database_service(supabase)

    # Validate session
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the specific generated ad
    ad = db.get_generated_ad(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Generated ad not found")

    if ad["session_id"] != session_id:
        raise HTTPException(status_code=403, detail="Ad does not belong to this session")

    # Generate a fresh signed URL with longer expiry for download
    download_url = storage.get_signed_url(
        bucket=settings.bucket_generated_ads,
        path=ad["storage_path"],
        expires_in=7200,  # 2 hours for download
    )

    return {"download_url": download_url}
