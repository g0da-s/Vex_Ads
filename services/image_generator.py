"""
Image generation service using Google Gemini.
Generates ad images based on visual concepts and product context.
"""

import io
import time
from typing import Optional
from PIL import Image
from google import genai

from config import get_settings

settings = get_settings()

# Configure Gemini client
client = genai.Client(api_key=settings.gemini_api_key)


async def generate_ad_image(
    visual_concept: str,
    product: str,
    style_directive: str = "",
    aspect_ratio: str = "1:1",
    product_image_bytes: Optional[bytes] = None,
) -> tuple[bytes, int]:
    """
    Generate an ad image featuring the actual product (background only, no text).

    Args:
        visual_concept: Detailed art-directed prompt for the image
        product: Product name for context
        style_directive: Brand style guide from visual bible
        aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16)
        product_image_bytes: Actual product image to feature in the ad

    Returns:
        Tuple of (image bytes, generation time in ms)
    """
    start_time = time.time()

    # Build cinematic prompt for scroll-stopping ad image generation
    prompt_text = f"""You are generating a scroll-stopping advertising image for Facebook/Instagram. This needs to stop thumbs mid-scroll.

PRODUCT TO FEATURE: {product}
(Use the product shown in the reference image - integrate it naturally into the scene)

CREATIVE DIRECTION (execute this exactly):
{visual_concept}

BRAND AESTHETIC (maintain this vibe):
{style_directive if style_directive else "Modern, cinematic, emotionally resonant advertising photography"}

EXECUTION REQUIREMENTS:

1. CINEMATIC QUALITY:
   - Execute the lighting, composition, and mood EXACTLY as described in the creative direction
   - Think editorial photography, not stock photos
   - Create visual tension and emotional resonance
   - Use depth of field strategically (shallow for portraits, deeper for environmental shots)
   - Add film grain or texture if it enhances the mood

2. HUMAN CONNECTION:
   - If people are shown: faces must be CLEAR, SHARP, IN FOCUS with REAL EXPRESSIONS
   - Show genuine emotion - pain, relief, joy, exhaustion, satisfaction
   - Body language must tell the story (hunched shoulders = pain, relaxed posture = relief)
   - No fake smiling models - show REAL human moments

3. LIGHTING AS STORYTELLING:
   - Execute the exact lighting described (golden hour, screen glow, harsh fluorescent, etc.)
   - Use shadows and highlights to create drama
   - Let lighting convey emotion (warm = comfort, harsh blue = stress, etc.)

4. PRODUCT INTEGRATION:
   - Feature the product from the reference image naturally in the scene
   - Show it IN USE, not just displayed
   - Let the product be part of the story, not just placed in frame
   - The human moment matters more than perfect product placement

5. COMPOSITION:
   - Follow the composition direction exactly (camera angle, framing, negative space)
   - Create natural areas for text overlay where specified
   - Use the rule of thirds, leading lines, and visual hierarchy
   - Make the viewer's eye move through the frame

6. STYLE & MOOD:
   - Match the exact emotional tone described
   - Use color grading to enhance mood (desaturate for stress, warm for comfort, etc.)
   - Add environmental details that reinforce the story
   - Reference the cinematic styles mentioned

ABSOLUTE REQUIREMENTS:
- NO text, typography, words, letters, or graphic overlays of any kind
- NO white boxes, UI elements, or text placeholders
- NO brand names or slogans written in the image
- Pure photography/cinematography only
- 1080x1080 square format
- If people appear, their faces MUST be clear and in focus (no blur, no obscured faces)

This image must make someone stop scrolling and FEEL something immediately."""

    try:
        # Use Gemini 3 Pro Image - Google's advanced image generation model
        print(f"Generating image with Gemini 3 Pro Image...")

        # Prepare contents with product image reference
        contents = [prompt_text]

        if product_image_bytes:
            # Add product image as reference
            contents.append({
                'inline_data': {
                    'mime_type': 'image/png',
                    'data': product_image_bytes
                }
            })

        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=contents
        )

        # Get the generated image from the response
        # The image is in the response parts
        image_part = None
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                image_part = part.inline_data
                break

        if not image_part:
            raise Exception("No image generated in response")

        # Convert inline data to PIL Image
        import io
        from PIL import Image as PILImage
        image = PILImage.open(io.BytesIO(image_part.data))

        # Ensure it's RGB mode
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize to 1080x1080
        image = image.resize((1080, 1080), Image.Resampling.LANCZOS)

        # Save to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG', quality=95)
        img_bytes = img_byte_arr.getvalue()

        generation_time_ms = int((time.time() - start_time) * 1000)
        print(f"Successfully generated image in {generation_time_ms}ms")

        return img_bytes, generation_time_ms

    except Exception as e:
        print(f"Error generating image with Imagen: {e}")
        print(f"Falling back to gradient background")
        # Fallback: create a simple colored background image
        return _create_fallback_image(), int((time.time() - start_time) * 1000)


def _create_fallback_image() -> bytes:
    """
    Create a simple fallback image when generation fails.

    Returns:
        Image bytes
    """
    from PIL import Image, ImageDraw

    # Simple neutral gradient
    color1 = (30, 30, 35)  # Dark
    color2 = (50, 50, 60)  # Lighter

    # Create a 1080x1080 gradient image
    img = Image.new('RGB', (1080, 1080))
    draw = ImageDraw.Draw(img)

    # Create diagonal gradient
    for i in range(1080):
        # Calculate gradient position (0.0 to 1.0)
        t = i / 1080

        # Interpolate between color1 and color2
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)

        color = (r, g, b)
        draw.line([(0, i), (1080, i)], fill=color)

    # Save to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG', quality=95)
    return img_byte_arr.getvalue()
