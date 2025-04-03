import os
from flask import Flask, request, jsonify, send_from_directory
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Get environment variables
def get_env(var_name, default=None, required=True):
    value = os.getenv(var_name, default)
    if required and not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value

try:
    API_ID = int(get_env('API_ID'))
    API_HASH = get_env('API_HASH')
    BOT_TOKEN = get_env('BOT_TOKEN')
    CHANNEL = get_env('CHANNEL_USERNAME')
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    raise

# Initialize Telegram client
try:
    bot = TelegramClient(StringSession(), API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    print("✅ Bot connected successfully")
except Exception as e:
    print(f"❌ Failed to initialize bot: {e}")
    bot = None

@app.route('/')
def serve_frontend():
    """Serve the static HTML frontend"""
    return send_from_directory('static', 'index.html')

@app.route('/upload', methods=['POST'])
def handle_upload():
    """Process image upload to Telegram"""
    if not bot or not bot.is_connected():
        return json_response(False, "Bot not connected", 500)

    if 'image' not in request.files:
        return json_response(False, "No file uploaded", 400)

    file = request.files['image']
    if not file or file.filename == '':
        return json_response(False, "Invalid file", 400)

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    try:
        file.save(file_path)
        message = bot.send_file(CHANNEL, file_path)
        return json_response(True, "Image sent successfully", data={'message_id': message.id})
    except Exception as e:
        return json_response(False, f"Upload failed: {str(e)}", 500)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def json_response(success, message, status=200, data=None):
    """Standardized JSON response format"""
    response = {
        'success': success,
        'message': message,
        'data': data or {}
    }
    return jsonify(response), status

if __name__ == "__main__":
    port = int(get_env('PORT', '5000'))
    app.run(host='0.0.0.0', port=port)
