"""
Visual Bible Creator - Analyzes brand images to extract comprehensive style guide.
Uses Gemini 3 Pro to understand brand aesthetics, colors, mood, and visual language.
"""

import base64
from typing import List
from google import genai
from config import get_settings

settings = get_settings()
client = genai.Client(api_key=settings.gemini_api_key)


async def create_visual_bible(brand_images: List[bytes], brand_name: str, product_description: str) -> dict:
    """
    Analyze brand images to create a comprehensive visual style guide (Visual Bible).

    Args:
        brand_images: List of brand/product image bytes (3-5 images)
        brand_name: Name of the brand
        product_description: What the product/service is

    Returns:
        Visual bible dictionary containing style guide elements
    """

    # Prepare images for Gemini (convert to base64)
    image_parts = []
    for img_bytes in brand_images:
        b64_image = base64.b64encode(img_bytes).decode('utf-8')
        image_parts.append({
            "mime_type": "image/jpeg",
            "data": b64_image
        })

    # Prompt for visual bible creation
    prompt = f"""You have been given a brand's images. Create a visual guide that can be used to produce more visuals in the style of this brand.

Brand: {brand_name}
Product: {product_description}
Number of reference images: {len(brand_images)}

Analyze these brand images comprehensively and create a detailed visual bible covering:

## Brand Philosophy & Mood
- Core concept and brand positioning
- Key descriptive terms and the overall vibe
- What lifestyle or feeling this brand sells

## Color Palette
- Primary base colors (walls, surfaces, key elements)
- Secondary/accent tones
- Environmental context colors
- Special use colors
Use specific color names like "Clinic White", "Slate Grey" or hex codes.

## Photography & Environment
- Setting details (studio, natural environment, office, etc.)
- View/background elements
- Interior/exterior styling choices
- Lighting: source, quality, color temperature, special notes
- Composition: framing style, camera angles, use of space
- Human element: how people are shown, positioned, dressed

## Product Styling
- Product positioning and state
- Key features highlighted
- Props and context elements

## Typography & Graphics (if visible)
- Font styles and text treatment
- Graphic elements used
- Copy tone

## Do's and Don'ts
List specific DO's and DON'Ts for maintaining brand consistency.

Be extremely specific and actionable. This guide will be used to generate new images that look like they came from the same photoshoot.
"""

    try:
        # Use Gemini Pro for analysis - build content with PIL images
        from PIL import Image
        import io

        # Convert bytes to PIL Images
        pil_images = []
        for img_bytes in brand_images:
            pil_images.append(Image.open(io.BytesIO(img_bytes)))

        # Build contents list
        contents = [prompt]
        contents.extend(pil_images)

        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=contents
        )

        visual_bible_text = response.text

        # Also generate a concise "style directive" for image generation
        style_directive_prompt = f"""Based on the visual bible analysis above, create a CONCISE 2-3 sentence style directive that can be appended to image generation prompts to maintain brand consistency.

Visual Bible:
{visual_bible_text}

Style Directive (be concise but specific about colors, lighting, mood, and aesthetic):"""

        directive_response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=style_directive_prompt
        )

        style_directive = directive_response.text.strip()

        return {
            "full_analysis": visual_bible_text,
            "style_directive": style_directive,
            "brand_name": brand_name,
            "num_reference_images": len(brand_images)
        }

    except Exception as e:
        print(f"Error creating visual bible: {e}")
        # Fallback minimal style guide
        return {
            "full_analysis": f"Brand: {brand_name}. Product: {product_description}. Professional photography style.",
            "style_directive": f"Professional, high-quality photography for {brand_name} showing {product_description}",
            "brand_name": brand_name,
            "num_reference_images": len(brand_images)
        }
