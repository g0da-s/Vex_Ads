"""
Ad generation routes for AdAngle.
Generates 3 ad concepts using different marketing psychology frameworks.
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from supabase import Client

from api.dependencies import get_supabase
from services.visual_bible_creator import create_visual_bible
from services.creative_director import generate_ad_concepts
from services.image_generator import generate_ad_image
from services.image_compositor import create_final_ad_image
from services.storage import get_storage_service
from models.database import get_database_service
from models.schemas import (
    GenerateAdsRequest,
    GenerateAdsResponse,
    GeneratedAd,
)
from config import get_settings

settings = get_settings()

router = APIRouter(prefix="/generate", tags=["Generation"])


@router.post("", response_model=GenerateAdsResponse)
async def generate_ad_angles(
    request: GenerateAdsRequest,
    supabase: Client = Depends(get_supabase),
):
    """
    Generate 5 diverse ad concepts using Visual Bible workflow.

    **New Workflow:**
    1. **Visual Bible Creation** - Analyzes brand images to extract style guide
    2. **Creative Director** - Generates 5 unique ad concepts with visual prompts and copy
    3. **Parallel Image Generation** - Generates 5 on-brand images using Gemini 3 Pro Image
    4. **Text Compositing** - Overlays marketing copy on each image

    **Input:**
    - `session_id`: From previous asset upload (validates user has uploaded brand images)
    - `brand_name`: Brand name
    - `product`: What you sell (e.g., "Ergonomic office chair")
    - `target_customer`: Who buys it (e.g., "Remote workers with back pain")

    **Output:**
    - 5 diverse ad concepts, each with:
      - Unique visual (AI-generated, brand-consistent)
      - Marketing copy (hook, body, CTA)
      - Full-resolution ad image (1080x1080) with text overlay and logo
      - Different marketing angles and frameworks

    **Note:** Generates complete visual ads ready to download and run.
    """
    import time as time_module
    start_time = time_module.time()

    # Initialize services
    db = get_database_service(supabase)
    storage = get_storage_service(supabase)

    # Validate session exists
    session = db.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload your brand images first.",
        )

    try:
        # Step 1: Get user's uploaded brand images (3-5 images)
        brand_image_assets = db.get_user_assets_by_type(request.session_id, "brand_image")
        if not brand_image_assets or len(brand_image_assets) < 1:
            raise HTTPException(
                status_code=400,
                detail="No brand images found. Please upload 3-5 brand/product images first."
            )

        # Download all brand images
        brand_image_bytes_list = []
        for asset in brand_image_assets[:5]:  # Max 5 images
            try:
                img_bytes = storage.download_file(
                    settings.bucket_user_assets,
                    asset["storage_path"]
                )
                brand_image_bytes_list.append(img_bytes)
            except Exception as e:
                print(f"Error downloading brand image: {e}")
                continue

        if not brand_image_bytes_list:
            raise HTTPException(
                status_code=400,
                detail="Failed to download brand images"
            )

        # Get logo (required)
        logo_asset = db.get_user_asset_by_type(request.session_id, "logo")
        logo_bytes = None
        if logo_asset:
            try:
                logo_bytes = storage.download_file(
                    settings.bucket_user_assets,
                    logo_asset["storage_path"]
                )
            except Exception as e:
                print(f"Error downloading logo: {e}")

        if not logo_bytes:
            raise HTTPException(
                status_code=400,
                detail="Logo is required. Please upload a logo."
            )

        # Get product image (required)
        product_image_asset = db.get_user_asset_by_type(request.session_id, "product_image")
        product_image_bytes = None
        if product_image_asset:
            try:
                product_image_bytes = storage.download_file(
                    settings.bucket_user_assets,
                    product_image_asset["storage_path"]
                )
            except Exception as e:
                print(f"Error downloading product image: {e}")

        if not product_image_bytes:
            raise HTTPException(
                status_code=400,
                detail="Product image is required. Please upload a product image."
            )

        # Step 2: Create Visual Bible
        print(f"Creating visual bible from {len(brand_image_bytes_list)} brand images...")
        visual_bible = await create_visual_bible(
            brand_images=brand_image_bytes_list,
            brand_name=request.brand_name,
            product_description=request.product
        )
        print(f"Visual Bible created: {visual_bible['style_directive'][:100]}...")

        # Step 3: Generate 5 ad concepts with Creative Director
        print("Generating 5 ad concepts with Creative Director...")
        ad_concepts = await generate_ad_concepts(
            visual_bible=visual_bible,
            brand_name=request.brand_name,
            product_description=request.product,
            target_customer=request.target_customer
        )
        print(f"Generated {len(ad_concepts)} ad concepts")

        # Step 4: Generate images and composite for all 5 ads in parallel
        async def generate_and_composite_ad(concept, index):
            """Generate image and composite ad."""
            try:
                print(f"Generating ad {index + 1}/{len(ad_concepts)}...")

                # Generate AI image featuring the actual product (background only, no text)
                image_bytes, gen_time = await generate_ad_image(
                    visual_concept=concept["visual_prompt"],
                    product=request.product,
                    style_directive=visual_bible["style_directive"],
                    product_image_bytes=product_image_bytes,
                )

                # Skip compositor - use raw LLM-generated image
                final_image_bytes = image_bytes

                # # Composite final ad with hook text overlay
                # final_image_bytes = create_final_ad_image(
                #     background_bytes=image_bytes,
                #     hook=concept["hook"],
                #     logo_bytes=logo_bytes,
                # )

                # Upload to storage
                upload_result = storage.upload_file(
                    bucket=settings.bucket_generated_ads,
                    file_bytes=final_image_bytes,
                    original_filename=f"ad_{index + 1}.png",
                    folder=request.session_id,
                )

                # Generate signed URL
                image_url = storage.get_signed_url(
                    bucket=settings.bucket_generated_ads,
                    path=upload_result["path"],
                    expires_in=86400,
                )

                # Create GeneratedAd object
                ad = GeneratedAd(
                    hook=concept["hook"],
                    visual_concept=concept["visual_prompt"],
                    image_url=image_url,
                    image_path=upload_result["path"],
                )

                print(f"Ad {index + 1} generated successfully")
                return ad, gen_time

            except Exception as e:
                print(f"Error generating ad {index + 1}: {e}")
                import traceback
                traceback.print_exc()

                # Create ad without image
                ad = GeneratedAd(
                    hook=concept.get("hook", ""),
                    visual_concept=concept.get("visual_prompt", ""),
                    image_url=None,
                    image_path=None,
                )
                return ad, 0

        # Generate all 5 ads in parallel
        results = await asyncio.gather(*[
            generate_and_composite_ad(concept, i) for i, concept in enumerate(ad_concepts)
        ])

        ads = [result[0] for result in results]
        image_gen_times = [result[1] for result in results]

        total_generation_time_ms = int((time_module.time() - start_time) * 1000)

        # Step 5: Save to database
        db.create_generated_ad_set(
            session_id=request.session_id,
            brand_name=request.brand_name,
            product=request.product,
            target_customer=request.target_customer,
            ads=ads,
            generation_time_ms=total_generation_time_ms,
        )

        print(f"All {len(ads)} ads generated in {total_generation_time_ms}ms")

        return GenerateAdsResponse(
            session_id=request.session_id,
            product=request.product,
            ads=ads,
            generation_time_ms=total_generation_time_ms,
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


@router.get("/download/{session_id}/{ad_number}")
async def download_ad_image(
    session_id: str,
    ad_number: int,
    supabase: Client = Depends(get_supabase),
):
    """
    Get a download URL for a specific ad image.

    Args:
        session_id: Session UUID
        ad_number: Ad number (1-10)

    Returns:
        Signed download URL that forces browser download
    """
    if ad_number not in range(1, 11):
        raise HTTPException(status_code=400, detail="ad_number must be between 1 and 10")

    db = get_database_service(supabase)
    storage = get_storage_service(supabase)

    # Get the most recent ad set for this session
    ad_sets = db.get_generated_ad_sets(session_id)
    if not ad_sets:
        raise HTTPException(status_code=404, detail="No ad sets found for this session")

    ad_set = ad_sets[0]  # Most recent

    # Get the image path for the requested ad
    image_path_key = f"ad{ad_number}_image_path"
    image_path = ad_set.get(image_path_key)

    if not image_path:
        raise HTTPException(
            status_code=404,
            detail=f"Ad {ad_number} image not found"
        )

    # Generate signed URL with download header
    download_filename = f"adangle_ad_{ad_number}_{ad_set['id'][:8]}.png"
    download_url = storage.get_signed_url(
        bucket=settings.bucket_generated_ads,
        path=image_path,
        expires_in=300,  # 5 minutes
        download=True,
        download_filename=download_filename,
    )

    return {
        "download_url": download_url,
        "filename": download_filename,
    }
