"""
Ad generation routes for AdAngle.
Generates 3 ad concepts using different marketing psychology frameworks.
"""

from fastapi import APIRouter, HTTPException, Depends
from supabase import Client

from api.dependencies import get_supabase
from services.ai_generator import generate_ads
from models.database import get_database_service
from models.schemas import (
    GenerateAdsRequest,
    GenerateAdsResponse,
)

router = APIRouter(prefix="/generate", tags=["Generation"])


@router.post("", response_model=GenerateAdsResponse)
async def generate_ad_angles(
    request: GenerateAdsRequest,
    supabase: Client = Depends(get_supabase),
):
    """
    Generate 3 ad concepts using different marketing psychology frameworks.

    **Frameworks Used:**
    1. **Problem-Agitate-Solution (PAS)** - Calls out pain, agitates it, offers solution
    2. **Social Proof** - Leads with impressive numbers/results, invites to join
    3. **Transformation** - Shows current state vs aspirational future state

    **Input:**
    - `session_id`: From previous asset upload (validates user has uploaded images)
    - `product`: What you sell (e.g., "Organic protein powder")
    - `target_customer`: Who buys it (e.g., "Busy professionals who want to stay fit")
    - `main_benefit`: What problem it solves (e.g., "Build muscle without spending hours cooking")

    **Output:**
    - 3 psychologically different ad concepts, each with:
      - Hook (5-8 words)
      - Body (2-3 sentences)
      - CTA (3-5 words)
      - Visual concept (what the image should show)

    **Note:** This is text-only generation. Image generation is Phase 2.
    """
    # Initialize services
    db = get_database_service(supabase)

    # Validate session exists
    session = db.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload your product image first.",
        )

    try:
        # Generate ads using Claude
        ads, generation_time_ms = await generate_ads(
            product=request.product,
            target_customer=request.target_customer,
            main_benefit=request.main_benefit,
        )

        if len(ads) < 3:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate all 3 ad concepts. Please try again.",
            )

        # Save to database
        db.create_generated_ad_set(
            session_id=request.session_id,
            product=request.product,
            target_customer=request.target_customer,
            main_benefit=request.main_benefit,
            ads=ads,
            generation_time_ms=generation_time_ms,
        )

        return GenerateAdsResponse(
            session_id=request.session_id,
            product=request.product,
            ads=ads,
            generation_time_ms=generation_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate ads: {str(e)}",
        )


@router.get("/{session_id}")
async def get_generated_ads(
    session_id: str,
    supabase: Client = Depends(get_supabase),
):
    """
    Get all generated ad sets for a session.

    Returns previously generated ad sets for this session.
    """
    db = get_database_service(supabase)

    # Validate session
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get generated ad sets
    ad_sets = db.get_generated_ad_sets(session_id)

    return {"session_id": session_id, "ad_sets": ad_sets}
