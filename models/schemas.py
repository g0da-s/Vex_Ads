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
    LOGO = "logo"


class AdFramework(str, Enum):
    """Marketing psychology frameworks for ad generation."""
    PAS = "Problem-Agitate-Solution"
    SOCIAL_PROOF = "Social Proof"
    TRANSFORMATION = "Transformation"


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
    product: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="What do you sell? (product or service name)",
        examples=["Organic protein powder", "Online yoga classes", "Project management SaaS"],
    )
    target_customer: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Who buys it? (target audience)",
        examples=["Busy professionals who want to stay fit", "Beginners looking to reduce stress"],
    )
    main_benefit: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="What problem does it solve? (key benefit)",
        examples=["Build muscle without spending hours cooking", "Find calm in just 10 minutes a day"],
    )


class GeneratedAd(BaseModel):
    """A single generated ad using a specific framework."""
    framework: AdFramework = Field(
        ...,
        description="The marketing psychology framework used",
    )
    hook: str = Field(
        ...,
        description="Attention-grabbing headline (5-8 words)",
    )
    body: str = Field(
        ...,
        description="Main ad copy (2-3 sentences)",
    )
    cta: str = Field(
        ...,
        description="Call-to-action text (3-5 words)",
    )
    visual_concept: str = Field(
        ...,
        description="Description of what the ad image should show",
    )


class GenerateAdsResponse(BaseModel):
    """Response containing 3 generated ads with different frameworks."""
    session_id: str
    product: str
    ads: List[GeneratedAd] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Three ads using different psychological frameworks",
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
    """Schema for a stored ad set in the database."""
    id: str
    session_id: str
    product: str
    target_customer: str
    main_benefit: str

    # Ad 1 - PAS
    ad1_framework: str
    ad1_hook: str
    ad1_body: str
    ad1_cta: str
    ad1_visual_concept: str

    # Ad 2 - Social Proof
    ad2_framework: str
    ad2_hook: str
    ad2_body: str
    ad2_cta: str
    ad2_visual_concept: str

    # Ad 3 - Transformation
    ad3_framework: str
    ad3_hook: str
    ad3_body: str
    ad3_cta: str
    ad3_visual_concept: str

    generation_time_ms: int
    created_at: datetime


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: Optional[str] = None
