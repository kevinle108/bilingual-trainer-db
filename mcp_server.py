from fastmcp import FastMCP
import sqlite3
import base64
import os
from pathlib import Path
from typing import Optional

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
def update_word(english_word: str, new_english_word: Optional[str] = None, new_image_file: Optional[str] = None):
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

@mcp.tool()
def add_flashcard_with_image(english_word: str, image_data: str, image_extension: str, 
                              language_code: str, translated_word: str):
    """Add a new flashcard by uploading an image and adding a translation.
    
    This tool:
    1. Saves the image to the image-library folder
    2. Creates a new Word_Image entry (or uses existing)
    3. Adds the translation
    
    Args:
        english_word: The English word (e.g., 'apple')
        image_data: Base64 encoded image data
        image_extension: File extension (e.g., 'png', 'jpg', 'jpeg')
        language_code: Language code (e.g., 'es', 'fr', 'vi')
        translated_word: The translated word
    
    Returns:
        Dictionary with success status and details
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    
    try:
        # Decode the base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Create image filename
        image_filename = f"{english_word}.{image_extension}"
        image_path = Path("image-library") / image_filename
        
        # Check if file already exists, add number if needed
        counter = 0
        while image_path.exists():
            image_filename = f"{english_word}_{counter}.{image_extension}"
            image_path = Path("image-library") / image_filename
            counter += 1
        
        # Save the image file
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        # Check if word already exists
        cur.execute('SELECT id FROM Word_Image WHERE english_word = ?', (english_word,))
        result = cur.fetchone()
        
        if result:
            # Word exists, just add translation
            word_id = result[0]
            
            # Check if translation already exists
            cur.execute('SELECT id FROM Translation WHERE word_id = ? AND language_code = ?',
                       (word_id, language_code))
            if cur.fetchone():
                os.remove(image_path)  # Remove the uploaded image since we're not using it
                return {"error": f"Translation for '{english_word}' in '{language_code}' already exists"}
            
            # Add translation
            cur.execute('INSERT INTO Translation (word_id, language_code, translated_word) VALUES (?, ?, ?)',
                       (word_id, language_code, translated_word))
            
            conn.commit()
            return {
                "success": True,
                "action": "translation_added",
                "word_id": word_id,
                "english_word": english_word,
                "image_file": image_filename,
                "language_code": language_code,
                "translated_word": translated_word,
                "note": "Word already existed, added new translation"
            }
        else:
            # New word, create entry and translation
            cur.execute('INSERT INTO Word_Image (english_word, image_file) VALUES (?, ?)',
                       (english_word, image_filename))
            word_id = cur.lastrowid
            
            cur.execute('INSERT INTO Translation (word_id, language_code, translated_word) VALUES (?, ?, ?)',
                       (word_id, language_code, translated_word))
            
            conn.commit()
            return {
                "success": True,
                "action": "flashcard_created",
                "word_id": word_id,
                "english_word": english_word,
                "image_file": image_filename,
                "image_path": str(image_path),
                "language_code": language_code,
                "translated_word": translated_word
            }
            
    except Exception as e:
        conn.rollback()
        # Try to remove image if it was created
        if 'image_path' in locals() and image_path.exists():
            try:
                os.remove(image_path)
            except:
                pass
        return {"error": str(e)}
    finally:
        conn.close()

@mcp.tool()
def add_multiple_translations_with_image(english_word: str, image_data: str, 
                                        image_extension: str, translations: dict):
    """Add a new flashcard with an image and multiple translations at once.
    
    This tool:
    1. Saves the image to the image-library folder
    2. Creates a new Word_Image entry
    3. Adds all provided translations
    
    Args:
        english_word: The English word (e.g., 'apple')
        image_data: Base64 encoded image data
        image_extension: File extension (e.g., 'png', 'jpg', 'jpeg')
        translations: Dictionary mapping language codes to translated words
                     e.g., {"es": "manzana", "fr": "pomme", "vi": "táo"}
    
    Returns:
        Dictionary with success status and details
    """
    conn = sqlite3.connect('BilingualTrainer.db')
    cur = conn.cursor()
    
    try:
        # Check if word already exists
        cur.execute('SELECT id FROM Word_Image WHERE english_word = ?', (english_word,))
        if cur.fetchone():
            return {"error": f"Word '{english_word}' already exists. Use add_flashcard_with_image for single translations or update_word to change image."}
        
        # Decode the base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Create image filename
        image_filename = f"{english_word}.{image_extension}"
        image_path = Path("image-library") / image_filename
        
        # Check if file already exists, add number if needed
        counter = 0
        while image_path.exists():
            image_filename = f"{english_word}_{counter}.{image_extension}"
            image_path = Path("image-library") / image_filename
            counter += 1
        
        # Save the image file
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        # Create word entry
        cur.execute('INSERT INTO Word_Image (english_word, image_file) VALUES (?, ?)',
                   (english_word, image_filename))
        word_id = cur.lastrowid
        
        # Add all translations
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
            "image_file": image_filename,
            "image_path": str(image_path),
            "translations_added": translation_count,
            "translations": translations
        }
            
    except Exception as e:
        conn.rollback()
        # Try to remove image if it was created
        if 'image_path' in locals() and image_path.exists():
            try:
                os.remove(image_path)
            except:
                pass
        return {"error": str(e)}
    finally:
        conn.close()

if __name__ == '__main__':
    # Run the MCP server using stdio transport
    mcp.run(transport="stdio")