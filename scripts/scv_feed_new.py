from typing import Iterable
import os
import logging
import time
from dataclasses import dataclass
from datetime import datetime
import web3_utils
from enum import Enum
from telethon import TelegramClient
from utils import get_metadata
from datatypes import Metadata, Horn, Color, Type
from scvfeed.models import Rule
from scvfeed.config import rules

# Enable logging
log_filename = datetime.now().strftime('log/scvfeed_%Y%m%d.log')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename=log_filename,
                    filemode='a+')
logger = logging.getLogger(__name__)

TELEGRAM_CHAT_ID = -1001597613597
SCV_CONTRACT = '0x9437E3E2337a78D324c581A4bFD9fe22a1aDBf04'

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
                return rule
        except Exception as e:
            logger.error(f"encountered exception {rule}\n{e}")
            pass
    return None


def get_color_by_spb(spb: int) -> str:
    if spb < 4000:
        return "🟢"
    elif spb < 7000:
        return "🔵"
    elif spb < 10000:
        return "🟡"
    else:
        return "🟣"


# https://core.telegram.org/bots/api#html-style
def to_html(side, token_id, price, score, matched_rule: Rule):
    score_per_bnb = int(score / price * 1E18)
    url = f"https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/{token_id}"
    desc = "{} {:.4f} BNB | score: {:,}".format(side, price / 1E18, score)
    delimiter = f"===={matched_rule.name}====\n"
    spb_msg = "SPB: {} {:,}".format(get_color_by_spb(score_per_bnb), score_per_bnb)
    msg = f"{delimiter}<a href='{url}'>{desc}</a>\n{spb_msg}"
    return msg


def on_start_intro() -> str:
    header = "Start earning money mode"
    body = "Tracking configuration:\n- {}".format("\n- ".join(map(lambda r: str(r), rules)))
    return f"{header}\n{body}"


def send_msg(tele_bot, msg, parse_mode=None):
    tele_bot.loop.run_until_complete(tele_bot.send_message(TELEGRAM_CHAT_ID, msg, parse_mode=parse_mode))


def handle_new_entries(evt_filter):
    for e in evt_filter.get_new_entries():
        if not pmon_contract(e):
            continue
        side, token_id, price = new_event_handler(e)
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
    bot = TelegramClient('session', api_id, api_hash).start(bot_token=bot_token)
    send_msg(bot, on_start_intro())
    while bot.is_connected():
        try:
            for side, meta, price, matched_rule in handle_new_entries(scv_filter_event):
                logger.info(f"{meta.id} matched rule {matched_rule}")
                try:
                    send_msg(bot,
                             to_html(side, meta.id, price, meta.rarity_score, matched_rule),
                             parse_mode='html')
                except Exception as e:
                    logging.error(e)
            time.sleep(0.2)

        except ValueError:
            pass

        except KeyboardInterrupt as e:
            send_msg(bot, f"BOT IS SHUTTING DOWN...\nReason: {e}")
            bot.disconnect()
            raise KeyboardInterrupt from e

        except Exception:
            continue


if __name__ == '__main__':
    while True:
        try:
            main()
        except KeyboardInterrupt as e:
            logging.error(e)
            logging.info("graceful shutdown")
            break
