"""
Pollinations.ai Image Generation Test Script
Test API for generating flashcard images using Pollinations.ai

API Documentation: https://pollinations.ai/
Endpoint: https://image.pollinations.ai/prompt/{prompt}
"""

import requests
import os
import time
from urllib.parse import quote

# Test configuration
OUTPUT_DIR = "test_images"
API_BASE_URL = "https://image.pollinations.ai/prompt"
REQUEST_DELAY = 10  # Seconds between requests to avoid rate limiting (increased due to strict limits)
MAX_RETRIES = 2     # Max retries for failed requests (reduced to avoid long waits)

def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"✓ Created directory: {OUTPUT_DIR}")

def generate_image(prompt: str, filename: str = None, width: int = 512, height: int = 512, model: str = "flux") -> str:
    """
    Generate an image using Pollinations.ai
    
    Args:
        prompt: Text description of the image
        filename: Output filename (without extension)
        width: Image width (default: 512)
        height: Image height (default: 512)
        model: AI model to use (default: "flux", alternatives: "turbo")
    
    Returns:
        Path to saved image file
    """
    ensure_output_dir()
    
    # Create safe filename
    if not filename:
        safe_prompt = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = safe_prompt.replace(' ', '_').lower()[:50]
    
    # Encode the prompt for URL
    encoded_prompt = quote(prompt)
    
    # Build URL with parameters
    # Pollinations.ai supports various parameters
    url = f"{API_BASE_URL}/{encoded_prompt}"
    params = {
        "width": width,
        "height": height,
        "model": model,
        "nologo": "true",  # Remove Pollinations logo
        "enhance": "true"   # Enhance prompt automatically
    }
    
    print(f"\n🎨 Generating image...")
    print(f"   Prompt: {prompt}")
    print(f"   Model: {model}")
    print(f"   Size: {width}x{height}")
    
    # Retry logic for rate limiting
    for attempt in range(MAX_RETRIES):
        try:
            # Make request
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Save image
            output_path = os.path.join(OUTPUT_DIR, f"{filename}.jpg")
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024  # Size in KB
            print(f"✓ Success! Saved to: {output_path}")
            print(f"   File size: {file_size:.1f} KB")
            
            return output_path
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = (attempt + 1) * 10  # Exponential backoff: 10s, 20s
                print(f"⚠ Rate limited. Waiting {wait_time}s before retry {attempt + 1}/{MAX_RETRIES}...")
                time.sleep(wait_time)
            else:
                print(f"✗ HTTP Error: {e}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Error generating image: {e}")
            return None
    
    print(f"✗ Failed after {MAX_RETRIES} retries")
    return None

def test_single_image():
    """Test with just ONE image (safest option)"""
    print("\n" + "="*60)
    print("TEST: Single Image (Safest - No Rate Limiting)")
    print("="*60)
    
    prompt = "a red apple on white background, simple, centered"
    generate_image(prompt, filename="test_apple", width=512, height=512)

def test_simple_objects():
    """Test generation with simple object prompts (good for flashcards)"""
    print("\n" + "="*60)
    print("TEST 1: Simple Objects (Flashcard Style)")
    print("="*60)
    print("⚠️ WARNING: This will take ~50 seconds with 10s delays between requests")
    print()
    
    test_prompts = [
        "a red apple on white background, simple, centered",
        "a yellow banana on white background, simple, centered",
        "a cute cat on white background, simple, centered",
        "a blue car on white background, simple, centered",
        "a green tree on white background, simple, centered"
    ]
    
    for i, prompt in enumerate(test_prompts):
        generate_image(prompt, width=512, height=512)
        if i < len(test_prompts) - 1:  # Don't wait after last image
            print(f"⏳ Waiting {REQUEST_DELAY}s before next request...")
            time.sleep(REQUEST_DELAY)

def test_different_styles():
    """Test different artistic styles"""
    print("\n" + "="*60)
    print("TEST 2: Different Styles")
    print("="*60)
    
    base_object = "a dog"
    styles = [
        "realistic photo",
        "cartoon illustration",
        "flat design icon",
        "3D render",
        "watercolor painting"
    ]
    
    for i, style in enumerate(styles):
        prompt = f"{base_object}, {style}, white background, high quality"
        filename = f"dog_{style.replace(' ', '_')}"
        generate_image(prompt, filename=filename)
        if i < len(styles) - 1:
            print(f"⏳ Waiting {REQUEST_DELAY}s before next request...")
            time.sleep(REQUEST_DELAY)

