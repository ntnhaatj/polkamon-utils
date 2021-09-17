from typing import Iterable
import os
import logging
import time
import requests
import backoff
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from datatypes import Metadata, Type, Horn, Color, Glitter
from utils import get_metadata
from helpers import SCVFilterBuilder
import scvfeed.config as config
from scvfeed.models import Rule
from scvfeed.blocksearch import OfferInfo
from scvfeed.exceptions import FilterNotFoundError
from scvfeed.blocksearch import ScvBlockSearch

# Enable logging
log_filename = datetime.now().strftime('log/scvfeed_%Y%m%d.log')
logging.basicConfig(format='%(asctime)s - {%(filename)s:%(lineno)d} - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename=log_filename,
                    filemode='a+')
logger = logging.getLogger(__name__)

BOT_INTRO_TEMPLATE = "Start earning money mode\n" \
                 "Tracking configuration:\n- {}".format("\n- ".join(map(lambda r: str(r), config.rules)))


def get_color_by_spb(spb: int) -> str:
    if spb < 6000:
        return "🟢"
    elif spb < 9000:
        return "🔵"
    elif spb < 12000:
        return "🟡"
    else:
        return "🟣"


def get_scv_ref(meta: Metadata):
    scv_link = ''
    try:
        scv_link = SCVFilterBuilder(
            type=Type.of(meta.attributes.type),
            horn=Horn.of(meta.attributes.horn),
            color=Color.of(meta.attributes.color),
            glitter=Glitter.of(meta.attributes.glitter)
        ).url
    except Exception as e:
        pass
    return scv_link.replace(" ", "%20")


# https://core.telegram.org/bots/api#html-style
def to_html(meta, price, score, matched_rule: Rule):
    score_per_bnb = int(score / price * 1E18)
    url = f"https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/{meta.id}"
    desc = "{} <b>{:.3f}</> BNB\n" \
           "<b>SPB {} {:,}</b>\n" \
           "Score: {:,}".format(
        meta.name, price / 1E18, get_color_by_spb(score_per_bnb), score_per_bnb, score)
    scv_ref = get_scv_ref(meta)
    msg = f"<a href='{meta.image}'>.</a>" \
          f"{desc}\n" \
          f"{url}\n" \
          f"========================\n" \
          f"{scv_ref}"
    return msg


@backoff.on_exception(backoff.constant,
                      exception=(requests.exceptions.RequestException,
                                 requests.exceptions.ConnectTimeout),
                      max_tries=2)
def send_msg(msg):
    params = {
        'chat_id': config.TELEGRAM_CHAT_ID[os.getenv("TID", "scvfeed")],
        'text': msg,
        'parse_mode': 'html'
    }
    requests.get("https://api.telegram.org/bot{}/sendMessage".format(
        config.TELEGRAM_BOT_TOKEN), timeout=2, params=params)


class ScvFeed:
    def __init__(self):
        self.scv_block_search = ScvBlockSearch(config.BSC_WS_PROVIDER)

    def reconnect(self):
        logger.info("reconnecting...")
        self.scv_block_search = ScvBlockSearch(config.BSC_WS_PROVIDER)

    @classmethod
    def get_matched_rule(
            cls, price: int, metadata: Metadata, rul3s: Iterable[Rule]) -> Rule:
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

    @classmethod
    def handle_sell_offer(cls, sell_offer: OfferInfo):
        meta = Metadata.from_metadata(get_metadata(str(sell_offer.token_id)))
        matched_rule = cls.get_matched_rule(sell_offer.price, meta, config.rules)
        if matched_rule:
            msg = to_html(meta, sell_offer.price, meta.rarity_score, matched_rule)
            send_msg(msg)
        return meta, sell_offer, matched_rule

    def run(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            while True:
                try:
                    time.sleep(0.5)
                    executor.map(self.handle_sell_offer,
                                 self.scv_block_search.get_sell_event())

                except FilterNotFoundError:
                    self.reconnect()
                    continue

                except KeyboardInterrupt as e:
                    raise KeyboardInterrupt from e

                except Exception as e:
                    logger.exception(str(e))
                    continue


if __name__ == '__main__':
    send_msg(BOT_INTRO_TEMPLATE)
    scv_feed_app = ScvFeed()
    try:
        scv_feed_app.run()
    except KeyboardInterrupt as exc:
        logging.exception(str(exc))
        logging.info("graceful shutdown")
    finally:
        send_msg(f"BOT IS SHUTTING DOWN...")
