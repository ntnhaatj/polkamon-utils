from typing import Iterable
import os
import logging
import time
import requests
import backoff
from datetime import datetime
import web3_utils
from enum import Enum
from utils import get_metadata
from datatypes import Metadata
from scvfeed.models import Rule
from scvfeed.config import rules
import threading
import queue

# Enable logging
log_filename = datetime.now().strftime('log/scvfeed_%Y%m%d.log')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename=log_filename,
                    filemode='a+')
logger = logging.getLogger(__name__)

TELEGRAM_CHAT_ID = {
    'scvfeed': -1001597613597,
    'hihifeed': -1001532402384,
}
SCV_CONTRACT = '0x9437E3E2337a78D324c581A4bFD9fe22a1aDBf04'

# notification pool
messages = queue.Queue()

# get your api_id, api_hash, token
# from telegram as described above
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')


class TradeSide(Enum):
    SELL = 1
    BUY = 2

    @classmethod
    def of(cls, side: int):
        return cls.SELL if side == cls.SELL.value else cls.BUY

    def __str__(self):
        return 'SELL' if self == TradeSide.SELL else 'BUY'


# EvNewOffer (
#   index_topic_1 address user,
#   index_topic_2 address nft,
#   index_topic_3 uint256 tokenId,
#   uint256 price,
#   uint8 side,
#   uint256 id
# )
MethodTopic = web3_utils.web3.sha3(text='EvNewOffer(address,address,uint256,uint256,uint8,uint256)').hex()
PmonTokenTopic = '0x00000000000000000000000085f0e02cb992aa1f9f47112f815f519ef1a59e2d'

scv_filter_event = web3_utils.web3.eth.filter({"address": SCV_CONTRACT, "topics": [MethodTopic]})


def pmon_contract(e) -> bool:
    return e['topics'][2].hex() == PmonTokenTopic


def new_event_handler(e):
    try:
        token_id = int.from_bytes(e['topics'][3], 'big')
        data = e['data'].replace('0x', '')
        price_hexstr, side_hexstr, _ = [data[i:i + 64] for i in range(0, len(data), 64)]
        price = int(f"0x{price_hexstr}", 16)
        side = TradeSide.of(int(f"0x{side_hexstr}", 16))
        tx = e['transactionHash'].hex()
        logger.info("new event %s %d with price %.2f, tx %s", side, token_id, price, tx)
        return side, token_id, price
    except Exception as exc:
        logger.error("invalid entry %s \n%s", e, str(exc))
        return None


def get_matched_rule(price: int, metadata: Metadata, rul3s: Iterable[Rule]) -> Rule:
    price_in_bnb = price / 1E18

    for rule in rul3s:
        try:
            if rule.is_worth_buying(price_in_bnb, metadata):
                logger.info(f"worth buying monster {rule}")
                return rule
        except Exception as e:
            logger.error(f"encountered exception {rule}\n{e}")
            pass
    return None


def get_color_by_spb(spb: int) -> str:
    if spb < 5000:
        return "🟢"
    elif spb < 8000:
        return "🔵"
    elif spb < 11000:
        return "🟡"
    else:
        return "🟣"


# https://core.telegram.org/bots/api#html-style
def to_html(side, meta, price, score, matched_rule: Rule):
    score_per_bnb = int(score / price * 1E18)
    url = f"https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/{meta.id}"
    desc = "===={}====\n" \
           "{}> {:.4f} BNB | score: {:,}".format(matched_rule.name, side, price / 1E18, score)
    msg = f"<a href='{meta.image}'>.</a>" \
          f"<a href='{url}'>{desc}</a>\n" \
          f"<b>SBP {get_color_by_spb(score_per_bnb)} {score_per_bnb}</b>\n" \
          f"<b>PMONC {meta.id}</b>"
    return msg


def on_start_intro() -> str:
    header = "Start earning money mode"
    body = "Tracking configuration:\n- {}".format("\n- ".join(map(lambda r: str(r), rules)))
    return f"{header}\n{body}"


@backoff.on_exception(backoff.constant,
                      interval=1,
                      max_tries=3,
                      exception=(requests.exceptions.RequestException, requests.exceptions.ConnectionError))
def send_msg(msg, parse_mode=''):
    params = (
        f'chat_id={TELEGRAM_CHAT_ID[os.getenv("TID", "scvfeed")]}',
        f'text={msg}',
        f'parse_mode={parse_mode}'
    )
    requests.get("https://api.telegram.org/bot{}/sendMessage?{}".format(bot_token, '&'.join(params)))


class Notifier(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self) -> None:
        while True:
            while not messages.empty():
                msg = messages.get_nowait()
                try:
                    send_msg(msg, parse_mode='html')
                except Exception as e:
                    logger.error(f"failed to send {msg}: {e}")
                    pass
            time.sleep(0.1)


def handle_new_entries(evt_filter):
    for entry in evt_filter.get_new_entries():
        if not pmon_contract(entry):
            continue
        side, token_id, price = new_event_handler(entry)
        if side == TradeSide.SELL:
            try:
                metadata = get_metadata(token_id)
                meta = Metadata.from_metadata(metadata)
                matched_rule = get_matched_rule(price, meta, rules)
                if matched_rule:
                    yield side, meta, price, matched_rule
            except Exception as e:
                logger.error(f"could not parse metadata {token_id}: {e}")
                continue


def main():
    messages.put_nowait(on_start_intro())
    while True:
        try:
            for side, meta, price, matched_rule in handle_new_entries(scv_filter_event):
                try:
                    messages.put_nowait(to_html(side, meta, price, meta.rarity_score, matched_rule))
                except Exception as e:
                    logging.error(e)
            time.sleep(0.4)

        except KeyboardInterrupt as e:
            messages.put_nowait(f"BOT IS SHUTTING DOWN...\nReason: {e}")
            raise KeyboardInterrupt from e

        except Exception as e:
            logger.error(str(e))
            continue


if __name__ == '__main__':
    telegram_thread = Notifier("telegram")
    telegram_thread.start()
    time.sleep(0.5)
    try:
        main()
    except KeyboardInterrupt as exc:
        logging.error(exc)
        logging.info("graceful shutdown")
    telegram_thread.join()
