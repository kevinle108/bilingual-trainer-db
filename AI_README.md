# Bilingual Trainer - AI Chatbot with LangChain

## Overview
The chatbot feature now uses **LangChain** with GitHub Models API to provide intelligent, context-aware language learning assistance!

## ✨ New LangChain Features

### 🧠 Server-Side Conversation Memory
- **Managed Sessions**: Each chat session has its own conversation memory
- **Context Awareness**: The AI remembers previous questions and answers
- **Smart Context Window**: Maintains recent conversation history for better responses

### 📋 Structured Output Parsing
- **Type-Safe Responses**: Uses Pydantic models for quiz evaluation
- **Reliable JSON**: No more manual JSON parsing with regex
- **Consistent Format**: Guaranteed response structure

### 🔄 Better Prompt Management
- **Chat Templates**: Uses LangChain's `ChatPromptTemplate` for cleaner prompts
- **Message Types**: Proper system/user/assistant message handling
- **Flexible Chains**: Easy to modify or extend the conversation flow

### 🛡️ Enhanced Error Handling
- **Graceful Fallbacks**: If LangChain fails, falls back to simple matching
- **Better Logging**: Detailed error messages for debugging
- **Retry Logic**: Built-in LangChain retry mechanisms

## Features
✨ **Smart Answer Checking**: Accepts synonyms and minor spelling variations (e.g., "bunny" = "rabbit")
🎯 **Context-Aware Hints**: Provides helpful hints in practice mode based on conversation history
💬 **Natural Conversations**: Real conversations with memory of what you discussed
🧠 **Intelligent Feedback**: Explains why answers are right or wrong
📝 **Structured Responses**: Reliable JSON formatting with Pydantic validation

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

This now includes:
- `langchain>=0.1.0` - Core LangChain framework
- `langchain-openai>=0.0.5` - OpenAI integration
- `langchain-core>=0.1.0` - Core components

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

### LangChain Architecture

```
User Input → Frontend (generates sessionId)
     ↓
Flask /api/chat endpoint
     ↓
ConversationSession (manages state)
     ↓
ChatPromptTemplate (structures prompt)
     ↓
ChatOpenAI (calls GitHub Models API)
     ↓
JsonOutputParser (parses response)
     ↓
Response → Frontend → User
```

### Session Management
Each user gets a unique session ID:
```javascript
const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(7);
```

The server maintains conversation history per session:
```python
class ConversationSession:
    def __init__(self, language_name: str):
        self.language_name = language_name
        self.messages = []  # LangChain message objects
        self.current_card = None
        self.mode = 'quiz'
```

### Structured Output with Pydantic

Quiz responses use a defined schema:
```python
class QuizEvaluation(BaseModel):
    correct: bool = Field(description="Whether the student's answer is correct")
    message: str = Field(description="Encouraging feedback message")
    explanation: str = Field(default="", description="Optional explanation")
```

This ensures:
- ✅ Always get `correct` (boolean)
- ✅ Always get `message` (string)
- ✅ Optional `explanation` field
- ✅ Type validation by Pydantic

### Prompt Templates

LangChain templates make prompts cleaner:
```python
quiz_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a language tutor..."),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    HumanMessage(content="Current quiz question...")
])
```

### Chains

Simple composition pattern:
```python
chain = prompt | llm | parser
result = chain.invoke({"chat_history": session.get_recent_messages()})
```

## API Endpoint
The `/api/chat` endpoint now uses LangChain:

**POST** `/api/chat`

Request body:
```json
{
  "message": "user's answer",
  "currentCard": {"english_word": "cat", "translated_word": "mèo"},
  "mode": "quiz",
  "languageName": "Vietnamese",
  "sessionId": "session_1234567890_abc"
}
```

Response (quiz mode):
```json
{
  "correct": true,
  "message": "Great job! That's correct! 🎉",
  "explanation": "You recognized the synonym correctly!"
}
```

Response (conversation mode):
```json
{
  "message": "That's a great question! Let's practice more vocabulary together. 😊"
}
```

## Advantages over Previous Implementation

| Feature | Before (Raw OpenAI) | After (LangChain) |
|---------|-------------------|-------------------|
| **Conversation Memory** | Manual array management | Automatic session management |
| **Context Handling** | Sent history with each request | Server-side managed state |
| **Output Parsing** | Regex + try/catch | Structured Pydantic models |
| **Prompt Templates** | F-strings | ChatPromptTemplate |
| **Error Handling** | Basic try/catch | Built-in retries + fallbacks |
| **Extensibility** | Hard to add features | Easy to add tools/agents |
| **Type Safety** | Runtime JSON parsing | Compile-time type checking |

## Available Models
- `openai/gpt-4o-mini` (default, fast and cost-effective)
- `openai/gpt-4o` (more powerful)
- `meta-llama/Llama-3.3-70B-Instruct`
- And more available on GitHub Models

## Troubleshooting

### "AI service not configured" error
- Make sure your `.env` file exists and has `GITHUB_TOKEN` set
- Restart the Flask server after creating/modifying `.env`

### Import errors for LangChain
- Run `pip install -r requirements.txt` again
- Make sure you're in the virtual environment

### AI responses are slow
- Try switching to `gpt-4o-mini` in `.env` for faster responses
- Check your internet connection

### Session memory not working
- Sessions are stored in-memory (will reset on server restart)
- For production, consider using Redis or database storage

## Future Enhancements

With LangChain integrated, you can easily add:

1. **Tools/Agents**: Let the AI look up vocabulary in the database
2. **RAG (Retrieval)**: Search for related vocabulary during conversation
3. **Custom Chains**: Multi-step reasoning for complex language questions
4. **Streaming**: Stream AI responses token-by-token
5. **Memory Backends**: Persistent conversation storage (Redis, PostgreSQL)
6. **Multiple Agents**: Specialized agents for different learning modes

## Development Notes

The LangChain integration provides:
- **Better Architecture**: Separation of concerns (prompts, models, parsers)
- **Type Safety**: Pydantic models catch errors early
- **Extensibility**: Easy to add new features (tools, memory backends, etc.)
- **Production Ready**: Built-in error handling and retries
- **Testability**: Each component can be tested independently

Enjoy learning with your LangChain-powered language tutor! 🚀
