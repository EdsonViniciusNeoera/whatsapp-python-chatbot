# Affordable WhatsApp AI Chatbot Built in Python: Just $6/month

Create a powerful WhatsApp chatbot powered by Google's Gemini AI for just $6/month (WaSenderAPI subscription) plus Google's free Gemini API tier (1500 requests/month). This Python-based solution uses Flask to handle incoming messages via WaSenderAPI webhooks and leverages Gemini's advanced AI capabilities to generate intelligent, conversational responses.

## 💰 Cost-Effective Solution

- **WaSenderAPI**: Only $6/month for WhatsApp integration
- **Gemini AI**: Free tier with 1500 requests/month
- **Hosting**: Run locally or on low-cost cloud options
- **No WhatsApp Business API fees**: Uses WaSenderAPI as an affordable alternative

## 🔥 Key Features

- **WhatsApp Integration**: Receives and sends messages through WaSenderAPI
- **AI-Powered Responses**: Generates intelligent replies using Google's Gemini AI
- **Media Support**: Handles text, images, audio, video, and document messages
- **Smart Message Splitting**: Automatically breaks long responses into multiple messages for better readability
- **Customizable AI Persona**: Tailor the bot's personality and behavior via simple JSON configuration
- **Conversation History**: Maintains context between messages for natural conversations
- **Error Handling**: Robust logging and error management for reliable operation
- **Easy Configuration**: Simple setup with environment variables

## 📁 Project Structure

```
/whatsapp-python-chatbot/
├── script.py         # Main Flask application and bot logic
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (API keys, etc.)
├── persona.json      # Customizable AI personality settings
└── README.md         # This file
```

## 🚀 Setup and Installation

1.  **Clone the repository (if applicable) or create the files as described.**

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**

    ```bash
    pip3 install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the project root directory by copying the example below. **Do not commit your `.env` file to version control if it contains sensitive keys.**

    ```env
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"  # Free tier: 1500 requests/month
    WASENDER_API_TOKEN="YOUR_WASENDER_API_TOKEN_HERE"  # $6/month subscription
    # Optional: If you change the port in script.py, update it here too for ngrok or other services
    # FLASK_RUN_PORT=5000
    ```

    Replace the placeholder values with your actual API keys:

    - `GEMINI_API_KEY`: Your API key for the Gemini API (free tier available)
    - `WASENDER_API_TOKEN`: Your API token from WaSenderAPI ($6/month subscription)

## 🏃‍♂️ Running the Application

### 1. Development Mode (using Flask's built-in server)

This is suitable for local development and testing.

```bash
python3 script.py
```

The application will typically run on `http://0.0.0.0:5001/` by default.

### 2. Using ngrok for Webhook Testing

WaSenderAPI needs to send webhook events (incoming messages) to a publicly accessible URL. If you're running the Flask app locally, `ngrok` can expose your local server to the internet.

a. **Install ngrok** (if you haven't already) from [https://ngrok.com/](https://ngrok.com/).

b. **Start ngrok** to forward to your Flask app's port (e.g., 5001):

```bash
ngrok http 5001
```

c. **ngrok will provide you with a public URL** (e.g., `https://xxxx-xx-xxx-xxx-xx.ngrok-free.app`).

d. **Configure this ngrok URL as your webhook URL** in the WaSenderAPI dashboard for your connected device/session. Make sure to append the `/webhook` path (e.g., `https://xxxx-xx-xxx-xxx-xx.ngrok-free.app/webhook`).

### 3. Production Deployment (using Gunicorn)

For production, it's recommended to use a proper WSGI server like Gunicorn instead of Flask's built-in development server.

a. **Install Gunicorn:**

```bash
pip3 install gunicorn
```

b. **Run the application with Gunicorn:**
Replace `script:app` with `your_filename:your_flask_app_instance_name` if you change them.

```bash
gunicorn --workers 4 --bind 0.0.0.0:5001 script:app
```

- `--workers 4`: Adjust the number of worker processes based on your server's CPU cores (a common starting point is `2 * num_cores + 1`).
- `--bind 0.0.0.0:5001`: Specifies the address and port Gunicorn should listen on.

c. **Reverse Proxy (Recommended):**
In a typical production setup, you would run Gunicorn behind a reverse proxy like Nginx or Apache. The reverse proxy would handle incoming HTTPS requests, SSL termination, static file serving (if any), and forward requests to Gunicorn.

## 🔄 WaSenderAPI Webhook Configuration

- Log in to your WaSenderAPI dashboard.
- Navigate to the session management section.
- connect you phone number to the session.
- Find the option to set or update the webhook URL.
- Enter the publicly accessible URL where your Flask application's `/webhook` endpoint is running (e.g., your ngrok URL during development, or your production server's URL).
- make sure you only select only **message_upsert**.
- seve the changes.

## 📝 Customizing Your Bot's Personality

