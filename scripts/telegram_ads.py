import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import time
import yaml


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


def get_ads_from_conf(path: str):
    with open(path, 'r') as file:
        return yaml.safe_load(file)['ads']


while True:
    for ad in get_ads_from_conf('conf/ads.yml'):
        msg = '\n'.join(ad.values())
        print("======== send ads ===========")
        print(f"send message: {msg}")
        with client:
            client.loop.run_until_complete(client.send_message(entity='PolkamonTrading', message=msg))
        time.sleep(600)
