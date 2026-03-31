from flask import Flask, render_template, request, send_from_directory, jsonify
import sqlite3
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# GitHub Models API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
API_ENDPOINT = os.getenv("API_ENDPOINT", "https://models.github.ai/inference")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

# Initialize OpenAI client with GitHub Models endpoint
client = OpenAI(
    base_url=API_ENDPOINT,
    api_key=GITHUB_TOKEN,
) if GITHUB_TOKEN else None

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

@app.route('/chatbot')
def chatbot():
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
    
    # Convert to list of dicts for JSON serialization
    flashcards_list = [dict(card) for card in flashcards]
    
    language_names = {
        'es': 'Spanish',
        'fr': 'French',
        'vi': 'Vietnamese'
    }
    
    return render_template('chatbot.html',
                         flashcards=flashcards_list,
                         language=language,
                         language_name=language_names.get(language, language))

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI-powered chat endpoint for intelligent answer checking and conversation"""
    if not client:
        return jsonify({'error': 'AI service not configured. Please set GITHUB_TOKEN environment variable.'}), 500
    
    data = request.json
    user_message = data.get('message', '')
    current_card = data.get('currentCard')
    mode = data.get('mode', 'quiz')
    language_name = data.get('languageName', 'Vietnamese')
    conversation_history = data.get('history', [])
    
    try:
        # Build the system prompt
        system_prompt = f"""You are a helpful and encouraging language learning tutor for {language_name}. 
You help students learn vocabulary through interactive quizzes and conversations.

Your responsibilities:
1. Check if student answers are correct, accepting synonyms and minor spelling variations
2. Provide encouraging feedback
3. Give helpful hints in practice mode
4. Explain why answers are right or wrong
5. Keep responses concise and friendly
6. Use emojis occasionally to make it fun

When checking answers:
- Accept synonyms (e.g., "bunny" = "rabbit")
- Be lenient with minor typos
- Recognize articles (a/an/the) are optional
- Accept plural and singular forms"""

        # Build the conversation messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 10 messages to keep context manageable)
        for msg in conversation_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # If we're checking an answer for a quiz question
        if current_card:
            english_word = current_card['english_word']
            translated_word = current_card['translated_word']
            
            quiz_context = f"""
Current Quiz Question:
- {language_name} word: {translated_word}
- Correct English answer: {english_word}
- Student's answer: {user_message}
- Mode: {mode}

Please evaluate the student's answer. Respond in JSON format:
{{
    "correct": true/false,
    "message": "Your feedback message here",
    "explanation": "Brief explanation (optional)"
}}

Be encouraging! If correct, celebrate. If incorrect in quiz mode, give the answer and encourage them. 
If incorrect in practice mode, give a helpful hint without revealing the full answer."""
            
            messages.append({"role": "user", "content": quiz_context})
        else:
            # General conversation
            messages.append({"role": "user", "content": user_message})
        
        # Call the AI
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        ai_response = response.choices[0].message.content
        
        # Try to parse JSON if it's a quiz response
        if current_card:
            try:
                import json
                # Extract JSON from response (might have markdown code blocks)
                if '```json' in ai_response:
                    ai_response = ai_response.split('```json')[1].split('```')[0].strip()
                elif '```' in ai_response:
                    ai_response = ai_response.split('```')[1].split('```')[0].strip()
                
                result = json.loads(ai_response)
                return jsonify(result)
            except:
                # Fallback if JSON parsing fails
                return jsonify({
                    'correct': False,
                    'message': ai_response
                })
        else:
            return jsonify({
                'message': ai_response
            })
            
    except Exception as e:
        return jsonify({'error': f'AI service error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)