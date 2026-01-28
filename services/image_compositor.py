"""
Image compositing service for creating final ad images.
Overlays text (hook, body, CTA) and logo onto generated background images.
"""

import io
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from textwrap import wrap


def create_final_ad_image(
    background_bytes: bytes,
    hook: str,
    logo_bytes: Optional[bytes] = None,
) -> bytes:
    """
    Composite the final ad image with hook text overlay and logo.

    Args:
        background_bytes: Generated background image bytes
        hook: Ad hook/headline (the only text shown on the ad)
        logo_bytes: Optional logo image bytes

    Returns:
        Final composited ad image as bytes
    """
    # Load background image
    bg_image = Image.open(io.BytesIO(background_bytes))

    # Ensure RGB mode
    if bg_image.mode != 'RGB':
        bg_image = bg_image.convert('RGB')

    # Resize to standard Instagram square size if needed
    target_size = (1080, 1080)
    if bg_image.size != target_size:
        bg_image = bg_image.resize(target_size, Image.Resampling.LANCZOS)

    # Convert background to RGBA for text and logo compositing
    bg_image = bg_image.convert('RGBA')

    # Create drawing context
    draw = ImageDraw.Draw(bg_image)

    # Load fonts
    try:
        hook_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
    except:
        hook_font = ImageFont.load_default()

    # Find best position for text by analyzing image composition
    text_position = _find_best_text_position(bg_image, hook, hook_font)

    # Layout parameters
    padding = 60

    # Draw hook at optimal position
    hook_wrapped = _wrap_text(hook, 25)
    hook_lines = hook_wrapped.split('\n')
    current_y = text_position['y']

    for line in hook_lines:
        # Text shadow for readability
        shadow_offset = 3
        draw.text((padding + shadow_offset, current_y + shadow_offset), line, font=hook_font, fill=(0, 0, 0, 255))
        draw.text((padding, current_y), line, font=hook_font, fill=(255, 255, 255, 255))
        current_y += 80

    # Add logo if provided (with intelligent color adaptation)
    if logo_bytes:
        try:
            logo = Image.open(io.BytesIO(logo_bytes))
            logo = logo.convert('RGBA')

            # Resize logo to fit (max 150x150)
            logo.thumbnail((150, 150), Image.Resampling.LANCZOS)

            # Position logo in top-right corner
            logo_x = bg_image.size[0] - logo.size[0] - padding
            logo_y = padding

            # Analyze background color behind logo
            bg_rgb = bg_image.convert('RGB')
            logo_region = bg_rgb.crop((logo_x, logo_y, logo_x + logo.size[0], logo_y + logo.size[1]))

            # Calculate average brightness of background
            pixels = list(logo_region.getdata())
            avg_brightness = sum(sum(p) for p in pixels) / (len(pixels) * 3)

            # If background is dark, make logo lighter; if light, make logo darker
            if avg_brightness < 128:
                # Dark background - lighten logo or add white background
                # Create semi-transparent white background for logo
                logo_bg = Image.new('RGBA', logo.size, (255, 255, 255, 200))
                logo_bg.paste(logo, (0, 0), logo)
                logo = logo_bg
            else:
                # Light background - darken logo or add subtle dark background
                # Create semi-transparent dark background for logo
                logo_bg = Image.new('RGBA', logo.size, (0, 0, 0, 150))
                logo_bg.paste(logo, (0, 0), logo)
                logo = logo_bg

            # Paste logo with adapted background
            bg_image.paste(logo, (logo_x, logo_y), logo)

        except Exception as e:
            print(f"Error adding logo: {e}")

    # Convert back to RGB
    final_image = bg_image.convert('RGB')

    # Save to bytes
    img_byte_arr = io.BytesIO()
    final_image.save(img_byte_arr, format='PNG', quality=95)

    return img_byte_arr.getvalue()


def _find_best_text_position(image: Image.Image, text: str, font: ImageFont.FreeTypeFont) -> dict:
    """
    Analyze image to find the best position for text overlay.
    Looks for areas with least visual complexity and good contrast.

    Args:
        image: PIL Image to analyze
        text: Text that will be overlaid
        font: Font that will be used

    Returns:
        Dictionary with 'y' position for text
    """
    # Convert to RGB for analysis
    rgb_image = image.convert('RGB')
    width, height = rgb_image.size

    # Define candidate regions (top, middle, bottom thirds)
    regions = [
        {'name': 'top', 'y': 60, 'slice': (0, 0, width, height // 3)},
        {'name': 'middle', 'y': height // 2 - 100, 'slice': (0, height // 3, width, 2 * height // 3)},
        {'name': 'bottom', 'y': height - 220, 'slice': (0, 2 * height // 3, width, height)},
    ]

    best_region = regions[2]  # Default to bottom if nothing else works
    best_score = -1

    for region in regions:
        # Crop region
        region_crop = rgb_image.crop(region['slice'])

        # Calculate average brightness
        pixels = list(region_crop.getdata())
        if not pixels:
            continue

        avg_brightness = sum(sum(p) for p in pixels) / (len(pixels) * 3)

        # Calculate variance (lower = more uniform = better for text)
        brightness_values = [sum(p) / 3 for p in pixels]
        mean_brightness = sum(brightness_values) / len(brightness_values)
        variance = sum((b - mean_brightness) ** 2 for b in brightness_values) / len(brightness_values)

        # Score: prefer low variance (uniform areas) and moderate brightness
        # Avoid very bright (>200) or very dark (<50) regions
        brightness_penalty = 0
        if avg_brightness > 200 or avg_brightness < 50:
            brightness_penalty = 50

        score = 1000 - variance - brightness_penalty

        if score > best_score:
            best_score = score
            best_region = region

    return {'y': best_region['y']}


def _wrap_text(text: str, max_chars_per_line: int) -> str:
    """
    Wrap text to fit within specified character width.

    Args:
        text: Text to wrap
        max_chars_per_line: Maximum characters per line

    Returns:
        Wrapped text with newlines
    """
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_length = len(word)
        if current_length + word_length + len(current_line) <= max_chars_per_line:
            current_line.append(word)
            current_length += word_length
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length

    if current_line:
        lines.append(' '.join(current_line))

    return '\n'.join(lines)


