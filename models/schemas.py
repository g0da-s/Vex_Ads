"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class AssetType(str, Enum):
    """Type of user-uploaded asset."""
    PRODUCT_IMAGE = "product_image"
    LOGO = "logo"


# ============================================================================
# Base Models
# ============================================================================

class TimestampMixin(BaseModel):
    """Mixin for created_at timestamp."""
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Session Schemas
# ============================================================================

class SessionCreate(BaseModel):
    """Schema for creating a new session."""
    pass  # No fields needed, auto-generated


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
    image_url: str  # Signed URL for viewing


class AssetsUploadResponse(BaseModel):
    """Response after uploading both assets."""
    session_id: str
    product_image: AssetUploadResponse
    logo: AssetUploadResponse
    message: str = "Assets uploaded successfully"


# ============================================================================
# Competitor Ad Schemas
# ============================================================================

class CompetitorAnalyzeRequest(BaseModel):
    """Request to analyze competitor ads."""
    session_id: str
    ad_library_url: str = Field(
        ...,
        description="Facebook Ad Library URL with view_all_page_id parameter",
        examples=["https://www.facebook.com/ads/library/?view_all_page_id=123456789"],
    )


class CompetitorAdResponse(BaseModel):
    """Schema for a single competitor ad."""
    id: str
    page_id: str
    page_name: Optional[str] = None
    ad_id: str
    ad_text: Optional[str] = None
    image_url: str  # Signed URL for viewing
    impressions_lower: Optional[int] = None
    impressions_upper: Optional[int] = None
    ad_delivery_start: Optional[datetime] = None
    is_active: bool = False
    days_running: Optional[int] = None
    winner_score: float = 0.0  # Higher = more likely a winning ad


class CompetitorAnalyzeResponse(BaseModel):
    """Response after analyzing competitor ads."""
    session_id: str
    page_id: str
    ads_found: int
    ads_downloaded: int
    competitor_ads: List[CompetitorAdResponse]
    message: str = "Competitor ads analyzed successfully"


# ============================================================================
# Ad Generation Schemas
# ============================================================================

class GenerateAdsRequest(BaseModel):
    """Request to generate new ads."""
    session_id: str
    competitor_ad_id: Optional[str] = Field(
        default=None,
        description="Optional: specific competitor ad ID. If not provided, uses top winners automatically.",
    )
    num_variations: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Number of ad variations to generate per winner (1-3)",
    )
    product_description: Optional[str] = Field(
        default=None,
        description="Optional description of the product for better results",
    )
    max_winners: int = Field(
        default=3,
        ge=1,
        le=5,
        description="How many top winners to use for generation (1-5)",
    )


class GeneratedAdResponse(BaseModel):
    """Schema for a single generated ad."""
    id: str
    download_url: str  # Signed URL for download
    competitor_ad_id: str
    created_at: datetime


class GenerateAdsResponse(BaseModel):
    """Response after generating ads."""
    session_id: str
    generated_count: int
    generated_ads: List[GeneratedAdResponse]
    message: str = "Ads generated successfully"


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""
    detail: List[dict]
