import os
import logging
import time
from datetime import datetime
import web3_utils
from enum import Enum
from telethon import TelegramClient
from utils import get_metadata
from datatypes import Metadata, Horn, Color, Type

# Enable logging
log_filename = datetime.now().strftime('scvfeed_%Y%m%d_%H%M.log')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='scv_feed..log',
                    filemode='w')
logger = logging.getLogger(__name__)

SCV_CONTRACT = '0x9437E3E2337a78D324c581A4bFD9fe22a1aDBf04'

# get your api_id, api_hash, token
# from telegram as described above
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
MIN_SCORE = 100
MIN_SCORE_PER_BNB = 2500


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


class WorthToBuyReasonCode(Enum):
    NO = ""
    HIGH_SCORE_PER_BNB = f"Greater {MIN_SCORE_PER_BNB} SPB"
    SPECIAL = "Special"
    BLACK = "Black"
    RARE_ATTR_RARE_TYPES = "Diamond/Glitter Rare Types"

    def __str__(self):
        return self.value

    def __bool__(self):
        return True if self.value else False


def is_worth_buying(price: int, metadata: Metadata) -> WorthToBuyReasonCode:
    score = metadata.rarity_score
    score_per_price = score / price * 1E18

    # high rate score per bnb
    if score > MIN_SCORE:
        if score_per_price > MIN_SCORE_PER_BNB:
            return WorthToBuyReasonCode.HIGH_SCORE_PER_BNB

    # check all specials
    if metadata.attributes.special:
        return WorthToBuyReasonCode.SPECIAL

    # check all blacks
    color = Color.of(metadata.attributes.color)
    if color == Color.BLACK:
        return WorthToBuyReasonCode.BLACK

    try:
        horn = Horn.of(metadata.attributes.horn)
        typ3 = Type.of(metadata.attributes.type)
    except NotImplementedError:
        return WorthToBuyReasonCode.NO
    # check all diamonds or glitter with rare types
    rare_types = (Type.AIR, Type.AQUA, Type.BRANCH, Type.KLES, Type.TURTLE, Type.DRAGON)
    if typ3 in rare_types and (horn == Horn.DIAMOND_SPEAR
                               or metadata.attributes.glitter == "Yes"):
        return WorthToBuyReasonCode.RARE_ATTR_RARE_TYPES

    return WorthToBuyReasonCode.NO


# https://core.telegram.org/bots/api#html-style
def to_html(side, token_id, price, score, wtb: WorthToBuyReasonCode):
    url = f"https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/{token_id}"
    body = "{} {:.4f} BNB | score: {:,}".format(side, price / 1E18, score)
    delimiter = f"===={wtb}====\n"
    msg = f"{delimiter}<a href='{url}'>{body}</a>\n"
    return msg


def on_start_intro() -> str:
    header = "Starting SCV feed bot tracking"
    conf = [f"  - {track}" for track in WorthToBuyReasonCode.__members__.values() if track]
    return "{}\nTracking Configuration:\n{}".format(header, '\n'.join(conf))


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
                        wtb = is_worth_buying(price, meta)
                        if wtb:
                            try:
                                message = to_html(side, token_id, price, meta.rarity_score, wtb)
                                bot.loop.run_until_complete(bot.send_message("scvfeed", message, parse_mode='html'))
                            except Exception as e:
                                logging.error(e)
                time.sleep(2)
            except (ValueError, KeyError):
                pass
            except (KeyboardInterrupt, Exception):
                bot.loop.run_until_complete(bot.send_message("scvfeed", "BOT IS SHUTTING DOWN"))
                bot.disconnect()
                logging.info("graceful shutdown")
                break


if __name__ == '__main__':
    main()
