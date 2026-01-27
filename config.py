"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Supabase
    supabase_url: str
    supabase_key: str

    # Anthropic Claude API (for ad copy generation)
    anthropic_api_key: str

    # Google Gemini (optional - for image generation in Phase 2)
    gemini_api_key: str = ""

    # Application
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # Storage
    max_file_size_mb: int = 10
    signed_url_expiry_seconds: int = 3600

    # Supabase Storage bucket names
    bucket_user_assets: str = "user-assets"
    bucket_generated_ads: str = "generated-ads"

    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size to bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
