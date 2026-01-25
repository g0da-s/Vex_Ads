"""
AI Ad Generator service using Google Gemini.
Generates new ad creatives based on competitor ad patterns.
"""

import base64
from typing import Optional, List

from google import genai
from google.genai import types

from config import get_settings

settings = get_settings()

# Initialize Gemini client
client = genai.Client(api_key=settings.gemini_api_key)

# Model for image generation
# Only gemini-2.0-flash-exp supports multimodal input WITH image output
IMAGE_GENERATION_MODEL = "gemini-2.0-flash-exp"

# Default generation prompt template
DEFAULT_GENERATION_PROMPT = """You are an expert advertising creative director. Create a professional Facebook advertisement image.

ANALYZE the competitor ad provided to understand:
- Layout and composition patterns
- Color palette and mood
- Text placement and hierarchy
- Background style and lighting
- Overall aesthetic and brand feel

CREATE a new advertisement that:
1. Features the provided PRODUCT IMAGE prominently as the hero product
2. Incorporates the provided LOGO naturally (subtle placement, corner or bottom)
3. Matches the competitor's overall aesthetic and professional quality
4. Is suitable for Facebook/Instagram feed (square format preferred)

IMPORTANT REQUIREMENTS:
- Generate a complete, polished advertisement image
- The product must be the clear focal point
- Maintain professional, high-quality appearance
- Do NOT copy the competitor ad directly - create something inspired but original
- Include subtle branding with the logo
- Use clean, modern design principles

OUTPUT: A single, ready-to-use advertisement image."""


class RateLimitError(Exception):
    """Raised when Gemini API rate limit is hit."""
    pass


def build_generation_prompt(
    competitor_ad_text: Optional[str] = None,
    product_description: Optional[str] = None,
    style_notes: Optional[str] = None,
) -> str:
    """
    Build a customized generation prompt.

    Args:
        competitor_ad_text: Text from the competitor's ad for style reference
        product_description: Description of the user's product
        style_notes: Additional style instructions

    Returns:
        Complete prompt string
    """
    prompt = DEFAULT_GENERATION_PROMPT

    # Add competitor ad text context
    if competitor_ad_text:
        prompt += f"\n\nCOMPETITOR AD MESSAGING (for style reference only):\n\"{competitor_ad_text}\"\n"
        prompt += "Create similar emotional appeal but with ORIGINAL copy."

    # Add product description
    if product_description:
        prompt += f"\n\nPRODUCT CONTEXT:\n{product_description}"

    # Add style notes
    if style_notes:
        prompt += f"\n\nADDITIONAL STYLE NOTES:\n{style_notes}"

    return prompt


async def generate_ad_image(
    competitor_image: bytes,
    product_image: bytes,
    logo_image: bytes,
    competitor_ad_text: Optional[str] = None,
    product_description: Optional[str] = None,
    temperature: float = 0.8,
) -> Optional[bytes]:
    """
    Generate a new ad image using Gemini's multimodal capabilities.

    Args:
        competitor_image: Competitor ad image bytes
        product_image: User's product image bytes
        logo_image: User's logo image bytes
        competitor_ad_text: Optional text from competitor ad
        product_description: Optional product description
        temperature: Generation temperature (0.0-1.0)

    Returns:
        Generated image bytes or None if generation fails

    Raises:
        RateLimitError: If daily quota is exhausted
    """
    try:
        # Build the prompt
        prompt = build_generation_prompt(
            competitor_ad_text=competitor_ad_text,
            product_description=product_description,
        )

        # Create content parts with images
        contents = [
            "COMPETITOR AD (style reference):",
            types.Part.from_bytes(data=competitor_image, mime_type="image/jpeg"),
            "USER'S PRODUCT (feature this):",
            types.Part.from_bytes(data=product_image, mime_type="image/jpeg"),
            "USER'S LOGO (incorporate subtly):",
            types.Part.from_bytes(data=logo_image, mime_type="image/png"),
            prompt,
        ]

        # Generate content with image output
        response = client.models.generate_content(
            model=IMAGE_GENERATION_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                temperature=temperature,
            ),
        )

        # Extract generated image from response
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        # Data is already bytes from Gemini
                        return part.inline_data.data

        return None

    except Exception as e:
        error_str = str(e)
        # Check for rate limit error
        if "429" in error_str and "RESOURCE_EXHAUSTED" in error_str:
            if "limit: 0" in error_str or "PerDay" in error_str:
                raise RateLimitError(
                    "Gemini API daily quota exhausted. Please enable billing at "
                    "https://aistudio.google.com/ or wait until tomorrow for quota reset."
                )
            raise RateLimitError(f"Gemini API rate limited: {error_str}")
        print(f"Error generating ad image: {e}")
        return None


async def generate_multiple_ads(
    competitor_image: bytes,
    product_image: bytes,
    logo_image: bytes,
    competitor_ad_text: Optional[str] = None,
    product_description: Optional[str] = None,
    num_variations: int = 3,
) -> List[bytes]:
    """
    Generate multiple ad variations.

    Each variation uses slightly different temperature for diversity.

    Args:
        competitor_image: Competitor ad image bytes
        product_image: User's product image bytes
        logo_image: User's logo image bytes
        competitor_ad_text: Optional text from competitor ad
        product_description: Optional product description
        num_variations: Number of variations to generate (1-5)

    Returns:
        List of generated image bytes

    Raises:
        RateLimitError: If daily quota is exhausted (stops immediately)
    """
    generated_images = []

    # Base temperature, will vary per generation
    base_temp = 0.7

    for i in range(num_variations):
        # Vary temperature for each generation for diversity
        temp = base_temp + (i * 0.1)
        temp = min(temp, 1.0)  # Cap at 1.0

        try:
            image_bytes = await generate_ad_image(
                competitor_image=competitor_image,
                product_image=product_image,
                logo_image=logo_image,
                competitor_ad_text=competitor_ad_text,
                product_description=product_description,
                temperature=temp,
            )

            if image_bytes:
                generated_images.append(image_bytes)
        except RateLimitError:
            # Re-raise rate limit errors to stop immediately
            raise

    return generated_images


async def analyze_competitor_ad(image_bytes: bytes) -> dict:
    """
    Analyze a competitor ad to extract style insights.

    Useful for understanding the competitor's approach before generation.

    Args:
        image_bytes: Competitor ad image bytes

    Returns:
        Dict with analysis results
    """
    try:
        analysis_prompt = """Analyze this Facebook advertisement and provide insights:

1. COLOR_PALETTE: List primary colors used
2. LAYOUT: Describe the composition (where is the product, text, logo?)
3. MOOD: What emotion/feeling does this ad convey?
4. TEXT_STYLE: Typography observations (if visible)
5. TARGET_AUDIENCE: Who is this ad likely targeting?
6. CALL_TO_ACTION: How is the CTA presented (if visible)?
7. OVERALL_QUALITY: Rate 1-10 and explain

Respond in JSON format."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",  # Use stable model for analysis
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                analysis_prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        # Try to parse JSON response
        import json

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"raw_analysis": response.text}

    except Exception as e:
        print(f"Error analyzing ad: {e}")
        return {"error": str(e)}
