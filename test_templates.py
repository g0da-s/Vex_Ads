"""
Quick test to verify the prompt template system works.
"""

from services.prompt_templates import get_prompt_manager

# Test the template manager
manager = get_prompt_manager()

print("📋 Available Templates:")
for template in manager.list_templates():
    print(f"\n  ✓ {template['id']}")
    print(f"    Name: {template['name']}")
    print(f"    Description: {template['description']}")

print("\n" + "="*60)
print("\n🎨 Testing v1_creative_director template rendering:")
print("="*60)

prompt = manager.render_prompt(
    template_version="v1_creative_director",
    competitor_ad_text="Shop now for 50% off!",
    product_description="Premium wireless headphones",
    language="en"
)

print(prompt)

print("\n" + "="*60)
print("\n🎯 Testing v2_conversion_focused template rendering:")
print("="*60)

prompt = manager.render_prompt(
    template_version="v2_conversion_focused",
    competitor_ad_text="Limited time offer!",
    product_description="Stylish running shoes",
    language="es"
)

print(prompt)

print("\n✅ Template system working correctly!")
