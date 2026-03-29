from flask import Flask, render_template, request, send_from_directory
import sqlite3
import os

app = Flask(__name__)

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('image-library', filename)

def get_db_connection():
    conn = sqlite3.connect('BilingualTrainer.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_available_languages():
    conn = get_db_connection()
    languages = conn.execute('SELECT DISTINCT language_code FROM Translation ORDER BY language_code').fetchall()
    conn.close()
    return languages

@app.route('/')
def index():
    languages = get_available_languages()
    language_names = {
        'es': 'Spanish',
        'fr': 'French',
        'vi': 'Vietnamese'
    }
    return render_template('index.html', languages=languages, language_names=language_names)

@app.route('/flashcards')
def flashcards():
    language = request.args.get('lang', 'es')
    
    conn = get_db_connection()
    flashcards = conn.execute('''
        SELECT w.id, w.english_word, w.image_file, t.translated_word, t.language_code
        FROM Word_Image w
        JOIN Translation t ON w.id = t.word_id
        WHERE t.language_code = ?
        ORDER BY w.english_word
    ''', (language,)).fetchall()
    conn.close()
    
    language_names = {
        'es': 'Spanish',
        'fr': 'French',
        'vi': 'Vietnamese'
    }
    
    return render_template('flashcards.html', 
                         flashcards=flashcards, 
                         language=language,
                         language_name=language_names.get(language, language))

if __name__ == '__main__':
    app.run(debug=True)