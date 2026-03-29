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

if __name__ == '__main__':
    # Run the MCP server using stdio transport
    mcp.run(transport="stdio")