# Image Generation Service Testing

Testing various AI image generation services for flashcard creation.

## Available Services

### 1. Pollinations.ai

**Pollinations.ai** is a FREE AI image generation service with:
- ✅ **No API key required**
- ✅ **Simple REST API**
- ✅ **Multiple AI models** (Flux, Turbo)
- ✅ **Open source and free to use**
- ⚠️ **STRICT rate limits** (requires 10+ second delays between requests)
- ⚠️ **Not ideal for bulk generation** (generating 10 flashcards would take 2+ minutes)

### 2. ImageRouter.io (NEW!)

**ImageRouter.io** is an AI image generation API aggregator with:
- ✅ **3 free images per day** (no signup required)
- ✅ **OpenAI-compatible API**
- ✅ **Multiple models** (FLUX.1-schnell, SDXL Turbo, and more)
- ✅ **Better uptime** (automatic provider fallback)
- ✅ **Faster rate limits** (2s delays instead of 10s)
- ✅ **Optional API key** for unlimited usage
- ✅ **Better for testing** than Pollinations

**Recommended**: Start with **ImageRouter.io** for testing!

---

## Quick Start

### ImageRouter.io (Recommended)

```bash
# Navigate to POCs folder
cd POCs

# Run the ImageRouter test script
python imagerouter-image-gen.py
```

**Start with Option 0** (Single Image Test) to verify API connectivity!

Features:
- 3 free images per day with API key
- Get your free API key at: https://imagerouter.io/api-keys
- Add to `.env` file as: `IMAGE_ROUTER_API_KEY=your_key_here`
- Faster than Pollinations (2s delays vs 10s)

### Pollinations.ai

```bash
# Navigate to POCs folder
cd POCs

# Run the Pollinations test script
python pollinations-image-gen.py
```

**⚠️ IMPORTANT**: Due to strict rate limiting, start with **Option 0** (Single Image Test)!

---

## ImageRouter.io Details

### Features
- **Endpoint**: `https://api.imagerouter.io/v1/openai/images/generations`
- **Free Tier**: 3 images per day with free API key
- **API Key**: Required - get at https://imagerouter.io/api-keys
- **Setup**: Add `IMAGE_ROUTER_API_KEY=your_key` to `.env` file
- **Models**: 
  - `stabilityai/sdxl-turbo` (very fast, cheapest) - $0.02/100 images
  - `black-forest-labs/FLUX-2-klein-4b` (balanced) - $0.06/100 images
  - `black-forest-labs/FLUX-2-klein-9b` (high quality) - $0.08/100 images
- **Rate Limits**: Reasonable (2-3s delays recommended)
- **Format**: OpenAI-compatible API

### Usage Example

```python
import requests
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
api_key = os.getenv('IMAGE_ROUTER_API_KEY')

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"  # Required
}

payload = {
    "prompt": "a red apple on white background",
    "model": "stabilityai/sdxl-turbo",  # Default model
    "size": "512x512",
    "n": 1
}

response = requests.post(
    "https://api.imagerouter.io/v1/openai/images/generations",
    headers=headers,
    json=payload
)

result = response.json()
image_url = result['data'][0]['url']
```

### Available Models
- `stabilityai/sdxl-turbo` - Very fast generation, cheapest ($0.02/100 images)
- `black-forest-labs/FLUX-2-klein-4b` - Balanced speed/quality ($0.06/100 images)
- `black-forest-labs/FLUX-2-klein-9b` - High quality ($0.08/100 images)
- Many more at: https://imagerouter.io/models

---

## Pollinations.ai Details

```bash
# Navigate to POCs folder
cd POCs

# Run the test script
python pollinations-image-gen.py
```

**⚠️ IMPORTANT**: Due to strict rate limiting, start with **Option 0** (Single Image Test) first!

The full batch tests require 10-second delays between each image to avoid 429 errors.

## Usage

The script offers several test modes:

### 0. Single Image Test (RECOMMENDED)
Generates just ONE image - perfect for testing without rate limit issues.
- Best option to start with
- No delays needed
- Immediate result

### 1. Simple Objects Test
Generates basic objects with clean backgrounds (ideal for flashcards)
- Apple, banana, cat, car, tree
- ⚠️ Takes ~50 seconds (10s delays between each)

### 2. Different Styles Test
Same object in various artistic styles:
- Realistic photo
- Cartoon illustration
- Flat design
- 3D render
- Watercolor

### 3. Vocabulary Words Test
Tests with actual flashcard vocabulary:
- Duck, book, elephant (reduced to 3 to avoid rate limits)
- ⚠️ Takes ~30 seconds

### 4. Model Comparison
Compares different AI models:
- **Flux**: High quality, slower
- **Turbo**: Fast generation

### 5. Size Testing
Tests different image dimensions:
- Small: 256x256
- Medium: 512x512
- Large: 1024x1024

### 6. Interactive Mode
Enter your own prompts!

## API Details

### Endpoint
```
https://image.pollinations.ai/prompt/{your-prompt}
```

