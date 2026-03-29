# Bilingual Trainer MCP Server

This MCP (Model Context Protocol) server allows GitHub Copilot to interact with your BilingualTrainer database.

## Setup

1. **Install dependencies** (already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure VS Code**:
   - The MCP server is configured in `.vscode/mcp.json`
   - Restart VS Code to activate the connection

## Available Tools

The MCP server provides three tools for Copilot to use:

### 1. `query_flashcards(sql: str)`
Run any read-only SQL query against the BilingualTrainer database.

**Example queries:**
```sql
-- Get all words
SELECT * FROM Word_Image LIMIT 10;

-- Get Spanish flashcards
SELECT w.english_word, t.translated_word, w.image_file
FROM Word_Image w 
JOIN Translation t ON w.id = t.word_id 
WHERE t.language_code = 'es';

-- Count translations per language
SELECT language_code, COUNT(*) 
FROM Translation 
GROUP BY language_code;
```

### 2. `get_word_translations(english_word: str)`
Get all translations for a specific word.

**Example:**
```python
get_word_translations("cat")
# Returns: {"english_word": "cat", "image_file": "cat_0.png", 
#           "translations": [{"language": "es", "word": "gato"}, ...]}
```

### 3. `get_language_stats()`
Get database statistics - total words and translations per language.

**Returns:**
```python
{
    "total_words": 25,
    "languages": [
        {"code": "es", "count": 25},
        {"code": "fr", "count": 25},
        {"code": "vi", "count": 25}
    ]
}
```

## Using with GitHub Copilot

Once configured, you can ask Copilot things like:

- "How many Spanish translations are in the database?"
- "Show me all the animal words we have"
- "What are the Vietnamese translations for food items?"
- "Get the translation for 'dog' in all languages"

Copilot will automatically use the MCP tools to query your database and provide answers.

## Database Schema

**Word_Image table:**
- `id` - INTEGER PRIMARY KEY
- `english_word` - TEXT
- `image_file` - TEXT

**Translation table:**
- `id` - INTEGER PRIMARY KEY
- `word_id` - INTEGER (foreign key to Word_Image.id)
- `language_code` - TEXT ('es', 'fr', 'vi')
- `translated_word` - TEXT

## Troubleshooting

If the MCP server isn't working:

1. Check that the virtual environment exists at `.venv/`
2. Verify `fastmcp` is installed: `.venv/Scripts/python.exe -m pip list | Select-String fastmcp`
3. Restart VS Code after making changes to `mcp.json`
4. Check VS Code Output panel for MCP server logs
