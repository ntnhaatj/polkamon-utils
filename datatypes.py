from dataclasses import dataclass
from functools import reduce

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
    glitter: str
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
                .fromtimestamp(attributes['Birthday'], tz=pytz.timezone("Asia/Singapore"))
                .strftime('%Y-%m-%d %H:%M:%S'),
            color=attributes['Color'],
            horn=attributes['Horn'],
            type=attributes['Type'],
            glitter=attributes['Glitter'],
            special=(attributes['Special'] == 'Yes'))


@dataclass
class Metadata:
    id: str
    name: str
    image: str
    attributes: Attribute
    rarity: Rarity

    @classmethod
    def from_metadata(cls, metadata: dict):
        return cls(id=metadata['id'],
                   name=metadata['name'],
                   image=metadata['image'],
                   attributes=Attribute.from_metadata(metadata),
                   rarity=Rarity.from_metadata(metadata))

    @property
    def rarity_pct(self) -> float:
        if not self.attributes.special:
            rarity_fields = self.rarity.__dataclass_fields__.keys()
        else:
            rarity_fields = (
                f
                for f in self.rarity.__dataclass_fields__.keys()
                if f not in ['color', 'background']
            )

        return reduce(lambda r, k: r * getattr(self.rarity, k),
                      rarity_fields,
                      1)

    @property
    def rarity_score(self) -> int:
        return int(1 / self.rarity_pct / 40) if not self.attributes.special \
            else 'unsupported'
