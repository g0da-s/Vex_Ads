"""
Supabase Storage service for file operations.
Handles uploads, downloads, and signed URL generation.
"""

import uuid
from typing import Optional
from supabase import Client

from config import get_settings

settings = get_settings()


class StorageService:
    """Service for interacting with Supabase Storage."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def _get_content_type(self, filename: str) -> str:
        """Determine content type from filename extension."""
        extension = filename.lower().split(".")[-1] if "." in filename else ""
        content_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
        }
        return content_types.get(extension, "application/octet-stream")

    def upload_file(
        self,
        bucket: str,
        file_bytes: bytes,
        original_filename: str,
        folder: Optional[str] = None,
    ) -> dict:
        """
        Upload a file to Supabase Storage.

        Args:
            bucket: Storage bucket name
            file_bytes: File content as bytes
            original_filename: Original filename for extension detection
            folder: Optional folder path within bucket

        Returns:
            dict with 'path' (storage path) and 'id' (unique file id)
        """
        # Generate unique filename to avoid collisions
        file_id = str(uuid.uuid4())
        extension = original_filename.split(".")[-1] if "." in original_filename else "bin"
        unique_filename = f"{file_id}.{extension}"

        # Build full path
        storage_path = f"{folder}/{unique_filename}" if folder else unique_filename

        # Get content type
        content_type = self._get_content_type(original_filename)

        # Upload to Supabase
        self.supabase.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type},
        )

        return {
            "path": storage_path,
            "id": file_id,
            "bucket": bucket,
            "content_type": content_type,
        }

    def get_signed_url(
        self,
        bucket: str,
        path: str,
        expires_in: Optional[int] = None,
    ) -> str:
        """
        Generate a signed URL for private file access.

        Args:
            bucket: Storage bucket name
            path: File path within bucket
            expires_in: URL expiry time in seconds (default from settings)

        Returns:
            Signed URL string
        """
        if expires_in is None:
            expires_in = settings.signed_url_expiry_seconds

        response = self.supabase.storage.from_(bucket).create_signed_url(
            path=path,
            expires_in=expires_in,
        )
        return response["signedURL"]

    def download_file(self, bucket: str, path: str) -> bytes:
        """
        Download a file from Supabase Storage.

        Args:
            bucket: Storage bucket name
            path: File path within bucket

        Returns:
            File content as bytes
        """
        response = self.supabase.storage.from_(bucket).download(path)
        return response

    def delete_file(self, bucket: str, path: str) -> bool:
        """
        Delete a file from Supabase Storage.

        Args:
            bucket: Storage bucket name
            path: File path within bucket

        Returns:
            True if deleted successfully
        """
        self.supabase.storage.from_(bucket).remove([path])
        return True

    def list_files(self, bucket: str, folder: Optional[str] = None) -> list:
        """
        List files in a bucket or folder.

        Args:
            bucket: Storage bucket name
            folder: Optional folder path to list

        Returns:
            List of file objects
        """
        return self.supabase.storage.from_(bucket).list(path=folder or "")


def get_storage_service(supabase: Client) -> StorageService:
    """Factory function to create StorageService instance."""
    return StorageService(supabase)
