from scvfeed.models import Rule, ScvFeedHorn, ScvFeedType, ScvFeedColor

rules = (
    Rule(name='HIGH SCORE PER BNB',
         max_price_bnb=20,
         min_score_per_bnb=5000),
    Rule(name='ONLY SPECIAL',
         special=True,
         max_price_bnb=20),
    Rule(name='RARE COLOR HIGH SPB',
         color=ScvFeedColor.RARE,
         max_price_bnb=20,
         min_score_per_bnb=3000),
    Rule(name='ALL BLACKS',
         color=ScvFeedColor.SUPER_RARE,
         max_price_bnb=20),
    Rule(name='GLITTER RARE',
         glitter=True,
         type=ScvFeedType.RARE,
         max_price_bnb=20,
         min_score_per_bnb=4000),
    Rule(name='GLITTER SUPER RARE',
         glitter=True,
         type=ScvFeedType.SUPER_RARE,
         max_price_bnb=20,
         min_score_per_bnb=3000),
    Rule(name='SR-HORN RARE',
         type=ScvFeedType.RARE,
         horn=ScvFeedHorn.SUPER_RARE,
         max_price_bnb=20,
         min_score_per_bnb=2000),
    Rule(name='SR-HORN SUPER RARE',
         type=ScvFeedType.SUPER_RARE,
         horn=ScvFeedHorn.SUPER_RARE,
         max_price_bnb=20,
         min_score_per_bnb=1000),
    Rule(name='SR BABY',
         type=ScvFeedType.BABY_SUPER_RARE,
         max_price_bnb=20,
         min_score_per_bnb=1000),
    Rule(name='GLITTER SR BABY',
         type=ScvFeedType.BABY_SUPER_RARE,
         glitter=True,
         max_price_bnb=20,
         min_score_per_bnb=500)
)