### Rate Limits
⚠️ **CRITICAL**: Pollinations.ai has **VERY STRICT** rate limiting
- Wait **10+ seconds** between requests (even this sometimes fails)
- 429 errors (Too Many Requests) occur frequently with shorter delays
- The test script includes automatic retry with exponential backoff (10s, 20s)
- **Not practical for bulk generation** - generating 10 flashcards takes 2+ minutes
- **Best for**: Single images, occasional use, testing
- **Not good for**: Bulk flashcard generation, real-time generation

**Recommendation**: Use Pollinations.ai for testing only. For production, consider:
- Wikimedia Commons (despite occasional 403s, it's faster for bulk operations)
- Paid APIs (Unsplash, Pexels have generous free tiers)
- Pre-generated image libraries
- Local caching strategies

### Parameters
- `width`: Image width (default: 1024)
- `height`: Image height (default: 1024)
- `model`: AI model ("flux" or "turbo")
- `nologo`: Remove watermark (true/false)
- `enhance`: Auto-enhance prompt (true/false)

### Example
```python
from urllib.parse import quote
import requests

prompt = "a red apple on white background"
encoded = quote(prompt)
url = f"https://image.pollinations.ai/prompt/{encoded}"

params = {
    "width": 512,
    "height": 512,
    "model": "flux",
    "nologo": "true"
}

response = requests.get(url, params=params)
with open("apple.jpg", "wb") as f:
    f.write(response.content)
```

## Tips for Flashcard Images

### Good Prompts
✅ "a red apple on white background, simple, centered"
✅ "a yellow banana, clean background, front view"
✅ "a cute cat, cartoon style, white background"
✅ "a blue car, side view, simple illustration"

### Bad Prompts
❌ "apple" (too vague)
❌ "apple in a forest with mountains" (too complex)
❌ "abstract apple art" (not clear for learning)

### Best Practices
1. **Be specific**: Mention the object clearly
2. **Simple background**: Use "white background" or "clean background"
3. **Centered**: Add "centered" for consistency
4. **Style**: Specify "cartoon", "illustration", or "simple"
5. **View**: Mention "front view", "side view", "top view" for consistency

## Output

Generated images are saved to `test_images/` folder in the POCs directory.

## Integration Ideas

Once tested, you can integrate into the main app:

1. **Replace Wikimedia Commons**: Use Pollinations instead of Commons
2. **Generate on demand**: Create images when generating flashcards
3. **Fallback option**: Try Pollinations if Commons fails
4. **Batch generation**: Generate images for all words at once

## Example Integration Code

```python
def fetch_pollinations_image(word: str) -> Optional[str]:
    """Fetch image from Pollinations.ai"""
    from urllib.parse import quote
    
    prompt = f"{word}, simple object, white background, centered"
    encoded = quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}"
    
    params = {
        "width": 512,
        "height": 512,
        "model": "flux",
        "nologo": "true"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        filename = f"{word}_{int(time.time())}.jpg"
        path = os.path.join('image-library', filename)
        
        with open(path, 'wb') as f:
            f.write(response.content)
        
        return filename
    except Exception as e:
        print(f"Error: {e}")
        return None
```

## Service Comparison

| Feature | ImageRouter.io | Pollinations.ai | Wikimedia Commons |
|---------|---------------|-----------------|-------------------|
| **API Key** | Optional (3/day free) | Not required | Not required |
| **Rate Limits** | Moderate (2s) | Very strict (10s+) | Loose |
| **Success Rate** | ~90% | ~70% (with retries) | ~60-70% |
| **Bulk Generation** | Good (30s for 10) | Poor (2+ min for 10) | Good (20s for 10) |
| **Consistency** | High (same style) | High (same style) | Variable |
| **Customization** | Full control | Full control | Limited |
| **Speed (single)** | 3-5s | 10-20s (with delays) | 1-2s |
| **Quality** | AI-generated (excellent) | AI-generated (good) | Real photos |
| **Copyright** | Free to use | Free to use | CC licensed |
| **Best for** | Flashcards, testing | Testing only | Bulk, production |

**Recommendations**:
- **Testing**: ImageRouter.io (best balance of quality, speed, and ease)
- **Production (small scale)**: ImageRouter.io with API key
- **Production (bulk)**: Wikimedia Commons or paid API
- **Avoid**: Pollinations.ai for anything beyond single images

---

## Next Steps

After testing both services:

1. **Run ImageRouter test** first (Option 0 for single image)
2. **Compare results** with Pollinations version
3. **Test with your vocabulary words** using interactive mode
4. **Choose best service** based on quality and rate limits
5. **Get API key** if you like ImageRouter (https://imagerouter.io/api-keys)
6. **Integrate** chosen service into `app.py`
7. **Update generator UI** to offer image generation option

## Resources

### ImageRouter.io
- **Website**: https://imagerouter.io/
- **API Keys**: https://imagerouter.io/api-keys
- **Documentation**: https://docs.imagerouter.io/
- **Models**: https://imagerouter.io/models
- **Pricing**: https://imagerouter.io/pricing

### Pollinations.ai
- **Website**: https://pollinations.ai/
- **GitHub**: https://github.com/pollinations/pollinations
- **API**: Simple REST API (no official docs)

Enjoy testing! 🎨
