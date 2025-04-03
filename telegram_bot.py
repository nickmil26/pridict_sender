import os
from flask import Flask, request, jsonify, send_from_directory
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Telegram credentials - set these in Render
API_ID = int(os.getenv('API_ID', 12345))          # Required
API_HASH = os.getenv('API_HASH', 'your_api_hash') # Required
BOT_TOKEN = os.getenv('BOT_TOKEN')                # Required
CHANNEL = os.getenv('CHANNEL_USERNAME')           # Required

# Initialize bot connection
try:
    bot = TelegramClient(StringSession(), API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    print("✅ Bot connected successfully")
except Exception as e:
    print(f"❌ Bot connection failed: {e}")
    bot = None

@app.route('/')
def home():
    """Serve the HTML interface"""
    return send_from_directory('static', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """Handle image upload to Telegram"""
    # Check if bot is connected
    if not bot or not bot.is_connected():
        return jsonify(success=False, error="Bot not connected"), 500

    # Validate file upload
    if 'image' not in request.files:
        return jsonify(success=False, error="No file uploaded"), 400
    
    file = request.files['image']
    if not file or file.filename == '':
        return jsonify(success=False, error="Invalid file"), 400

    # Process file upload
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    try:
        file.save(file_path)
        
        # Send to Telegram
        message = bot.send_file(
            entity=CHANNEL,
            file=file_path,
            caption="New Betting Card"
        )
        
        return jsonify(
            success=True,
            message="Image sent successfully",
            message_id=message.id
        )
        
    except Exception as e:
        # Ensure proper JSON error response
        return jsonify(success=False, error=f"Telegram error: {str(e)}"), 500
        
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
