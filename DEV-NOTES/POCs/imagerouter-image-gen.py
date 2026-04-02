"""
ImageRouter.io Image Generation Test Script
Test API for generating flashcard images using ImageRouter.io

API Documentation: https://docs.imagerouter.io/
Endpoint: https://api.imagerouter.io/v1/openai/images/generations

Setup:
1. Get free API key at: https://imagerouter.io/api-keys
2. Add to .env file: IMAGE_ROUTER_API_KEY=your_key_here
3. Run this script

Key Features:
- OpenAI-compatible API
- 3 free images daily with free API key
- Multiple models available
- Automatic fallback routing
"""

import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Test configuration
OUTPUT_DIR = "test_images"
API_BASE_URL = "https://api.imagerouter.io/v1/openai/images/generations"
REQUEST_DELAY = 2  # Seconds between requests
MAX_RETRIES = 2    # Max retries for failed requests

# API Key - loaded from .env file (IMAGE_ROUTER_API_KEY)
# Get your free API key at: https://imagerouter.io/api-keys
API_KEY = os.getenv('IMAGE_ROUTER_API_KEY')

if not API_KEY:
    print("⚠ WARNING: IMAGE_ROUTER_API_KEY not found in .env file!")
    print("   Get your free API key at: https://imagerouter.io/api-keys")
    print("   Add it to .env file as: IMAGE_ROUTER_API_KEY=your_key_here")
    exit(1)

def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"✓ Created directory: {OUTPUT_DIR}")

