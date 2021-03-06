import os
from scvfeed.models import Rule, SFHorn, SFType, SFColor

rules = (
    Rule(name='HIGH SCORE PER BNB',
         type=SFType.ALL,
         min_score_per_bnb=7000),
    Rule(name='HIGH SCORE PER BNB',
         type=(SFType.RARE + SFType.BABY),
         min_score_per_bnb=5000),
    Rule(name='HIGH SCORE PER BNB',
         type=SFType.SUPER_RARE,
         min_score_per_bnb=2500),
    Rule(name='NICE COLOR',
         type=(SFType.SUPER_RARE + SFType.RARE),
         color=SFColor.SUPER_RARE,
         min_score_per_bnb=1500),
    Rule(name='GLITTER',
         glitter=True,
         type=(SFType.RARE + SFType.BABY),
         min_score_per_bnb=4000),
    Rule(name='GLITTER',
         glitter=True,
         type=SFType.SUPER_RARE,
         min_score_per_bnb=3000),
    Rule(name='GLITTER',
         glitter=True,
         color=(SFColor.RARE + SFColor.SUPER_RARE),
         min_score_per_bnb=3000),
    Rule(name='NICE HORN',
         horn=SFHorn.SUPER_RARE,
         color=SFColor.SUPER_RARE,
         min_score_per_bnb=3000),
    Rule(name='DIAMOND HORN',
         horn=SFHorn.DIAMOND,
         min_score_per_bnb=1000),
    Rule(name='ALL BLACKS',
         color=SFColor.BLACK,
         max_price_bnb=10),
    Rule(name='ONLY SPECIAL',
         special=True,
         max_price_bnb=15),
)

BSC_PROVIDER = os.getenv("BSC_PROVIDER", "wss://bsc-ws-node.nariox.org:443")
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = {
    'scvfeed': -1001597613597,
    'hihifeed': -1001532402384,
}
