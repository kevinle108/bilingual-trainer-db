from flask import Flask, render_template, request, send_from_directory, jsonify
import sqlite3
import os
import json
import requests
import time
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser

# Load environment variables
load_dotenv()

app = Flask(__name__)

# GitHub Models API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
API_ENDPOINT = os.getenv("API_ENDPOINT", "https://models.github.ai/inference")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

# Initialize LangChain ChatOpenAI
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=0.7,
    max_tokens=300,
    base_url=API_ENDPOINT,
    api_key=GITHUB_TOKEN,
) if GITHUB_TOKEN else None

# Session storage for conversation memory (in production, use Redis/database)
conversation_sessions = {}

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

@app.route('/generator')
def generator():
    """Flashcard generator page"""
    return render_template('generator.html')

# Pydantic models for structured output
class FlashcardItem(BaseModel):
    """Model for a single flashcard"""
    english: str = Field(description="The English word or phrase")
    translated: str = Field(description="The translation in the target language")
    hint: Optional[str] = Field(default="", description="Optional learning hint or context")

class QuizEvaluation(BaseModel):
    """Model for quiz answer evaluation"""
    correct: bool = Field(description="Whether the student's answer is correct")
    message: str = Field(description="Encouraging feedback message for the student")
    explanation: str = Field(default="", description="Optional explanation of why the answer is right or wrong")

class ConversationSession:
    """Manages conversation state for a user session"""
    def __init__(self, language_name: str):
        self.language_name = language_name
        self.messages = []
        self.current_card = None
        self.mode = 'quiz'
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        if role == "system":
            self.messages.append(SystemMessage(content=content))
        elif role == "user":
            self.messages.append(HumanMessage(content=content))
        elif role == "assistant":
            self.messages.append(AIMessage(content=content))
    
    def get_recent_messages(self, limit: int = 10):
        """Get recent messages for context"""
        return self.messages[-limit:] if len(self.messages) > limit else self.messages
    
    def clear(self):
        """Clear conversation history"""
        self.messages = []

def get_or_create_session(session_id: str, language_name: str) -> ConversationSession:
    """Get or create a conversation session"""
    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = ConversationSession(language_name)
    return conversation_sessions[session_id]

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI-powered chat endpoint using LangChain for intelligent answer checking and conversation"""
    if not llm:
        return jsonify({'error': 'AI service not configured. Please set GITHUB_TOKEN environment variable.'}), 500
    
    data = request.json
    user_message = data.get('message', '')
    current_card = data.get('currentCard')
    mode = data.get('mode', 'quiz')
    language_name = data.get('languageName', 'Vietnamese')
    session_id = data.get('sessionId', 'default')
    
    # Get or create session
    session = get_or_create_session(session_id, language_name)
    session.mode = mode
    
    try:
        # If we're checking an answer for a quiz question
        if current_card:
            english_word = current_card['english_word']
            translated_word = current_card['translated_word']
            
            # Create structured output parser for quiz evaluation
            parser = JsonOutputParser(pydantic_object=QuizEvaluation)
            
            # Build the quiz evaluation prompt
            quiz_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=f"""You are a helpful and encouraging language learning tutor for {language_name}. 
You help students learn vocabulary through interactive quizzes and conversations.

Your responsibilities:
1. Check if student answers are correct, accepting synonyms and minor spelling variations
2. Provide encouraging feedback
3. Give helpful hints in practice mode
4. Explain why answers are right or wrong
5. Keep responses concise and friendly
6. Use emojis occasionally to make it fun

When checking answers:
- Accept synonyms (e.g., "bunny" = "rabbit", "puppy" = "dog")
- Be lenient with minor typos (1-2 character differences)
- Recognize articles (a/an/the) are optional
- Accept plural and singular forms
- Consider context and common variations"""),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                HumanMessage(content=f"""Current Quiz Question:
- {language_name} word: {translated_word}
- Correct English answer: {english_word}
- Student's answer: {user_message}
- Mode: {mode}

Evaluate the student's answer. Consider synonyms and minor variations.

{parser.get_format_instructions()}

