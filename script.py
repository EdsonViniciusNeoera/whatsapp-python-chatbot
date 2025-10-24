import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import google.generativeai as genai
import json
from wasenderapi import create_sync_wasender, WasenderSyncClient
from wasenderapi.errors import WasenderAPIError
from wasenderapi.webhook import WasenderWebhookEvent
from wasenderapi.models import RetryConfig
import asyncio
import time
from functools import wraps
from message_splitter import split_message
import base64
import requests
from datetime import datetime, timedelta
import mimetypes
import shutil

# Load environment variables
load_dotenv()

# Flask application setup
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('whatsapp_bot.log')
    ]
)
logger = logging.getLogger("whatsapp_bot")

# Application configuration
CONFIG = {
    "CONVERSATIONS_DIR": os.getenv('CONVERSATIONS_DIR', 'conversations'),
    "TEMP_MEDIA_DIR": os.getenv('TEMP_MEDIA_DIR', 'temp_media'),
    "GEMINI_API_KEY": os.getenv('GEMINI_API_KEY'),
    "WASENDER_API_TOKEN": os.getenv('WASENDER_API_TOKEN'),
    "GEMINI_MODEL": os.getenv('GEMINI_MODEL', 'gemini-2.0-flash'),
    "WEBHOOK_SECRET": os.getenv('WEBHOOK_SECRET'),
    "MAX_RETRIES": int(os.getenv('MAX_RETRIES', '3')),
    "MESSAGE_CHUNK_MAX_LINES": int(os.getenv('MESSAGE_CHUNK_MAX_LINES', '10')),
    "MESSAGE_CHUNK_MAX_CHARS": int(os.getenv('MESSAGE_CHUNK_MAX_CHARS', '400')),
    "MESSAGE_DELAY_MIN": float(os.getenv('MESSAGE_DELAY_MIN', '0.55')),
    "MESSAGE_DELAY_MAX": float(os.getenv('MESSAGE_DELAY_MAX', '1.5')),
    "NOTIFICATION_GROUP_ID": os.getenv('NOTIFICATION_GROUP_ID'),
    "MEDIA_CLEANUP_HOURS": int(os.getenv('MEDIA_CLEANUP_HOURS', '24')),
    "WEBHOOK_BASE_URL": os.getenv('WEBHOOK_BASE_URL', 'http://localhost:5001'),
}

# Directory for storing conversations
if not os.path.exists(CONFIG["CONVERSATIONS_DIR"]):
    os.makedirs(CONFIG["CONVERSATIONS_DIR"])
    logger.info(f"Created conversations directory at {CONFIG['CONVERSATIONS_DIR']}")

# Directory for temporary media storage
if not os.path.exists(CONFIG["TEMP_MEDIA_DIR"]):
    os.makedirs(CONFIG["TEMP_MEDIA_DIR"])
    logger.info(f"Created temporary media directory at {CONFIG['TEMP_MEDIA_DIR']}")

# Configure retry options for WaSenderAPI
retry_config = RetryConfig(
    enabled=True,
    max_retries=CONFIG["MAX_RETRIES"]
)

# Initialize WaSenderAPI client
try:
    wasender_client = create_sync_wasender(
        api_key=CONFIG["WASENDER_API_TOKEN"],
        webhook_secret=CONFIG["WEBHOOK_SECRET"],
        retry_options=retry_config
    )
    logger.info("WaSenderAPI client initialized successfully with retry support")
except Exception as e:
    logger.error(f"Error initializing WaSenderAPI client: {e}", exc_info=True)
    wasender_client = None

# Initialize Gemini client
if CONFIG["GEMINI_API_KEY"]:
    genai.configure(api_key=CONFIG["GEMINI_API_KEY"])
    logger.info("Gemini API client initialized successfully")
else:
    logger.error("GEMINI_API_KEY not found in environment variables. The application might not work correctly.")

@app.errorhandler(Exception)
def handle_global_exception(e):
    """Global handler for unhandled exceptions."""
    logger.error(f"Unhandled Exception: {e}", exc_info=True)
    return jsonify(status='error', message='An internal server error occurred.'), 500

@app.route('/', methods=['GET'])
def index():
    """Main page showing bot status and available endpoints."""
    return jsonify({
        'message': 'WhatsApp Gemini AI Chatbot is running!',
        'status': 'active',
        'endpoints': {
            '/': 'This page - Bot status',
            '/health': 'Health check endpoint',
            '/status': 'Detailed bot status',
            '/webhook': 'Webhook endpoint for WhatsApp messages (POST only)',
            '/clear_history/<user_id>': 'Clear conversation history for a user (POST only)',
            '/media/<filename>': 'Serve temporary media files (GET only)'
        },
        'documentation': 'Send POST requests to /webhook for WhatsApp integration',
        'version': '1.0.0'
    })

@app.route('/media/<filename>', methods=['GET'])
def serve_media(filename):
    """
    Serve temporary media files for WhatsApp API access.
    
    This endpoint allows the WaSender API to download prescription images/PDFs
    via public URLs (through ngrok or your server domain).
    
    Args:
        filename: The name of the file to serve from temp_media directory
        
    Returns:
        The requested file or 404 if not found
        
    Security:
        - Only serves files from TEMP_MEDIA_DIR (no path traversal)
        - Files are automatically cleaned up after 24 hours
        - No authentication required (temporary files only)
    """
    try:
        # Security: Validate filename (no path traversal)
        if '..' in filename or '/' in filename or '\\' in filename:
            logger.warning(f"⚠️ Attempted path traversal: {filename}")
            return jsonify({'error': 'Invalid filename'}), 400
        
        # Check if file exists
        file_path = os.path.join(CONFIG["TEMP_MEDIA_DIR"], filename)
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ File not found: {filename}")
            return jsonify({'error': 'File not found'}), 404
        
        # Determine mimetype
        mimetype = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        
        logger.info(f"📤 Serving media file: {filename} (type: {mimetype})")
        
        # Serve file with appropriate headers
        return send_from_directory(
            CONFIG["TEMP_MEDIA_DIR"],
            filename,
            mimetype=mimetype,
            as_attachment=False,  # Display inline in browser
            max_age=86400  # Cache for 24 hours (matches cleanup time)
        )
    except Exception as e:
        logger.error(f"❌ Error serving media file {filename}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    status = {
        'status': 'ok',
        'wasender_client': wasender_client is not None,
        'gemini_client': CONFIG["GEMINI_API_KEY"] is not None,
        'conversations_dir': os.path.exists(CONFIG["CONVERSATIONS_DIR"]),
        'timestamp': time.time()
    }
    
    if not wasender_client:
        status['status'] = 'degraded'
        status['issues'] = ['WaSender client not initialized']
    
    if not CONFIG["GEMINI_API_KEY"]:
        status['status'] = 'degraded'
        if 'issues' not in status:
            status['issues'] = []
        status['issues'].append('Gemini API key not configured')
    
    status_code = 200 if status['status'] == 'ok' else 503
    return jsonify(status), status_code



