import os
import random
from flask import Flask, request, jsonify, send_from_directory
from telethon import TelegramClient
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
import csv

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Telegram API credentials - Move these to environment variables
api_id = os.getenv('API_ID', '25805299')  # Default value for development only
api_hash = os.getenv('API_HASH', '77a9f45c0d8e3b5004ff1f689ad91aad')  # Default for development
channel_username = os.getenv('CHANNEL_USERNAME', 'testsub01')

# List of reactions (Telegram emojis)
reactions = ['👍', '❤️', '🔥', '🎉', '👏']

# Load accounts from CSV - consider moving to database or environment variables
# Replace pandas CSV reading with:

def load_accounts():
    accounts = []
    with open('accounts.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            accounts.append(row)
    return accounts
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/upload', methods=['POST'])
async def upload_file():
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save the file
    file_path = os.path.join(UPLOAD_FOLDER, 'betting_card.png')
    file.save(file_path)
    
    # Process the image with Telegram
    try:
        message_id = await process_telegram(file_path)
        return jsonify({'success': True, 'message_id': message_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

async def process_telegram(image_path):
    clients = await authenticate_accounts()
    if not clients:
        raise Exception("No accounts authenticated.")
    
    # Use the first account as the main account to send the image
    main_client = clients[0]
    await main_client.start()
    
    # Send the image using the main account
    message_id = await send_image_to_channel(main_client, image_path)
    if not message_id:
        await main_client.disconnect()
        raise Exception("Failed to send image.")
    
    # Add reactions using all accounts (including the main account)
    for client in clients:
        await client.start()
        await add_reaction(client, message_id)
        await client.disconnect()
    
    return message_id

async def authenticate_accounts():
    clients = []
    for index, account in accounts.iterrows():
        session_file = f"session_{account['phone_number']}"
        client = TelegramClient(session_file, account['api_id'], account['api_hash'])
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(account['phone_number'])
            code = input(f"Enter the code sent to {account['phone_number']}: ")
            await client.sign_in(account['phone_number'], code)
        clients.append(client)
    return clients

async def send_image_to_channel(client, image_path):
    try:
        message = await client.send_file(channel_username, image_path)
        print("Image sent successfully by main account!")
        return message.id
    except Exception as e:
        print(f"Failed to send image: {e}")
        return None

async def add_reaction(client, message_id):
    try:
        reaction = random.choice(reactions)
        await client(SendReactionRequest(
            peer=channel_username,
            msg_id=message_id,
            reaction=[ReactionEmoji(emoticon=reaction)]
        ))
        print(f"Reaction {reaction} added by {client.session.filename}")
    except Exception as e:
        print(f"Failed to add reaction: {e}")

if __name__ == "__main__":
    import asyncio
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
