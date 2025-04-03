import os
from flask import Flask, request, jsonify, send_from_directory
from telethon.sync import TelegramClient  # Note: using sync version

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Telegram credentials
API_ID = int(os.getenv('API_ID'))  # Required from my.telegram.org
API_HASH = os.getenv('API_HASH')   # Required from my.telegram.org
BOT_TOKEN = os.getenv('BOT_TOKEN') # From @BotFather
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'testsub01')

# Initialize bot client (synchronous)
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
    
    try:
        # Save file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        
        # Synchronous file sending
        message = bot.send_file(CHANNEL_USERNAME, file_path)
        
        # Clean up
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': 'Image sent successfully',
            'message_id': message.id
        })
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
