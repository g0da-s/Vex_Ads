"""
Database operations for Supabase PostgreSQL tables.
Provides CRUD operations for sessions, assets, competitor ads, and generated ads.
"""

from typing import Optional, List
from datetime import datetime
from supabase import Client


class DatabaseService:
    """Service for database operations via Supabase."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    # =========================================================================
    # Sessions
    # =========================================================================

    def create_session(self) -> dict:
        """
        Create a new session.

        Returns:
            Created session record with id and created_at
        """
        response = self.supabase.table("sessions").insert({}).execute()
        return response.data[0]

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get a session by ID.

        Args:
            session_id: UUID of the session

        Returns:
            Session record or None if not found
        """
        response = (
            self.supabase.table("sessions")
            .select("*")
            .eq("id", session_id)
            .execute()
        )
        return response.data[0] if response.data else None

    # =========================================================================
    # User Assets
    # =========================================================================

    def create_user_asset(
        self,
        session_id: str,
        asset_type: str,
        storage_path: str,
        original_filename: str,
    ) -> dict:
        """
        Create a user asset record.

        Args:
            session_id: Session UUID
            asset_type: 'product_image' or 'logo'
            storage_path: Path in Supabase Storage
            original_filename: Original uploaded filename

        Returns:
            Created asset record
        """
        response = (
            self.supabase.table("user_assets")
            .insert(
                {
                    "session_id": session_id,
                    "asset_type": asset_type,
                    "storage_path": storage_path,
                    "original_filename": original_filename,
                }
            )
            .execute()
        )
        return response.data[0]

    def get_user_assets(self, session_id: str) -> List[dict]:
        """
        Get all assets for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of asset records
        """
        response = (
            self.supabase.table("user_assets")
            .select("*")
            .eq("session_id", session_id)
            .execute()
        )
        return response.data

    def get_user_asset_by_type(
        self, session_id: str, asset_type: str
    ) -> Optional[dict]:
        """
        Get a specific asset type for a session.

        Args:
            session_id: Session UUID
            asset_type: 'product_image' or 'logo'

        Returns:
            Asset record or None
        """
        response = (
            self.supabase.table("user_assets")
            .select("*")
            .eq("session_id", session_id)
            .eq("asset_type", asset_type)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    # =========================================================================
    # Competitor Ads
    # =========================================================================

    def create_competitor_ad(
        self,
        session_id: str,
        page_id: str,
        ad_id: str,
        page_name: Optional[str] = None,
        ad_text: Optional[str] = None,
        original_image_url: Optional[str] = None,
        storage_path: Optional[str] = None,
        impressions_lower: Optional[int] = None,
        impressions_upper: Optional[int] = None,
        ad_delivery_start: Optional[datetime] = None,
        is_active: bool = False,
        winner_score: float = 0.0,
    ) -> dict:
        """
        Create a competitor ad record.

        Args:
            session_id: Session UUID
            page_id: Meta page ID
            ad_id: Meta ad ID
            page_name: Advertiser page name
            ad_text: Ad creative text
            original_image_url: Direct image URL from Meta API
            storage_path: Path in Supabase Storage (downloaded copy)
            impressions_lower: Lower bound of impressions
            impressions_upper: Upper bound of impressions
            ad_delivery_start: When the ad started running

        Returns:
            Created competitor ad record
        """
        data = {
            "session_id": session_id,
            "page_id": page_id,
            "ad_id": ad_id,
            "page_name": page_name,
            "ad_text": ad_text,
            "original_image_url": original_image_url,
            "storage_path": storage_path,
            "impressions_lower": impressions_lower,
            "impressions_upper": impressions_upper,
            "is_active": is_active,
            "winner_score": winner_score,
        }

        if ad_delivery_start:
            data["ad_delivery_start"] = ad_delivery_start.isoformat()

        response = self.supabase.table("competitor_ads").insert(data).execute()
        return response.data[0]

    def get_competitor_ads(self, session_id: str) -> List[dict]:
        """
        Get all competitor ads for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of competitor ad records
        """
        response = (
            self.supabase.table("competitor_ads")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def get_competitor_ad(self, ad_id: str) -> Optional[dict]:
        """
        Get a competitor ad by ID.

        Args:
            ad_id: Competitor ad UUID (our internal ID, not Meta's ad_id)

        Returns:
            Competitor ad record or None
        """
        response = (
            self.supabase.table("competitor_ads")
            .select("*")
            .eq("id", ad_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_competitor_ad_by_meta_id(
        self, session_id: str, meta_ad_id: str
    ) -> Optional[dict]:
        """
        Check if a competitor ad already exists for this session.

        Args:
            session_id: Session UUID
            meta_ad_id: Meta's ad_id (ad_archive_id from SearchAPI)

        Returns:
            Existing competitor ad record or None
        """
        response = (
            self.supabase.table("competitor_ads")
            .select("*")
            .eq("session_id", session_id)
            .eq("ad_id", meta_ad_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    # =========================================================================
    # Generated Ads
    # =========================================================================

    def create_generated_ad(
        self,
        session_id: str,
        competitor_ad_id: str,
        storage_path: str,
        prompt_used: Optional[str] = None,
    ) -> dict:
        """
        Create a generated ad record.

        Args:
            session_id: Session UUID
            competitor_ad_id: UUID of the competitor ad used as reference
            storage_path: Path in Supabase Storage
            prompt_used: The prompt used for generation

        Returns:
            Created generated ad record
        """
        response = (
            self.supabase.table("generated_ads")
            .insert(
                {
                    "session_id": session_id,
                    "competitor_ad_id": competitor_ad_id,
                    "storage_path": storage_path,
                    "prompt_used": prompt_used,
                }
            )
            .execute()
        )
        return response.data[0]

    def get_generated_ads(self, session_id: str) -> List[dict]:
        """
        Get all generated ads for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of generated ad records
        """
        response = (
            self.supabase.table("generated_ads")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def get_generated_ad(self, ad_id: str) -> Optional[dict]:
        """
        Get a generated ad by ID.

        Args:
            ad_id: Generated ad UUID

        Returns:
            Generated ad record or None
        """
        response = (
            self.supabase.table("generated_ads")
            .select("*")
            .eq("id", ad_id)
            .execute()
        )
        return response.data[0] if response.data else None


def get_database_service(supabase: Client) -> DatabaseService:
    """Factory function to create DatabaseService instance."""
    return DatabaseService(supabase)
