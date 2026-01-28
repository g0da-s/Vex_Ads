"""
Creative Director - Generates 10 diverse ad concepts with visual prompts and marketing copy.
Acts as an expert creative director specializing in social media advertising.
"""

import json
from typing import List, Dict
from google import genai
from config import get_settings

settings = get_settings()
client = genai.Client(api_key=settings.gemini_api_key)


async def generate_ad_concepts(
    visual_bible: dict,
    brand_name: str,
    product_description: str,
    target_customer: str
) -> List[Dict]:
    """
    Generate 5 diverse ad concepts, each with visual prompt and marketing copy.

    Args:
        visual_bible: Style guide from visual_bible_creator
        brand_name: Brand name
        product_description: Product/service description
        target_customer: Target audience description

    Returns:
        List of 5 ad concept dictionaries
    """

    prompt = f"""You are a world-class creative director for performance marketing. Your ads are scroll-stopping, emotionally charged, and consistently hit 10%+ CTR.

Your task: Create 5 DIVERSE, cinematically powerful ad concepts for {brand_name}.

BRAND CONTEXT:
- Product: {product_description}
- Target Customer: {target_customer}
- Brand Name: {brand_name}

VISUAL STYLE GUIDE (maintain this aesthetic):
{visual_bible['style_directive']}

YOUR CREATIVE PHILOSOPHY:
1. EMOTION FIRST - Every frame must make people FEEL something visceral
2. STORY OVER PRODUCT - Show the human moment, not just the product
3. CINEMATIC TENSION - Use lighting, composition, and mood like a film director
4. REAL PEOPLE, REAL MOMENTS - Not models posing, but humans living

REQUIREMENTS FOR EACH AD CONCEPT:

1. VISUAL CONCEPT (art direction for AI image generation):

   Write this like you're briefing a world-class commercial photographer or cinematographer.

   STRUCTURE YOUR VISUAL PROMPT LIKE THIS:

   "SCENE: [Describe the human moment/story]
   COMPOSITION: [Camera angle, framing, what's in focus]
   LIGHTING: [Mood, direction, quality - be specific]
   EMOTION: [What feeling should radiate from this image]
   PRODUCT INTEGRATION: [How the product naturally fits into this moment]
   STYLE: [Cinematic references, color palette, texture]"

   EXAMPLES OF POWERFUL VISUAL DIRECTION:
   ✓ "SCENE: A frustrated remote worker hunched over a laptop at 2AM, face lit only by screen glow, rubbing their lower back in visible pain. Empty coffee cups scattered around.
   COMPOSITION: Tight medium shot, slightly from above, shallow depth of field with the person's pained expression in sharp focus
   LIGHTING: Harsh blue computer light on face, warm desk lamp creating dramatic side lighting and deep shadows
   EMOTION: Exhaustion, physical pain, desperation
   PRODUCT INTEGRATION: The ergonomic chair is barely visible in the background, symbolizing the solution they don't have yet
   STYLE: Cinematic realism, desaturated colors except for the blue screen glow, film noir shadows, 35mm film grain"

   ✓ "SCENE: A person sitting in the product chair, eyes closed, head tilted back in pure relief, golden hour sunlight streaming through window
   COMPOSITION: Profile shot, Dutch angle for visual interest, negative space in upper third for text
   LIGHTING: Warm, directional golden hour light from window, rim lighting on hair, soft shadows
   EMOTION: Pure relief, almost meditative calm, the moment pain finally stops
   PRODUCT INTEGRATION: Chair is hero but person's body language tells the story
   STYLE: Editorial photography, warm color grading, Wes Anderson symmetry meets documentary realism"

   BE SPECIFIC ABOUT:
   - Exact lighting direction and mood
   - Camera angle and focal length feel
   - Facial expressions and body language
   - Environmental storytelling details
   - Color palette and texture
   - Where negative space for text naturally occurs

2. HOOK (the ONLY text on the ad):

   LENGTH: 3-8 words maximum

   USE RAW CUSTOMER LANGUAGE:
   - Pattern interrupts (unexpected statements)
   - Specific numbers, timeframes, or costs
   - Raw emotions and frustrations
   - How people ACTUALLY talk (not marketing speak)

   GOOD HOOKS (specific, visceral, real):
   * "3AM. Still working. Again."
   * "Your back called. It's quitting."
   * "Coffee #6. It's only Tuesday."
   * "$2,400 on chiropractors last year"
   * "Week 3 of 'just one more email'"

   BAD HOOKS (generic bullshit - NEVER DO THIS):
   * "Say goodbye to back pain"
   * "Transform your workspace"
   * "The ultimate office chair"
   * "Work happy, live better"

3. DIVERSITY REQUIREMENTS:
   Each of the 5 ads must be RADICALLY DIFFERENT:
   - Different emotional tone (pain → relief → aspiration → FOMO → contrarian)
   - Different time of day / lighting scenario
   - Different composition style
   - Different customer pain point
   - Different visual storytelling approach

OUTPUT FORMAT (JSON):
{{
  "concept_number": 1-5,
  "visual_prompt": "Detailed cinematographic art direction as described above",
  "hook": "3-8 word customer-language headline"
}}

Make each concept feel like a frame from a different film.
Think: Apple's emotional storytelling + Oatly's raw authenticity + Netflix documentary realism.

Return ONLY the JSON array, no other text."""

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )

        # Parse JSON response
        response_text = response.text.strip()

        # Remove markdown code fences if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        ad_concepts = json.loads(response_text)

        # Validate we got 5 concepts
        if len(ad_concepts) < 5:
            print(f"Warning: Only got {len(ad_concepts)} concepts, expected 5")

        return ad_concepts[:5]  # Ensure max 5

    except Exception as e:
        print(f"Error generating ad concepts: {e}")
        print(f"Response was: {response.text if 'response' in locals() else 'No response'}")

        # Re-raise the error - no fallback concepts
        raise Exception(f"Failed to generate ad concepts: {str(e)}")