# --- Load Persona ---
def load_persona(file_path='persona.json'):
    """
    Load persona configuration from a JSON file.
    Returns a tuple of (persona_description, persona_name, few_shot_examples, menu_config).
    """
    default_name = "Assistant"
    default_description = "You are a helpful assistant."
    default_base_prompt = (
        "You are a helpful and concise AI assistant replying in a WhatsApp chat. "
        "Do not use Markdown formatting. Keep your answers short, friendly, and easy to read. "
        "Split long answers every 3 lines using a real newline character Use \n to break the message."
        "Each \n means a new WhatsApp message. Avoid long paragraphs or unnecessary explanations."
    )
    default_menu_config = {
        "enabled": False,
        "welcome_message": "",
        "menu_options": {},
        "greeting_keywords": []
    }

    try:
        if not os.path.exists(file_path):
            logger.warning(f"Persona file not found at {file_path}. Using default persona.")
            return f"{default_base_prompt}\n\n{default_description}", default_name, [], default_menu_config
            
        with open(file_path, 'r', encoding='utf-8') as f:
            persona_data = json.load(f)
            
        custom_description = persona_data.get('description', default_description)
        base_prompt = persona_data.get('base_prompt', default_base_prompt)
        persona_name = persona_data.get('name', default_name)
        few_shot_examples = persona_data.get('responses', [])
        
        # Load menu configuration
        menu_config = {
            "enabled": persona_data.get('menu_enabled', False),
            "welcome_message": persona_data.get('welcome_message', ''),
            "menu_options": persona_data.get('menu_options', {}),
            "greeting_keywords": persona_data.get('greeting_keywords', [])
        }
        
        full_persona = f"{base_prompt}\n\n{custom_description}"
        logger.info(f"Successfully loaded persona: {persona_name}")
        logger.info(f"Loaded {len(few_shot_examples)} few-shot examples")
        logger.info(f"Interactive menu: {'Enabled' if menu_config['enabled'] else 'Disabled'}")
        
        return full_persona, persona_name, few_shot_examples, menu_config
        
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}. Using default persona.")
        return f"{default_base_prompt}\n\n{default_description}", default_name, [], default_menu_config
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading persona: {e}. Using default persona.")
        return f"{default_base_prompt}\n\n{default_description}", default_name, [], default_menu_config

# Load persona configuration
PERSONA_FILE_PATH = os.getenv('PERSONA_FILE_PATH', 'persona.json')
PERSONA_DESCRIPTION, PERSONA_NAME, FEW_SHOT_EXAMPLES, MENU_CONFIG = load_persona(PERSONA_FILE_PATH)
logger.info(f"Using persona '{PERSONA_NAME}' with {len(FEW_SHOT_EXAMPLES)} training examples")
# --- End Load Persona ---

def build_few_shot_history(examples):
    """
    Converts few-shot examples from persona.json into Gemini chat history format.
    
    Args:
        examples: List of dicts with 'input' and 'output' keys
        
    Returns:
        List of message dicts in Gemini format (alternating user/model roles)
    """
    history = []
    for example in examples:
        if 'input' in example and 'output' in example:
            # Add user message
            history.append({
                'role': 'user',
                'parts': [example['input']]
            })
            # Add model response
            history.append({
                'role': 'model',
                'parts': [example['output']]
            })
    
    logger.debug(f"Built few-shot history with {len(history)} messages ({len(history)//2} examples)")
    return history

def is_greeting(message_text, greeting_keywords):
    """
    Check if the message is a greeting or initial interaction.
    
    Args:
        message_text: The message to check
        greeting_keywords: List of greeting keywords
        
    Returns:
        True if message is a greeting, False otherwise
    """
    if not message_text:
        return False
    
    message_lower = message_text.lower().strip()
    
    # Check if message matches any greeting keyword
    for keyword in greeting_keywords:
        if keyword.lower() in message_lower:
            return True
    
    return False

def is_menu_option(message_text, menu_options):
    """
    Check if the message is a menu option selection.
    
    Args:
        message_text: The message to check
        menu_options: Dict of menu options
        
    Returns:
        The option key if valid, None otherwise
    """
    if not message_text:
        return None
    
    message_stripped = message_text.strip()
    
    # Check if it's a number or emoji number
    if message_stripped in menu_options:
        return message_stripped
    
    # Check for emoji numbers like "1️⃣"
    emoji_to_number = {
        "1️⃣": "1", "2️⃣": "2", "3️⃣": "3", "4️⃣": "4",
        "5️⃣": "5", "6️⃣": "6", "7️⃣": "7", "8️⃣": "8", "9️⃣": "9"
    }
    
    if message_stripped in emoji_to_number:
        option_key = emoji_to_number[message_stripped]
        if option_key in menu_options:
            return option_key
    
    return None

def get_menu_response(option_key, menu_options):
    """
    Get the response for a selected menu option.
    
    Args:
        option_key: The selected option key
        menu_options: Dict of menu options
        
    Returns:
        The response text for the option
    """
    option = menu_options.get(option_key)
    if option and 'response' in option:
        return option['response']
    
    return None

