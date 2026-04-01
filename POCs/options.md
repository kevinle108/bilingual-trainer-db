- pollinations.ai
    - ⚠️ Very strict rate limits (10s+ delays)
    - ❌ Not practical for bulk generation
    - ✅ Free, no API key
- imagerouter.io ⭐ RECOMMENDED
    - ✅ 3 free images/day with API key
    - ✅ Get free key: https://imagerouter.io/api-keys
    - ✅ Add to .env: IMAGE_ROUTER_API_KEY=your_key
    - ✅ OpenAI-compatible API
    - ✅ Better rate limits (2s delays)
    - ✅ Multiple models with auto-fallback
    - Models:
        - stabilityai/sdxl-turbo (very fast, cheapest) - $0.02/100
        - black-forest-labs/FLUX-2-klein-4b (balanced) - $0.06/100
        - black-forest-labs/FLUX-2-klein-9b (high quality) - $0.08/100 
    - API: https://api.imagerouter.io/v1/openai/images/generations
- google ai 
- https://fal.ai/models/fal-ai/gpt-image-1-mini
- openai gpt image


- use Tavily to search the internet for a image link to the word


---

- a simple picture of a house, suitable for a kid's flashcard
- I am making flashcards for children and need a simple art for the card respresenting "car" on a blank background

- a cute picture of a bunny, suitable for a kid's flashcard

Pricing per 100 images:
- stabilityai/sdxl-turbo -> $0.02 
- black-forest-labs/FLUX-2-klein-4b -> $0.06 
- black-forest-labs/FLUX-2-klein-9b -> $0.08

Eliminated:
- black-forest-labs/FLUX-1-schnell -> $0.13

Conclusion:
black-forest-labs/FLUX-2-klein-9b -> $0.08
prompt = "a cute picture of a computer mouse with no text, suitable for a kid's flashcard"