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

The MCP server provides **9 tools** for full CRUD operations:

### Read Operations

#### 1. `query_flashcards(sql: str)`
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

#### 2. `get_word_translations(english_word: str)`
Get all translations for a specific word.

**Example:**
```python
get_word_translations("cat")
# Returns: {"english_word": "cat", "image_file": "cat_0.png", 
#           "translations": [{"language": "es", "word": "gato"}, ...]}
```

#### 3. `get_language_stats()`
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

### Create Operations

#### 4. `add_flashcard(english_word: str, image_file: str, translations: dict)`
Add a new flashcard with translations.

**Example:**
```python
add_flashcard("apple", "apple.png", {
    "es": "manzana",
    "fr": "pomme", 
    "vi": "táo"
})
```

#### 5. `add_translation(english_word: str, language_code: str, translated_word: str)`
Add a translation to an existing word.

**Example:**
```python
add_translation("cat", "de", "Katze")  # Add German translation
```

### Update Operations

#### 6. `update_word(english_word: str, new_english_word: str, new_image_file: str)`
Update a word's English name or image file.

**Example:**
```python
update_word("cat", new_image_file="cat_new.png")
update_word("bunny", new_english_word="rabbit")
```

#### 7. `update_translation(english_word: str, language_code: str, new_translated_word: str)`
Update an existing translation.

**Example:**
```python
update_translation("cat", "es", "gatito")  # Change from "gato" to "gatito"
```

### Delete Operations

#### 8. `delete_flashcard(english_word: str)`
Delete a flashcard and all its translations.

**Example:**
```python
delete_flashcard("pizza")  # Removes word and all translations
```

#### 9. `delete_translation(english_word: str, language_code: str)`
Delete a specific translation.

**Example:**
```python
delete_translation("pizza", "fr")  # Remove only French translation
```

## Using with GitHub Copilot

Once configured, you can ask Copilot to perform CRUD operations:

**Read/Query:**
- "How many Spanish translations are in the database?"
- "Show me all the animal words we have"
- "What are the Vietnamese translations for food items?"
- "Get the translation for 'dog' in all languages"

**Create:**
- "Add a new flashcard for 'apple' with Spanish 'manzana', French 'pomme', and Vietnamese 'táo'"
- "Add a German translation for 'cat'"
- "Create a flashcard for 'table' with the image 'table.png'"

**Update:**
- "Change the image file for 'dog' to 'dog_new.png'"
- "Update the Spanish translation of 'cat' to 'gatito'"
- "Rename 'bunny' to 'rabbit'"

**Delete:**
- "Remove the French translation for 'pizza'"
- "Delete the entire flashcard for 'computer'"

Copilot will automatically use the appropriate MCP tools to make changes to your database!

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
