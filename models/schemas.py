"""
Pydantic schemas for request/response validation.
AdAngle - Framework-driven ad generator.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class AssetType(str, Enum):
    """Type of user-uploaded asset."""
    PRODUCT_IMAGE = "product_image"
    BRAND_IMAGE = "brand_image"
    LOGO = "logo"


# ============================================================================
# Session Schemas
# ============================================================================

class SessionResponse(BaseModel):
    """Schema for session response."""
    id: str
    created_at: datetime


# ============================================================================
# Asset Schemas
# ============================================================================

class AssetUploadResponse(BaseModel):
    """Response after uploading an asset."""
    id: str
    asset_type: AssetType
    storage_path: str
    original_filename: str
    image_url: str


class AssetsUploadResponse(BaseModel):
    """Response after uploading assets."""
    session_id: str
    product_image: AssetUploadResponse
    logo: Optional[AssetUploadResponse] = None
    message: str = "Assets uploaded successfully"


# ============================================================================
# Ad Generation Schemas (AdAngle)
# ============================================================================

class GenerateAdsRequest(BaseModel):
    """Request to generate ads using marketing frameworks."""
    session_id: str = Field(
        ...,
        description="Session ID from asset upload",
    )
    brand_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Brand name",
        examples=["FitFuel", "Nike", "Apple"],
    )
    product: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="What's your product? (one sentence description)",
        examples=["Organic plant-based protein powder with 25g protein per serving"],
    )
    target_customer: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Who is it for? (target audience)",
        examples=["Busy professionals who work out but struggle to get enough protein"],
    )


class GeneratedAd(BaseModel):
    """A single generated ad."""
    hook: str = Field(
        ...,
        description="Scroll-stopping headline (3-8 words) - the only text on the ad",
    )
    visual_concept: str = Field(
        ...,
        description="Description of what the ad image should show",
    )
    image_url: Optional[str] = Field(
        None,
        description="Signed URL to the generated ad image",
    )
    image_path: Optional[str] = Field(
        None,
        description="Storage path to the generated ad image",
    )


class GenerateAdsResponse(BaseModel):
    """Response containing 5 generated ads with different frameworks."""
    session_id: str
    product: str
    ads: List[GeneratedAd] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Up to 5 ads using different psychological frameworks",
    )
    generation_time_ms: int = Field(
        ...,
        description="Time taken to generate ads in milliseconds",
    )
    message: str = "Ads generated successfully"


# ============================================================================
# Stored Ad Schema (for database)
# ============================================================================

class StoredAdSet(BaseModel):
    """Schema for a stored ad set in the database (10 ads)."""
    id: str
    session_id: str
    brand_name: str
    product: str
    target_customer: str

    # Store ads as JSON array instead of individual fields
    ads: List[dict]  # Array of ad objects with framework, hook, body, cta, visual_concept, image_path

    generation_time_ms: int
    created_at: datetime


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: Optional[str] = None
