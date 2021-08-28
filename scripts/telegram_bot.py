import logging
import os

from utils import get_metadata, transform_displayed_info
from datatypes import Metadata
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

PRODUCTION = os.environ.get('PRODUCTION', False)

# telegram configurations
WEBHOOK_PORT = int(os.environ.get('PORT', '8443'))
APP_NAME = os.environ.get('APP_NAME', 'https://pmon-helper.herokuapp.com/')
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']

SCV_DOMAIN = "https://scv.finance/nft/"
SCV_URL = SCV_DOMAIN + "bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/{id}"
SCV_REF_URL = SCV_DOMAIN + "collection/polychain-monsters" \
                           "?meta_text_0={name}" \
                           "&meta_text_1={horn}" \
                           "&meta_text_2={color}" \
                           "&sort=price_asc"

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
INFO_TEMPLATE = "<a href='{image}'>&#8205;</a>" \
                "<a href='{scv_link}'>SCV link</a> | " \
                "<a href='{ref_link}'>Ref prices</a>\n" \
                "score: {score} | birthday: {birthday}"


def start(update, context):
    update.message.reply_text(INTRODUCTION, parse_mode=ParseMode.MARKDOWN_V2)


def info(update, context):
    try:
        pmon_id = update.message.text.split(" ")[-1]
        metadata = get_metadata(pmon_id)
        meta = Metadata.from_metadata(metadata)
    except Exception as e:
        update.message.reply_text(f"Invalid {update.message.text}")
        raise Exception from e

    update.message.reply_text(
        INFO_TEMPLATE.format(image=meta.image,
                             scv_link=SCV_URL.format(id=pmon_id),
                             ref_link=SCV_REF_URL.format(
                                 name=meta.attributes.type,
                                 horn=meta.attributes.horn,
                                 color=meta.attributes.color),
                             score=meta.rarity_score,
                             birthday=meta.attributes.birthday),
        parse_mode=ParseMode.HTML
    )


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
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("mi", info, pass_args=True))

    # log all errors
    dp.add_error_handler(error)

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