def generate_image(
    prompt: str, 
    filename: str = None, 
    model: str = "stabilityai/sdxl-turbo",
    size: str = "auto"
) -> str:
    """
    Generate an image using ImageRouter.io
    
    Args:
        prompt: Text description of the image
        filename: Output filename (without extension)
        model: AI model to use
               - "stabilityai/sdxl-turbo" (very fast, cheapest, DEFAULT) - $0.02/100 images
               - "black-forest-labs/FLUX-2-klein-4b" (balanced) - $0.06/100 images
               - "black-forest-labs/FLUX-2-klein-9b" (high quality) - $0.08/100 images
        size: Image dimensions (e.g., "256x256", "512x512", "1024x1024", "auto")
    
    Returns:
        Path to saved image file or None if failed
    """
    ensure_output_dir()
    
    # Create safe filename
    if not filename:
        safe_prompt = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = safe_prompt.replace(' ', '_').lower()[:50]
    
    # Add timestamp to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename}_{timestamp}"
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # Prepare request body
    payload = {
        "prompt": prompt,
        "model": model,
        "size": size,
        "n": 1  # Number of images to generate
    }
    
    print(f"\n🎨 Generating image...")
    print(f"   Prompt: {prompt}")
    print(f"   Model: {model}")
    print(f"   Size: {size}")
    
    # Retry logic
    for attempt in range(MAX_RETRIES):
        try:
            # Make request
            response = requests.post(
                API_BASE_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # Check for errors
            if response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                print(f"✗ API Error ({response.status_code}): {error_msg}")
                
                if response.status_code == 429:  # Rate limit
                    if attempt < MAX_RETRIES - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"⚠ Rate limited. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                
                return None
            
            # Parse response
            result = response.json()
            
            # ImageRouter returns URL in OpenAI format
            if 'data' not in result or len(result['data']) == 0:
                print(f"✗ No image data in response")
                return None
            
            image_url = result['data'][0].get('url') or result['data'][0].get('b64_json')
            
            if not image_url:
                print(f"✗ No image URL or data in response")
                return None
            
            # Download image from URL
            if image_url.startswith('http'):
                print(f"📥 Downloading image from: {image_url[:50]}...")
                img_response = requests.get(image_url, timeout=30)
                img_response.raise_for_status()
                image_data = img_response.content
            else:
                # Handle base64 encoded image
                import base64
                image_data = base64.b64decode(image_url)
            
            # Save image
            output_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            file_size = len(image_data) / 1024  # Size in KB
            print(f"✓ Success! Saved to: {output_path}")
            print(f"   File size: {file_size:.1f} KB")
            
            # Show usage info if available
            if 'usage' in result:
                print(f"   Usage: {result['usage']}")
            
            return output_path
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error generating image: {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"   Retrying... ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(2)
            else:
                return None
    
    print(f"✗ Failed after {MAX_RETRIES} retries")
    return None

def test_single_image():
    """Test with a single image - safest option"""
    print("\n" + "="*60)
    print("TEST 0: Single Image Test")
    print("="*60)
    print("Testing with one simple image to verify API connectivity.\n")
    
    generate_image(
        prompt="A simple red apple on white background, clean and minimal",
        filename="test_apple"
        # Uses default model: stabilityai/sdxl-turbo
    )
    
    print("\n✓ Single image test complete!")

def test_flashcard_objects():
    """Test with simple objects suitable for flashcards"""
    print("\n" + "="*60)
    print("TEST 1: Flashcard Objects Test")
    print("="*60)
    print("Testing with simple objects ideal for language flashcards.\n")
    
    objects = [
        ("A simple red apple on white background", "apple"),
        ("A yellow banana on white background", "banana"),
        ("A cute orange cat on white background", "cat")
    ]
    
    for idx, (prompt, name) in enumerate(objects, 1):
        print(f"\n--- Image {idx}/{len(objects)} ---")
        generate_image(prompt, name)
        # Uses default model: stabilityai/sdxl-turbo
        
        # Delay between requests (except for last one)
        if idx < len(objects):
            print(f"⏳ Waiting {REQUEST_DELAY}s before next request...")
            time.sleep(REQUEST_DELAY)
    
    print("\n✓ Flashcard objects test complete!")

def test_model_comparison():
    """Test different models available on ImageRouter"""
    print("\n" + "="*60)
    print("TEST 2: Model Comparison")
    print("="*60)
    print("Testing same prompt with different models.\n")
    print("Pricing per 100 images:")
    print("  • SDXL Turbo: $0.02")
    print("  • FLUX-2-klein-4b: $0.06")
    print("  • FLUX-2-klein-9b: $0.08\n")
    
    # prompt = "A blue car on white background, simple illustration"
    prompt = "a cute picture of a computer mouse with no text, suitable for a kid's flashcard"
    # prompt = "a cute picture of a turtle on white background, simple illustration"
    models = [
        ("stabilityai/sdxl-turbo", "SDXL Turbo - Very Fast ($0.02/100)"),
        ("black-forest-labs/FLUX-2-klein-4b", "FLUX-2-klein-4b - Balanced ($0.06/100)"),
        ("black-forest-labs/FLUX-2-klein-9b", "FLUX-2-klein-9b - High Quality ($0.08/100)")
    ]
    
    for idx, (model, description) in enumerate(models, 1):
        print(f"\n--- Model {idx}/{len(models)}: {description} ---")
        generate_image(
            prompt=prompt,
            filename=f"car_{model.split('/')[-1]}",
            model=model
        )
        
        # Delay between requests
        if idx < len(models):
            print(f"⏳ Waiting {REQUEST_DELAY}s before next request...")
            time.sleep(REQUEST_DELAY)
    
    print("\n✓ Model comparison test complete!")

def test_size_options():
    """Test different image sizes"""
    print("\n" + "="*60)
    print("TEST 3: Size Options Test")
    print("="*60)
    print("Testing different image dimensions.\n")
    
    sizes = [
        ("256x256", "Small"),
        ("512x512", "Medium"),
        ("1024x1024", "Large")
    ]
    
    prompt = "A green tree on white background"
    
    for idx, (size, description) in enumerate(sizes, 1):
        print(f"\n--- Size {idx}/{len(sizes)}: {description} ({size}) ---")
        generate_image(
            prompt=prompt,
            filename=f"tree_{size}",
            size=size
            # Uses default model: stabilityai/sdxl-turbo
        )
        
        # Delay between requests
        if idx < len(sizes):
            print(f"⏳ Waiting {REQUEST_DELAY}s before next request...")
            time.sleep(REQUEST_DELAY)
    
    print("\n✓ Size options test complete!")

def test_interactive():
    """Interactive mode - enter your own prompts"""
    print("\n" + "="*60)
    print("TEST 4: Interactive Mode")
    print("="*60)
    print("Enter your own prompts to test the API.\n")
    
    while True:
        prompt = input("\n🎨 Enter image prompt (or 'quit' to exit): ").strip()
        
        if prompt.lower() in ['quit', 'exit', 'q']:
            break
        
        if not prompt:
            print("⚠ Please enter a valid prompt")
            continue
        
        # Ask for model
        print("\nAvailable models (pricing per 100 images):")
        print("1. SDXL Turbo - very fast, cheapest ($0.02/100, default)")
        print("2. FLUX-2-klein-4b - balanced ($0.06/100)")
        print("3. FLUX-2-klein-9b - high quality ($0.08/100)")
        model_choice = input("Choose model (1-3, default=1): ").strip() or "1"
        
        models = {
            "1": "stabilityai/sdxl-turbo",
            "2": "black-forest-labs/FLUX-2-klein-4b",
            "3": "black-forest-labs/FLUX-2-klein-9b"
        }
        
        model = models.get(model_choice, models["1"])
        
        generate_image(prompt, model=model)
    
    print("\n✓ Interactive mode ended!")

def main():
    """Main test menu"""
    print("="*60)
    print("ImageRouter.io Image Generation Test Script")
    print("="*60)
    print("\nImageRouter.io Features:")
    print("✅ OpenAI-compatible API")
    print("✅ 3 free images per day with API key")
    print("✅ Multiple AI models available (pricing per 100 images):")
    print("   • SDXL Turbo - $0.02 (very fast, default)")
    print("   • FLUX-2-klein-4b - $0.06 (balanced)")
    print("   • FLUX-2-klein-9b - $0.08 (high quality)")
    print("✅ Automatic provider fallback")
    print("✅ Generally better uptime than single providers")
    print(f"\n🔑 Using API Key: {API_KEY[:20]}...{API_KEY[-10:]}")
    
    print("\n" + "="*60)
    print("Select a test to run:")
    print("="*60)
    print("0. Single Image Test (RECOMMENDED - safest option)")
    print("1. Flashcard Objects (3 simple objects)")
    print("2. Model Comparison (test all 3 models)")
    print("3. Size Options (test different dimensions)")
    print("4. Interactive Mode (enter your own prompts)")
    print("5. Run All Tests (may use up free tier quickly!)")
    print("="*60)
    
    choice = input("\nEnter your choice (0-5): ").strip()
    
    tests = {
        '0': test_single_image,
        '1': test_flashcard_objects,
        '2': test_model_comparison,
        '3': test_size_options,
        '4': test_interactive
    }
    
    if choice == '5':
        print("\n⚠ WARNING: Running all tests will generate multiple images!")
        print("⚠ This will use several of your daily quota")
        confirm = input("Continue? (yes/no): ").strip().lower()
        if confirm == 'yes':
            for test_func in tests.values():
                test_func()
                print("\n" + "-"*60 + "\n")
    elif choice in tests:
        tests[choice]()
    else:
        print("❌ Invalid choice!")
        return
    
    print("\n" + "="*60)
    print("🎉 Test complete!")
    print("="*60)
    print(f"Images saved to: {OUTPUT_DIR}/")
    print("\nNext steps:")
    print("1. Check the generated images in the output folder")
    print("2. Compare quality vs. other services (Pollinations, etc.)")
    print("3. Choose preferred model for your flashcards")
    print("4. Review pricing at: https://imagerouter.io/pricing")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
