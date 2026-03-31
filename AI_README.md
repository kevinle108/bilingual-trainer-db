# Bilingual Trainer - AI Chatbot Setup

## Overview
The chatbot feature now uses real AI (via GitHub Models API) to provide intelligent language learning assistance!

## Features
✨ **Smart Answer Checking**: Accepts synonyms and minor spelling variations (e.g., "bunny" = "rabbit")
🎯 **Context-Aware Hints**: Provides helpful hints in practice mode
💬 **Natural Conversations**: Have real conversations about vocabulary
🧠 **Intelligent Feedback**: Explains why answers are right or wrong

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get GitHub Token
1. Go to https://github.com/settings/tokens
2. Generate a personal access token with appropriate permissions
3. Copy the token

### 3. Configure Environment Variables
Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your token:
```
GITHUB_TOKEN=your_github_token_here
API_ENDPOINT=https://models.github.ai/inference
MODEL_NAME=openai/gpt-4o-mini
```

### 4. Run the Application
```bash
python app.py
```

Visit http://localhost:5000 and click "AI Chatbot" for any language!

## How It Works

### AI-Powered Answer Checking
When you answer a quiz question, the chatbot:
1. Sends your answer to the AI with context (the correct answer, your answer, mode)
2. AI evaluates if your answer is correct, considering:
   - Exact matches
   - Synonyms (bunny/rabbit, dog/puppy)
   - Minor typos
   - Plural/singular forms
   - Articles (a/an/the)
3. Provides encouraging, contextual feedback

### Fallback Mode
If the AI service is unavailable, the chatbot falls back to simple exact string matching.

## Available Models
- `openai/gpt-4o-mini` (default, fast and cost-effective)
- `openai/gpt-4o` (more powerful)
- `meta-llama/Llama-3.3-70B-Instruct`
- And more available on GitHub Models

## API Endpoint
The `/api/chat` endpoint handles AI interactions:
- **POST** `/api/chat`
- Request body:
  ```json
  {
    "message": "user's answer",
    "currentCard": {"english_word": "cat", "translated_word": "mèo"},
    "mode": "quiz",
    "languageName": "Vietnamese",
    "history": [...]
  }
  ```
- Response:
  ```json
  {
    "correct": true,
    "message": "Great job! That's correct! 🎉",
    "explanation": "Optional explanation"
  }
  ```

## Troubleshooting

### "AI service not configured" error
- Make sure your `.env` file exists and has `GITHUB_TOKEN` set
- Restart the Flask server after creating/modifying `.env`

### AI responses are slow
- Try switching to `gpt-4o-mini` in `.env` for faster responses
- Check your internet connection

### Fallback to simple matching
- Check if your GitHub token is valid
- Verify the API endpoint is accessible
- Check console logs for error details

## Development Notes

The AI integration uses:
- **OpenAI Python SDK** configured for GitHub Models endpoint
- **Conversation history** tracking for context-aware responses
- **JSON response format** for structured answer evaluation
- **Graceful fallback** to simple string matching if AI fails

Enjoy learning with your AI-powered language tutor! 🚀
