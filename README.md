# Bilingual Trainer

A comprehensive AI-powered language learning application with interactive flashcards, an intelligent chatbot tutor, and automated flashcard generation. Built with Flask, LangChain, and GitHub Models API.

![Language Learning](https://img.shields.io/badge/Languages-Spanish%20%7C%20French%20%7C%20Vietnamese-blue)
![AI Powered](https://img.shields.io/badge/AI-LangChain%20%7C%20GPT--4o--mini-green)
![MCP](https://img.shields.io/badge/MCP-Copilot%20Integration-purple)

## 🌟 Features

### 📚 Interactive Flashcards
- **Multi-language Support**: Learn Spanish, French, and Vietnamese
- **Visual Learning**: Image-based flashcards for better memory retention
- **Organized Database**: SQLite backend with efficient storage
- **Clean Interface**: Easy-to-navigate flashcard viewer

### 🤖 AI Chatbot Tutor (LangChain-Powered)
- **Intelligent Answer Checking**: Accepts synonyms, typos, and variations
- **Conversation Memory**: Remembers context across the entire chat session
- **Two Modes**:
  - **Quiz Mode**: Tests your knowledge with immediate feedback
  - **Practice Mode**: Provides hints without giving away answers
- **Structured Responses**: Reliable JSON output using Pydantic validation
- **Encouraging Feedback**: Friendly, emoji-enhanced responses
- **Context-Aware**: Maintains conversation history for natural interactions

### ✨ AI Flashcard Generator
- **Custom Topics**: Generate flashcards on any theme (animals, food, travel, etc.)
- **Flexible Count**: Create 3-30 flashcards per generation
- **Automatic Images**: Optional Wikimedia Commons integration
- **Database Integration**: Generated cards are automatically saved
- **Duplicate Prevention**: Smart checking to avoid redundant entries
- **Multi-Language**: Supports all available languages

### 🔌 MCP Server (Model Context Protocol)
- **GitHub Copilot Integration**: Interact with your database through Copilot
- **11 CRUD Tools**: Full create, read, update, delete operations
- **Image Upload Support**: Add flashcards with images via chat
- **Query Flexibility**: Run custom SQL for advanced operations
- **Statistics**: Get language breakdowns and database stats

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- GitHub account with API access
- (Optional) ImageRouter API key for image generation

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd bilingual-trainer-db
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Mac/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Required for AI features
   GITHUB_TOKEN=your_github_token_here
   API_ENDPOINT=https://models.github.ai/inference
   MODEL_NAME=openai/gpt-4o-mini
   
   # Optional for image generation
   IMAGE_ROUTER_API_KEY=your_imagerouter_key_here
   ```

   To get a GitHub token:
   1. Go to https://github.com/settings/tokens
   2. Generate a personal access token
   3. Copy and paste into `.env`

5. **Initialize the database**
   ```bash
   python create_db.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Open your browser**
   ```
   http://localhost:5000
   ```

## 📖 Usage Guide

### Viewing Flashcards
1. From the home page, select a language (Spanish, French, or Vietnamese)
2. Click the flashcard cards to flip between English and translation
3. Navigate through your vocabulary collection

### Using the AI Chatbot
1. Click **"AI Chatbot"** for your chosen language
2. Choose your mode:
   - **Quiz Mode**: Type your answer to each flashcard prompt
   - **Practice Mode**: Get hints when you're stuck
3. Have natural conversations - the bot remembers your context!
4. Get instant feedback with explanations

**Chatbot Tips:**
- The AI accepts synonyms (e.g., "bunny" for "rabbit")
- Minor typos are forgiven
- Articles (a/an/the) are optional
- Use practice mode for learning, quiz mode for testing

### Generating Flashcards
1. Click **"✨ AI Flashcard Generator"** from home
2. Fill in the form:
   - **Theme**: e.g., "kitchen items", "travel phrases", "animals"
   - **Language**: Spanish, French, or Vietnamese
   - **Count**: 3-30 flashcards
   - **Details** (optional): Specify level, preferences
   - **Fetch Images**: Check to auto-download images from Wikimedia
3. Click **"✨ Generate Flashcards with AI"**
4. Wait 10-30 seconds
5. View your new flashcards immediately!

**Generation Examples:**
```
Theme: farm animals
Language: Vietnamese
Count: 10
Fetch Images: ✓
```

```
Theme: business vocabulary
Language: French
Count: 15
Details: Focus on beginner business terms
Fetch Images: ✗
```

### Using the MCP Server with Copilot

The MCP server allows GitHub Copilot to interact with your database directly!

#### Available MCP Tools:
- `query_flashcards` - Run SQL queries
- `get_word_translations` - Get all translations for a word
- `get_language_stats` - Database statistics
- `add_flashcard` - Add new flashcards
- `add_translation` - Add translation to existing word
- `add_flashcard_with_image` - Upload image + create flashcard
- `add_multiple_translations_with_image` - Batch add with image
- `update_word` - Update word details
- `update_translation` - Update translation
- `delete_flashcard` - Remove flashcard
- `delete_translation` - Remove specific translation

**Example Copilot Interactions:**
```
"Show me all Spanish flashcards about animals"
"Add a new flashcard for 'computer' in all three languages"
"How many Vietnamese words are in the database?"
"Update the French translation for 'cat' to 'chaton'"
```

## 🏗️ Architecture

### Technology Stack
- **Backend**: Flask (Python web framework)
- **AI/ML**: 
  - LangChain (conversation management)
  - GitHub Models API (GPT-4o-mini)
  - Pydantic (structured output validation)
- **Database**: SQLite with relational schema
- **Image Sources**: 
  - Wikimedia Commons (free, educational)
  - ImageRouter API (FLUX-2-klein-9b model)
- **MCP**: FastMCP for Copilot integration

### Database Schema
```sql
Word_Image
├── id (PRIMARY KEY)
├── english_word
└── image_file

Translation
├── id (PRIMARY KEY)
├── word_id (FOREIGN KEY)
├── language_code (es/fr/vi)
└── translated_word
```

### LangChain Architecture
```
User Input → Flask Endpoint
     ↓
Session Management (conversation memory)
     ↓
ChatPromptTemplate (structured prompts)
     ↓
ChatOpenAI (GitHub Models API)
     ↓
JsonOutputParser (Pydantic validation)
     ↓
Response → User Interface
```

## 📁 Project Structure
```
bilingual-trainer-db/
├── app.py                    # Main Flask application
├── create_db.py             # Database initialization
├── mcp_server.py            # MCP server for Copilot
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
│
├── templates/               # HTML templates
│   ├── index.html          # Home page
│   ├── flashcards.html     # Flashcard viewer
│   ├── chatbot.html        # AI chatbot interface
│   └── generator.html      # Flashcard generator
│
├── static/images/          # Static web images
├── image-library/          # Flashcard images
├── test_images/            # Test image assets
│
├── README.md               # This file
├── AI_README.md           # LangChain/Chatbot details
├── GENERATOR_README.md    # Generator user guide
├── MCP_README.md          # MCP server documentation
│
├── NOTES/                  # Development notes
├── POCs/                   # Proof of concepts
└── REFERENCE/              # Reference implementations
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GITHUB_TOKEN` | GitHub API token | ✅ Yes | - |
| `API_ENDPOINT` | GitHub Models endpoint | No | `https://models.github.ai/inference` |
| `MODEL_NAME` | LLM model to use | No | `openai/gpt-4o-mini` |
| `IMAGE_ROUTER_API_KEY` | ImageRouter API key | No (for generator) | - |

### Available Models
- `openai/gpt-4o-mini` (default - fast, cost-effective)
- `openai/gpt-4o` (more powerful)
- `meta-llama/Llama-3.3-70B-Instruct`
- More on [GitHub Models](https://github.com/marketplace/models)

## 🐛 Troubleshooting

### "AI service not configured" error
- Ensure `.env` file exists with `GITHUB_TOKEN`
- Restart Flask server after creating/modifying `.env`
- Verify token has necessary permissions

### LangChain import errors
```bash
pip install -r requirements.txt --upgrade
```

### Database errors
```bash
# Recreate database
python create_db.py
```

### MCP server not connecting
- Check `.vscode/mcp.json` configuration
- Restart VS Code
- Verify Python environment in config matches your virtual environment

### Images not displaying
- Check `image-library/` directory exists
- Verify image file paths in database
- Ensure Flask is serving from correct directory

## 📚 Additional Documentation

- **[AI_README.md](AI_README.md)** - Detailed LangChain implementation and chatbot features
- **[GENERATOR_README.md](GENERATOR_README.md)** - Complete flashcard generator guide
- **[MCP_README.md](MCP_README.md)** - MCP server setup and tool reference

## 🎯 Use Cases

### Students
- Build vocabulary in Spanish, French, or Vietnamese
- Practice with AI-powered quiz and hints
- Generate custom study sets for exams

### Teachers
- Create themed flashcard sets for lessons
- Track vocabulary coverage with database queries
- Use MCP to manage class materials

### Language Enthusiasts
- Self-study with intelligent tutoring
- Generate topic-specific vocabulary
- Build comprehensive personal dictionary

## 🔮 Future Enhancements
- [ ] User authentication and personal progress tracking
- [ ] Spaced repetition algorithm (SRS)
- [ ] Audio pronunciation support
- [ ] More languages (German, Italian, Japanese, etc.)
- [ ] Mobile app version
- [ ] Export flashcards to Anki format
- [ ] Collaborative learning features

## 🤝 Contributing
Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📄 License
This project is open source and available for educational purposes.

## 🙏 Acknowledgments
- **GitHub Models API** - AI model access
- **LangChain** - Conversation framework
- **Wikimedia Commons** - Free educational images
- **ImageRouter** - Image generation service
- **FastMCP** - Model Context Protocol implementation

---

**Happy Learning!** 🎓✨

For questions or support, please open an issue on GitHub.
