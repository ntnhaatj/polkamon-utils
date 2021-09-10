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
logging.basicConfig(format='%(asctime)s - {%(filename)s:%(lineno)d} - %(levelname)s - %(message)s',
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
PMON_TOKEN_TOPIC = '0x00000000000000000000000085f0e02cb992aa1f9f47112f815f519ef1a59e2d'
METHOD_TOPIC = web3_utils.web3.sha3(text='EvNewOffer(address,address,uint256,uint256,uint8,uint256)').hex()


def get_filter_event():
    scv_filter_event = web3_utils.web3.eth.filter({
        "address": SCV_CONTRACT, "topics": [METHOD_TOPIC]})
    return scv_filter_event


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
    desc = "{}\n" \
           "SPB {} {}\n" \
           "{}> {:.4f} BNB\n" \
           "Score: {:,}".format(
        meta.name, get_color_by_spb(score_per_bnb), score_per_bnb, side, price / 1E18, score)
    msg = f"<a href='{meta.image}'>.</a>" \
          f"<a href='{url}'>{desc}</a>\n" \
          f"<b>PMONC {meta.id}</b>\n" \
          f"<b>Reason {matched_rule.name}</b>"
    return msg


def on_start_intro() -> str:
    header = "Start earning money mode"
    body = "Tracking configuration:\n- {}".format("\n- ".join(map(lambda r: str(r), rules)))
    return f"{header}\n{body}"


@backoff.on_exception(backoff.constant,
                      interval=1,
                      max_tries=3,
                      exception=(requests.exceptions.RequestException, ))
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
            try:
                while not messages.empty():
                    msg = messages.get_nowait()
                    try:
                        send_msg(msg, parse_mode='html')
                    except Exception as e:
                        logger.error(f"failed to send {msg}: {e}")
                        pass
                time.sleep(0.1)
            except KeyboardInterrupt as e:
                raise KeyboardInterrupt from e


class FilterNotFoundError(Exception):
    """ new entry filter not found """
    pass


def new_event_handler(evt):
    logger.debug(f"processing {evt}")
    token_topic = evt['topics'][2].hex()
    if token_topic == PMON_TOKEN_TOPIC:
        token_id = int.from_bytes(evt['topics'][3], 'big')
        data = evt['data'].replace('0x', '')
        price_hexstr, side_hexstr, _ = [data[i:i + 64] for i in range(0, len(data), 64)]
        side = TradeSide.of(int(f"0x{side_hexstr}", 16))
        price = int(f"0x{price_hexstr}", 16)
        tx = evt['transactionHash'].hex()
        logger.info("new event %s %d with price %.2f, tx %s", side, token_id, price, tx)
        return side, token_id, price


def get_sell_event(evt_filter):
    try:
        new_entries = evt_filter.get_new_entries()
    except Exception as e:
        logger.exception(str(e))
        raise FilterNotFoundError from e
    # to avoid duplicated event emit
    pre_token_id = None
    for e in new_entries:
        side, token_id, price = new_event_handler(e)
        if side == TradeSide.SELL and token_id != pre_token_id:
            pre_token_id = token_id
            yield side, token_id, price


def main():
    messages.put_nowait(on_start_intro())
    scv_filter_event = get_filter_event()
    while True:
        try:
            time.sleep(1)
            for side, token_id, price in get_sell_event(scv_filter_event):
                meta = Metadata.from_metadata(get_metadata(str(token_id)))
                matched_rule = get_matched_rule(price, meta, rules)
                if matched_rule:
                    try:
                        messages.put_nowait(to_html(side, meta, price, meta.rarity_score, matched_rule))
                    except Exception as e:
                        logging.exception(str(e))

        except FilterNotFoundError as e:
            logger.error(f"cannot get new entries: {e}")
            logger.info("reconnecting")
            scv_filter_event = get_filter_event()
            continue

        except KeyboardInterrupt as e:
            # messages.put_nowait(f"BOT IS SHUTTING DOWN...\nReason: {e}")
            raise KeyboardInterrupt from e

        except Exception as e:
            logger.exception(str(e))
            continue


if __name__ == '__main__':
    telegram_thread = Notifier("telegram")
    telegram_thread.start()
    time.sleep(1)
    try:
        main()
    except KeyboardInterrupt as exc:
        logging.exception(str(exc))
        logging.info("graceful shutdown")
