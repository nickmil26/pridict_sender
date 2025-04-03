import os
from flask import Flask, request, jsonify, send_from_directory
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Initialize Flask app
app = Flask(__name__)

# ======================
# CONFIGURATION
# ======================
UPLOAD_FOLDER = 'temp_uploads'  # Temporary folder for uploads
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Get environment variables (set these in Render dashboard)
API_ID = int(os.getenv('API_ID'))         # From my.telegram.org (required)
API_HASH = os.getenv('API_HASH')          # From my.telegram.org (required)
BOT_TOKEN = os.getenv('BOT_TOKEN')        # From @BotFather (format: "123456:abc123")
CHANNEL = os.getenv('CHANNEL_USERNAME')   # Your channel username (without @)

# ======================
# TELEGRAM BOT SETUP
# ======================
try:
    # Initialize bot (using in-memory session)
    bot = TelegramClient(StringSession(), API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    print("✅ Bot connected successfully")
except Exception as e:
    print(f"❌ Failed to connect bot: {e}")
    # Exit if bot can't connect (Render will restart)
    raise SystemExit(1)

# ======================
# FLASK ROUTES
# ======================
@app.route('/')
def home():
    """Serve the HTML interface"""
    return send_from_directory('static', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Handle image upload and send to Telegram channel
    Returns JSON response with success/error message
    """
    # Check if file was uploaded
    if 'image' not in request.files:
        return jsonify(success=False, error="No file uploaded"), 400
    
    file = request.files['image']
    if not file or file.filename == '':
        return jsonify(success=False, error="No selected file"), 400

    # Save file temporarily
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    try:
        file.save(file_path)
        
        # Send to Telegram (synchronous operation)
        message = bot.send_file(
            entity=CHANNEL,
            file=file_path,
            caption="New Betting Card"
        )
        
        return jsonify(
            success=True,
            message="Image sent to Telegram",
            message_id=message.id
        )
        
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500
        
    finally:
        # Always clean up the temp file
        if os.path.exists(file_path):
            os.remove(file_path)

# ======================
# START APPLICATION
# ======================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