Be encouraging! If correct, celebrate enthusiastically. If incorrect in quiz mode, kindly give the answer and encourage them. 
If incorrect in practice mode, give a helpful hint without revealing the full answer (e.g., first letter, rhyme, or category).""")
            ])
            
            # Create the chain
            chain = quiz_prompt | llm | parser
            
            # Invoke with conversation history
            result = chain.invoke({
                "chat_history": session.get_recent_messages(limit=6)
            })
            
            # Add to conversation history
            session.add_message("user", user_message)
            session.add_message("assistant", result.get('message', ''))
            
            return jsonify(result)
        
        else:
            # General conversation (non-quiz)
            conversation_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=f"""You are a friendly and encouraging language learning tutor for {language_name}. 
You help students learn vocabulary through conversation, encouragement, and guidance.

Keep responses concise (2-3 sentences max), friendly, and motivating. Use emojis occasionally."""),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessage(content="{user_message}")
            ])
            
            # Create the chain
            chain = conversation_prompt | llm
            
            # Invoke with conversation history
            response = chain.invoke({
                "chat_history": session.get_recent_messages(limit=8),
                "user_message": user_message
            })
            
            # Add to conversation history
            session.add_message("user", user_message)
            session.add_message("assistant", response.content)
            
            return jsonify({
                'message': response.content
            })
            
    except Exception as e:
        # Better error handling with fallback
        print(f"LangChain error: {e}")
        
        # Fallback to simple string matching if LangChain fails
        if current_card:
            correct = current_card['english_word'].lower()
            user_answer = user_message.lower().strip()
            
            is_correct = user_answer == correct
            
            return jsonify({
                'correct': is_correct,
                'message': f"{'✨ Correct!' if is_correct else f'Not quite! The answer is {current_card["english_word"]}.'} (AI unavailable)"
            })
        else:
            return jsonify({
                'message': "I'm having trouble connecting right now. Please try again! 😊",
                'error': str(e)
            })

# Helper functions for flashcard generation
def fetch_wikimedia_image(word: str) -> Optional[str]:
    """Fetch an image URL from Wikimedia Commons for a given word"""
    try:
        # Search for images on Wikimedia Commons
        search_url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"File:{word}",  # Search in File namespace
            "gsrnamespace": 6,  # File namespace
            "gsrlimit": 3,  # Get more results to try
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 512
        }
        
        headers = {
            "User-Agent": "BilingualTrainer/1.0 (https://github.com/; educational flashcard app) Python/requests"
        }
        
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            imageinfo = page.get("imageinfo", [])
            if imageinfo and len(imageinfo) > 0:
                # Try thumburl first, fall back to url
                thumb_url = imageinfo[0].get("thumburl") or imageinfo[0].get("url")
                if thumb_url:
                    downloaded = download_and_save_image(thumb_url, word)
                    if downloaded:  # If download succeeded, return it
                        return downloaded
        
        return None
    except Exception as e:
        print(f"Error fetching image for '{word}': {e}")
        return None

def download_and_save_image(url: str, word: str) -> Optional[str]:
    """Download an image and save it to the image-library folder"""
    try:
        headers = {
            "User-Agent": "BilingualTrainer/1.0 (https://github.com/; educational flashcard app) Python/requests"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Determine file extension
        ext = ".jpg"
        if "png" in url.lower():
            ext = ".png"
        elif "gif" in url.lower():
            ext = ".gif"
        
        # Create safe filename
        safe_word = "".join(c for c in word if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_word = safe_word.replace(' ', '_').lower()
        filename = f"{safe_word}_{int(time.time())}{ext}"
        
        # Save to image-library
        image_path = os.path.join('image-library', filename)
        with open(image_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Downloaded image: {filename}")
        return filename
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error downloading image for '{word}': {e.response.status_code}")
        return None
    except Exception as e:
        print(f"✗ Error downloading image for '{word}': {e}")
        return None

@app.route('/api/generate', methods=['POST'])
def generate_flashcards():
    """Generate flashcards using AI"""
    if not llm:
        return jsonify({
            'success': False, 
            'error': 'AI service not configured. Please set GITHUB_TOKEN environment variable.'
        }), 500
    
    data = request.json
    theme = data.get('theme', '').strip()
    language_code = data.get('language', 'vi')
    count = int(data.get('count', 10))
    description = data.get('description', '').strip()
    fetch_images = data.get('fetchImages', False)
    
    # Validate inputs
    if not theme:
        return jsonify({'success': False, 'error': 'Theme is required'}), 400
    
    if count < 3 or count > 30:
        return jsonify({'success': False, 'error': 'Count must be between 3 and 30'}), 400
    
    language_names = {
        'es': 'Spanish',
        'fr': 'French',
        'vi': 'Vietnamese'
    }
    language_name = language_names.get(language_code, language_code)
    
    try:
        # Build the generation prompt
        system_prompt = f"""You are a helpful language learning assistant that creates vocabulary flashcards.

