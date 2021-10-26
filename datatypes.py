from dataclasses import dataclass
from functools import reduce
from enum import Enum

from datetime import datetime
import pytz


@dataclass
class Rarity:
    horn: float
    color: float
    background: float
    glitter: float
    type: float

    @classmethod
    def from_metadata(cls, metadata: dict):
        rarity = metadata['initialProbabilities']
        return cls(horn=rarity['horn'],
                   color=rarity['color'],
                   background=rarity['background'],
                   glitter=rarity['glitter'],
                   type=rarity['type'])


@dataclass
class Attribute:
    birthday: str
    type: str
    horn: str
    color: str
    glitter: bool
    special: bool

    @classmethod
    def __array_to_dict(cls, attributes: list):
        attributes_dict = {
            attr['trait_type']: attr['value']
            for attr in attributes
        }
        return attributes_dict

    @classmethod
    def from_metadata(cls, metadata: dict):
        attributes = cls.__array_to_dict(metadata['attributes'])
        return cls(
            birthday=datetime
                .fromtimestamp(attributes['Birthday'], tz=pytz.timezone("Etc/GMT+7"))
                .strftime('%Y-%m-%d'),
            color=attributes['Color'],
            horn=attributes['Horn'],
            type=attributes['Type'],
            glitter=(attributes['Glitter'] == 'Yes'),
            special=(attributes['Special'] == 'Yes'))


RARITY_SCORE_MAX_CAP = 1_000_000


@dataclass
class Metadata:
    id: str
    name: str
    image: str
    attributes: Attribute
    rarity: Rarity

    @classmethod
    def from_metadata(cls, metadata: dict):
        try:
            rarity = Rarity.from_metadata(metadata)
        except KeyError:
            # Colchian Unidragon
            rarity = Rarity(horn=0, color=0, background=0, glitter=0, type=0)

        return cls(id=metadata['id'],
                   name=metadata['name'],
                   image=metadata['image'],
                   attributes=Attribute.from_metadata(metadata),
                   rarity=rarity)

    @property
    def rarity_score(self) -> float:
        if not self.attributes.special:
            rarity_fields = (
                f
                for f in self.rarity.__dataclass_fields__.keys()
                if f not in ['background']
            )
        else:
            rarity_fields = (
                f
                for f in self.rarity.__dataclass_fields__.keys()
                if f not in ['color', 'background']
            )
        if self.attributes.special:
            try:
                rarity_score = reduce(lambda r, k: r * ((1 / getattr(self.rarity, k) - 1) / 8 + 1),
                                      rarity_fields,
                                      1) * 40
            except ArithmeticError:
                rarity_score = 0
        else:
            rarity_score = reduce(lambda r, k: r * (1 / getattr(self.rarity, k)),
                                  rarity_fields,
                                  1) * 0.0325
            if self.attributes.horn == Horn.BABY_HORN.value:
                rarity_score = rarity_score * 5  # 20% spiral horn

        return min(RARITY_SCORE_MAX_CAP, int(rarity_score))


class Traits(Enum):
    @classmethod
    def of(cls, i: str):
        for mem in cls.__members__.values():
            if i in mem.value or i in mem.value.lower().replace(" ", ""):
                return mem
        raise NotImplementedError(f"not found {i}")

    def __str__(self):
        return self.value


class Type(Traits):
    DONKEY = "Unidonkey"
    SHEEP = "Unisheep"
    CHICK = "Unichick"
    FAIRY = "Unifairy"
    CURSED = "Unicursed"
    TURTLE = "Uniturtle"
    AIR = "Uniair"
    KLES = "Unikles"
    BRANCH = "Unibranch"
    AQUA = "Uniaqua"
    DRAGON = "Unidragon"
    BABY_DONKEY = "Baby Unidonkey"
    BABY_SHEEP = "Baby Unisheep"
    BABY_CHICK = "Baby Unichick"
    BABY_FAIRY = "Baby Unifairy"
    BABY_CURSED = "Baby Unicursed"
    BABY_TURTLE = "Baby Uniturtle"
    BABY_AIR = "Baby Uniair"
    BABY_KLES = "Baby Unikles"
    BABY_BRANCH = "Baby Unibranch"
    BABY_AQUA = "Baby Uniaqua"
    BABY_DRAGON = "Baby Unidragon"


class Color(Traits):
    GREEN = "Green"
    BLUE = "Blue"
    RED = "Red"
    YELLOW = "Yellow"
    PURPLE = "Purple"
    BLACK = "Black"


class Horn(Traits):
    BABY_HORN = "Baby Horn"
    CANDY_CANE = "Candy Cane"
    DIAMOND_SPEAR = "Diamond Spear"
    DRAGON_CLAW = "Dragon Claw"
    GOLDEN_HORN = "Golden Horn"
    IVORY_FANG = "Ivory Fang"
    SHADOW_BRANCH = "Shadow Branch"
    SILVER_CLAW = "Silver Claw"
    SILVER_EDGE = "Silver Edge"
    SPIRAL_HORN = "Spiral Horn"
    WICKED_SPEAR = "Wicked Spear"


class Glitter(Traits):
    YES = "Yes"
    NO = "No"

    @classmethod
    def of(cls, i):
        if isinstance(i, bool):
            return cls.YES if i else cls.NO

        if isinstance(i, str):
            return cls.YES if i and (i in "glitter" or i in "Glitter") else cls.NO

        return cls.NO

    def __str__(self):
        return "Glitter" if self == Glitter.YES else ""
