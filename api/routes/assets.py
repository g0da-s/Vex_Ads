"""
Asset upload routes for AdAngle.
Handles product image and optional logo uploads.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from supabase import Client

from api.dependencies import get_supabase
from services.storage import get_storage_service
from models.database import get_database_service
from models.schemas import AssetsUploadResponse, AssetUploadResponse, AssetType
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/assets", tags=["Assets"])

# Allowed image MIME types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}


def validate_image_file(file: UploadFile, field_name: str) -> None:
    """
    Validate an uploaded image file.

    Args:
        file: The uploaded file
        field_name: Name of the field for error messages

    Raises:
        HTTPException: If validation fails
    """
    # Check content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type for {field_name}. "
            f"Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    # Check file size (if available)
    if hasattr(file, "size") and file.size:
        if file.size > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File {field_name} exceeds maximum size of {settings.max_file_size_mb}MB",
            )


@router.post("/upload", response_model=AssetsUploadResponse)
async def upload_assets(
    logo: Annotated[
        UploadFile,
        File(description="Brand logo file (JPEG, PNG, GIF, or WebP)"),
    ],
    product_image: Annotated[
        UploadFile,
        File(description="Product image file (JPEG, PNG, GIF, or WebP)"),
    ],
    brand_image: Annotated[
        list[UploadFile],
        File(description="3-5 brand/style image files (JPEG, PNG, GIF, or WebP)"),
    ],
    supabase: Client = Depends(get_supabase),
):
    """
    Upload logo, product image, and 3-5 brand images.

    Creates a new session and stores assets in Supabase Storage.
    Returns session_id for use in subsequent API calls.

    **File Requirements:**
    - Supported formats: JPEG, PNG, GIF, WebP
    - Maximum file size: 10MB per file
    - Logo: Required
    - Product image: Required (featured in all ads)
    - Brand images: 3-5 required (for Visual Bible style guide)
    """
    # Validate logo (required)
    if not logo or not logo.filename:
        raise HTTPException(
            status_code=400,
            detail="Logo is required"
        )
    validate_image_file(logo, "logo")

    # Validate product image (required)
    if not product_image or not product_image.filename:
        raise HTTPException(
            status_code=400,
            detail="Product image is required"
        )
    validate_image_file(product_image, "product_image")

    # Validate we have 3-5 brand images
    if not brand_image or len(brand_image) < 3 or len(brand_image) > 5:
        raise HTTPException(
            status_code=400,
            detail="Please upload 3-5 brand images"
        )

    # Validate all brand images
    for img in brand_image:
        validate_image_file(img, "brand_image")

    # Initialize services
    storage = get_storage_service(supabase)
    db = get_database_service(supabase)

    try:
        # Create a new session
        session = db.create_session()
        session_id = session["id"]

        # Upload logo
        logo_bytes = await logo.read()
        if len(logo_bytes) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Logo exceeds maximum size of {settings.max_file_size_mb}MB",
            )

        logo_upload = storage.upload_file(
            bucket=settings.bucket_user_assets,
            file_bytes=logo_bytes,
            original_filename=logo.filename or "logo.png",
            folder=session_id,
        )

        logo_asset = db.create_user_asset(
            session_id=session_id,
            asset_type=AssetType.LOGO.value,
            storage_path=logo_upload["path"],
            original_filename=logo.filename or "logo.png",
        )

        logo_url = storage.get_signed_url(
            bucket=settings.bucket_user_assets,
            path=logo_upload["path"],
        )

        logo_response = AssetUploadResponse(
            id=logo_asset["id"],
            asset_type=AssetType.LOGO,
            storage_path=logo_upload["path"],
            original_filename=logo.filename or "logo.png",
            image_url=logo_url,
        )

        # Upload product image
        product_bytes = await product_image.read()
        if len(product_bytes) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Product image exceeds maximum size of {settings.max_file_size_mb}MB",
            )

        product_upload = storage.upload_file(
            bucket=settings.bucket_user_assets,
            file_bytes=product_bytes,
            original_filename=product_image.filename or "product.jpg",
            folder=session_id,
        )

        product_asset = db.create_user_asset(
            session_id=session_id,
            asset_type=AssetType.PRODUCT_IMAGE.value,
            storage_path=product_upload["path"],
            original_filename=product_image.filename or "product.jpg",
        )

        product_url = storage.get_signed_url(
            bucket=settings.bucket_user_assets,
            path=product_upload["path"],
        )

        product_response = AssetUploadResponse(
            id=product_asset["id"],
            asset_type=AssetType.PRODUCT_IMAGE,
            storage_path=product_upload["path"],
            original_filename=product_image.filename or "product.jpg",
            image_url=product_url,
        )

        # Upload all brand images
        brand_image_responses = []
        for idx, img in enumerate(brand_image):
            # Read image
            img_bytes = await img.read()

            # Check file size
            if len(img_bytes) > settings.max_file_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Brand image {idx + 1} exceeds maximum size of {settings.max_file_size_mb}MB",
                )

            # Upload to storage
            upload_result = storage.upload_file(
                bucket=settings.bucket_user_assets,
                file_bytes=img_bytes,
                original_filename=img.filename or f"brand_{idx + 1}.jpg",
                folder=session_id,
            )

            # Save to database
            asset = db.create_user_asset(
                session_id=session_id,
                asset_type="brand_image",
                storage_path=upload_result["path"],
                original_filename=img.filename or f"brand_{idx + 1}.jpg",
            )

            # Generate signed URL
            img_url = storage.get_signed_url(
                bucket=settings.bucket_user_assets,
                path=upload_result["path"],
            )

            brand_image_responses.append(AssetUploadResponse(
                id=asset["id"],
                asset_type=AssetType.BRAND_IMAGE,
                storage_path=upload_result["path"],
                original_filename=img.filename or f"brand_{idx + 1}.jpg",
                image_url=img_url,
            ))

        return AssetsUploadResponse(
            session_id=session_id,
            product_image=product_response,
            logo=logo_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload assets: {str(e)}",
        )