The chatbot includes a customizable base prompt that defines the AI's persona and behavior. Edit the `persona.json` file to change how Gemini responds to messages, making the bot more formal, casual, informative, or conversational as needed for your use case.

```json
{
  "name": "WhatsApp Assistant",
  "base_prompt": "You are a helpful and concise AI assistant replying in a WhatsApp chat...",
  "description": "You are a helpful WhatsApp assistant. Keep your responses concise..."
}
```

## 🎓 Training Your Bot with Few-Shot Learning

**NEW!** This chatbot now supports **Few-Shot Learning**, allowing the AI to learn from examples of how you want it to respond.

### How It Works

The bot automatically loads conversation examples from `persona.json` and uses them to understand:
- The style and tone of responses
- How to handle specific types of questions
- When to escalate to human agents
- The format and structure of ideal answers

### Adding Training Examples

Simply add examples to the `responses` array in `persona.json`:

```json
{
  "responses": [
    {
      "input": "What are your hours?",
      "output": "We're open Monday-Friday 9am-6pm, and Saturday 9am-12pm. We're closed on Sundays 😊"
    },
    {
      "input": "Do you deliver?",
      "output": "Unfortunately no! Most clients pick up in-store for potential adjustments. For alternatives like bike courier, please consult our specialists."
    }
  ]
}
```

### Quick Start Guide

1. **Add examples**: Edit `persona.json` → add to `responses` array
2. **Restart bot**: The new examples are loaded automatically
3. **Test**: Send similar messages to see improved responses

For detailed training instructions, see:
- 📖 **[GUIA_TREINAMENTO.md](GUIA_TREINAMENTO.md)** - Quick training guide (Portuguese)
- 📚 **[FEW_SHOT_LEARNING.md](FEW_SHOT_LEARNING.md)** - Technical documentation

### Testing Your Training

Run the test script to validate your examples:

```bash
python test_few_shot.py
```

This will verify:
- ✅ Examples are loading correctly
- ✅ Format is compatible with Gemini API
- ✅ Few-shot learning is active

### Benefits

- ✓ **More consistent responses** - Bot learns from your examples
- ✓ **Easy to update** - Just edit JSON, no coding required
- ✓ **Immediate effect** - Restart bot and changes apply
- ✓ **No retraining needed** - Uses Gemini's in-context learning

---

## 📱 Interactive Menu System

**NEW!** The bot now includes an **Interactive Menu** that presents pre-defined options when users start a conversation.

### Features

- 🎯 **Auto-detection** - Recognizes greetings like "hi", "hello", "menu"
- 📋 **7 Pre-defined Options** - Organized menu with common queries
- ⚡ **Instant Responses** - No AI delay for menu selections
- 🔄 **Hybrid Mode** - Menu for simple queries, AI for complex ones
- 🎨 **Customizable** - Easy to modify in `persona.json`

### How It Works

```
User: "Hi"
Bot: [Shows menu with 7 options]

User: "1" 
Bot: [Instant response with address and hours]

User: "Can you work with progressive lenses?"
Bot: [AI generates contextual response]
```

### Menu Configuration

Enable/disable in `persona.json`:

```json
{
  "menu_enabled": true,
  "welcome_message": "Hello! Choose an option:\n1️⃣ Address\n2️⃣ Schedule...",
  "menu_options": {
    "1": {
      "title": "Address and hours",
      "response": "We're located at..."
    }
  },
  "greeting_keywords": ["hi", "hello", "menu", "options"]
}
```

### Testing the Menu

```bash
python test_menu_interativo.py
```

For complete documentation:
- 📱 **[MENU_INTERATIVO.md](MENU_INTERATIVO.md)** - Complete menu guide (Portuguese)

### Benefits

- ✓ **Faster responses** - No API calls for common questions
- ✓ **100% accurate** - Pre-defined responses, no errors
- ✓ **Better UX** - Clear options for users
- ✓ **Cost effective** - Reduces API usage
- ✓ **Easy to maintain** - Update responses in JSON

## 📊 Logging and Error Handling

- The application uses Python's built-in `logging` module.
- Logs are printed to the console by default.
- Log format: `%(asctime)s - %(levelname)s - %(message)s`.
- Unhandled exceptions are also logged.
- **Important for Production:** Consider configuring logging to write to files, use a centralized logging service (e.g., ELK stack, Sentry, Datadog), and implement log rotation.

## 📚 WaSenderAPI Documentation

Refer to the official WaSenderAPI documentation for the most up-to-date information on API endpoints, request/response formats, and webhook details: [https://wasenderapi.com/api-docs](https://wasenderapi.com/api-docs)

## 💡 Why This Solution?

This chatbot offers an incredibly cost-effective way to deploy an AI-powered WhatsApp bot without the high costs typically associated with WhatsApp Business API. By combining WaSenderAPI's affordable $6/month subscription with Google's free Gemini API tier, you get a powerful, customizable chatbot solution at a fraction of the cost of enterprise alternatives.
