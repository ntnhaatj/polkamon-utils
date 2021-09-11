from dataclasses import dataclass
from datatypes import Type, Color, Horn, Metadata


class SFType:
    ALL = ()
    RARE = (Type.TURTLE, Type.AIR, Type.KLES, )
    SUPER_RARE = (Type.DRAGON, Type.AQUA, Type.BRANCH,)
    BABY = (Type.BABY_AQUA, Type.BABY_BRANCH, Type.BABY_CHICK, Type.BABY_FAIRY,)


class SFColor:
    ALL = ()
    RARE = (Color.YELLOW, )
    SUPER_RARE = (Color.BLACK, Color.PURPLE)
    BLACK = (Color.BLACK,)


class SFHorn:
    ALL = ()
    RARE = (Horn.DIAMOND_SPEAR, Horn.WICKED_SPEAR, Horn.IVORY_FANG, Horn.DRAGON_CLAW, Horn.SILVER_CLAW)
    SUPER_RARE = (Horn.WICKED_SPEAR, Horn.IVORY_FANG)
    DIAMOND = (Horn.DIAMOND_SPEAR, )


@dataclass
class Rule:
    name: str
    special: bool = None
    type: SFType = None
    color: SFColor = None
    horn: SFHorn = None
    glitter: bool = None
    max_price_bnb: int = None
    min_score_per_bnb: int = None

    def is_worth_buying(self, price_in_bnb: float, metadata: Metadata) -> bool:
        score = metadata.rarity_score
        score_per_bnb = score / price_in_bnb
        return ((score_per_bnb > self.min_score_per_bnb if self.min_score_per_bnb is not None else True)
                and (price_in_bnb < self.max_price_bnb if self.max_price_bnb is not None else True)
                and (metadata.attributes.special == self.special if self.special is not None else True)
                and (metadata.attributes.glitter == self.glitter if self.glitter is not None else True)
                # could raise exception
                and (Type.of(metadata.attributes.type) in self.type if self.type else True)
                and (Horn.of(metadata.attributes.horn) in self.horn if self.horn else True)
                and (Color.of(metadata.attributes.color) in self.color if self.color else True))

    def __str__(self):
        filtered_rules = (
            f"{a}={getattr(self, a)}"
            for a in self.__dataclass_fields__.keys()
            if getattr(self, a) is not None
        )
        return ", ".join(filtered_rules)
