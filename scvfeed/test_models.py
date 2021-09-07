from datatypes import Metadata
import unittest
from scripts.scv_feed import get_matched_rule
from scvfeed.models import Rule, SFType, SFColor
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
                 type=SFType.RARE,
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
        matched_rule = get_matched_rule(2 * int(1E18), meta, rules)
        assert matched_rule != None
        assert matched_rule.name == 'GLITTER RARE'

    def test_worth_buying_black(self):
        rules = (
            Rule(name='HIGH SCORE PER BNB',
                 max_price_bnb=20,
                 min_score_per_bnb=5000),
            Rule(name='ONLY SPECIAL',
                 special=True,
                 max_price_bnb=20),
            Rule(name='RARE COLOR HIGH SPB',
                 color=SFColor.RARE,
                 max_price_bnb=20,
                 min_score_per_bnb=3000),
            Rule(name='ALL BLACKS',
                 color=SFColor.SUPER_RARE,
                 max_price_bnb=20),
            Rule(name='GLITTER RARE',
                 glitter=True,
                 type=SFType.RARE,
                 max_price_bnb=20,
                 min_score_per_bnb=4000)
        )
        meta = Metadata.from_metadata({"boosterId": 10000000388986, "id": "10001166957",
                                       "image": "https://assets.polkamon.com/images/Unimons_T05C06H06B04G00.jpg",
                                       "name": "Unikles",
                                       "initialProbabilities": {"horn": 0.2, "color": 0.0005, "background": 1,
                                                                "glitter": 0.99, "type": 0.06},
                                       "attributes": [{"trait_type": "Type", "value": "Unikles"},
                                                      {"trait_type": "Horn", "value": "Spiral Horn"},
                                                      {"trait_type": "Color", "value": "Black"},
                                                      {"trait_type": "Background", "value": "Mountain Range"},
                                                      {"trait_type": "Opening Network", "value": "Binance Smart Chain"},
                                                      {"trait_type": "Glitter", "value": "No"},
                                                      {"trait_type": "Special", "value": "No"},
                                                      {"display_type": "date", "trait_type": "Birthday",
                                                       "value": 1630438738},
                                                      {"display_type": "number", "trait_type": "Booster",
                                                       "value": 10000000388986}]})
        matched_rule = get_matched_rule(int(3.95 * 1E18), meta, rules)
        assert matched_rule != None
        assert matched_rule.name == 'ALL BLACKS'

    def test_worth_buying_baby_glitter(self):
        rules = (
            Rule(name='GLITTER SR BABY',
                 type=SFType.BABY_SUPER_RARE,
                 glitter=True,
                 max_price_bnb=20,
                 min_score_per_bnb=500),
        )
        meta = Metadata.from_metadata({"id": "10001336587",
                                       "image": "https://assets.polkamon.com/images/Unimons_T17C04H01B05G01.jpg",
                                       "name": "Baby Unichick",
                                       "initialProbabilities": {"horn": 1, "color": 0.05, "background": 1,
                                                                "glitter": 0.01, "type": 0.015},
                                       "attributes": [{"trait_type": "Type", "value": "Baby Unichick"},
                                                      {"trait_type": "Horn", "value": "Baby Horn"},
                                                      {"trait_type": "Color", "value": "Purple"},
                                                      {"trait_type": "Background", "value": "Green Gardens"},
                                                      {"trait_type": "Opening Network", "value": "Binance Smart Chain"},
                                                      {"trait_type": "Glitter", "value": "Yes"},
                                                      {"trait_type": "Special", "value": "No"},
                                                      {"display_type": "date", "trait_type": "Birthday",
                                                       "value": 1630667240},
                                                      {"display_type": "number", "trait_type": "Booster",
                                                       "value": 10000000445529}]})
        matched_rule = get_matched_rule(int(5.5 * 1E18), meta, rules)
        assert matched_rule != None
        assert matched_rule.name == 'GLITTER SR BABY'

    def test_worth_buying_glitter_rare(self):
        rules = (
            Rule(name='GLITTER RARE',
                 glitter=True,
                 type=SFType.RARE,
                 max_price_bnb=20,
                 min_score_per_bnb=4000),
        )
        meta = Metadata.from_metadata({"boosterId": 10000000440771, "id": "10001322311",
                                       "image": "https://assets.polkamon.com/images/Unimons_T04C05H08B04G01.jpg",
                                       "name": "Uniturtle",
                                       "initialProbabilities": {"horn": 0.16, "color": 0.2, "background": 1,
                                                                "glitter": 0.01, "type": 0.06},
                                       "attributes": [{"trait_type": "Type", "value": "Uniturtle"},
                                                      {"trait_type": "Horn", "value": "Candy Cane"},
                                                      {"trait_type": "Color", "value": "Red"},
                                                      {"trait_type": "Background", "value": "Mountain Range"},
                                                      {"trait_type": "Opening Network", "value": "Binance Smart Chain"},
                                                      {"trait_type": "Glitter", "value": "Yes"},
                                                      {"trait_type": "Special", "value": "No"},
                                                      {"display_type": "date", "trait_type": "Birthday",
                                                       "value": 1630645436},
                                                      {"display_type": "number", "trait_type": "Booster",
                                                       "value": 10000000440771}]})
        matched_rule = get_matched_rule(int(0.1 * 1E18), meta, rules)
        assert matched_rule != None
        assert matched_rule.name == 'GLITTER RARE'

    def test_(self):
        from scvfeed.config import rules
        meta = Metadata.from_metadata({"boosterId": 10000000396048, "id": "10001188144",
                                       "txHash": "0x3294acafdef60787efe58770fb82cb99cece3235f6c4096abcc4b509f6cd9d87",
                                       "randomNumber": "0x4b344c081024b20a4b961a7d29ca16be2742fd825b47a558254da23df32a154f",
                                       "image": "https://assets.polkamon.com/images/Unimons_T12C05H01B05G00.jpg",
                                       "external_url": "https://polkamon.com/polkamon/T12C05H01B05G00",
                                       "description": "Said to be born from magic, the Baby Unifairy belongs to the most wonderful and enchanting family of Polymon. Before growing the majestic wings of their parents, these babies thrive in a tranquil environment where they can hone their magical abilities in peace.",
                                       "name": "Baby Unifairy",
                                       "initialProbabilities": {"horn": 1, "color": 0.2, "background": 1,
                                                                "glitter": 0.99, "type": 0.015},
                                       "attributes": [{"trait_type": "Type", "value": "Baby Unifairy"},
                                                      {"trait_type": "Horn", "value": "Baby Horn"},
                                                      {"trait_type": "Color", "value": "Red"},
                                                      {"trait_type": "Background", "value": "Green Gardens"},
                                                      {"trait_type": "Opening Network", "value": "Binance Smart Chain"},
                                                      {"trait_type": "Glitter", "value": "No"},
                                                      {"trait_type": "Special", "value": "No"},
                                                      {"display_type": "date", "trait_type": "Birthday",
                                                       "value": 1630481910},
                                                      {"display_type": "number", "trait_type": "Booster",
                                                       "value": 10000000396048}],
                                       "opening_network": "Binance Smart Chain", "background_color": "FFFFFF",
                                       "animation_url": "https://assets.polkamon.com/videos/Unimons_T12C05H01B05G00.mp4"})
        matched_rule = get_matched_rule(int(0.1 * 1E18), meta, rules)
        print(matched_rule)

    def test_should_ignore_high_price(self):
        rules = (
            Rule(name='GLITTER RARE',
                 glitter=True,
                 type=SFType.RARE,
                 max_price_bnb=20,
                 min_score_per_bnb=4000),
        )
        meta = Metadata.from_metadata({"boosterId": 10000000440771, "id": "10001322311",
                                       "image": "https://assets.polkamon.com/images/Unimons_T04C05H08B04G01.jpg",
                                       "name": "Uniturtle",
                                       "initialProbabilities": {"horn": 0.16, "color": 0.2, "background": 1,
                                                                "glitter": 0.01, "type": 0.06},
                                       "attributes": [{"trait_type": "Type", "value": "Uniturtle"},
                                                      {"trait_type": "Horn", "value": "Candy Cane"},
                                                      {"trait_type": "Color", "value": "Red"},
                                                      {"trait_type": "Background", "value": "Mountain Range"},
                                                      {"trait_type": "Opening Network", "value": "Binance Smart Chain"},
                                                      {"trait_type": "Glitter", "value": "Yes"},
                                                      {"trait_type": "Special", "value": "No"},
                                                      {"display_type": "date", "trait_type": "Birthday",
                                                       "value": 1630645436},
                                                      {"display_type": "number", "trait_type": "Booster",
                                                       "value": 10000000440771}]})
        matched_rule = get_matched_rule(int(40 * 1E18), meta, rules)
        assert matched_rule != None
        assert matched_rule.name == 'GLITTER RARE'
