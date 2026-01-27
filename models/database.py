"""
Database operations for Supabase PostgreSQL tables.
Provides CRUD operations for sessions, assets, and generated ad sets.
"""

from typing import Optional, List
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
    # Generated Ad Sets (AdAngle)
    # =========================================================================

    def create_generated_ad_set(
        self,
        session_id: str,
        product: str,
        target_customer: str,
        main_benefit: str,
        ads: list,
        generation_time_ms: int,
    ) -> dict:
        """
        Create a generated ad set record with all 3 framework ads.

        Args:
            session_id: Session UUID
            product: Product/service name
            target_customer: Target audience description
            main_benefit: Key benefit/problem solved
            ads: List of 3 GeneratedAd objects
            generation_time_ms: Time taken to generate

        Returns:
            Created ad set record
        """
        # Extract data from the 3 ads
        ad1 = ads[0] if len(ads) > 0 else None
        ad2 = ads[1] if len(ads) > 1 else None
        ad3 = ads[2] if len(ads) > 2 else None

        data = {
            "session_id": session_id,
            "product": product,
            "target_customer": target_customer,
            "main_benefit": main_benefit,
            "generation_time_ms": generation_time_ms,
        }

        # Ad 1 - PAS
        if ad1:
            data["ad1_framework"] = ad1.framework.value
            data["ad1_hook"] = ad1.hook
            data["ad1_body"] = ad1.body
            data["ad1_cta"] = ad1.cta
            data["ad1_visual_concept"] = ad1.visual_concept

        # Ad 2 - Social Proof
        if ad2:
            data["ad2_framework"] = ad2.framework.value
            data["ad2_hook"] = ad2.hook
            data["ad2_body"] = ad2.body
            data["ad2_cta"] = ad2.cta
            data["ad2_visual_concept"] = ad2.visual_concept

        # Ad 3 - Transformation
        if ad3:
            data["ad3_framework"] = ad3.framework.value
            data["ad3_hook"] = ad3.hook
            data["ad3_body"] = ad3.body
            data["ad3_cta"] = ad3.cta
            data["ad3_visual_concept"] = ad3.visual_concept

        response = self.supabase.table("generated_ad_sets").insert(data).execute()
        return response.data[0]

    def get_generated_ad_sets(self, session_id: str) -> List[dict]:
        """
        Get all generated ad sets for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of ad set records
        """
        response = (
            self.supabase.table("generated_ad_sets")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def get_generated_ad_set(self, ad_set_id: str) -> Optional[dict]:
        """
        Get a generated ad set by ID.

        Args:
            ad_set_id: Ad set UUID

        Returns:
            Ad set record or None
        """
        response = (
            self.supabase.table("generated_ad_sets")
            .select("*")
            .eq("id", ad_set_id)
            .execute()
        )
        return response.data[0] if response.data else None


def get_database_service(supabase: Client) -> DatabaseService:
    """Factory function to create DatabaseService instance."""
    return DatabaseService(supabase)
