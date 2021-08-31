import logging
import os
from collections import namedtuple

from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

from utils import (
    get_metadata,
    get_datatype_from_list,
    get_total_scores,
    get_leaderboard,
    get_share_on_score,
    get_weekly_birthday_snapshot,
)
from datatypes import Metadata, Color, Type, Horn, Glitter
from helpers import SCVFilterBuilder, OSFilterBuilder
from enum import Enum

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
    desc="SCV",
    url="https://scv.finance/nft/bsc/0x85F0e02cb992aa1F9F47112F815F519EF1A59E2D/{id}")
SCV_REF_URL = DescUrl(
    desc="SCV ref",
    url="https://scv.finance/nft/collection/polychain-monsters"
        "?meta_text_0={type}"
        "&meta_text_1={horn}"
        "&meta_text_2={color}"
        "&meta_text_5={glitter}"
        "&sort=price_asc")
OS_REF_URL = DescUrl(
    desc="OS ref",
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
  /help ID \- show help

This bot is open\-source, you can contribute it at [github link](https://github.com/ntnhaatj/polkamon-utils)

*Donate*
  ETH: {os.environ['DONATE_ADDR']}
  BSC: {os.environ['DONATE_ADDR']}
"""

HELP = f"""
Commands
  /mi <ID>  - monster info (birthday, score)
  /r <type> <color/horn> <color/horn> - get marketplace filter links
  /total    - get total collector staking scores
  /lb <to_rank (optional)>  - get leaderboard
  /rw <score> <pool_per_week>  - calculate reward per week
  /openstats  - open booster stats
"""

# https://core.telegram.org/bots/api#html-style
INFO_HTML_TEMPLATE = "<a href='{image}'>&#8205;</a>" \
                     "{ref_links}\n" \
                     "s: {score} | b: {birthday}"


def to_html(url_desc: DescUrl, **fmt_args):
    ref_link = url_desc.url.format(**fmt_args)
    return f"<a href='{ref_link}'>{url_desc.desc}</a>"


def get_ref_links(meta: Metadata) -> tuple:
    return (
       to_html(SCV_URL, id=meta.id),
    ) + tuple(map(lambda url: to_html(
        url,
        type=meta.attributes.type,
        horn=meta.attributes.horn,
        glitter=meta.attributes.glitter,
        color=meta.attributes.color), REF_URLS))


class PmonTokenomics(Enum):
    # NFT_STAKING_POOL = 0.25
    # STAKING_POOL = 0.15
    # BURNED = 0.5
    # DEVELOPMENT = 0.1
    NFT_STAKING_POOL = 0.20
    STAKING_POOL = 0
    BURNED = 0
    DEVELOPMENT = 0

    def to_pct(self):
        return f"{self.value * 100}%"


class BotHandlers:
    @staticmethod
    def start(update, context):
        update.message.reply_text(INTRODUCTION,
                                  parse_mode=ParseMode.MARKDOWN_V2,
                                  disable_web_page_preview=True)

    @staticmethod
    def help(update, context):
        update.message.reply_text(HELP)

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
                                      ref_links=" | ".join(get_ref_links(meta)),
                                      score=meta.rarity_score,
                                      birthday=meta.attributes.birthday),
            parse_mode=ParseMode.HTML)

    @staticmethod
    def get_ref_links(update, context):
        typ3, attrs_str = update.message.text.split(" ", 2)[1:]
        typ3 = Type.of(typ3)
        attrs = attrs_str.split(" ")
        horn = get_datatype_from_list(Horn, attrs)
        color = get_datatype_from_list(Color, attrs)
        glitter = get_datatype_from_list(Glitter, attrs)
        scv = SCVFilterBuilder(type=typ3, horn=horn, color=color, glitter=glitter)
        opensea = OSFilterBuilder(type=typ3, horn=horn, color=color, glitter=glitter)
        scv_url_html = to_html(DescUrl(desc="SCV", url=scv.url))
        os_url_html = to_html(DescUrl(desc="Opensea", url=opensea.url))
        update.message.reply_text(
            f"{scv.name}\n"
            f"{scv_url_html} | {os_url_html}",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True)

    @staticmethod
    def get_total_staking_score(update, context):
        total_scores = "{:,}".format(get_total_scores())
        update.message.reply_text(f"total staking scores: {total_scores}")

    @staticmethod
    def get_leaderboard(update, context):
        try:
            anchor_rank = int(update.message.text.split(" ")[-1])
        except ValueError:
            anchor_rank = 3

        try:
            leaderboard = get_leaderboard(anchor_rank)
            user_score_ranking = map(lambda u: f"{u['rank']}/"
                                               f" {u['username']}"
                                               f" - {'{:,}'.format(u['score'])}",
                                     leaderboard)
            update.message.reply_text('\n'.join(user_score_ranking))
        except NotImplementedError as e:
            update.message.reply_text(str(e))
            raise Exception from e

    @staticmethod
    def calc_reward(update, context):
        score, pool_per_week = map(lambda x: int(x), update.message.text.split(" ")[1:])
        share = get_share_on_score(score)
        update.message.reply_text("{:,} score gains "
                                  "{:.2f} $pmon per week "
                                  "(pool: {:,} $pmon)".format(
            score, pool_per_week * share, pool_per_week))

    @staticmethod
    def get_open_booster_stats(update, context):
        stats, total = get_weekly_birthday_snapshot()
        stats = sorted(stats, key=lambda k: k['value'])
        booster_stats = map(lambda s: "{}: {:,}".format(s['value'], int(int(s['count'])/3)), stats)
        total_booster = int(total / 3)
        update.message.reply_text(
            "Open booster from last snapshot:\n\n"
            "{}\n\n"
            "Total: {:,}\n"
            "NFT staking pool ({}): {:,}\n"
            "Staking pool ({}): {:,}\n"
            "Burned ({}): {:,}\n"
            "Development ({}): {:,}".format(
                "\n".join(booster_stats),
                total_booster,
                PmonTokenomics.NFT_STAKING_POOL.to_pct(),
                int(total_booster * PmonTokenomics.NFT_STAKING_POOL.value),
                PmonTokenomics.STAKING_POOL.to_pct(),
                int(total_booster * PmonTokenomics.STAKING_POOL.value),
                PmonTokenomics.BURNED.to_pct(),
                int(total_booster * PmonTokenomics.BURNED.value),
                PmonTokenomics.DEVELOPMENT.to_pct(),
                int(total_booster * PmonTokenomics.DEVELOPMENT.value),
            ))

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
    dp.add_handler(CommandHandler("help", BotHandlers.help))
    dp.add_handler(CommandHandler("mi", BotHandlers.info, pass_args=True))
    dp.add_handler(CommandHandler("r", BotHandlers.get_ref_links, pass_args=True))
    dp.add_handler(CommandHandler("total", BotHandlers.get_total_staking_score))
    dp.add_handler(CommandHandler("lb", BotHandlers.get_leaderboard))
    dp.add_handler(CommandHandler("rw", BotHandlers.calc_reward))
    dp.add_handler(CommandHandler("openstats", BotHandlers.get_open_booster_stats))

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
