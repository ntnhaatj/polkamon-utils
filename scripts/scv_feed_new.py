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
log_filename = datetime.now().strftime('log/scvfeed_%Y%m%d_%H%M.log')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename=log_filename,
                    filemode='a')
logger = logging.getLogger(__name__)

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


# https://core.telegram.org/bots/api#html-style
def to_html(side, token_id, price, score, matched_rule: Rule):
    url = f"https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/{token_id}"
    body = "{} {:.4f} BNB | score: {:,} | SPB: {:,}".format(side, price / 1E18, score, int(score / price * 1E18))
    delimiter = f"===={matched_rule.name}====\n"
    msg = f"{delimiter}<a href='{url}'>{body}</a>\n"
    return msg


def on_start_intro() -> str:
    header = "Starting SCV feed bot tracking"
    body = "Tracking Configuration:\n- {}".format("\n- ".join(map(lambda r: str(r), rules)))
    return f"{header}\n{body}"


def main():
    bot = TelegramClient('session', api_id, api_hash).start(bot_token=bot_token)
    bot.loop.run_until_complete(bot.send_message("scvfeed", on_start_intro()))
    with bot:
        while True:
            try:
                for e in scv_filter_event.get_new_entries():
                    if not pmon_contract(e):
                        continue
                    side, token_id, price = new_event_handler(e)
                    if side == TradeSide.SELL:
                        metadata = get_metadata(token_id)
                        meta = Metadata.from_metadata(metadata)
                        matched_rule = get_matched_rule(price, meta, rules)
                        if matched_rule:
                            try:
                                message = to_html(side, token_id, price, meta.rarity_score, matched_rule)
                                bot.loop.run_until_complete(bot.send_message("scvfeed", message, parse_mode='html'))
                            except Exception as e:
                                logging.error(e)
                time.sleep(0.2)
            except (ValueError, KeyError):
                pass
            except (KeyboardInterrupt, Exception) as e:
                bot.loop.run_until_complete(bot.send_message("scvfeed", f"BOT IS SHUTTING DOWN...\nReason: {e}"))
                bot.disconnect()
                logging.error(e)
                logging.info("graceful shutdown")
                break


if __name__ == '__main__':
    main()