Generate exactly {count} vocabulary flashcards for learning {language_name}.

Requirements:
- Theme/Topic: {theme}
- Each flashcard should have an English word/phrase and its {language_name} translation
- Choose practical, useful vocabulary that a learner would encounter
- Include a mix of nouns, verbs, and common phrases when appropriate
- Words should be appropriate for beginners to intermediate learners
- Optionally include a brief learning hint or context clue"""

        if description:
            system_prompt += f"\n- Additional requirements: {description}"
        
        system_prompt += f"""

Respond with a JSON array containing exactly {count} flashcard objects.
Each object must have:
- "english": the English word or phrase
- "translated": the {language_name} translation
- "hint": (optional) a brief learning tip or mnemonic

Example format:
[
  {{"english": "hello", "translated": "xin chào", "hint": "Common greeting"}},
  {{"english": "thank you", "translated": "cảm ơn", "hint": "Shows gratitude"}}
]

IMPORTANT: Return ONLY the JSON array, no other text."""

        # Create the LangChain prompt and parser
        parser = JsonOutputParser()
        
        generation_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate {count} {language_name} vocabulary flashcards about: {theme}")
        ])
        
        # Create and invoke the chain
        chain = generation_prompt | llm
        response = chain.invoke({})
        
        # Parse the response
        content = response.content
        
        # Extract JSON from response (might have markdown code blocks)
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        flashcards = json.loads(content)
        
        if not isinstance(flashcards, list):
            raise ValueError("AI did not return a list of flashcards")
        
        if len(flashcards) < count - 2:  # Allow some tolerance
            raise ValueError(f"AI only generated {len(flashcards)} cards instead of {count}")
        
        # Insert into database
        conn = get_db_connection()
        cur = conn.cursor()
        
        inserted_count = 0
        for card in flashcards[:count]:  # Ensure we don't exceed requested count
            english_word = card.get('english', '').strip()
            translated_word = card.get('translated', '').strip()
            
            if not english_word or not translated_word:
                continue
            
            # Try to fetch image if requested (default to empty string if none found)
            image_file = ""
            if fetch_images:
                fetched_image = fetch_wikimedia_image(english_word)
                if fetched_image:
                    image_file = fetched_image
                time.sleep(0.5)  # Be polite to Wikimedia API
            
            # Check if word already exists
            existing = cur.execute(
                'SELECT id FROM Word_Image WHERE english_word = ?',
                (english_word,)
            ).fetchone()
            
            if existing:
                word_id = existing['id']
                # Check if translation exists for this language
                existing_trans = cur.execute(
                    'SELECT id FROM Translation WHERE word_id = ? AND language_code = ?',
                    (word_id, language_code)
                ).fetchone()
                
                if not existing_trans:
                    # Add translation for existing word
                    cur.execute(
                        'INSERT INTO Translation (word_id, language_code, translated_word) VALUES (?, ?, ?)',
                        (word_id, language_code, translated_word)
                    )
                    inserted_count += 1
            else:
                # Insert new word with image_file (empty string if no image)
                cur.execute(
                    'INSERT INTO Word_Image (english_word, image_file) VALUES (?, ?)',
                    (english_word, image_file)
                )
                word_id = cur.lastrowid
                
                # Insert translation
                cur.execute(
                    'INSERT INTO Translation (word_id, language_code, translated_word) VALUES (?, ?, ?)',
                    (word_id, language_code, translated_word)
                )
                inserted_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'count': inserted_count,
            'theme': theme,
            'language': language_code
        })
        
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to generate flashcards: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)