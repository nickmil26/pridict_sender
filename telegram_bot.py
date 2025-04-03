import os
from flask import Flask, request, jsonify, send_from_directory
from telethon.sync import TelegramClient
from telethon.sessions import StringSession  # For in-memory session

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Telegram credentials - ALL required
API_ID = int(os.getenv('API_ID'))        # From my.telegram.org (required)
API_HASH = os.getenv('API_HASH')         # From my.telegram.org (required)
BOT_TOKEN = os.getenv('BOT_TOKEN')       # From @BotFather (required)
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'testsub01')

# Initialize bot client ONCE at startup
bot = None
try:
    bot = TelegramClient(StringSession(), API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    print("✅ Bot initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize bot: {e}")
    raise

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if not bot:
        return jsonify({'success': False, 'error': 'Bot not initialized'}), 500
        
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    try:
        # Save file
        file.save(file_path)
        
        # SYNC operation - no async/await
        message = bot.send_file(
            entity=CHANNEL_USERNAME,
            file=file_path,
            caption="New betting card"
        )
        
        return jsonify({
            'success': True,
            'message': 'Image sent successfully',
            'message_id': message.id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
