from dataclasses import dataclass
from enum import Enum
from datatypes import Type, Color, Horn, Metadata


class ScvFeedType(Enum):
    ALL = ()
    RARE = (Type.BRANCH, Type.TURTLE, Type.AIR, Type.KLES)
    SUPER_RARE = (Type.DRAGON, Type.AQUA)
    BABY_SUPER_RARE = (Type.BABY_AQUA, Type.BABY_BRANCH, Type.BABY_CHICK, Type.BABY_FAIRY,)
    CUSTOM = (Type.DRAGON, )

    @classmethod
    def of(cls, i: str):
        for k in cls.__members__.keys():
            if i == k or i == k.lower():
                return cls[k]
        raise NotImplementedError


class ScvFeedColor(Enum):
    ALL = ()
    RARE = (Color.YELLOW, Color.PURPLE)
    SUPER_RARE = (Color.BLACK,)

    @classmethod
    def of(cls, i: str):
        for k in cls.__members__.keys():
            if i == k or i == k.lower():
                return cls[k]
        raise NotImplementedError


class ScvFeedHorn(Enum):
    ALL = ()
    RARE = (Horn.DIAMOND_SPEAR, Horn.WICKED_SPEAR, Horn.IVORY_FANG, Horn.DRAGON_CLAW, Horn.SILVER_CLAW)
    SUPER_RARE = (Horn.DIAMOND_SPEAR, Horn.WICKED_SPEAR, Horn.IVORY_FANG)

    @classmethod
    def of(cls, i: str):
        for k in cls.__members__.keys():
            if i == k or i == k.lower():
                return cls[k]
        raise NotImplementedError


@dataclass
class Rule:
    name: str
    special: bool = None
    type: ScvFeedType = None
    color: ScvFeedColor = None
    horn: ScvFeedHorn = None
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
                and (Type.of(metadata.attributes.type) in self.type.value if self.type is not None else True)
                and (Horn.of(metadata.attributes.horn) in self.horn.value if self.horn is not None else True)
                and (Color.of(metadata.attributes.color) in self.color.value if self.color is not None else True))

    def __str__(self):
        filtered_rules = (
            f"{a}={getattr(self, a)}"
            for a in self.__dataclass_fields__.keys()
            if getattr(self, a) is not None
        )
        return ", ".join(filtered_rules)


@dataclass
class IgnoreRule:
    name: str
    special: bool = None
    max_price_bnb_threshold: int = None
    min_score_per_bnb_threshold: int = None

    def should_ignore(self, price_in_bnb: float, metadata: Metadata) -> bool:
        score = metadata.rarity_score
        score_per_bnb = score / price_in_bnb
        return ((score_per_bnb < self.min_score_per_bnb_threshold if self.min_score_per_bnb_threshold is not None else True)
                and (price_in_bnb > self.max_price_bnb_threshold if self.max_price_bnb_threshold is not None else True)
                and (metadata.attributes.special == self.special if self.special is not None else True))

    def __str__(self):
        filtered_rules = (
            f"{a}={getattr(self, a)}"
            for a in self.__dataclass_fields__.keys()
            if getattr(self, a) is not None
        )
        return ", ".join(filtered_rules)
