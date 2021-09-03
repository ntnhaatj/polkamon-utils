from datatypes import Metadata
import unittest
from scripts.scv_feed_new import get_matched_rule
from scvfeed.models import Rule, ScvFeedType
import sys
import logging

if len(sys.argv) > 1 and sys.argv[1] == 'test':
    logging.disable(logging.CRITICAL)


class RulesTest(unittest.TestCase):
    def test_worth_buying_high_score_per_bnb(self):
        rules = (
            Rule(name='HIGH SCORE PER BNB',
                 max_price_bnb=20,
                 min_score_per_bnb=5000),
        )
        meta = Metadata.from_metadata({"id": "10001290268",
                                       "image": "",
                                       "name": "Uniturtle",
                                       "initialProbabilities": {"horn": 0.05, "color": 0.05, "background": 1,
                                                                "glitter": 0.01, "type": 0.06},
                                       "attributes": [{"trait_type": "Type", "value": "Uniturtle"},
                                                      {"trait_type": "Horn", "value": "Shadow Branch"},
                                                      {"trait_type": "Color", "value": "Purple"},
                                                      {"trait_type": "Background", "value": "Mountain Range"},
                                                      {"trait_type": "Opening Network", "value": "Binance Smart Chain"},
                                                      {"trait_type": "Glitter", "value": "Yes"},
                                                      {"trait_type": "Special", "value": "No"},
                                                      {"display_type": "date", "trait_type": "Birthday",
                                                       "value": 1630614938},
                                                      {"display_type": "number", "trait_type": "Booster",
                                                       "value": 10000000430090}]})
        matched_rule = get_matched_rule(int(1E18), meta, rules)
        assert matched_rule != None
        assert matched_rule.name == 'HIGH SCORE PER BNB'

    def test_worth_buying_glitter_rare(self):
        rules = (
            Rule(name='HIGH SCORE PER BNB',
                 max_price_bnb=20,
                 min_score_per_bnb=10000),
            Rule(name='ONLY SPECIAL',
                 special=True,
                 max_price_bnb=20),
            Rule(name='GLITTER RARE',
                 glitter=True,
                 type=ScvFeedType.RARE,
                 max_price_bnb=20,
                 min_score_per_bnb=4000)
        )
        meta = Metadata.from_metadata({"id": "10001290268",
                                       "image": "",
                                       "name": "Uniturtle",
                                       "initialProbabilities": {"horn": 0.05, "color": 0.05, "background": 1,
                                                                "glitter": 0.01, "type": 0.06},
                                       "attributes": [{"trait_type": "Type", "value": "Uniturtle"},
                                                      {"trait_type": "Horn", "value": "Shadow Branch"},
                                                      {"trait_type": "Color", "value": "Purple"},
                                                      {"trait_type": "Background", "value": "Mountain Range"},
                                                      {"trait_type": "Opening Network", "value": "Binance Smart Chain"},
                                                      {"trait_type": "Glitter", "value": "Yes"},
                                                      {"trait_type": "Special", "value": "No"},
                                                      {"display_type": "date", "trait_type": "Birthday",
                                                       "value": 1630614938},
                                                      {"display_type": "number", "trait_type": "Booster",
                                                       "value": 10000000430090}]})
        matched_rule = get_matched_rule(2*int(1E18), meta, rules)
        assert matched_rule != None
        assert matched_rule.name == 'GLITTER RARE'
