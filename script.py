import os
import logging
from flask import Flask, request, jsonify
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
    "GEMINI_API_KEY": os.getenv('GEMINI_API_KEY'),
    "WASENDER_API_TOKEN": os.getenv('WASENDER_API_TOKEN'),
    "GEMINI_MODEL": os.getenv('GEMINI_MODEL', 'gemini-2.0-flash'),
    "WEBHOOK_SECRET": os.getenv('WEBHOOK_SECRET'),
    "MAX_RETRIES": int(os.getenv('MAX_RETRIES', '3')),
    "MESSAGE_CHUNK_MAX_LINES": int(os.getenv('MESSAGE_CHUNK_MAX_LINES', '3')),
    "MESSAGE_CHUNK_MAX_CHARS": int(os.getenv('MESSAGE_CHUNK_MAX_CHARS', '100')),
    "MESSAGE_DELAY_MIN": float(os.getenv('MESSAGE_DELAY_MIN', '0.55')),
    "MESSAGE_DELAY_MAX": float(os.getenv('MESSAGE_DELAY_MAX', '1.5')),
    "NOTIFICATION_GROUP_ID": os.getenv('NOTIFICATION_GROUP_ID'),
}

# Directory for storing conversations
if not os.path.exists(CONFIG["CONVERSATIONS_DIR"]):
    os.makedirs(CONFIG["CONVERSATIONS_DIR"])
    logger.info(f"Created conversations directory at {CONFIG['CONVERSATIONS_DIR']}")

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
            '/clear_history/<user_id>': 'Clear conversation history for a user (POST only)'
        },
        'documentation': 'Send POST requests to /webhook for WhatsApp integration',
        'version': '1.0.0'
    })

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
        
        if not wasender_client:
            logger.error("WaSender API client is not initialized. Cannot process webhook.")
            return jsonify({'status': 'error', 'message': 'WaSender client not initialized'}), 500

        data = request.json
        logger.info(f"Received webhook data: {data}")
        
        if data.get('event') == 'messages.upsert' and data.get('data') and data['data'].get('messages'):
            message_info = data['data']['messages']
            logger.info(f"Processing message info: {message_info}")
            
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
                logger.info(f"Message content object: {msg_content_obj}")
                
                if 'conversation' in msg_content_obj:
                    incoming_message_text = msg_content_obj['conversation']
                    message_type = 'text'
                    logger.info(f"Found conversation text: {incoming_message_text}")
                elif 'extendedTextMessage' in msg_content_obj and 'text' in msg_content_obj['extendedTextMessage']:
                    incoming_message_text = msg_content_obj['extendedTextMessage']['text']
                    message_type = 'text'
                    logger.info(f"Found extended text: {incoming_message_text}")

            if not sender_number:
                logger.warning("Webhook received message without sender information.")
                return jsonify({'status': 'error', 'message': 'Incomplete sender data'}), 400

            safe_sender_id = "".join(c if c.isalnum() else '_' for c in sender_number)
            logger.info(f"Safe sender ID: {safe_sender_id}")
            
            # we should do this in queue in production if we take too long to respond the request will timeout
            if message_type == 'text' and incoming_message_text:
                logger.info(f"Processing text message: '{incoming_message_text}' from {sender_number}")
                
                conversation_history = load_conversation_history(safe_sender_id)
                logger.info(f"Loaded conversation history for {safe_sender_id}")
                
                response_text = None
                should_notify_group = False
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
                        
                        # Check if this option requires notification (options 2-6 need specialist)
                        if option_key in ['2', '3', '4', '6']:
                            should_notify_group = True
                            option_title = MENU_CONFIG.get('menu_options', {}).get(option_key, {}).get('title', f'Opção {option_key}')
                            selected_menu_option = f"{option_key} - {option_title}"
                
                # If no menu response, use Gemini AI
                if not response_text:
                    logger.info(f"Using Gemini AI for response")
                    response_text = get_gemini_response(incoming_message_text, conversation_history)
                    logger.info(f"Gemini reply: {response_text}")
                    
                    # Check if AI response suggests contacting specialist
                    keywords_for_notification = ['jailson', 'josimar', 'consultor', 'especialista', 'atendimento']
                    if any(keyword in response_text.lower() for keyword in keywords_for_notification):
                        should_notify_group = True
                
                if response_text:
                    message_chunks = split_message(response_text)
                    logger.info(f"Sending {len(message_chunks)} message chunks to {sender_number}")
                    for i, chunk in enumerate(message_chunks):
                        logger.info(f"Sending chunk {i+1}/{len(message_chunks)}: {chunk[:50]}...")
                        send_result = send_whatsapp_message(sender_number, chunk, message_type='text')
                        if not send_result:
                            logger.error(f"Failed to send message chunk {i+1} to {sender_number}")
                            break
                        else:
                            logger.info(f"Successfully sent chunk {i+1} to {sender_number}")
                        
                        # Delay between messages
                        import random
                        import time
                        if i < len(message_chunks) - 1:
                            delay = random.uniform(5, 7)
                            logger.info(f"Waiting {delay:.1f} seconds before next chunk...")
                            time.sleep(delay)
                    
                    # Send notification to group if needed
                    if should_notify_group:
                        logger.info(f"Sending notification to group for {sender_number}")
                        send_notification_to_group(
                            sender_number,
                            incoming_message_text,
                            menu_option=selected_menu_option
                        )
                    
                    # Save conversation history
                    conversation_manager.add_exchange(safe_sender_id, incoming_message_text, response_text)
                    logger.info(f"Saved conversation history for {safe_sender_id}")
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
