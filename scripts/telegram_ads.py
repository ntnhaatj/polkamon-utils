import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import time


# get your api_id, api_hash, token
# from telegram as described above
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
phone = '+84356626707'
username = 'ntnhaatj'

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)
client.start()
print("Client Created")
# Ensure you're authorized
if not client.is_user_authorized():
    client.send_code_request(phone)
    try:
        client.sign_in(phone, input('Enter the code: '))
    except SessionPasswordNeededError:
        client.sign_in(password=input('Password: '))


SELLING_LIST = (
    ('glitter turtle, accept reasonable offer',
     'https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/10001290268'),

    ('🔥 20k staking score, accept reasonable offer',
     'https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/10001256850'),

    ('glitter baby chick, accept reasonable offer',
     'https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/10000419976'),

    ('cheap glitter fairy',
     'https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/10001464289'),

    ('black turtle, accept reasonable offer',
     'https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/10001381330')
)

while True:
    for sell in SELLING_LIST:
        msg = '\n'.join(sell)
        with client:
            client.loop.run_until_complete(client.send_message(entity='PolkamonTrading', message=msg))
        time.sleep(600)
