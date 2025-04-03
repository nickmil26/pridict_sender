import os
from flask import Flask, request, jsonify, send_from_directory
from telethon.sync import TelegramClient

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Bot setup
BOT_TOKEN = os.getenv('BOT_TOKEN')  # From @BotFather
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'testsub01')

# Initialize bot
bot = TelegramClient('bot', 0, 0).start(bot_token=BOT_TOKEN)

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
        file_path = os.path.join(UPLOAD_FOLDER, 'betting_card.png')
        file.save(file_path)
        
        # Send to Telegram
        message = bot.send_file(CHANNEL_USERNAME, file_path)
        
        # Clean up
        os.remove(file_path)
        
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

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
