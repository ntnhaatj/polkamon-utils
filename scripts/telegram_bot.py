import logging
import os
from collections import namedtuple

from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

from utils import get_metadata
from datatypes import Metadata

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

PRODUCTION = os.environ.get('PRODUCTION', False)

# telegram configurations
WEBHOOK_PORT = int(os.environ.get('PORT', '8443'))
APP_NAME = os.environ.get('APP_NAME', 'https://pmon-helper.herokuapp.com/')
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']

# url with desc
DescUrl = namedtuple('DescUrl', ('desc', 'url'))
SCV_URL = DescUrl(
    desc="SCV link",
    url="https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/{id}")
SCV_REF_URL = DescUrl(
    desc="SCV ref prices",
    url="https://scv.finance/nft/collection/polychain-monsters"
        "?meta_text_0={type}"
        "&meta_text_1={horn}"
        "&meta_text_2={color}"
        "&meta_text_5={glitter}"
        "&sort=price_asc")
OS_REF_URL = DescUrl(
    desc="OS ref prices",
    url="https://opensea.io/collection/polychainmonsters"
        "?search[resultModel]=ASSETS"
        "&search[sortAscending]=true"
        "&search[sortBy]=PRICE"
        "&search[stringTraits][0][name]=Horn"
        "&search[stringTraits][0][values][0]={horn}"
        "&search[stringTraits][1][name]=Glitter"
        "&search[stringTraits][1][values][0]={glitter}"
        "&search[stringTraits][2][name]=Color"
        "&search[stringTraits][2][values][0]={color}"
        "&search[stringTraits][3][name]=Type"
        "&search[stringTraits][3][values][0]={type}")

REF_URLS = (SCV_REF_URL, OS_REF_URL,)

# https://core.telegram.org/bots/api#markdown-style
INTRODUCTION = f"""
Hi\! I'm Polychain monster helper bot\!

*Commands*
  /mi ID \- monster info \(birthday, score\)

This bot is open\-source, you can contribute it at [github link](https://github.com/ntnhaatj/polkamon-utils)

*Donate*
  ETH: {os.environ['DONATE_ADDR']}
  BSC: {os.environ['DONATE_ADDR']}
"""

# https://core.telegram.org/bots/api#html-style
INFO_HTML_TEMPLATE = "<a href='{image}'>&#8205;</a>" \
                     "{ref_links}\n" \
                     "score: {score}   |   birthday: {birthday}"


def get_ref_links(meta: Metadata) -> tuple:
    def gen_ref_links_v2(url_desc: DescUrl, **fmt_args):
        ref_link = url_desc.url.format(**fmt_args)
        return f"<a href='{ref_link}'>{url_desc.desc}</a>"

    return (
       gen_ref_links_v2(SCV_URL, id=meta.id),
    ) + tuple(map(lambda url: gen_ref_links_v2(
        url,
        type=meta.attributes.type,
        horn=meta.attributes.horn,
        glitter=meta.attributes.glitter,
        color=meta.attributes.color), REF_URLS))


class BotHandlers:
    @staticmethod
    def start(update, context):
        update.message.reply_text(INTRODUCTION, parse_mode=ParseMode.MARKDOWN_V2)

    @staticmethod
    def info(update, context):
        try:
            pmon_id = update.message.text.split(" ")[-1]
            metadata = get_metadata(pmon_id)
            meta = Metadata.from_metadata(metadata)
        except Exception as e:
            update.message.reply_text(f"Invalid {update.message.text}")
            raise Exception from e

        update.message.reply_text(
            INFO_HTML_TEMPLATE.format(image=meta.image,
                                      ref_links="   |   ".join(get_ref_links(meta)),
                                      score=meta.rarity_score,
                                      birthday=meta.attributes.birthday),
            parse_mode=ParseMode.HTML)

    @staticmethod
    def error(update, context):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", BotHandlers.start))
    dp.add_handler(CommandHandler("mi", BotHandlers.info, pass_args=True))

    # log all errors
    dp.add_error_handler(BotHandlers.error)

    # Start the Bot
    if PRODUCTION:
        updater.start_webhook(listen="0.0.0.0",
                              port=WEBHOOK_PORT,
                              url_path=TELEGRAM_BOT_TOKEN,
                              webhook_url=APP_NAME + TELEGRAM_BOT_TOKEN)
    else:
        # Start the Bot
        updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
