import os
import random
import asyncio
import csv
from flask import Flask, request, jsonify, send_from_directory
from telethon import TelegramClient
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize accounts list
accounts = []
try:
    with open('accounts.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Reorder to match expected format: phone_number, api_id, api_hash
            accounts.append({
                'phone_number': row['phone_number'],
                'api_id': row['api_id'],
                'api_hash': row['api_hash']
            })
    print(f"Loaded {len(accounts)} accounts")
except Exception as e:
    print(f"Error loading accounts.csv: {e}")

# Telegram configuration
reactions = ['👍', '❤️', '🔥', '🎉', '👏']

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
        file_path = os.path.join(UPLOAD_FOLDER, 'betting_card.png')
        file.save(file_path)
        
        message_id = asyncio.run(process_telegram(file_path))
        return jsonify({
            'success': True,
            'message': 'Image sent successfully',
            'message_id': message_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

async def process_telegram(image_path):
    clients = await authenticate_accounts()
    if len(clients) == 0:
        raise Exception("No accounts authenticated")
    
    main_client = clients[0]
    await main_client.start()
    
    try:
        channel_username = os.getenv('CHANNEL_USERNAME', 'testsub01')
        message = await main_client.send_file(channel_username, image_path)
        if not message:
            raise Exception("Failed to send image")
        
        for client in clients:
            await client.start()
            reaction = random.choice(reactions)
            await client(SendReactionRequest(
                peer=channel_username,
                msg_id=message.id,
                reaction=[ReactionEmoji(emoticon=reaction)]
            ))
    finally:
        for client in clients:
            await client.disconnect()
    
    return message.id

async def authenticate_accounts():
    clients = []
    for account in accounts:
        try:
            session_file = f"session_{account['phone_number']}"
            client = TelegramClient(
                session_file,
                int(account['api_id']),
                account['api_hash']
            )
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.send_code_request(account['phone_number'])
                print(f"Verification code sent to {account['phone_number']}")
                # For production, you'll need to:
                # 1. Check logs for the verification code
                # 2. Manually enter via Render's console
                code = input("Enter verification code: ")
                await client.sign_in(account['phone_number'], code)
                
            clients.append(client)
        except Exception as e:
            print(f"Failed to authenticate {account['phone_number']}: {e}")
    return clients

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
