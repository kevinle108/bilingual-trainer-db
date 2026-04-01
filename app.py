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

# ImageRouter API configuration
# Using FLUX-2-klein-9b model for high-quality kid-friendly flashcard images
# Cost: $0.08 per 100 images
# Prompt format: "a cute picture of [word] with no text, suitable for a kid's flashcard"
IMAGE_ROUTER_API_KEY = os.getenv("IMAGE_ROUTER_API_KEY")
IMAGE_ROUTER_API_URL = "https://api.imagerouter.io/v1/openai/images/generations"
IMAGE_ROUTER_MODEL = "black-forest-labs/FLUX-2-klein-9b"  # $0.08/100 images - high quality

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

class GenerationIntent(BaseModel):
    """Model for detecting flashcard generation intent"""
    wants_generation: bool = Field(description="Whether the user wants to generate new flashcards")
    theme: Optional[str] = Field(default="", description="The topic/theme for flashcards (if requested)")
    count: Optional[int] = Field(default=10, description="Number of cards to generate (if specified)")

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
            # General conversation (non-quiz) - check for generation intent first
            lower_message = user_message.lower()
            
            # Check if user wants to generate flashcards
            if any(keyword in lower_message for keyword in ['generate', 'create cards', 'make flashcards', 'new cards', 'add cards']):
                # Use AI to detect generation intent and extract details
                intent_prompt = ChatPromptTemplate.from_messages([
                    SystemMessage(content=f"""Analyze if the user wants to generate new flashcards. Extract:
1. wants_generation: true/false
2. theme: the topic (if mentioned, e.g., "animals", "food")  
3. count: number of cards (if mentioned, default 10)

Respond in JSON format exactly like this:
{{"wants_generation": true, "theme": "animals", "count": 10}}"""),
                    HumanMessage(content=user_message)
                ])
                
                try:
                    intent_chain = intent_prompt | llm
                    intent_response = intent_chain.invoke({})
                    
                    # Parse intent
                    intent_content = intent_response.content
                    if '```json' in intent_content:
                        intent_content = intent_content.split('```json')[1].split('```')[0].strip()
                    elif '```' in intent_content:
                        intent_content = intent_content.split('```')[1].split('```')[0].strip()
                    
                    intent_data = json.loads(intent_content)
                    
                    if intent_data.get('wants_generation'):
                        theme = intent_data.get('theme', 'general vocabulary')
                        count = min(max(intent_data.get('count', 10), 5), 15)  # Limit 5-15 for chatbot
                        
                        # Generate flashcards
                        session.add_message("user", user_message)
                        session.add_message("assistant", f"Generating {count} {language_name} flashcards about {theme}...")
                        
                        # Map language name to code
                        lang_code_map = {
                            'Vietnamese': 'vi',
                            'Spanish': 'es',
                            'French': 'fr'
                        }
                        lang_code = lang_code_map.get(language_name, 'vi')
                        
                        result = generate_flashcard_set(theme, lang_code, count, fetch_images=True)
                        
                        if result['success']:
                            response_msg = f"✨ Great! I've generated {result['count']} new {language_name} flashcards about {theme}! They're now available in your flashcard deck. Would you like to practice them with a quiz?"
                            session.add_message("assistant", response_msg)
                            return jsonify({
                                'message': response_msg,
                                'generated': True,
                                'count': result['count']
                            })
                        else:
                            error_msg = f"Sorry, I had trouble generating those flashcards. {result.get('error', '')} Try being more specific about the topic!"
                            session.add_message("assistant", error_msg)
                            return jsonify({'message': error_msg})
                
                except Exception as e:
                    print(f"Error detecting generation intent: {e}")
                    # Fall through to normal conversation
            
            # Normal conversation
            conversation_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=f"""You are a friendly and encouraging language learning tutor for {language_name}. 
You help students learn vocabulary through conversation, encouragement, and guidance.

You can also help generate new flashcards! If the user asks, you can create custom vocabulary sets on any topic.

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
def generate_image_with_imagerouter(word: str) -> Optional[str]:
    """Generate an image using ImageRouter.io AI image generation"""
    if not IMAGE_ROUTER_API_KEY:
        print(f"⚠ ImageRouter API key not configured, skipping AI generation for '{word}'")
        print(f"   Please set IMAGE_ROUTER_API_KEY in your .env file")
        return None
    
    try:
        # Create kid-friendly prompt
        prompt = f"a cute picture of {word} with no text, suitable for a kid's flashcard"
        
        print(f"🎨 Generating AI image for '{word}'...")
        print(f"   Prompt: {prompt}")
        print(f"   Model: {IMAGE_ROUTER_MODEL}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {IMAGE_ROUTER_API_KEY}"
        }
        
        payload = {
            "prompt": prompt,
            "model": IMAGE_ROUTER_MODEL,
            "size": "auto",
            "n": 1
        }
        
        print(f"🎨 Generating AI image for '{word}' using {IMAGE_ROUTER_MODEL}...")
        
        response = requests.post(
            IMAGE_ROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            print(f"✗ ImageRouter API Error ({response.status_code}): {error_msg}")
            return None
        
        result = response.json()
        
        # Get image URL from response
        if 'data' not in result or len(result['data']) == 0:
            print(f"✗ No image data in ImageRouter response for '{word}'")
            return None
        
        image_url = result['data'][0].get('url') or result['data'][0].get('b64_json')
        
        if not image_url:
            print(f"✗ No image URL in ImageRouter response for '{word}'")
            return None
        
        # Download and save the generated image
        if image_url.startswith('http'):
            downloaded = download_and_save_image(image_url, word, source="imagerouter")
            if downloaded:
                print(f"✓ Successfully generated AI image for '{word}': {downloaded}")
                return downloaded
        else:
            # Handle base64 encoded image
            import base64
            image_data = base64.b64decode(image_url)
            
            # Create safe filename
            safe_word = "".join(c for c in word if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_word = safe_word.replace(' ', '_').lower()
            filename = f"{safe_word}_{int(time.time())}_ai.png"
            
            # Save to image-library
            image_path = os.path.join('image-library', filename)
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            print(f"✓ Successfully generated AI image for '{word}': {filename}")
            return filename
        
        return None
        
    except requests.exceptions.Timeout:
        print(f"✗ Timeout generating AI image for '{word}'")
        return None
    except Exception as e:
        print(f"✗ Error generating AI image for '{word}': {e}")
        return None

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

def download_and_save_image(url: str, word: str, source: str = "wikimedia") -> Optional[str]:
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
        
        # Add source suffix for tracking
        source_suffix = "_ai" if source == "imagerouter" else ""
        filename = f"{safe_word}_{int(time.time())}{source_suffix}{ext}"
        
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

def generate_flashcard_set(theme: str, language_code: str, count: int = 10, fetch_images: bool = False) -> dict:
    """
    Internal function to generate a set of flashcards
    
    Args:
        theme: Topic/theme for the flashcards
        language_code: Language code (es, fr, vi)
        count: Number of flashcards to generate (default: 10)
        fetch_images: Whether to fetch/generate images for flashcards (default: False)
                      When True, uses ImageRouter AI generation first, falls back to Wikimedia
    
    Returns:
        dict with success status and details
    """
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

Respond with a JSON array containing exactly {count} flashcard objects.
Each object must have:
- "english": the English word or phrase
- "translated": the {language_name} translation

Example format:
[
  {{"english": "hello", "translated": "xin chào"}},
  {{"english": "thank you", "translated": "cảm ơn"}}
]

IMPORTANT: Return ONLY the JSON array, no other text."""

        # Create the LangChain prompt
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
        
        if len(flashcards) < max(3, count - 2):  # Allow some tolerance
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
            
            # Try to fetch image if requested
            image_file = ""
            if fetch_images:
                # Try ImageRouter AI generation first (better quality, kid-friendly)
                print(f"Generating image for '{english_word}'...")
                fetched_image = generate_image_with_imagerouter(english_word)
                
                # Fall back to Wikimedia if ImageRouter fails
                if not fetched_image:
                    print(f"  Falling back to Wikimedia for '{english_word}'...")
                    fetched_image = fetch_wikimedia_image(english_word)
                
                if fetched_image:
                    image_file = fetched_image
                
                time.sleep(2)  # Delay between requests to be respectful to APIs
            
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
        
        return {
            'success': True,
            'count': inserted_count,
            'theme': theme,
            'language': language_code
        }
        
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/api/generate', methods=['POST'])
def generate_flashcards_api():
    """Generate flashcards using AI (API endpoint for form submission)"""
    if not llm:
        return jsonify({
            'success': False, 
            'error': 'AI service not configured. Please set GITHUB_TOKEN environment variable.'
        }), 500
    
    data = request.json
    theme = data.get('theme', '').strip()
    language_code = data.get('language', 'vi')
    count = int(data.get('count', 10))
    fetch_images = data.get('fetchImages', False)
    
    # Validate inputs
    if not theme:
        return jsonify({'success': False, 'error': 'Theme is required'}), 400
    
    if count < 3 or count > 30:
        return jsonify({'success': False, 'error': 'Count must be between 3 and 30'}), 400
    
    # Use the helper function
    result = generate_flashcard_set(theme, language_code, count, fetch_images)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/api/flashcard/<int:card_id>', methods=['DELETE'])
def delete_flashcard(card_id):
    """Delete a flashcard (word and all its translations)"""
    try:
        conn = get_db_connection()
        
        # Check if the word exists
        word = conn.execute('SELECT english_word FROM Word_Image WHERE id = ?', (card_id,)).fetchone()
        
        if not word:
            conn.close()
            return jsonify({'error': 'Flashcard not found'}), 404
        
        # Delete translations first (foreign key constraint)
        conn.execute('DELETE FROM Translation WHERE word_id = ?', (card_id,))
        
        # Delete the word
        conn.execute('DELETE FROM Word_Image WHERE id = ?', (card_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted "{word["english_word"]}"'
        })
        
    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    print("="*60)
    print("🚀 Bilingual Trainer App Starting")
    print("="*60)
    print(f"GitHub Token: {'✓ Configured' if GITHUB_TOKEN else '✗ Missing'}")
    print(f"ImageRouter API Key: {'✓ Configured' if IMAGE_ROUTER_API_KEY else '✗ Missing (images will not be generated)'}")
    if IMAGE_ROUTER_API_KEY:
        print(f"   Model: {IMAGE_ROUTER_MODEL}")
        print(f"   Cost: $0.08 per 100 images")
    print("="*60)
    print()
    app.run(debug=True)