from flask import Flask, render_template, request, send_from_directory, jsonify
import sqlite3
import os
import json
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

# Pydantic models for structured output
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

if __name__ == '__main__':
    app.run(debug=True)