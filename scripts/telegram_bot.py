import logging
import os

from utils import get_metadata, transform_displayed_info
from datatypes import Rarity, Attribute
from telegram.ext import Updater, CommandHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
INTRODUCTION = f"""
Hi! I'm Polychain monster helper bot!

Commands
  /mi <id> - monster info (birthday, score)

Donate:
  ETH: {os.environ['DONATE_ADDR']}
  BSC: {os.environ['DONATE_ADDR']}
"""


def start(update, context):
    update.message.reply_text(INTRODUCTION)


def info(update, context):
    try:
        pmon_id = update.message.text.split(" ")[-1]
        metadata = get_metadata(pmon_id)
        rarity = Rarity.from_metadata(metadata)
        attribute = Attribute.from_metadata(metadata)
        update.message.reply_text(transform_displayed_info({
            'Score': rarity.rarity_score,
            'Birthday': attribute.birthday
        }))
    except Exception:
        pass


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
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
