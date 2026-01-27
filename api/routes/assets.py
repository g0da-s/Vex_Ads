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
    product_image: Annotated[
        UploadFile,
        File(description="Product image file (JPEG, PNG, GIF, or WebP)"),
    ],
    logo: Annotated[
        Optional[UploadFile],
        File(description="Brand logo file (optional - JPEG, PNG, GIF, or WebP)"),
    ] = None,
    supabase: Client = Depends(get_supabase),
):
    """
    Upload product image and optional logo.

    Creates a new session and stores assets in Supabase Storage.
    Returns session_id for use in subsequent API calls.

    **File Requirements:**
    - Supported formats: JPEG, PNG, GIF, WebP
    - Maximum file size: 10MB per file
    - Product image: Required
    - Logo: Optional (for MVP, can be added later)
    """
    # Validate product image (required)
    validate_image_file(product_image, "product_image")

    # Validate logo if provided
    if logo and logo.filename:
        validate_image_file(logo, "logo")

    # Initialize services
    storage = get_storage_service(supabase)
    db = get_database_service(supabase)

    try:
        # Create a new session
        session = db.create_session()
        session_id = session["id"]

        # Read product image
        product_bytes = await product_image.read()

        # Check file size after reading
        if len(product_bytes) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Product image exceeds maximum size of {settings.max_file_size_mb}MB",
            )

        # Upload product image to storage
        product_upload = storage.upload_file(
            bucket=settings.bucket_user_assets,
            file_bytes=product_bytes,
            original_filename=product_image.filename or "product.jpg",
            folder=session_id,
        )

        # Save product asset to database
        product_asset = db.create_user_asset(
            session_id=session_id,
            asset_type=AssetType.PRODUCT_IMAGE.value,
            storage_path=product_upload["path"],
            original_filename=product_image.filename or "product.jpg",
        )

        # Generate signed URL for product image
        product_url = storage.get_signed_url(
            bucket=settings.bucket_user_assets,
            path=product_upload["path"],
        )

        # Build product image response
        product_response = AssetUploadResponse(
            id=product_asset["id"],
            asset_type=AssetType.PRODUCT_IMAGE,
            storage_path=product_upload["path"],
            original_filename=product_image.filename or "product.jpg",
            image_url=product_url,
        )

        # Handle optional logo
        logo_response = None
        if logo and logo.filename:
            logo_bytes = await logo.read()

            if len(logo_bytes) > settings.max_file_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Logo exceeds maximum size of {settings.max_file_size_mb}MB",
                )

            # Upload logo to storage
            logo_upload = storage.upload_file(
                bucket=settings.bucket_user_assets,
                file_bytes=logo_bytes,
                original_filename=logo.filename or "logo.png",
                folder=session_id,
            )

            # Save logo asset to database
            logo_asset = db.create_user_asset(
                session_id=session_id,
                asset_type=AssetType.LOGO.value,
                storage_path=logo_upload["path"],
                original_filename=logo.filename or "logo.png",
            )

            # Generate signed URL for logo
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
