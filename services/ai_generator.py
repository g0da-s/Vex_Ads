"""
AI Ad Generator service using Anthropic Claude.
Generates ad copy using proven marketing psychology frameworks.
"""

import json
import time
from typing import List

import anthropic

from config import get_settings
from models.schemas import GeneratedAd, AdFramework

settings = get_settings()

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

# System prompt for direct-response copywriting
SYSTEM_PROMPT = """You are a world-class direct-response copywriter specializing in Facebook/Instagram ads.

CORE PRINCIPLES:
- Specificity > Vagueness ("Save 3 hours/day" not "Save time")
- Benefits > Features ("Sleep better tonight" not "Memory foam technology")
- One clear CTA per ad
- Use numbers when possible
- Active voice, present tense
- Speak directly to the reader ("you", "your")

FRAMEWORKS TO USE:

1. Problem/Agitate/Solution (PAS):
   - Hook: Call out the specific pain point
   - Body: Agitate the problem, show consequences of not solving it
   - CTA: Present your solution as the answer

2. Social Proof:
   - Hook: Lead with an impressive number, stat, or testimonial
   - Body: Show specific transformation or results others achieved
   - CTA: Invite them to join the successful group

3. Transformation:
   - Hook: Describe their current frustrating state (relatable)
   - Body: Paint the aspirational future state they desire
   - CTA: Position your product as the bridge between the two

STRICT RULES:
- Hook: EXACTLY 5-8 words. Punchy. Curiosity-inducing.
- Body: EXACTLY 2-3 sentences. Specific benefits, not vague promises.
- CTA: EXACTLY 3-5 words. Action-oriented verb.
- Visual concept: Brief description of what the ad image should show.

AVOID:
- Clichés ("game-changer", "revolutionary", "unlock your potential")
- Vague claims ("best", "amazing", "incredible")
- More than 3 sentences in body
- ALL CAPS or excessive punctuation (!!!)
- Emojis in hooks or CTAs
- Generic stock photo descriptions

OUTPUT FORMAT:
Return ONLY valid JSON array with exactly 3 ad objects. No markdown, no explanation."""


USER_PROMPT_TEMPLATE = """Create 3 Facebook ad concepts for this product. Each MUST use a DIFFERENT framework.

PRODUCT: {product}
TARGET CUSTOMER: {target_customer}
KEY BENEFIT: {main_benefit}

Generate exactly 3 ads:
1. First ad: Use Problem/Agitate/Solution (PAS) framework
2. Second ad: Use Social Proof framework
3. Third ad: Use Transformation framework

Return as JSON array:
[
  {{
    "framework": "Problem-Agitate-Solution",
    "hook": "5-8 word attention grabber",
    "body": "2-3 sentences of compelling copy",
    "cta": "3-5 word call to action",
    "visual_concept": "What the ad image should show"
  }},
  {{
    "framework": "Social Proof",
    "hook": "...",
    "body": "...",
    "cta": "...",
    "visual_concept": "..."
  }},
  {{
    "framework": "Transformation",
    "hook": "...",
    "body": "...",
    "cta": "...",
    "visual_concept": "..."
  }}
]

Make each ad SPECIFIC to this product and customer. No generic copy."""


async def generate_ads(
    product: str,
    target_customer: str,
    main_benefit: str,
) -> tuple[List[GeneratedAd], int]:
    """
    Generate 3 ad concepts using different marketing frameworks.

    Args:
        product: What the user sells
        target_customer: Who the target audience is
        main_benefit: The key problem it solves

    Returns:
        Tuple of (list of 3 GeneratedAd objects, generation time in ms)
    """
    start_time = time.time()

    # Build the user prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(
        product=product,
        target_customer=target_customer,
        main_benefit=main_benefit,
    )

    # Call Claude API
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": user_prompt,
            }
        ],
        system=SYSTEM_PROMPT,
    )

    # Parse response
    response_text = message.content[0].text

    # Clean up response if it has markdown code blocks
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    response_text = response_text.strip()

    # Parse JSON
    ads_data = json.loads(response_text)

    # Convert to GeneratedAd objects
    ads = []
    framework_map = {
        "Problem-Agitate-Solution": AdFramework.PAS,
        "PAS": AdFramework.PAS,
        "Social Proof": AdFramework.SOCIAL_PROOF,
        "Transformation": AdFramework.TRANSFORMATION,
    }

    for ad_data in ads_data:
        framework_str = ad_data.get("framework", "")
        framework = framework_map.get(framework_str, AdFramework.PAS)

        ads.append(
            GeneratedAd(
                framework=framework,
                hook=ad_data["hook"],
                body=ad_data["body"],
                cta=ad_data["cta"],
                visual_concept=ad_data["visual_concept"],
            )
        )

    # Calculate generation time
    generation_time_ms = int((time.time() - start_time) * 1000)

    return ads, generation_time_ms