class ConversationManager:
    """Manages conversation history with context window management."""
    
    def __init__(self, storage_dir, max_history=10):
        """
        Initialize the conversation manager.
        
        Args:
            storage_dir: Directory to store conversation histories
            max_history: Maximum number of message pairs to retain in history
        """
        self.storage_dir = storage_dir
        self.max_history = max_history
        
    def load(self, user_id):
        """
        Load conversation history for a given user_id with context window management.
        
        Args:
            user_id: The user identifier
            
        Returns:
            A list of message dictionaries suitable for Gemini
        """
        file_path = os.path.join(self.storage_dir, f"{user_id}.json")
        
        try:
            if not os.path.exists(file_path):
                return []
                
            with open(file_path, 'r') as f:
                history = json.load(f)
                
            # Validate history format
            if not isinstance(history, list) or not all(
                isinstance(item, dict) and 'role' in item and 'parts' in item 
                for item in history):
                logger.warning(f"Invalid history format in {file_path}. Starting fresh.")
                return []
                
            # Limit history to most recent exchanges to prevent context overflow
            if len(history) > self.max_history * 2:  # Each exchange is 2 messages (user + model)
                logger.info(f"Trimming history for {user_id} to last {self.max_history} exchanges")
                history = history[-self.max_history * 2:]
                
            return history
                
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {file_path}. Starting fresh.")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading history from {file_path}: {e}")
            return []
            
    def save(self, user_id, history):
        """
        Saves conversation history for a given user_id.
        
        Args:
            user_id: The user identifier
            history: The conversation history to save
        """
        file_path = os.path.join(self.storage_dir, f"{user_id}.json")
        
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save the history
            with open(file_path, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving conversation history to {file_path}: {e}")
    
    def add_exchange(self, user_id, user_message, model_response):
        """
        Add a new message exchange to the conversation history.
        
        Args:
            user_id: The user identifier
            user_message: The message from the user
            model_response: The response from the model
        """
        history = self.load(user_id)
        
        # Add the new exchange
        history.append({'role': 'user', 'parts': [user_message]})
        history.append({'role': 'model', 'parts': [model_response]})
        
        # Save the updated history
        self.save(user_id, history)
        
        return history

# Initialize the conversation manager
conversation_manager = ConversationManager(CONFIG["CONVERSATIONS_DIR"], max_history=20)

# Message deduplication cache
# Stores message IDs that have been processed recently to avoid duplicates
processed_messages = {}
PROCESSED_MESSAGE_TTL = 300  # Keep message IDs for 5 minutes (300 seconds)

# Active message sending tracking
# Stores active message sending sessions per user to allow cancellation
active_sending_sessions = {}  # {safe_sender_id: {'cancel': False, 'timestamp': time}}
SENDING_SESSION_TTL = 60  # Keep session info for 1 minute

# Customer form data collection
# Stores customer information being collected before notifying attendants
customer_forms = {}  # {safe_sender_id: {'step': str, 'data': {}, 'timestamp': time, 'reason': str}}
CUSTOMER_FORM_TTL = 600  # Keep form data for 10 minutes

def cleanup_processed_messages():
    """Remove old message IDs from the processed messages cache."""
    current_time = time.time()
    expired_ids = [msg_id for msg_id, timestamp in processed_messages.items() 
                   if current_time - timestamp > PROCESSED_MESSAGE_TTL]
    for msg_id in expired_ids:
        del processed_messages[msg_id]

def is_message_processed(message_id):
    """
    Check if a message has already been processed.
    
    Args:
        message_id: The unique message ID
        
    Returns:
        True if the message was already processed, False otherwise
    """
    cleanup_processed_messages()
    return message_id in processed_messages

def mark_message_processed(message_id):
    """
    Mark a message as processed by storing its ID with a timestamp.
    
    Args:
        message_id: The unique message ID
    """
    processed_messages[message_id] = time.time()

def start_sending_session(safe_sender_id):
    """
    Start a new message sending session for a user.
    If there's an active session, it will be cancelled.
    
    Args:
        safe_sender_id: The safe sender identifier
    """
    # Cancel any existing session for this user
    if safe_sender_id in active_sending_sessions:
        logger.info(f"Cancelling previous sending session for {safe_sender_id}")
        active_sending_sessions[safe_sender_id]['cancel'] = True
    
    # Create new session
    active_sending_sessions[safe_sender_id] = {
        'cancel': False,
        'timestamp': time.time()
    }
    logger.info(f"Started new sending session for {safe_sender_id}")

def should_cancel_sending(safe_sender_id):
    """
    Check if the current sending session should be cancelled.
    
    Args:
        safe_sender_id: The safe sender identifier
        
    Returns:
        True if sending should be cancelled, False otherwise
    """
    if safe_sender_id not in active_sending_sessions:
        return False
    
    return active_sending_sessions[safe_sender_id].get('cancel', False)

def cleanup_sending_sessions():
    """Remove old sending sessions from the cache."""
    current_time = time.time()
    expired_ids = [user_id for user_id, session in active_sending_sessions.items() 
                   if current_time - session['timestamp'] > SENDING_SESSION_TTL]
    for user_id in expired_ids:
        del active_sending_sessions[user_id]

def end_sending_session(safe_sender_id):
    """
    End a message sending session for a user.
    
    Args:
        safe_sender_id: The safe sender identifier
    """
    if safe_sender_id in active_sending_sessions:
        del active_sending_sessions[safe_sender_id]
        logger.info(f"Ended sending session for {safe_sender_id}")

def start_customer_form(safe_sender_id, reason):
    """
    Start collecting customer information before notifying attendants.
    
    Args:
        safe_sender_id: The safe sender identifier
        reason: The reason for the form (menu option or description)
    """
    customer_forms[safe_sender_id] = {
        'step': 'consultant',  # Possible steps: consultant, name, phone, cpf, prescription, confirm
        'data': {},
        'timestamp': time.time(),
        'reason': reason
    }
    logger.info(f"Started customer form for {safe_sender_id} - reason: {reason}")

def get_customer_form(safe_sender_id):
    """
    Get current customer form state.
    
    Args:
        safe_sender_id: The safe sender identifier
        
    Returns:
        Form data dict or None if no form active
    """
    cleanup_customer_forms()
    return customer_forms.get(safe_sender_id)

def update_customer_form(safe_sender_id, step, data_key=None, data_value=None):
    """
    Update customer form with new data and move to next step.
    
    Args:
        safe_sender_id: The safe sender identifier
        step: The next step to move to
        data_key: Optional key to store data
        data_value: Optional value to store
    """
    if safe_sender_id in customer_forms:
        if data_key and data_value is not None:
            customer_forms[safe_sender_id]['data'][data_key] = data_value
        customer_forms[safe_sender_id]['step'] = step
        customer_forms[safe_sender_id]['timestamp'] = time.time()
        logger.info(f"Updated customer form for {safe_sender_id} - step: {step}")

def cancel_customer_form(safe_sender_id):
    """
    Cancel customer form collection.
    
    Args:
        safe_sender_id: The safe sender identifier
    """
    if safe_sender_id in customer_forms:
        del customer_forms[safe_sender_id]
        logger.info(f"Cancelled customer form for {safe_sender_id}")

def cleanup_customer_forms():
    """Remove expired customer forms from the cache."""
    current_time = time.time()
    expired_ids = [user_id for user_id, form in customer_forms.items() 
                   if current_time - form['timestamp'] > CUSTOMER_FORM_TTL]
    for user_id in expired_ids:
        del customer_forms[user_id]
        logger.info(f"Expired customer form for {user_id}")

# ==================== TEMPORARY MEDIA STORAGE ====================

def save_media_from_base64(base64_data, sender_id, media_type='image', extension='jpg'):
    """
    Save media from base64 data to temporary storage.
    
    Args:
        base64_data: Base64 encoded media data
        sender_id: User identifier
        media_type: Type of media (image, document)
        extension: File extension
        
    Returns:
        Path to saved file or None if failed
    """
    try:
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{media_type}_{sender_id}_{timestamp}.{extension}"
        filepath = os.path.join(CONFIG["TEMP_MEDIA_DIR"], filename)
        
        # Decode and save
        media_bytes = base64.b64decode(base64_data)
        with open(filepath, 'wb') as f:
            f.write(media_bytes)
        
        logger.info(f"✅ Media saved: {filepath} ({len(media_bytes)} bytes)")
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Error saving media from base64: {e}", exc_info=True)
        return None

def download_and_save_media(url, sender_id, media_type='image', extension='jpg'):
    """
    Download media from URL and save to temporary storage.
    
    Args:
        url: Media URL to download
        sender_id: User identifier
        media_type: Type of media (image, document)
        extension: File extension
        
    Returns:
        Path to saved file or None if failed
    """
    try:
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{media_type}_{sender_id}_{timestamp}.{extension}"
        filepath = os.path.join(CONFIG["TEMP_MEDIA_DIR"], filename)
        
        # Download media
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save to file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"✅ Media downloaded: {filepath} ({len(response.content)} bytes)")
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Error downloading media from {url}: {e}", exc_info=True)
        return None

def cleanup_old_media():
    """Remove media files older than configured hours."""
    try:
        media_dir = CONFIG["TEMP_MEDIA_DIR"]
        if not os.path.exists(media_dir):
            return
        
        cutoff_time = datetime.now() - timedelta(hours=CONFIG["MEDIA_CLEANUP_HOURS"])
        removed_count = 0
        
        for filename in os.listdir(media_dir):
            filepath = os.path.join(media_dir, filename)
            
            # Check if it's a file and get its modification time
            if os.path.isfile(filepath):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_mtime < cutoff_time:
                    os.remove(filepath)
                    removed_count += 1
                    logger.info(f"🗑️ Removed old media: {filename}")
        
        if removed_count > 0:
            logger.info(f"🧹 Cleanup complete: {removed_count} old media files removed")
            
    except Exception as e:
        logger.error(f"❌ Error during media cleanup: {e}", exc_info=True)

