"""
Meta Ad Library API service via SearchAPI.
Fetches competitor ads and downloads ad images.
"""

import re
from typing import Optional, List
from datetime import datetime, timezone
import httpx

from config import get_settings

settings = get_settings()

# SearchAPI endpoint
SEARCHAPI_URL = "https://www.searchapi.io/api/v1/search"


def extract_page_id_or_query(ad_library_url: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract page_id or search query from input.

    Supports:
    - Ad Library URLs with page_id: https://www.facebook.com/ads/library/?view_all_page_id=123456789
    - Plain text search queries: "nike shoes"

    Args:
        ad_library_url: Full Ad Library URL or search query

    Returns:
        Tuple of (page_id, query) - one will be set, the other None
    """
    # Check for page_id patterns
    patterns = [
        r"view_all_page_id=(\d+)",
        r"page_id=(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, ad_library_url)
        if match:
            return match.group(1), None

    # If no page_id found, treat as keyword search
    # Clean up the input - if it looks like a URL but no page_id, return None
    if "facebook.com" in ad_library_url.lower():
        return None, None

    # Treat as keyword search query
    return None, ad_library_url.strip()


def extract_page_id(ad_library_url: str) -> Optional[str]:
    """
    Extract page_id from a Meta Ad Library URL (backwards compatibility).

    Args:
        ad_library_url: Full Ad Library URL

    Returns:
        page_id string or None if not found
    """
    page_id, _ = extract_page_id_or_query(ad_library_url)
    return page_id


async def fetch_ads_from_searchapi(
    page_id: Optional[str] = None,
    query: Optional[str] = None,
    country: str = "all",
    limit: int = 10,
    ad_type: str = "all",
    active_status: str = "all",  # Fetch both active and inactive ads
    media_type: str = "image",   # Only fetch image ads, not video/dynamic
) -> dict:
    """
    Fetch ads from Meta Ad Library via SearchAPI.

    SearchAPI provides access to Meta Ad Library without the EU restrictions.
    Supports both page_id lookup and keyword search.

    Args:
        page_id: Meta page ID to fetch ads for (optional)
        query: Keyword search query (optional) - use this if page_id doesn't work
        country: Country code (default: "us")
        limit: Maximum number of ads to fetch
        ad_type: "all", "political_and_issue_ads", etc.
        active_status: "active", "inactive", or "all"
        media_type: "image", "video", or "all"

    Returns:
        Raw API response dict with 'ads' array

    Raises:
        httpx.HTTPStatusError: If API request fails
    """
    params = {
        "engine": "meta_ad_library",
        "api_key": settings.searchapi_key,
        "country": country,
        "ad_type": ad_type,
        "active_status": active_status,
        "media_type": media_type,
    }

    # Use page_id if provided, otherwise use keyword query
    if page_id:
        params["page_id"] = page_id
    elif query:
        params["q"] = query
    else:
        raise ValueError("Either page_id or query must be provided")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(SEARCHAPI_URL, params=params)
        response.raise_for_status()
        return response.json()


def calculate_winner_score(ad_data: dict) -> float:
    """
    Calculate a "winner score" for an ad based on duration and active status.

    Scoring logic:
    - Base score = days running
    - Active ads get 1.5x multiplier (still converting, not fatigued)
    - Inactive ads get 1.0x multiplier (proven but possibly fatigued)
    - Minimum 7 days to be considered (skip brand new ads)

    Args:
        ad_data: Processed ad data dict with ad_delivery_start and is_active

    Returns:
        Winner score (higher = more likely a winner)
    """
    start_date = ad_data.get("ad_delivery_start")
    is_active = ad_data.get("is_active", False)

    if not start_date:
        return 0.0

    # Calculate days running
    if isinstance(start_date, str):
        try:
            start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            return 0.0

    now = datetime.now(timezone.utc)
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)

    days_running = (now - start_date).days

    # Skip ads running less than 7 days (too new to judge)
    if days_running < 7:
        return 0.0

    # Apply multiplier based on active status
    multiplier = 1.5 if is_active else 1.0

    return days_running * multiplier


def process_ad_data(raw_ad: dict) -> dict:
    """
    Process a raw ad from SearchAPI into a structured format.

    Args:
        raw_ad: Raw ad object from SearchAPI

    Returns:
        Processed ad dict with structured fields
    """
    # SearchAPI's end_date field is unreliable (shows incorrect years)
    # Since we request active_status="active", assume all returned ads are active
    # This gives them the 1.5x multiplier in winner scoring
    is_active = True

    # Parse delivery start date
    ad_delivery_start = None
    start_time_str = raw_ad.get("start_date")
    if start_time_str:
        try:
            ad_delivery_start = datetime.fromisoformat(
                start_time_str.replace("Z", "+00:00")
            )
        except ValueError:
            pass

    # Get ad text from snapshot body
    snapshot = raw_ad.get("snapshot", {})
    ad_text = None
    if isinstance(snapshot, dict):
        body = snapshot.get("body", {})
        if isinstance(body, dict):
            ad_text = body.get("text")
        elif isinstance(body, str):
            ad_text = body

    # Fallback to other text fields
    if not ad_text:
        ad_text = raw_ad.get("body_text") or raw_ad.get("link_description")

    # Get image URL - SearchAPI provides images in different locations
    image_url = None

    if isinstance(snapshot, dict):
        # Try snapshot.images first
        images = snapshot.get("images", [])
        if images and isinstance(images, list) and len(images) > 0:
            first_image = images[0]
            if isinstance(first_image, dict):
                image_url = first_image.get("resized_image_url") or first_image.get("original_image_url")
            elif isinstance(first_image, str):
                image_url = first_image

        # Try snapshot.cards (carousel/dynamic ads)
        if not image_url:
            cards = snapshot.get("cards", [])
            if cards and isinstance(cards, list) and len(cards) > 0:
                first_card = cards[0]
                if isinstance(first_card, dict):
                    image_url = first_card.get("resized_image_url") or first_card.get("original_image_url")

    # Fallback to other image fields
    if not image_url:
        image_url = raw_ad.get("image_url") or raw_ad.get("thumbnail")

    # Get page info - SearchAPI has page_id at top level and page_name in snapshot
    page_id = raw_ad.get("page_id")
    page_name = raw_ad.get("page_name")

    # Fallback to snapshot for page_name
    if not page_name and isinstance(snapshot, dict):
        page_name = snapshot.get("page_name")

    # Get ad_id - SearchAPI uses ad_archive_id
    ad_id = raw_ad.get("ad_archive_id") or raw_ad.get("archive_id") or raw_ad.get("id")

    # Note: is_active was already determined at the top based on end_date

    ad_data = {
        "ad_id": ad_id,
        "page_id": page_id or "unknown",  # Fallback to prevent null
        "page_name": page_name,
        "ad_snapshot_url": raw_ad.get("snapshot_url"),
        "ad_text": ad_text,
        "original_image_url": image_url,
        "resized_image_url": image_url,  # SearchAPI doesn't differentiate
        # Metrics (SearchAPI may not provide these)
        "impressions_lower": None,
        "impressions_upper": None,
        "spend_lower": None,
        "spend_upper": None,
        # Timing
        "ad_delivery_start": ad_delivery_start,
        "ad_delivery_stop": raw_ad.get("end_date"),
        # Platforms
        "platforms": raw_ad.get("platforms", []),
        # Status
        "is_active": is_active,
    }

    # Calculate winner score
    ad_data["winner_score"] = calculate_winner_score(ad_data)

    return ad_data


async def download_image(image_url: str) -> Optional[bytes]:
    """
    Download an image from a URL.

    Args:
        image_url: Direct URL to the image

    Returns:
        Image bytes or None if download fails
    """
    if not image_url:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as e:
        print(f"Failed to download image from {image_url}: {e}")
        return None


async def fetch_and_process_competitor_ads(
    page_id: str,
    limit: int = 10,
) -> List[dict]:
    """
    Fetch ads from SearchAPI and process them into structured format.

    Args:
        page_id: Meta page ID
        limit: Maximum ads to fetch

    Returns:
        List of processed ad dicts
    """
    response = await fetch_ads_from_searchapi(page_id, limit=limit)
    ads_data = response.get("ads", [])
    return [process_ad_data(ad) for ad in ads_data[:limit]]


# Keep the old function name for backwards compatibility
async def fetch_ads_from_meta(
    page_id: str,
    ad_reached_countries: List[str] = None,
    limit: int = 10,
    ad_active_status: str = "ALL",
) -> dict:
    """
    Wrapper for backwards compatibility.
    Now uses SearchAPI instead of direct Meta API.
    """
    country = "us"
    if ad_reached_countries and len(ad_reached_countries) > 0:
        country = ad_reached_countries[0].lower()

    active_status = "all"
    if ad_active_status == "ACTIVE":
        active_status = "active"
    elif ad_active_status == "INACTIVE":
        active_status = "inactive"

    result = await fetch_ads_from_searchapi(
        page_id=page_id,
        country=country,
        limit=limit,
        active_status=active_status,
    )

    # Convert to old format for compatibility
    return {"data": result.get("ads", [])}