def test_vocabulary_words():
    """Test with actual vocabulary words for flashcards"""
    print("\n" + "="*60)
    print("TEST 3: Vocabulary Words")
    print("="*60)
    print("⚠️ WARNING: This will take ~50 seconds with 10s delays between requests")
    print()
    
    # Reduced to 3 words to avoid excessive rate limiting
    vocab_words = [
        ("carrot", "an orange carrot, simple, centered, white background"),
        ("fish", "a blue fish, simple, centered, white background"),
        ("frog", "a green frog, simple, centered, white background"),
        ("duck", "a yellow rubber duck toy, simple, clean background"),
        ("book", "a closed book, simple illustration, white background"),
        ("elephant", "a gray elephant, side view, cartoon style, white background"),
        ("strawberry", "a red strawberry, simple, centered, white background"),
    ]
    
    for i, (word, prompt) in enumerate(vocab_words):
        print(f"\nWord: {word.upper()}")
        generate_image(prompt, filename=word)
        if i < len(vocab_words) - 1:
            print(f"⏳ Waiting {REQUEST_DELAY}s before next request...")
            time.sleep(REQUEST_DELAY)

def test_models():
    """Test different AI models"""
    print("\n" + "="*60)
    print("TEST 4: Different Models")
    print("="*60)
    
    prompt = "a red strawberry on white background, simple, centered"
    models = ["flux", "turbo"]
    
    for i, model in enumerate(models):
        print(f"\nTesting model: {model}")
        filename = f"strawberry_{model}"
        generate_image(prompt, filename=filename, model=model)
        if i < len(models) - 1:
            print(f"⏳ Waiting {REQUEST_DELAY}s before next request...")
            time.sleep(REQUEST_DELAY)

def test_sizes():
    """Test different image sizes"""
    print("\n" + "="*60)
    print("TEST 5: Different Sizes")
    print("="*60)
    
    prompt = "an orange on white background, simple, centered"
    sizes = [
        (256, 256, "small"),
        (512, 512, "medium"),
        (1024, 1024, "large")
    ]
    
    for i, (width, height, label) in enumerate(sizes):
        print(f"\nSize: {label} ({width}x{height})")
        filename = f"orange_{label}"
        generate_image(prompt, filename=filename, width=width, height=height)
        if i < len(sizes) - 1:
            print(f"⏳ Waiting {REQUEST_DELAY}s before next request...")
            time.sleep(REQUEST_DELAY)

def interactive_mode():
    """Interactive mode - generate custom images"""
    print("\n" + "="*60)
    print("INTERACTIVE MODE")
    print("="*60)
    print("Enter your own prompts to generate images.")
    print("Tips for flashcard images:")
    print("  - Keep it simple and clear")
    print("  - Mention 'white background' or 'simple background'")
    print("  - Add 'centered' or 'front view' for consistency")
    print("  - Use 'cartoon' or 'illustration' for kid-friendly style")
    print("\nType 'quit' to exit.\n")
    
    while True:
        prompt = input("Enter prompt (or 'quit'): ").strip()
        
        if prompt.lower() == 'quit':
            break
        
        if not prompt:
            continue
        
        generate_image(prompt)
        print()

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("POLLINATIONS.AI IMAGE GENERATION TEST")
    print("="*60)
    print("Testing image generation for flashcard images")
    print()
    
    # Run tests
    tests = [
        ("0", "Single Image Test (RECOMMENDED - No rate limits)", test_single_image),
        ("1", "Simple Objects (5 images, ~50s)", test_simple_objects),
        ("2", "Different Styles (5 images, ~50s)", test_different_styles),
        ("3", "Vocabulary Words (3 images, ~30s)", test_vocabulary_words),
        ("4", "Different Models (2 images, ~20s)", test_models),
        ("5", "Different Sizes (3 images, ~30s)", test_sizes),
        ("i", "Interactive Mode (1 image at a time)", interactive_mode),
        ("a", "Run All Tests (NOT RECOMMENDED - will take 3+ minutes)", None)
    ]
    
    print("Choose a test to run:")
    for key, name, _ in tests:
        print(f"  {key}: {name}")
    print()
    
    choice = input("Enter choice (or 'q' to quit): ").strip().lower()
    
    if choice == 'q':
        print("Exiting...")
        return
    
    if choice == 'a':
        # Run all tests except interactive
        for key, name, func in tests[:-2]:  # Exclude interactive and "all"
            func()
    elif choice == 'i':
        interactive_mode()
    else:
        # Run selected test
        for key, name, func in tests:
            if key == choice and func:
                func()
                break
        else:
            print("Invalid choice!")
    
    print("\n" + "="*60)
    print(f"✓ Done! Check the '{OUTPUT_DIR}' folder for generated images.")
    print("="*60)

if __name__ == "__main__":
    main()
