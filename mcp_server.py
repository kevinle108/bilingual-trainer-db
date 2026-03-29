from fastmcp import FastMCP
import sqlite3

mcp = FastMCP("bilingual-trainer")

@mcp.tool()
def query_flashcards(sql: str):
    """Run a read-only SQL query against BilingualTrainer.db and return rows as a list.
    
    Database schema:
    
    Table: Word_Image
    - id (INTEGER PRIMARY KEY)
    - english_word (TEXT)
    - image_file (TEXT)
    
    Table: Translation
    - id (INTEGER PRIMARY KEY)
    - word_id (INTEGER, foreign key to Word_Image.id)
    - language_code (TEXT, e.g., 'es', 'fr', 'vi')
    - translated_word (TEXT)
    
    Example queries:
    - SELECT * FROM Word_Image LIMIT 10;
    - SELECT w.english_word, t.translated_word, t.language_code 
      FROM Word_Image w JOIN Translation t ON w.id = t.word_id 
      WHERE t.language_code = 'es';
    - SELECT COUNT(*) as total FROM Translation WHERE language_code = 'vi';
    - SELECT DISTINCT language_code FROM Translation;
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    try:
        cur.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        # return as list of dicts for easier client use
        result = [dict(zip(cols, row)) for row in rows]
        return {"rows": result, "count": len(result)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@mcp.tool()
def get_word_translations(english_word: str):
    """Get all translations for a specific English word.
    
    Args:
        english_word: The English word to get translations for (e.g., 'cat', 'dog')
    
    Returns:
        Dictionary with the word info and all its translations
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    try:
        # Get the word and image
        cur.execute('SELECT id, english_word, image_file FROM Word_Image WHERE english_word = ?', (english_word,))
        word_data = cur.fetchone()
        
        if not word_data:
            return {"error": f"Word '{english_word}' not found"}
        
        word_id, word, image = word_data
        
        # Get all translations
        cur.execute('SELECT language_code, translated_word FROM Translation WHERE word_id = ?', (word_id,))
        translations = cur.fetchall()
        
        return {
            "english_word": word,
            "image_file": image,
            "translations": [{
                "language": lang,
                "word": trans
            } for lang, trans in translations]
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@mcp.tool()
def get_language_stats():
    """Get statistics about the database - total words and translations per language.
    
    Returns:
        Dictionary with total word count and breakdown by language
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    try:
        # Get total words
        cur.execute('SELECT COUNT(*) FROM Word_Image')
        total_words = cur.fetchone()[0]
        
        # Get translations per language
        cur.execute('SELECT language_code, COUNT(*) FROM Translation GROUP BY language_code')
        translations_by_lang = cur.fetchall()
        
        return {
            "total_words": total_words,
            "languages": [{
                "code": lang,
                "count": count
            } for lang, count in translations_by_lang]
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@mcp.tool()
def add_flashcard(english_word: str, image_file: str, translations: dict):
    """Add a new flashcard with translations to the database.
    
    Args:
        english_word: The English word (e.g., 'apple')
        image_file: The image filename (e.g., 'apple.png')
        translations: Dictionary mapping language codes to translated words
                     e.g., {"es": "manzana", "fr": "pomme", "vi": "táo"}
    
    Returns:
        Dictionary with success status and the new word_id
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    try:
        # Check if word already exists
        cur.execute('SELECT id FROM Word_Image WHERE english_word = ?', (english_word,))
        existing = cur.fetchone()
        if existing:
            return {"error": f"Word '{english_word}' already exists with id {existing[0]}"}
        
        # Insert the word
        cur.execute('INSERT INTO Word_Image (english_word, image_file) VALUES (?, ?)', 
                   (english_word, image_file))
        word_id = cur.lastrowid
        
        # Insert translations
        translation_count = 0
        for lang_code, translated_word in translations.items():
            cur.execute('INSERT INTO Translation (word_id, language_code, translated_word) VALUES (?, ?, ?)',
                       (word_id, lang_code, translated_word))
            translation_count += 1
        
        conn.commit()
        return {
            "success": True,
            "word_id": word_id,
            "english_word": english_word,
            "translations_added": translation_count
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()

@mcp.tool()
def add_translation(english_word: str, language_code: str, translated_word: str):
    """Add a translation for an existing word.
    
    Args:
        english_word: The English word to add translation for
        language_code: Language code (e.g., 'es', 'fr', 'vi', 'de', 'ja')
        translated_word: The translated word
    
    Returns:
        Dictionary with success status
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    try:
        # Get the word_id
        cur.execute('SELECT id FROM Word_Image WHERE english_word = ?', (english_word,))
        result = cur.fetchone()
        if not result:
            return {"error": f"Word '{english_word}' not found"}
        
        word_id = result[0]
        
        # Check if translation already exists
        cur.execute('SELECT id FROM Translation WHERE word_id = ? AND language_code = ?',
                   (word_id, language_code))
        if cur.fetchone():
            return {"error": f"Translation for '{english_word}' in '{language_code}' already exists"}
        
        # Insert translation
        cur.execute('INSERT INTO Translation (word_id, language_code, translated_word) VALUES (?, ?, ?)',
                   (word_id, language_code, translated_word))
        conn.commit()
        
        return {
            "success": True,
            "english_word": english_word,
            "language_code": language_code,
            "translated_word": translated_word
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()

@mcp.tool()
def update_word(english_word: str, new_english_word: str = None, new_image_file: str = None):
    """Update an existing word's English name or image file.
    
    Args:
        english_word: The current English word
        new_english_word: New English word (optional)
        new_image_file: New image filename (optional)
    
    Returns:
        Dictionary with success status
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    try:
        # Check if word exists
        cur.execute('SELECT id FROM Word_Image WHERE english_word = ?', (english_word,))
        result = cur.fetchone()
        if not result:
            return {"error": f"Word '{english_word}' not found"}
        
        # Build update query
        updates = []
        params = []
        if new_english_word:
            updates.append("english_word = ?")
            params.append(new_english_word)
        if new_image_file:
            updates.append("image_file = ?")
            params.append(new_image_file)
        
        if not updates:
            return {"error": "No updates provided"}
        
        params.append(english_word)
        query = f"UPDATE Word_Image SET {', '.join(updates)} WHERE english_word = ?"
        cur.execute(query, params)
        conn.commit()
        
        return {
            "success": True,
            "updated": {
                "english_word": new_english_word if new_english_word else english_word,
                "image_file": new_image_file if new_image_file else "unchanged"
            }
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()

@mcp.tool()
def update_translation(english_word: str, language_code: str, new_translated_word: str):
    """Update an existing translation.
    
    Args:
        english_word: The English word
        language_code: Language code (e.g., 'es', 'fr', 'vi')
        new_translated_word: The new translated word
    
    Returns:
        Dictionary with success status
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    try:
        # Get word_id
        cur.execute('SELECT id FROM Word_Image WHERE english_word = ?', (english_word,))
        result = cur.fetchone()
        if not result:
            return {"error": f"Word '{english_word}' not found"}
        
        word_id = result[0]
        
        # Update translation
        cur.execute('''UPDATE Translation 
                      SET translated_word = ? 
                      WHERE word_id = ? AND language_code = ?''',
                   (new_translated_word, word_id, language_code))
        
        if cur.rowcount == 0:
            return {"error": f"Translation for '{english_word}' in '{language_code}' not found"}
        
        conn.commit()
        return {
            "success": True,
            "english_word": english_word,
            "language_code": language_code,
            "new_translation": new_translated_word
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()

@mcp.tool()
def delete_flashcard(english_word: str):
    """Delete a flashcard and all its translations.
    
    Args:
        english_word: The English word to delete
    
    Returns:
        Dictionary with success status and count of deleted translations
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    try:
        # Get word_id
        cur.execute('SELECT id FROM Word_Image WHERE english_word = ?', (english_word,))
        result = cur.fetchone()
        if not result:
            return {"error": f"Word '{english_word}' not found"}
        
        word_id = result[0]
        
        # Count translations to delete
        cur.execute('SELECT COUNT(*) FROM Translation WHERE word_id = ?', (word_id,))
        translation_count = cur.fetchone()[0]
        
        # Delete translations first (foreign key constraint)
        cur.execute('DELETE FROM Translation WHERE word_id = ?', (word_id,))
        
        # Delete word
        cur.execute('DELETE FROM Word_Image WHERE id = ?', (word_id,))
        
        conn.commit()
        return {
            "success": True,
            "deleted_word": english_word,
            "deleted_translations": translation_count
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()

@mcp.tool()
def delete_translation(english_word: str, language_code: str):
    """Delete a specific translation for a word.
    
    Args:
        english_word: The English word
        language_code: Language code to delete (e.g., 'es', 'fr', 'vi')
    
    Returns:
        Dictionary with success status
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    try:
        # Get word_id
        cur.execute('SELECT id FROM Word_Image WHERE english_word = ?', (english_word,))
        result = cur.fetchone()
        if not result:
            return {"error": f"Word '{english_word}' not found"}
        
        word_id = result[0]
        
        # Delete translation
        cur.execute('DELETE FROM Translation WHERE word_id = ? AND language_code = ?',
                   (word_id, language_code))
        
        if cur.rowcount == 0:
            return {"error": f"Translation for '{english_word}' in '{language_code}' not found"}
        
        conn.commit()
        return {
            "success": True,
            "deleted": {
                "english_word": english_word,
                "language_code": language_code
            }
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()

if __name__ == '__main__':
    # Run the MCP server using stdio transport
    mcp.run(transport="stdio")