def get_extension_from_mimetype(mimetype):
    """Get file extension from mimetype."""
    extension_map = {
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg',
        'image/png': 'png',
        'image/webp': 'webp',
        'application/pdf': 'pdf',
        'application/msword': 'doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    }
    return extension_map.get(mimetype, 'bin')

# ==================== END TEMPORARY MEDIA STORAGE ====================

def process_customer_form_step(safe_sender_id, sender_number, message_text, message_info):
    """
    Process one step of the customer form collection.
    
    Args:
        safe_sender_id: The safe sender identifier
        sender_number: The sender's phone number
        message_text: The message text
        message_info: The full message info for media detection
        
    Returns:
        Response text to send to customer, or None if form is complete
    """
    form = get_customer_form(safe_sender_id)
    if not form:
        return None
    
    current_step = form['step']
    form_data = form['data']
    
    # Step 1: Select Consultant (FIRST)
    if current_step == 'consultant':
        consultant_choice = message_text.strip()
        
        if consultant_choice in ['1', '01', 'josimar', 'Josimar']:
            consultant_name = "Josimar"
            consultant_phone = "(81) 99974-5545"
        elif consultant_choice in ['2', '02', 'jailson', 'Jailson']:
            consultant_name = "Jailson"
            consultant_phone = "(81) 99750-7161"
        else:
            return "Por favor, escolha uma opção válida:\n\n*01* - Josimar\n*02* - Jailson\n\n_Digite 01 ou 02_"
        
        form_data['consultant_name'] = consultant_name
        form_data['consultant_phone'] = consultant_phone
        update_customer_form(safe_sender_id, 'name', 'consultant_name', consultant_name)
        update_customer_form(safe_sender_id, 'name', 'consultant_phone', consultant_phone)
        
        return f"Ótimo! O *{consultant_name}* vai te atender! 😊\n\nAgora preciso de algumas informações.\n\n👤 Por favor, me diga seu *nome completo*:"
    
    # Step 2: Collect name
    elif current_step == 'name':
        if len(message_text.strip()) < 2:
            return "Por favor, digite seu nome completo:"
        
        form_data['name'] = message_text.strip()
        update_customer_form(safe_sender_id, 'phone', 'name', message_text.strip())
        return "Perfeito! Agora, qual seu *telefone* para contato?\n_(Digite apenas números)_"
    
    # Step 3: Collect phone
    elif current_step == 'phone':
        # Remove non-digits
        phone = ''.join(filter(str.isdigit, message_text))
        if len(phone) < 10:
            return "Por favor, digite um telefone válido com DDD:\n_(Exemplo: 81999887766)_"
        
        form_data['phone'] = phone
        update_customer_form(safe_sender_id, 'cpf', 'phone', phone)
        return "Ótimo! Agora preciso do seu *CPF*:\n_(Digite apenas números)_"
    
    # Step 4: Collect CPF
    elif current_step == 'cpf':
        # Remove non-digits
        cpf = ''.join(filter(str.isdigit, message_text))
        if len(cpf) != 11:
            return "Por favor, digite um CPF válido com 11 dígitos:\n_(Apenas números)_"
        
        # Format CPF for display
        cpf_formatted = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        form_data['cpf'] = cpf_formatted
        
        # Check if this is for budget (opção 2) - only ask for prescription in this case
        form_reason = form.get('reason', '')
        is_budget = '2 -' in form_reason or 'orçamento' in form_reason.lower()
        
        if is_budget:
            # Only ask for prescription if it's a budget request
            update_customer_form(safe_sender_id, 'prescription', 'cpf', cpf_formatted)
            return "Perfeito! Você possui *receita de óculos*?\n\n✅ Se *SIM*: Envie uma foto ou PDF da receita\n❌ Se *NÃO*: Digite 'não' ou 'nao'"
        else:
            # For other options, skip prescription and go to confirmation
            form_data['prescription'] = "Não solicitado (apenas para orçamentos)"
            form_data['has_prescription'] = False
            update_customer_form(safe_sender_id, 'confirm', 'cpf', cpf_formatted)
            update_customer_form(safe_sender_id, 'confirm', 'prescription', "Não solicitado")
            
            # Show summary for confirmation
            summary = f"""
📋 *Confirmação dos Dados*

👨‍💼 *Consultor:* {form_data.get('consultant_name')} - {form_data.get('consultant_phone')}
👤 *Nome:* {form_data.get('name')}
📱 *Telefone:* {form_data.get('phone')}
🆔 *CPF:* {cpf_formatted}

*Motivo do contato:* {form['reason']}

_Seus dados estão corretos?_

✅ Digite *SIM* para confirmar
❌ Digite *NÃO* para recomeçar
"""
            return summary.strip()
    
    # Step 5: Collect prescription
    elif current_step == 'prescription':
        has_prescription = False
        prescription_info = "Não possui receita"
        prescription_file_path = None
        
        # Check if message has image
        if message_info.get('message', {}).get('imageMessage'):
            has_prescription = True
            image_data = message_info['message']['imageMessage']
            
            # Get additional info
            caption = image_data.get('caption', '')
            mimetype = image_data.get('mimetype', 'image/jpeg')
            extension = get_extension_from_mimetype(mimetype)
            
            logger.info(f"📸 Processing image message:")
            logger.info(f"   - MIME type: {mimetype}")
            logger.info(f"   - Caption: {caption if caption else 'N/A'}")
            
            # Strategy 1: Try to download the FULL RESOLUTION image from URL first (best quality!)
            image_url = image_data.get('url')
            if image_url:
                logger.info(f"📥 Strategy 1: Attempting to download full resolution image from URL")
                logger.info(f"   - URL: {image_url[:100]}..." if len(image_url) > 100 else f"   - URL: {image_url}")
                prescription_file_path = download_and_save_media(
                    image_url,
                    safe_sender_id,
                    'prescription',
                    extension
                )
                if prescription_file_path:
                    logger.info(f"✅ SUCCESS: Full resolution image downloaded and saved!")
                else:
                    logger.warning(f"⚠️ FAILED: Could not download from URL, trying fallback...")
            else:
                logger.warning(f"⚠️ No 'url' field in imageMessage, skipping URL download")
            
            # Strategy 2: Fallback to jpegThumbnail (lower quality but more reliable)
            if not prescription_file_path:
                jpeg_thumbnail = image_data.get('jpegThumbnail')
                if jpeg_thumbnail:
                    logger.info(f"📥 Strategy 2: Using jpegThumbnail (base64 encoded)")
                    logger.info(f"   - Thumbnail size: {len(jpeg_thumbnail)} characters (base64)")
                    prescription_file_path = save_media_from_base64(
                        jpeg_thumbnail, 
                        safe_sender_id, 
                        'prescription', 
                        extension
                    )
                    if prescription_file_path:
                        logger.info(f"✅ SUCCESS: Thumbnail image saved (lower quality)")
                    else:
                        logger.error(f"❌ FAILED: Could not save thumbnail image")
                else:
                    logger.error(f"❌ CRITICAL: No 'jpegThumbnail' available - cannot save image!")
            
            # Log final status
            logger.info(f"📊 Final image processing status:")
            logger.info(f"   - File saved: {prescription_file_path is not None}")
            if prescription_file_path:
                logger.info(f"   - File path: {prescription_file_path}")
                logger.info(f"   - File size: {os.path.getsize(prescription_file_path)} bytes")
            
            if prescription_file_path:
                prescription_info = f"✅ Cliente enviou FOTO da receita (salva localmente)"
            else:
                prescription_info = f"⚠️ Cliente enviou FOTO da receita (falha ao salvar)"
            
            if caption:
                prescription_info += f" (legenda: {caption})"
        
        # Check if message has document/PDF
        elif message_info.get('message', {}).get('documentMessage'):
            has_prescription = True
            doc_data = message_info['message']['documentMessage']
            
            doc_name = doc_data.get('fileName', 'documento.pdf')
            mimetype = doc_data.get('mimetype', 'application/pdf')
            extension = get_extension_from_mimetype(mimetype)
            
            # Note: Documents usually don't have thumbnails, would need actual download
            logger.info(f"📄 Document received - filename: {doc_name}, mimetype: {mimetype}")
            prescription_info = f"✅ Cliente enviou ARQUIVO da receita: {doc_name}"
        
        # Check for text response
        elif message_text.lower().strip() in ['não', 'nao', 'n', 'sem receita', 'não tenho', 'nao tenho']:
            prescription_info = "❌ Cliente informou que NÃO possui receita"
        
        elif message_text.lower().strip() in ['sim', 's', 'tenho', 'possuo']:
            return "Por favor, *envie a foto ou PDF* da sua receita de óculos 📸"
        
        form_data['prescription'] = prescription_info
        form_data['has_prescription'] = has_prescription
        form_data['prescription_file_path'] = prescription_file_path
        update_customer_form(safe_sender_id, 'confirm', 'prescription', prescription_info)
        if prescription_file_path:
            update_customer_form(safe_sender_id, 'confirm', 'prescription_file_path', prescription_file_path)
        
        # Show summary for confirmation
        summary = f"""
📋 *Confirmação dos Dados*

👨‍💼 *Consultor:* {form_data.get('consultant_name')} - {form_data.get('consultant_phone')}
👤 *Nome:* {form_data.get('name')}
📱 *Telefone:* {form_data.get('phone')}
🆔 *CPF:* {form_data.get('cpf')}
💊 *Receita:* {prescription_info}

*Motivo do contato:* {form['reason']}

_Seus dados estão corretos?_

✅ Digite *SIM* para confirmar
❌ Digite *NÃO* para recomeçar
"""
        return summary.strip()
    
    # Step 6: Confirm and send to group
    elif current_step == 'confirm':
        if message_text.lower().strip() in ['sim', 's', 'confirmo', 'correto', 'ok']:
            # Send notification to group with all collected data
            send_customer_form_to_group(sender_number, form)
            
            # Get consultant name for personalized message
            consultant_name = form_data.get('consultant_name', 'nosso consultor')
            
            cancel_customer_form(safe_sender_id)
            return f"✅ Perfeito! Suas informações foram enviadas para o *{consultant_name}*.\n\nEle entrará em contato com você em breve! 😊\n\n_Posso ajudar com mais alguma coisa?_"
        
        elif message_text.lower().strip() in ['não', 'nao', 'n', 'cancelar', 'recomeçar', 'recomecar']:
            cancel_customer_form(safe_sender_id)
            return "❌ Formulário cancelado. Vamos recomeçar!\n\n_Como posso ajudar você?_"
        
        else:
            return "Por favor, digite *SIM* para confirmar ou *NÃO* para recomeçar:"
    
    return None

def send_customer_form_to_group(customer_number, form):
    """
    Send complete customer form data to the notification group.
    
    Args:
        customer_number: The customer's phone number
        form: The form data with customer information
    """
    if not CONFIG["NOTIFICATION_GROUP_ID"]:
        logger.warning("NOTIFICATION_GROUP_ID not configured. Skipping group notification.")
        return False
    
    form_data = form['data']
    
    # Format customer number for display
    display_number = customer_number.replace('@s.whatsapp.net', '').replace('@g.us', '')
    
    # Build notification message
    from datetime import datetime
    timestamp = datetime.now().strftime('%d/%m/%Y às %H:%M')
    
    notification_parts = [
        "🔔 *NOVA SOLICITAÇÃO DE ATENDIMENTO*",
        "",
        f"⏰ *Horário:* {timestamp}",
        f"📋 *Motivo:* {form['reason']}",
        "",
        "�‍💼 *CONSULTOR SOLICITADO*",
        f"• *{form_data.get('consultant_name', 'Não especificado')}*",
        f"• *Telefone:* {form_data.get('consultant_phone', 'Não informado')}",
        "",
        "👤 *DADOS DO CLIENTE*",
        f"• *Nome:* {form_data.get('name', 'Não informado')}",
        f"• *Telefone:* {form_data.get('phone', 'Não informado')}",
        f"• *WhatsApp:* {display_number}",
        f"• *CPF:* {form_data.get('cpf', 'Não informado')}",
        "",
    ]
    
    # Add prescription info (only if it was collected - budget requests)
    prescription_info = form_data.get('prescription', 'Não solicitado')
    prescription_file_path = form_data.get('prescription_file_path')
    
    # Check if prescription was actually collected (not skipped)
    if form_data.get('has_prescription', False):
        notification_parts.append("💊 *RECEITA DE ÓCULOS*")
        notification_parts.append(prescription_info)
        
        if prescription_file_path:
            notification_parts.append("📎 _Arquivo da receita será enviado a seguir_")
        else:
            notification_parts.append("⚠️ _Arquivo não disponível - solicite ao cliente_")
        
        notification_parts.append("")
    elif prescription_info and prescription_info != "Não solicitado (apenas para orçamentos)":
        # Prescription was asked but customer doesn't have one
        notification_parts.append(f"💊 *Receita de óculos:* {prescription_info}")
    # If prescription_info contains "Não solicitado", don't show it at all
    
    notification_parts.extend([
        "",
        "---",
        "_Atender o cliente iniciando conversa com o WhatsApp dele_"
    ])
    
    notification_message = "\n".join(notification_parts)
    
    try:
        # Send text notification first
        result = send_whatsapp_message(
            CONFIG["NOTIFICATION_GROUP_ID"],
            notification_message,
            message_type='text'
        )
        
        if result:
            logger.info(f"✅ Customer form sent to group for {display_number}")
            
            # If there's a saved prescription file, send it to the group
            if prescription_file_path and os.path.exists(prescription_file_path):
                logger.info(f"📎 === SENDING PRESCRIPTION FILE TO GROUP ===")
                logger.info(f"📎 File path: {prescription_file_path}")
                logger.info(f"📎 File exists: {os.path.exists(prescription_file_path)}")
                logger.info(f"📎 File size: {os.path.getsize(prescription_file_path)} bytes")
                
                # Determine message type based on file extension
                file_ext = os.path.splitext(prescription_file_path)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    media_type = 'image'
                elif file_ext == '.pdf':
                    media_type = 'document'
                else:
                    media_type = 'document'
                
                logger.info(f"📎 Media type determined: {media_type}")
                
                # Build public URL for WaSender API to download the file
                # Format: https://your-ngrok-url.com/media/prescription_xxx.jpg
                filename = os.path.basename(prescription_file_path)
                public_url = f"{CONFIG['WEBHOOK_BASE_URL']}/media/{filename}"
                
                logger.info(f"🌐 === CONSTRUCTING PUBLIC URL ===")
                logger.info(f"🌐 WEBHOOK_BASE_URL: {CONFIG['WEBHOOK_BASE_URL']}")
                logger.info(f"🌐 Filename: {filename}")
                logger.info(f"🌐 Complete public URL: {public_url}")
                
                # Validate URL before sending
                if not CONFIG['WEBHOOK_BASE_URL'] or CONFIG['WEBHOOK_BASE_URL'] == 'http://localhost:5001':
                    logger.error(f"❌ CRITICAL: WEBHOOK_BASE_URL is not configured correctly!")
                    logger.error(f"❌ Current value: {CONFIG['WEBHOOK_BASE_URL']}")
                    logger.error(f"❌ WhatsApp API requires HTTPS public URL (use ngrok for dev)")
                    send_whatsapp_message(
                        CONFIG["NOTIFICATION_GROUP_ID"],
                        f"⚠️ *ERRO DE CONFIGURAÇÃO*\n\nWebhook URL não configurada corretamente.\nArquivo salvo localmente: {filename}\n\n_Solicite a receita diretamente ao cliente: {display_number}_",
                        message_type='text'
                    )
                    return result
                
                try:
                    logger.info(f"📤 === CALLING WASENDER API ===")
                    logger.info(f"📤 Sending to group: {CONFIG['NOTIFICATION_GROUP_ID']}")
                    logger.info(f"📤 Message type: {media_type}")
                    logger.info(f"📤 Media URL: {public_url}")
                    logger.info(f"📤 Caption: 💊 *Receita de óculos de {form_data.get('name', 'Cliente')}*")
                    
                    media_result = send_whatsapp_message(
                        CONFIG["NOTIFICATION_GROUP_ID"],
                        f"💊 *Receita de óculos de {form_data.get('name', 'Cliente')}*",
                        message_type=media_type,
                        media_url=public_url  # Use public URL instead of data URL
                    )
                    
                    if media_result:
                        logger.info(f"✅ === SUCCESS: Prescription file sent to group! ===")
                    else:
                        logger.warning(f"⚠️ === FAILED: WaSender API returned False ===")
                        logger.warning(f"⚠️ Possible causes:")
                        logger.warning(f"   1. URL is not publicly accessible")
                        logger.warning(f"   2. WaSender API key is invalid")
                        logger.warning(f"   3. File format not supported")
                        logger.warning(f"   4. Network/firewall issue")
                        send_whatsapp_message(
                            CONFIG["NOTIFICATION_GROUP_ID"],
                            f"⚠️ Não foi possível enviar o arquivo automaticamente.\n📁 Arquivo salvo localmente: {filename}\n\n_Solicite a receita diretamente ao cliente: {display_number}_",
                            message_type='text'
                        )
                        
                except Exception as e:
                    logger.error(f"❌ === EXCEPTION while sending prescription file ===")
                    logger.error(f"❌ Exception type: {type(e).__name__}")
                    logger.error(f"❌ Exception message: {str(e)}")
                    logger.error(f"❌ Full traceback:", exc_info=True)
                    send_whatsapp_message(
                        CONFIG["NOTIFICATION_GROUP_ID"],
                        f"⚠️ Erro ao enviar arquivo da receita.\n_Solicite diretamente ao cliente: {display_number}_",
                        message_type='text'
                    )
            else:
                if prescription_file_path:
                    logger.warning(f"⚠️ Prescription file path exists but file not found: {prescription_file_path}")
                else:
                    logger.info(f"ℹ️ No prescription file to send (customer doesn't have one or upload failed)")
        
        return result
    except Exception as e:
        logger.error(f"❌ Error sending customer form to group: {e}")
        return False

def load_conversation_history(user_id):
    """Loads conversation history for a given user_id."""
    return conversation_manager.load(user_id)

def save_conversation_history(user_id, history):
    """Saves conversation history for a given user_id."""
    conversation_manager.save(user_id, history)

class GeminiClient:
    """Client for interacting with the Gemini AI API."""
    
    def __init__(self, api_key, model_name, system_instruction, few_shot_examples=None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: The Gemini API key
            model_name: The model to use (e.g., 'gemini-2.0-flash')
            system_instruction: System instruction for persona
            few_shot_examples: List of example conversations for few-shot learning
        """
        self.api_key = api_key
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.few_shot_examples = few_shot_examples or []
        
        if not api_key:
            logger.error("Gemini API key is not configured.")
            raise ValueError("Gemini API key is required")
            
        genai.configure(api_key=api_key)
        logger.info(f"Gemini client initialized with model: {model_name}")
        logger.info(f"Few-shot learning: {'Enabled' if self.few_shot_examples else 'Disabled'} ({len(self.few_shot_examples)} examples)")
        
    def generate_response(self, message_text, conversation_history=None):
        """
        Generate a response from Gemini using the provided message and optional history.
        
        Args:
            message_text: The message to respond to
            conversation_history: Optional conversation history
            
        Returns:
            The generated response text
        """
        if not self.api_key:
            logger.error("Gemini API key is not configured.")
            return "Sorry, I'm having trouble connecting to my brain right now (API key issue)."

        try:
            # Create model with system instruction for persona
            model = genai.GenerativeModel(
                self.model_name, 
                system_instruction=self.system_instruction
            )
            
            logger.info(f"Sending prompt to Gemini (system persona active): {message_text[:200]}...")

            # Build complete history with few-shot examples
            if conversation_history or self.few_shot_examples:
                # Convert few-shot examples to history format
                few_shot_history = build_few_shot_history(self.few_shot_examples)
                
                # Combine few-shot examples with actual conversation history
                complete_history = few_shot_history.copy()
                if conversation_history:
                    complete_history.extend(conversation_history)
                
                logger.debug(f"Using history with {len(complete_history)} messages (few-shot: {len(few_shot_history)}, conversation: {len(conversation_history) if conversation_history else 0})")
                
                # Start chat with combined history
                chat = model.start_chat(history=complete_history)
                response = chat.send_message(message_text)
            else:
                # For first message with no history and no examples
                response = model.generate_content(message_text)

            # Extract the text from the response
            if response and hasattr(response, 'text') and response.text:
                return response.text.strip()
            elif response and response.candidates:
                # Fallback if .text is not directly available but candidates are
                try:
                    return response.candidates[0].content.parts[0].text.strip()
                except (IndexError, AttributeError, KeyError) as e:
                    logger.error(f"Error parsing Gemini response candidates: {e}. Response: {response}")
                    return "I received an unusual response structure from Gemini. Please try again."
            else:
                logger.error(f"Gemini API returned an empty or unexpected response: {response}")
                return "I received an empty or unexpected response from Gemini. Please try again."

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            return "I'm having trouble processing that request with my AI brain. Please try again later."

# Initialize Gemini client if API key is available
gemini_client = None
if CONFIG["GEMINI_API_KEY"]:
    try:
        gemini_client = GeminiClient(
            api_key=CONFIG["GEMINI_API_KEY"],
            model_name=CONFIG["GEMINI_MODEL"],
            system_instruction=PERSONA_DESCRIPTION,
            few_shot_examples=FEW_SHOT_EXAMPLES
        )
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}", exc_info=True)

def get_gemini_response(message_text, conversation_history=None):
    """
    Generates a response from Gemini using the gemini_client.
    This wrapper maintains compatibility with the existing code.
    """
    if not gemini_client:
        logger.error("Gemini client is not initialized.")
        return "Sorry, I'm having trouble connecting to my brain right now (API key issue)."
    
    return gemini_client.generate_response(message_text, conversation_history)

def send_notification_to_group(customer_number, customer_message, menu_option=None):
    """
    Sends notification to the notification group when customer requests assistance.
    
    Args:
        customer_number: The customer's phone number
        customer_message: The message from the customer
        menu_option: Optional menu option selected by customer
    """
    if not CONFIG["NOTIFICATION_GROUP_ID"]:
        logger.warning("NOTIFICATION_GROUP_ID not configured. Skipping group notification.")
        return False
    
    # Format customer number for display (remove @s.whatsapp.net)
    display_number = customer_number.replace('@s.whatsapp.net', '').replace('@g.us', '')
    
    # Build notification message
    from datetime import datetime
    timestamp = datetime.now().strftime('%d/%m/%Y às %H:%M')
    
    notification_parts = [
        "🔔 *NOVA SOLICITAÇÃO DE ATENDIMENTO*",
        "",
        f"👤 *Cliente:* {display_number}",
        f"⏰ *Horário:* {timestamp}",
        ""
    ]
    
    if menu_option:
        notification_parts.append(f"📋 *Opção do menu:* {menu_option}")
        notification_parts.append("")
    
    notification_parts.extend([
        "📝 *Mensagem:*",
        customer_message,
        "",
        "---",
        "_Atender o cliente iniciando conversa com o número dele_"
    ])
    
    notification_message = "\n".join(notification_parts)
    
    try:
        result = send_whatsapp_message(
            CONFIG["NOTIFICATION_GROUP_ID"],
            notification_message,
            message_type='text'
        )
        if result:
            logger.info(f"✅ Notification sent to group for customer {display_number}")
        return result
    except Exception as e:
        logger.error(f"❌ Error sending notification to group: {e}")
        return False

def send_whatsapp_message(recipient_number, message_content, message_type='text', media_url=None):
    """Sends a message via WaSenderAPI SDK. Supports text and media messages."""
    if not wasender_client:
        logger.error("WaSender API client is not initialized. Please check .env file.")
        return False
    
    # Sanitize recipient_number to remove "@s.whatsapp.net" (but keep @g.us for groups)
    if recipient_number and "@s.whatsapp.net" in recipient_number:
        formatted_recipient_number = recipient_number.split('@')[0]
    elif recipient_number and "@g.us" in recipient_number:
        # Keep group ID as is
        formatted_recipient_number = recipient_number
    else:
        formatted_recipient_number = recipient_number
    
    try:
        if message_type == 'text':
            # Send typing indicator first for better UX
            try:
                wasender_client.send_presence(
                    to=formatted_recipient_number,
                    state='composing'
                )
                logger.info(f"Typing indicator sent to {recipient_number}")
            except Exception as e:
                logger.warning(f"Could not send typing indicator: {e}")
            
            response = wasender_client.send_text(
                to=formatted_recipient_number,
                text_body=message_content
            )
            logger.info(f"Text message sent to {recipient_number}.")
            return True
        elif message_type == 'image' and media_url:
            response = wasender_client.send_image(
                to=formatted_recipient_number,
                url=media_url,
                caption=message_content if message_content else None
            )
            logger.info(f"Image message sent to {recipient_number}.")
            return True
        elif message_type == 'video' and media_url:
            response = wasender_client.send_video(
                to=formatted_recipient_number,
                url=media_url,
                caption=message_content if message_content else None
            )
            logger.info(f"Video message sent to {recipient_number}. ")
            return True
        elif message_type == 'audio' and media_url:
            response = wasender_client.send_audio(
                to=formatted_recipient_number,
                url=media_url
            )
            logger.info(f"Audio message sent to {recipient_number}.")
            return True
        elif message_type == 'document' and media_url:
            response = wasender_client.send_document(
                to=formatted_recipient_number,
                url=media_url,
                filename="receita.pdf",  # Default filename for prescription documents
                caption=message_content if message_content else None
            )
            logger.info(f"Document message sent to {recipient_number}. ")
            return True
        else:
            if message_type != 'text':
                logger.error(f"Media URL is required for message type '{message_type}'.")
                return False
            logger.error(f"Unsupported message type or missing content/media_url: {message_type}")
            return False
    except WasenderAPIError as e:
        logger.error(f"WaSenderAPI Error sending {message_type} to {recipient_number}: {e.message} (Status: {e.status_code})")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending WhatsApp message: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming WhatsApp messages via webhook using the WaSenderAPI SDK."""
    try:        
        logger.info("=== WEBHOOK CALLED ===")
        
        # Run media cleanup periodically (every webhook call)
        cleanup_old_media()
        
        if not wasender_client:
            logger.error("WaSender API client is not initialized. Cannot process webhook.")
            return jsonify({'status': 'error', 'message': 'WaSender client not initialized'}), 500

        data = request.json
        logger.info(f"Received webhook data: {data}")
        
        if data.get('event') == 'messages.upsert' and data.get('data') and data['data'].get('messages'):
            message_info = data['data']['messages']
            logger.info(f"Processing message info: {message_info}")
            
            # Get message ID for deduplication
            message_id = message_info.get('key', {}).get('id')
            
            # Check if this message was already processed
            if message_id and is_message_processed(message_id):
                logger.info(f"Skipping duplicate message: {message_id}")
                return jsonify({'status': 'success', 'message': 'Duplicate message ignored'}), 200
            
            # Mark this message as processed
            if message_id:
                mark_message_processed(message_id)
            
            # Check if it's a message sent by the bot itself
            if message_info.get('key', {}).get('fromMe'):
                logger.info(f"Ignoring self-sent message: {message_info.get('key', {}).get('id')}")
                return jsonify({'status': 'success', 'message': 'Self-sent message ignored'}), 200

            sender_number = message_info.get('key', {}).get('remoteJid')
            logger.info(f"Sender number: {sender_number}")
            
            incoming_message_text = None
            message_type = 'unknown'

            # Extract message content based on message structure
            if message_info.get('message'):
                msg_content_obj = message_info['message']
                logger.info(f"Message content object keys: {msg_content_obj.keys()}")
                logger.info(f"Full message content object: {msg_content_obj}")
                
                if 'conversation' in msg_content_obj:
                    incoming_message_text = msg_content_obj['conversation']
                    message_type = 'text'
                    logger.info(f"Found conversation text: {incoming_message_text}")
                elif 'extendedTextMessage' in msg_content_obj and 'text' in msg_content_obj['extendedTextMessage']:
                    incoming_message_text = msg_content_obj['extendedTextMessage']['text']
                    message_type = 'text'
                    logger.info(f"Found extended text: {incoming_message_text}")
                elif 'imageMessage' in msg_content_obj:
                    incoming_message_text = "[Imagem enviada]"
                    message_type = 'image'
                    logger.info(f"Found image message - Full data: {msg_content_obj['imageMessage']}")
                elif 'documentMessage' in msg_content_obj:
                    incoming_message_text = "[Documento enviado]"
                    message_type = 'document'
                    logger.info(f"Found document message - Full data: {msg_content_obj['documentMessage']}")
                else:
                    logger.warning(f"Unknown message type. Available keys: {list(msg_content_obj.keys())}")
                    # Try to detect any message type that contains 'Message'
                    for key in msg_content_obj.keys():
                        if 'Message' in key:
                            logger.info(f"Found potential message type: {key} with data: {msg_content_obj[key]}")
                            incoming_message_text = f"[{key} recebido]"
                            message_type = key.replace('Message', '').lower()
                            break

            if not sender_number:
                logger.warning("Webhook received message without sender information.")
                return jsonify({'status': 'error', 'message': 'Incomplete sender data'}), 400

            safe_sender_id = "".join(c if c.isalnum() else '_' for c in sender_number)
            logger.info(f"Safe sender ID: {safe_sender_id}")
            
            # Cancel any active sending session for this user
            # This ensures we stop sending old chunks if user sends a new message
            start_sending_session(safe_sender_id)
            cleanup_sending_sessions()
            
            # Check if user is in the middle of filling a customer form (accepts text, image, and documents)
            active_form = get_customer_form(safe_sender_id)
            
            # Accept any message type that was detected (text, image, document, or others)
            if active_form and message_type != 'unknown':
                logger.info(f"Processing customer form step for {safe_sender_id} - message_type: {message_type}")
                
                # For media messages, use placeholder text
                if not incoming_message_text:
                    incoming_message_text = ""
                
                form_response = process_customer_form_step(safe_sender_id, sender_number, incoming_message_text, message_info)
                
                if form_response:
                    send_whatsapp_message(sender_number, form_response, message_type='text')
                    end_sending_session(safe_sender_id)
                    logger.info("=== WEBHOOK PROCESSING COMPLETE ===")
                    return jsonify({'status': 'success'}), 200
                else:
                    logger.info("Form step returned no response, continuing to normal flow")
            elif active_form:
                logger.warning(f"User has active form but message type is unknown: {message_type}")
            
            # Process text messages (normal conversation flow)
            if message_type == 'text' and incoming_message_text:
                logger.info(f"Processing text message: '{incoming_message_text}' from {sender_number}")
                
                conversation_history = load_conversation_history(safe_sender_id)
                logger.info(f"Loaded conversation history for {safe_sender_id}")
                
                response_text = None
                should_notify_group = False
                should_start_form = False
                selected_menu_option = None
                
                # Check if interactive menu is enabled
                if MENU_CONFIG.get('enabled', False):
                    # Check if it's a greeting (first interaction)
                    if is_greeting(incoming_message_text, MENU_CONFIG.get('greeting_keywords', [])):
                        logger.info(f"Greeting detected, showing menu to {sender_number}")
                        response_text = MENU_CONFIG.get('welcome_message', '')
                    
                    # Check if it's a menu option selection
                    elif is_menu_option(incoming_message_text, MENU_CONFIG.get('menu_options', {})):
                        option_key = is_menu_option(incoming_message_text, MENU_CONFIG.get('menu_options', {}))
                        logger.info(f"Menu option {option_key} selected by {sender_number}")
                        response_text = get_menu_response(option_key, MENU_CONFIG.get('menu_options', {}))
                        
                        # Check if this option requires collecting customer data (options 2-6 need specialist)
                        if option_key in ['2', '3', '4', '6']:
                            should_start_form = True
                            option_title = MENU_CONFIG.get('menu_options', {}).get(option_key, {}).get('title', f'Opção {option_key}')
                            selected_menu_option = f"{option_key} - {option_title}"
                            
                            # Start collecting customer information
                            start_customer_form(safe_sender_id, selected_menu_option)
                            logger.info(f"Started customer form for menu option {option_key}")
                            
                            # Add prompt to start form - ask for consultant first
                            response_text += "\n\n📋 Primeiro, escolha com qual *consultor* você prefere falar:\n\n*01* - Josimar (81) 99974-5545\n*02* - Jailson (81) 99750-7161\n\n_Digite 01 ou 02_"
                
                # If no menu response, use Gemini AI
                if not response_text:
                    logger.info(f"Using Gemini AI for response")
                    response_text = get_gemini_response(incoming_message_text, conversation_history)
                    logger.info(f"Gemini reply: {response_text}")
                    
                    # Detect intent from user's original message to determine if form is needed
                    user_message_lower = incoming_message_text.lower()
                    form_reason = None
                    should_start_form = False
                    
                    # Check for EXPLICIT request to speak with consultant
                    explicit_consultant_request = [
                        'quero falar com', 'prefiro falar com', 'falar com o', 'falar com a',
                        'quero o', 'quero a', 'preciso falar', 'gostaria de falar',
                        'pode chamar', 'chama o', 'chama a', 'contato do', 'contato da'
                    ]
                    
                    # Check if user is explicitly asking to speak with specific consultant
                    is_explicit_request = any(phrase in user_message_lower for phrase in explicit_consultant_request)
                    mentions_consultant = 'jailson' in user_message_lower or 'josimar' in user_message_lower
                    
                    # Only start form if user explicitly asks to speak with consultant
                    if is_explicit_request and mentions_consultant:
                        should_start_form = True
                        form_reason = "5 - Falar com consultor (solicitação direta)"
                        logger.info(f"User EXPLICITLY requested to speak with consultant")
                    
                    # Check for budget/quote request (should ask for prescription)
                    elif any(keyword in user_message_lower for keyword in ['orçamento', 'orcamento', 'orçar', 'fazer óculos', 'comprar óculos']):
                        should_start_form = True
                        form_reason = "2 - Fazer orçamento de óculos (solicitação via conversa)"
                        logger.info(f"Detected BUDGET request from user message")
                    
                    # Check for repair/adjustment request (no prescription needed)
                    elif any(keyword in user_message_lower for keyword in ['ajuste', 'ajustar', 'reparo', 'reparar', 'consertar', 'conserto', 'quebrou', 'quebrado']):
                        should_start_form = True
                        form_reason = "3 - Ajustes e reparos (solicitação via conversa)"
                        logger.info(f"Detected REPAIR request from user message")
                    
                    # Start form ONLY if we detected an explicit request
                    if should_start_form and form_reason:
                        selected_menu_option = form_reason
                        
                        # Start collecting customer information
                        start_customer_form(safe_sender_id, form_reason)
                        logger.info(f"Started customer form - reason: {form_reason}")
                        
                        # Add prompt to start form - ask for consultant first
                        response_text += "\n\n📋 Primeiro, escolha com qual *consultor* você prefere falar:\n\n*01* - Josimar (81) 99974-5545\n*02* - Jailson (81) 99750-7161\n\n_Digite 01 ou 02_"
                
                if response_text:
                    message_chunks = split_message(response_text)
                    logger.info(f"Sending {len(message_chunks)} message chunks to {sender_number}")
                    
                    chunks_sent = 0
                    for i, chunk in enumerate(message_chunks):
                        # Check if sending was cancelled by a new incoming message
                        if should_cancel_sending(safe_sender_id):
                            logger.warning(f"Sending cancelled for {sender_number} - user sent new message")
                            break
                        
                        logger.info(f"Sending chunk {i+1}/{len(message_chunks)}: {chunk[:50]}...")
                        send_result = send_whatsapp_message(sender_number, chunk, message_type='text')
                        if not send_result:
                            logger.error(f"Failed to send message chunk {i+1} to {sender_number}")
                            break
                        else:
                            chunks_sent += 1
                            logger.info(f"Successfully sent chunk {i+1} to {sender_number}")
                        
                        # Delay between messages (only if there are more chunks)
                        if i < len(message_chunks) - 1:
                            import random
                            import time
                            # Reduced delay for better responsiveness (1-2 seconds instead of 5-7)
                            delay = random.uniform(1.0, 2.0)
                            logger.info(f"Waiting {delay:.1f} seconds before next chunk...")
                            
                            # Check for cancellation during delay (check every 0.5 seconds)
                            delay_steps = int(delay / 0.5)
                            for _ in range(delay_steps):
                                if should_cancel_sending(safe_sender_id):
                                    logger.warning(f"Sending cancelled during delay for {sender_number}")
                                    break
                                time.sleep(0.5)
                            
                            # Final check after delay
                            if should_cancel_sending(safe_sender_id):
                                logger.warning(f"Sending cancelled for {sender_number}")
                                break
                    
                    # End the sending session
                    end_sending_session(safe_sender_id)
                    
                    # Only save history and send notifications if we completed successfully
                    if chunks_sent == len(message_chunks):
                        # NOTE: We no longer send notifications here - the form will handle that
                        # when the customer completes the data collection
                        
                        # Save conversation history
                        conversation_manager.add_exchange(safe_sender_id, incoming_message_text, response_text)
                        logger.info(f"Saved conversation history for {safe_sender_id}")
                    else:
                        logger.warning(f"Message sending incomplete for {sender_number} - only {chunks_sent}/{len(message_chunks)} chunks sent")
                else:
                    logger.error("No reply generated")
            else:
                logger.warning(f"Message type '{message_type}' not supported or no text content")
        else:
            logger.warning(f"Webhook data doesn't match expected format. Event: {data.get('event')}")
        
        logger.info("=== WEBHOOK PROCESSING COMPLETE ===")
        return jsonify({'status': 'success'}), 200
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/status', methods=['GET'])
def status():
    """Get status information about the service."""
    return jsonify({
        'status': 'active',
        'version': '1.0.0',
        'persona': PERSONA_NAME,
        'services': {
            'wasender': wasender_client is not None,
            'gemini': gemini_client is not None,
        },
        'config': {
            'conversation_dir': CONFIG["CONVERSATIONS_DIR"],
            'gemini_model': CONFIG["GEMINI_MODEL"],
        }
    })

@app.route('/clear_history/<user_id>', methods=['POST'])
def clear_history(user_id):
    """Clear conversation history for a user."""
    try:
        # Sanitize user_id to prevent directory traversal
        safe_user_id = "".join(c if c.isalnum() else '_' for c in user_id)
        file_path = os.path.join(CONFIG["CONVERSATIONS_DIR"], f"{safe_user_id}.json")
        
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleared conversation history for {safe_user_id}")
            return jsonify({'status': 'success', 'message': f'History cleared for {safe_user_id}'}), 200
        else:
            logger.info(f"No conversation history found for {safe_user_id}")
            return jsonify({'status': 'success', 'message': f'No history found for {safe_user_id}'}), 200
    except Exception as e:
        logger.error(f"Error clearing history for {user_id}: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    # Display startup information
    logger.info("======================================================")
    logger.info("  WhatsApp Gemini Chatbot Starting")
    logger.info("======================================================")
    logger.info(f"Persona: {PERSONA_NAME}")
    logger.info(f"Gemini Model: {CONFIG['GEMINI_MODEL']}")
    logger.info(f"Conversations Directory: {CONFIG['CONVERSATIONS_DIR']}")
    logger.info(f"WaSender API Client: {'Initialized' if wasender_client else 'NOT INITIALIZED'}")
    logger.info(f"Gemini API Client: {'Initialized' if gemini_client else 'NOT INITIALIZED'}")
    logger.info(f"Starting Flask server on port 5001...")
    logger.info("======================================================")
    
    # For development with webhook testing via ngrok
    port = int(os.getenv('PORT', '5001'))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, port=port, host='0.0.0.0')
